# Player walk/run leg animation repair

Verified on 2026-11-14 in UE 5.6.1, using `Map_Test` and the real `BP_FPCharacter`.

## Cause and change

`/Game/Animations/Player/Mannequins/Animations/ABP_Manny` had a disconnected component-space pose between `AnimGraphNode_LocalToComponentSpace_0` and `AnimGraphNode_ComponentToLocalSpace_0`. This prevented `Main States` and its locomotion animations from reaching the existing slide, turning, foot IK, upper-body blend and procedural arms chain. Movement speed and `ShouldMove` updated normally while both legs remained in the reference pose.

Restored that single connection, moved the first conversion node next to the second, and added a comment explaining the continuous locomotion pose path. Native graph inspection confirmed unchanged graph/node/pin counts and other links/defaults. No player movement values, animations, skeleton masks, foot IK settings or procedural-arm settings were changed.

## Validation

- The repaired asset was saved, reloaded in the ordinary interactive editor, and compiled again.
- Enhanced Input `IA_Move` and `IA_Run` exercised forward walking, running, backward movement and both lateral directions. Both calf joints changed rotation throughout each moving phase; running also selected the native run/sprint flags.
- Crouch walking retained both leg animations and the crouch animation flag. This fixture used the existing `BeginCrouch` / `StopCrouch` events.
- A fresh PIE using `IA_Jump` confirmed upward velocity, falling movement and the animation's falling flag. An earlier jump injected immediately after cancelling crouch did not trigger; that failed fixture observation is retained separately.
- Final targeted save left no dirty content or maps, and the AnimBP has no runtime dependency on the temporary authoring helper.

Evidence and the original asset backup are local-only under `Saved/Agent/PlayerLegs20261114/`: `repair_commandlet.json`, `native-before.json`, `native-after.json`, `live_reload.json`, `pie_validation.json`, `jump_validation.json`, and `final_validation.json`. `Backup/ABP_Manny.uasset` is the pre-task recovery copy. Restore through Unreal-aware asset recovery with the editor closed; do not overwrite a loaded asset or discard later user changes.

The existing duplicate `DefaultSlot` warning in `ABP_FP_ArmsProcedural` and stale Manny PoseAsset warnings predate this repair. No Blueprint runtime errors or `Accessed None` were observed during the final validation window. Packaged-build validation and a manual playthrough were not performed.
