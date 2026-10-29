# Relaxed hands and holstering — phase 1

2026-10-28 Dialogue integration: this behavior is retained together with real-time Shift tap/release timing, compensated procedural locomotion and the corrected fist IK path. Fist clips keep their authored targets with `LeftHandAlpha=0`; the existing one-second combat-base hold owns the return to relaxed locomotion. See [final repair and verification](player-fist-time-animation-fix.md#wingshing-同步与最终修正).

Implemented on 2026-10-24 for the player's existing Blueprint FPS system. This phase reuses existing animation assets and the procedural weapon-change motion; it does not introduce authored waist-reach pistol draw/holster sequences.

## Runtime behavior

- `BP_FPCharacter.BeginSetup` initializes the ordinary empty-hands item even when automatic loading is disabled. No save/load feature is re-enabled.
- `GetHandsRelaxed` returns a presentation state without changing equipment identity. Empty hands use relaxed locomotion outside a one-real-second punch hold.
- `BP_Weapon_EmptyHands.BeginFire` starts that hold before the original alternating additive punches and existing damage/cooldown path.
- `ABP_Manny` blends `EmptyArms` with the existing fist base inside its HANDS branch. Idle/walk retain existing locomotion; the Run state reuses `Anim_Character_FistSprint` to show arm swing at the lower edge of the first-person view. Its walk/run transitions read `IsRunOrSprint` through rebuilt getters (`RelaxedWalkToRun` / `RelaxedRunToWalk`). Other weapon-pose branches and the `upperbody` linked instance remain in place.
- `IA_Holster`, bound to H in `IMC_Player`, calls `ToggleHolster` on Started. It observes the existing dialogue/tutorial weapon-input gate. H holsters the current weapon or restores the last valid gun slot, with an owned-slot fallback; without a gun it does nothing. H is ignored during an active swap. Existing 1/2/3, wheel and melee bindings retain their roles.
- Slot requests share one swap pipeline. A request received during a transition replaces the pending slot request. Firing/ADS cannot start until raising is finished; release paths remain connected. Swapping exits sprint, retains the existing reload guard, and rejects dead-player requests.
- Lowering and raising use real-time deadlines (0.3 seconds each). The wait polls only while a transition is active. Death during lowering restores the pose instead of destroying the old weapon.
- Selected-slot ammunition is snapshotted before spawn and restored after attachment initialization, then written through the existing inventory synchronization. H does not refill ammunition.

## Changed assets

- `/Game/Blueprints/Player/BP_FPCharacter`
- `/Game/Animations/Player/Mannequins/Animations/ABP_Manny`
- `/Game/Blueprints/Weapons/Player/WeaponBases/BP_Weapon_EmptyHands`
- `/Game/Input/IMC_Player`
- `/Game/Input/Actions/IA_Holster` (new)

No animation sequence, map, weapon model, time-ability component or damage detector was changed. The local authoring helper is not a runtime dependency of the new Blueprint nodes.

## Validation and recovery

Local evidence and targeted pre-change backups are under `Saved/Agent/ArmsPhase1/` (ignored). The 40-case core suite and 11 boundary checks use temporary inventory fixtures and Enhanced Input actions, not direct swap calls. Three additional cold-start/F-pickup checks use the original interaction area and input path. All 54 checks passed after reloading the saved assets. The death check sets the death flag as a cancellation fixture; it is not a full damage/death/respawn acceptance test.

The H mapping was re-read after reload. Windows automation recorded a raw H press/release in one frame without a sampled held value; it was not counted as a successful physical-key acceptance test. The input-action toggle path is covered by the core and boundary suites. The demo uses the production pawn and input actions on a temporary flat runtime stage with owned-slot fixtures; the stage is not saved. Native frame captures are retained alongside the cropped GIF preview; they are not rendered mockups.

The three modified Blueprints compile with zero errors/warnings, including a fresh-process reload. The general commandlet still reports pre-existing Manny PoseAsset warnings. Blueprint Assist was used selectively on the new functions; existing graphs received scoped layout/comments. A connection/default audit confirms that formatting only changed layout and reroutes.

Restore only the four existing assets from the targeted backup and remove the new action through the editor to undo this task. Do not restore an entire workspace or discard unrelated work. Packaged/network play and bespoke cinematic draw animations are outside this phase.
