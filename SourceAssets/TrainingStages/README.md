# Training stage props

Original low-poly mesh kit for the Time Shuttler training arena. These are static layout assets. They do not implement enemies, pickups, weakpoint damage, falling physics, time abilities, melting transitions, ammo refills, or tutorial progression.

## Files

- `TrainingStageProps.blend`: editable Blender source, arranged in a library grid.
- `FBX/`: one mesh per file, exported at the origin.
- `manifest.json`: exact centimeter bounds, material slots and linear material parameters, triangle counts, source axes and SHA-256 hashes.
- `build_training_props.py`: deterministic local Blender generator. Run in a separate background process with factory startup; it must not replace the artist's active Blender session.
- `TrainingRoom_StageLayouts.blend`: full stage-layout companion built from `layout_manifest.json`; the original prop library above remains separate.
- `build_training_stage_layouts.py`: assembles the companion and renders S1, S3 and S7B cutaway previews under `Saved/Agent/TrainingStages/Assets/`.

## Full-room companion

Select a View Layer named `S1`, `S2`, `S2C`, `S3`, `S4`, `S5`, `S6`, `S7A`, or `S7B` to display its stage. Each stage has its own Collection. `SharedShooting` holds the table/equipment group. The S2C view also includes S2; S3 through S7A include SharedShooting. The file opens in S1.

The shell is a dimensional reference: 20 x 34.7 x 8 m clear inside, with 40 cm walls and the existing 120 x 220 cm entrance opening centered at (0,1200) cm. The actual Unreal level remains authoritative. The Blender companion turns target, enemy-proxy and counter fronts toward +Y, matching the entrance-facing orientation in Unreal. Floor guides are nonphysical curves; the player barrier and existing UE-only pistol are non-rendering reference markers. Previews temporarily omit the near/east walls for readability, while the saved source retains them.

## Engine conventions

Geometry uses centimeters. Local X is width, local Y is depth, and Z is up. Target and supply-counter fronts face local -Y. Every exported object has its pivot at the bottom center of its bounding box. Blender's source library uses display offsets; those offsets are not included in the individual FBX exports.

Use Unreal FBX scene/unit conversion with an import scale of 1, then verify the first counter measures 200 x 100 x 105 cm before importing the rest. If the importer changes horizontal axis orientation, align instances against their measured bounds and front face instead of applying a compensating size scale.

Use simple box collision for counters and covers, convex hulls for rocks, and suitable simplified collision for target proxies. The gantry needs separate column/beam collision or complex static collision: a single bounding-box collider would block its opening. Keep the breakable link independent from the gantry and suspended rock.

The supply counter is a solid 2 m module. Adjacent instances must meet without gaps, and the end modules must seal to the existing arena walls. Inactive stages also need collision disabled at runtime; Outliner visibility by itself is an editor organization feature.

## Verification evidence

Build logs, per-asset studio previews, a contact sheet, and FBX round-trip validation are written under `Saved/Agent/TrainingStages/Assets/`. Validation checks one imported mesh per file, bounds, bottom-center pivot, material-slot order, closed manifold components, and export hashes. Visual previews validate shape and material placement only; in-engine lighting, collisions and actual gameplay behavior require separate Unreal checks.

All geometry was authored locally for this project. No external meshes, textures, paid generation, or third-party asset licenses were used.
