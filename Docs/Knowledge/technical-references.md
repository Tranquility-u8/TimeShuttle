# Important technical references

Last reviewed: **2026-09-17**. These references inform investigation and integration work; they do not prove that a feature is configured or working in this repository.

## Tactical Shooter Pack Unreal — Procedural Recoil

- **Official source:** [Procedural Recoil | Tactical Shooter Pack Unreal](https://kinemation.gitbook.io/tactical-shooter-pack-unreal/blueprints/procedural-recoil)
- **Publisher:** KINEMATION
- **Role:** Important vendor reference for understanding and validating the Tactical Shooter Pack procedural recoil pipeline.
- **Authority boundary:** Use the installed asset version, Blueprint inspection, compile/save results, Output Log, and PIE evidence as implementation truth. Treat differences between those results and this living web page as a version mismatch to investigate, not as permission to overwrite local setup.

The documented pipeline centers on a Recoil Animation Actor Component initialized with a Recoil Data Asset and weapon fire rate. Firing drives `Play` and `Stop`; aiming state and fire mode are supplied separately. Recoil behavior is data-driven through hip/aim ranges, controller recoil, noise, pushback, accumulated progress, sway, pivot/general settings, and vector curves for single versus burst/automatic fire. The resulting `FTransform RecoilAnimation` can feed an Animation Blueprint, such as through a Transform (Modify) Bone node.

Before applying this reference to project work, verify the installed pack exposes the same component, functions, data fields, curve assets, and output transform. Also verify whether the project attaches recoil to the character or weapon and how fire rate, ADS state, fire mode, and animation-bone modification are currently wired.
