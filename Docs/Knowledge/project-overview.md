# Time Shuttler project overview

## Identity

- Game: **Time Shuttler**
- Team: **Undingable**
- Engine: **Unreal Engine 5.6**
- Genre/focus: single-player first-person shooter with time manipulation, environmental interactions, and light clue collection.
- Visual direction: minimalist near-future realism; time-stop state trends gray-blue.
- Production target: a polished vertical slice that demonstrates the full game's potential.

## Team

- Yitong Lu — gameplay programmer, narrative designer, producer.
- Yudong Gao — game designer, 3D artist.
- Wingshing Zeng — game designer, gameplay programmer.

These roles are a Drive snapshot and may change; confirm current ownership before assigning work.

## Player experience

The player operates from a laboratory safe hub and performs missions for Omen using a left-arm time device. The core experience combines readable FPS combat with tactical time manipulation: observe threats, stop or slow time, expose and hit armor weak points, and exploit physical objects. The longer narrative reveals that Omen's goals threaten the remaining human resistance.

## Current technical baseline

- `TimeShuttle.uproject` declares UE 5.6.
- The project is Blueprint-first; runtime implementation remains Blueprint-based as observed on 2026-09-26.
- Enabled project plugins observed: Modeling Tools Editor Mode and Gameplay State Tree.
- Startup/default map: `/Game/Maps/Map_Test`.
- Map_Test GameMode Override: `/Game/Blueprints/GameModes/GM_FP`; actual player: `/Game/Blueprints/Player/BP_FPCharacter`.
- Configured global fallback game mode remains `/Game/FirstPerson/Blueprints/BP_FirstPersonGameMode`; it is not Map_Test's override.
- Rendering targets desktop maximum quality with Lumen, Virtual Shadow Maps, DX12/SM6, and ray tracing enabled.
- Content is organized by purpose: `Blueprints`, `Animations`, `Maps`, `Data`, `Input`, `Weapons`, `Characters`, `Environment`, `Materials`, `Audio`, `VFX`, `UI`. `TimeReverseSystem`, `FirstPerson` and `LevelPrototyping` still contain retained framework/template resources.
- See [project-architecture.md](project-architecture.md) for verified gameplay entry points and [asset-naming.md](asset-naming.md) before creating assets. This technical refresh does not change the dated Drive-derived design/production sections below.

## Production outline

- Sprint 1: design/specification and concept work.
- Sprint 2: gameplay and art prototypes, including FPS controls, enemies, time systems, interactions, UI, and whiteboxes.
- Sprint 3: integration, content production, VFX, narrative progression, and refinement.
- Sprint 4: polished vertical slice, playtesting, and bug fixing.
- Sprint 5+: remaining chapters, balance, polish, regression testing, and performance work.

See `source-manifest.yaml` for the Drive documents behind this summary.
