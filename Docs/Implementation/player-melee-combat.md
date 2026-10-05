# Player melee combat

Implemented and verified in Unreal Engine 5.6 on 2026-10-04. This record describes the current player-to-enemy melee path and the extension boundary for a later `MeleeNPC -> player` task. It is repository/editor evidence, not a Google Drive design refresh.

## Runtime path

The player owns `/Game/Blueprints/Components/Combat/AC_MeleeHitDetector` and implements `/Game/Blueprints/Interfaces/BPI_MeleeAttackSource`.

`BPI_MeleeAttackSource.RequestMeleeAttack(Spec)` builds a camera-aligned segment from `BP_FPCharacter.FirstPersonCamera`, using `Spec.Range`, then delegates the sweep to `AC_MeleeHitDetector.ExecuteMeleeTrace`. The detector performs one sphere sweep over Pawn, WorldStatic and WorldDynamic object types, ignores its owner, stops on the first blocking hit and submits `Apply Point Damage` with the owning player and instigator controller. The engine damage event remains the receiver contract, so each target retains ownership of health, hit reaction, death and rewind guards.

The attack specification `/Game/Blueprints/Types/Structs/S_MeleeAttackSpec` currently carries:

- `Damage`;
- `Range`;
- `Radius`;
- `AttackId`;
- `StopOnWorldBlock`.

`StopOnWorldBlock` is reserved for a future selectable policy. The current single blocking sweep always stops at the first world or pawn blocker.

## Player weapon integration

The two player melee families keep their existing animation and fire cadence; they no longer reuse the ranged hitscan damage branch:

| Weapon path | Timing | Damage | Range | Radius | AttackId |
| --- | --- | ---: | ---: | ---: | --- |
| `BP_Weapon_EmptyHands` | Existing immediate `BeginFire` path | 20 | 150 | 18 | `Fist` |
| `BP_Weapon_MeleeBase` / `BP_Weapon_Knife` | Existing attack animation with 0.3 s strike delay | 25 | 200 | 12 | `Knife` |

Both weapon paths call the interface on their owner. `BP_Weapon_Knife` inherits the shared melee-base behavior. No player attack animation asset, enemy Blueprint or weakpoint resolver was modified for this feature.

This implementation uses one camera-aligned sweep at the established strike time, not a per-frame animation NotifyState window. A future attack that needs long active frames or moving limb trajectories can call the same detector more than once, but must add an attack-window identifier and per-target hit set before enabling repeated sweeps.

## Enemy receivers and damage boundaries

The existing enemy receivers required no change:

- `BP_MeleeNPC.Event AnyDamage` forwards floating-point damage to `AC_Combat.Apply Damage`.
- `BP_ShooterNPC.Event AnyDamage` updates `Current HP`, preserves its rewind/death guards and plays the existing non-lethal hit reaction.

Melee damage deliberately bypasses `AC_EnemyWeakPoints.ResolveShotDamage`. Activated weakpoints therefore do not multiply fist or knife damage. Rewinding enemies reject the incoming Point Damage through their existing receiver guards; damage resumes after rewind ends.

## Verification evidence

Cold editor compilation covered the structure, interface, detector, player, both melee weapon classes and both gameplay enemies. The final commandlet reported zero errors. Its 15 warnings are the pre-existing stale Manny PoseAsset notices and the legacy missing `PawnActionsComponent` reference.

PIE used production weapon `BeginFire` paths and real `BP_MeleeNPC` / `BP_ShooterNPC` receivers:

- fist against Shooter: `100 -> 80`, with the Shooter hit-reaction montage active;
- fist miss: no health change;
- knife against Melee: `100 -> 75`;
- two targets intersecting one sweep: total damage was one 20-point hit;
- a movable `BlockAll` cube between camera and target: target took 0 damage;
- rewinding Melee target: 0 damage; after rewind ended: 25 damage;
- FullStop: mode 1, world scale about 0.01, fist dealt 20 immediately;
- BulletTime: mode 2, world scale about 0.267, fist dealt 20 immediately;
- lethal fist hit removed the Shooter actor through its existing death path;
- equipped pistol regression: 25 body damage in Normal mode;
- final time mode and global dilation restored to Normal / 1.0.

The final PIE log contained no Blueprint Runtime Error, `Accessed None`, Python error, ensure or fatal entry. Visual graph inspection confirmed structured responsibility comments and local layout on `AC_MeleeHitDetector`, `BP_FPCharacter`, `BP_Weapon_EmptyHands` and `BP_Weapon_MeleeBase`.

## Future MeleeNPC-to-player extension

The shared boundary is the trace/damage submission layer, not enemy health storage. For the later NPC attack task:

1. Give the NPC an `AC_MeleeHitDetector`, or expose an equivalent caller that supplies its hand/weapon world segment.
2. Trigger the sweep from the NPC's existing attack Notify/NotifyState and pass an NPC-specific `S_MeleeAttackSpec`.
3. Keep the NPC as `DamageCauser` and its Controller as `EventInstigator`.
4. Add the player's generic Point Damage / AnyDamage receiver and adapt it to the player's real health owner; do not couple the detector to `BP_FPCharacter` health fields.
5. If the NotifyState sweeps across multiple frames, extend the detector with Begin/Update/End and a per-attack `HitActors` set so one attack cannot damage the same player every frame.
6. Verify team filtering, world obstruction, player invulnerability/death, time modes and rewind interaction in PIE.

Do not route NPC attacks through player weapon classes, `BPI_Combat` health ownership or `AC_EnemyWeakPoints`.
