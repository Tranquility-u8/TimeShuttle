# Lab v0.39 independent whitebox

Verified 2026-10-02. The user explicitly requested a new Blender project and a new UE map. The prior layout-only restriction was superseded by this implementation request.

## Scope and locations

- New map: `/Game/Maps/Map_LabV39`, ordinary non-World-Partition level.
- New assets: `/Game/Environment/LabV39/Scene_b1f78efcc816ac0b`.
- Blender source: `E:/Capstone/Test/1002/LabWhitebox_v39/TimeShuttler_Lab_v39.blend`.
- Blender scene ID: `0aa10ea02d3044aa819f0ec4aab976f3`; export collection `LAB_V39`.
- Bundle: `E:/Capstone/Test/1002/LabWhitebox_v39/lab_bundle/manifest.json`.
- Approved geometry: `1002/LabFlow_v39/v39-geometry.json`; source layout was not edited.
- Prior unsaved UE work was serialized separately to `/Game/Maps/Backups/Map_LabBridge_PreV39_20261002` before changing maps. The prior map's disk file and shared Omen assets are hash-checked against preflight.

The relative playable floors are 0 and 5.4 metres. The legacy geometry layer key `4.5` is an index, not the new upper elevation. Main roof is 14 metres and the Omen room is 40 × 42 × 25 metres. Other facility levels are represented by inaccessible galleries and shafts; actual floor numbers remain unspecified.

## Source and UE ownership

The architecture, frames, fixed glass, four stairs, furniture, signs and initial gate leaves are managed by SceneBridge. Omen's six existing mesh assets are reused by separate UE actors at `(0,3700,700)` cm, yaw 180 degrees, scale 1.2. Its Blender reference collection is outside the export scope. Existing Omen assets/materials were not reimported or edited.

The new scene uses independent IDs and namespace. UE-added lights, cameras, player start, reverse manager and Omen actors have `LabV39.Setup` tags and remain outside bridge ownership. The watcher configuration is machine-local in `Saved/SceneBridge/config.json`; the prior configuration is backed up in the whitebox output folder. `Export After Save` is enabled in the Blender file.

There are 80 initial closed door leaves, each named `GateLeaf::<opening_id>`. They carry phase/identity tags for future integration. These are static whitebox blockers, not working story-driven doors. This map does not implement narrative triggers, elevator operation, save-state progression or automatic door unlocking. It is not a free-exploration mode.

## Construction decisions

- Door/window headers use actual wall jamb sections, not the oversized 2D cutter depth.
- Windows without an explicit sill use a 0.9 metre sill and fixed glass.
- All four stairs use the plan's 31 rises to 5.4 metres and 30 visible 0.32 metre treads. A UCX convex ramp provides continuous character movement.
- Two furniture masses were shifted inward for door clearance: item 25 Y +0.8 m, item 27 Y +1.2 m. No rooms or openings moved.
- Room labels are placed inside current room polygons, replacing stale inherited label coordinates.
- Exterior terrain was rebuilt under the larger footprint; distant city masses remain non-colliding context.

## Collision importer correction

UE 5.6 `StaticMeshEditorSubsystem.get_simple_collision_count` counts boxes, spheres and capsules separately from convex hulls. SceneBridge previously rejected valid UCX-only meshes because it checked only the first count. Both source and installed importer now reject negative count queries and require a positive sum of simple and convex counts for custom collision.

Five isolated checks cover UCX-only, simple-only, empty and each negative query case. The four real UCX stairs then imported successfully, followed by actual CharacterMovement validation. No Blueprint graphs or shared gameplay assets were changed.

## Verification evidence

Evidence is stored under `1002/LabWhitebox_v39/`:

- `prepared_meshes.json`: 285 closed architectural solids with consistent winding, positive volume and finite coordinates.
- `ue-audit-report.json`: 1,568 bridge object identities/transforms/collision policies, 80 gates, 29 scheduled fixed windows, four stairs, three crouch passage segments, floor elevations and six Omen parts.
- `ue-pie-report.json`: all eight stair ascent/descent routes and both complete duct routes passed with the project's `BP_FPCharacter`.
- `ue-route-report.json`: five adjacent first-act routes passed, covering TIME, the complete duct, EX01's real east door, the upper gallery, S1 descent, the hall around reception and the Omen approach. These are separate test segments; teleportation is used only between segment starts, not within them.
- `Previews/`: Blender structural and UE editor captures.
- `completion-report.json`: old map/shared Omen hash preservation and final binding state.

Test limitations: collision queries and character routes cover the stated cases, not every room or future phase. Gates are initially closed and have no story script. Generated whitebox meshes use constant materials rather than production UV/textures; FBX tangent warnings were observed. PIE also emits an existing `BP_Weapon_EmptyHands` missing skeletal-mesh/socket warning; no weapon Blueprint was changed. Lighting is a review setup and has not undergone a production performance pass.
