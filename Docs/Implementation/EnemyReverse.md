# Enemy reverse integration

Implemented and verified in UE 5.6 on 2026-09-26, against recovery commit `63d0a5d`.

## Runtime architecture

The existing player `IA_Reverse` action (Q), `BP_ReverseSystemController`, and global manager remain the entry point. Both enemy Blueprints now own an `EnemyReverse` component. Their existing parents, controllers, normal animation Blueprints, and weapon assets remain in use.

| Asset | Responsibility |
| --- | --- |
| `/Game/Blueprints/TimeReverse/Enemies/BPI_RewindableEnemy` | `ReadRewindHealth`, `WriteRewindHealth`, `SetRewindActive`; separates enemy-specific health/combat handling from history playback. |
| `/Game/Blueprints/TimeReverse/Enemies/AC_EnemyReverse` | Extends the existing reverse base; records and restores actor transform, health, evaluated skeletal pose, mesh world transform and velocity on the same sampling/index lifecycle. |
| `/Game/Animations/TimeReverse/ABP_EnemyRewind_Melee` | Pose Snapshot playback for the melee enemy's skeleton. |
| `/Game/Animations/TimeReverse/ABP_EnemyRewind_Shooter` | Pose Snapshot playback for the ranged enemy's skeleton. |

The component uses the existing global history settings. Map_Test tests observed 50 samples/second and 250 retained frames, approximately five seconds. Health history and current restored health use floating-point values.

On rewind entry, the component stops AI logic, path movement and shooting; disables live skeletal physics, movement and actor collision; and switches the mesh to its pose playback AnimBP. It writes health directly through the interface rather than replaying damage events. Combat entry points ignore attacks/damage during rewind.

On a living rewind exit, it restores mesh attachment, normal AnimBP, collision profiles and movement velocity, then restarts AI decisions. The current enemies resume in Walking movement mode. Perception is refreshed after restart: the Shooter StateTree's sensing task binds perception events again, and a stale perception cache otherwise prevents reacquiring an already visible player.

On a dead rewind exit, AI stays stopped and the recorded death pose stays frozen. Another rewind can still reach a living frame. Once recording has evicted every living frame, deferred actor destruction allows normal owner/controller/weapon cleanup. `AliveFrameCount` is updated together with recording and trimming, including discarded future frames.

## Existing assets adapted

- `Blueprints/AI/Melee/BP_MeleeNPC`: interface implementation, actual `Health` access, health-widget restoration, transient combat flag reset, rewind damage guard, component attachment. Death hides rather than destroys the health widget.
- `Blueprints/AI/Shooter/BP_ShooterNPC`: interface implementation, actual `Current HP` access, stop-shooting adapter, rewind guards, component attachment. Immediate/deferred destruction from the original death chain is replaced by history-aware cleanup.
- `Blueprints/AI/Shooter/BP_ShooterAIController`: keeps possession/controller through reversible death.
- `Blueprints/AI/AC_Combat`: guards melee combat and delayed movement callbacks during rewind; defers despawn to the rewind component for supported owners. Owners without this component retain their existing behavior.

Do not additionally attach the original `BP_ReverseStatusComponent` or `BP_ReverseAnimMontageComponent` to these enemies: those components assume the demo enemy type. The new component already owns these channels.

## Extending another enemy

1. Implement the three interface functions against its real health storage. Health restoration must assign a value, not subtract damage or emit damage/death rewards again.
2. Add `AC_EnemyReverse` and configure a compatible `PlaybackAnimClass`; duplicate a playback AnimBP for a different skeleton if needed.
3. Stop attack timers and gate damage/attack callbacks during rewind. Preserve reversible death objects until no living history remains.
4. Check controller restart, perception, mesh attachment, collision and movement mode for that enemy. Flying/swimming/custom movement and custom controller types require an adapter extension.
5. For additional historical status fields, record, restore and trim them with the same sample index; do not create an independent clock.

## Validation evidence and boundaries

Local evidence is in ignored `Saved/Agent/EnemyReverse/`:

- `pie_test.json`: actual Q-bound Enhanced Input action injected in PIE; both enemies restored health after damage and lethal damage; captured rendered bone poses were compared with recorded snapshots.
- `pie_edge.json`: fractional health, short rewind that stays dead, a second rewind reaching life, history exhaustion, and eventual cleanup of both enemies, both controllers and the ranged weapon.
- `pie_final.json`: 405 observations after the perception fix; no mismatched history lengths or living-frame counts. After revival, ranged `Is Shooting` was true in 140 observations and melee attack montages were active in 157 observations. Both AI brains stopped during rewind and resumed after living restoration.
- `final_validation.log` / `final_validation.json`: all eight affected/new Blueprints loaded and compiled in a separate editor process without the local editing helper plugin; zero errors. One existing reverse-demo controller warning concerns its obsolete `PawnActionsComponent` reference.

The tests used scripted damage through each enemy's actual damage entry and injected the input action bound to Q. They did not simulate a physical keyboard hold. The player was temporarily invulnerable for these scenarios; actual damage to the player after revival was not asserted. Existing animation/weapon warnings were distinguished from new runtime errors; the final PIE test produced no new Blueprint runtime errors.

Playback restores evaluated skeletal poses, including attack/death poses. It does not replay AnimNotifies, sound/VFX events, or animation curves. On release, normal AI and animation restart; an interrupted attack montage does not resume at the exact historical montage time. Projectile history remains the existing projectile system's responsibility. Packaged builds, networking, large enemy counts, and the separate seek-reverse control mode were not validated in this task.

Task assets were saved through Unreal. Map_Test's existing instances inherit the component without changing their overrides. The original local player save was restored after testing. Three pre-existing dirty Control Rig assets were left untouched. No commit was created.

Asset names in this document were updated during the 2026-09-26 naming pass. Historical evidence files retain the names used when their tests ran; see the knowledge-base rename CSV for the mapping.
