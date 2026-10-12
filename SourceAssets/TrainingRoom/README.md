# Training room source meshes

Exported from the approved `TimeShuttler_TrainingRoom_v5_SlidingDoor.blend` in the workspace's `场景版本测试/训练室_极简空场_v5_滑门` directory on 2026-10-12.

- Interior: 20 × 24 × 8 m; doorway: 1.2 × 2.2 m.
- 25 evaluated meshes, including wall pocket cuts and separate moving door details.
- FBX contains local geometry and metric unit metadata. Import at scale 1 with scene/unit conversion, absolute vertex transformation, and `Force Front X Axis` disabled.
- `manifest.json` records placement in UE centimeters. Blender `(X,Y,Z)` maps to UE `(X,-Y,Z)`.
- Assets: `/Game/Environment/TrainingRoom/Meshes`; authored map: `/Game/Maps/Map_TrainingRoom`.
- Materials, lights, triggers, door motion and level travel are authored in UE. FBX does not carry the original procedural Blender materials or gameplay logic.
- Static architecture uses complex-as-simple collision. The moving door leaf uses a simple box; decorative light meshes and attached door details do not block the player.

These source files are retained for reimport. Reimport only a deliberately selected mesh; do not rebuild the map over hand-authored UE changes.
