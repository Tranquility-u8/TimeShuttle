# Omen v4 in the laboratory

Verified in UE 5.6.1 on 2026-10-02.

- Map: `/Game/Maps/Map_LabBridge`.
- Source: `output/omen-game-v4-wide-eye/TimeShuttler_Omen_Game_v4.blend` in the surrounding workspace; SHA256 `97ae2ccb3f4d14688ea14a3d9337ee4bcd10e1a188af34c02be1ec9cbe8b3af3`. This is the wide-eye model with the final uniform matte graphite shell.
- Assets: six static meshes and six materials under `/Game/Characters/Omen`. Total source triangles: 5,684. UVs, custom normals, material slots and separately editable parts are preserved.
- Placement follows the v32 layout: sphere center **(0, 2900, 700) cm**, **12 m** diameter, facing the entrance toward **UE −Y**. Source model diameter is 10 m, so the actor scale is 1.2 with yaw 180°. The center height is measured from the room floor, not the 15 cm platform top.
- Outliner: `Characters/Omen/OmenV4`. The upper shell is the parent, with the other five mesh actors attached. Move/scale the parent to move the complete model. All six have `OmenV4` and unique `OmenPart.*` tags.
- This is an independently placed UE asset, without SceneBridge ownership tags. The existing laboratory bundle does not include Omen; normal laboratory sync therefore leaves these actors alone. This placement is not bound to future edits of the separate Omen `.blend` file.
- Materials preserve source base colors, metallic/roughness and eye appearance. The two ring emission strengths are multiplied by 100 for the existing lab's fixed EV100 10 exposure; the parameter remains editable as `EmissionStrength`. Existing lab lighting/exposure is unchanged.
- Static mesh components use `BlockAll` with complex-as-simple mesh collision, without physics simulation. This setup supports the current stationary presentation; animated/physical Omen behavior has not been implemented by this placement.

Validation: source FBX round trips preserved all six parts, normals and UVs. Editor queries verified bounds, orientation, platform support, 36 segments around a 7.8 m radius route, entrance clearance and Omen body blocking. PIE used the actual `BP_FPCharacter` (48 cm capsule radius, 88 cm half-height): the entrance/platform step and eight perimeter segments all passed using normal CharacterMovement. Teleporting was used only to establish each independent route's start point. Original 997 actor transforms, mesh/material assignments and tags were preserved; the saved map now has 1,003 actors and no dirty packages.

Local evidence, exported FBXs, material metadata, screenshots and a pre-change map backup are in `1002/OmenPlacement/` in the surrounding workspace. The primary reports are `ue-final-result.json`, `ue-omen-validation.json` and `pie-omen-report.json`.
