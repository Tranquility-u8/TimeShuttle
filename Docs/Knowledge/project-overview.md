# Time Shuttler project overview

## Identity

- Game: **Time Shuttler**
- Team: **Undingable**
- Engine: **Unreal Engine 5.6**
- Genre/focus: single-player first-person shooter with time manipulation, environmental interactions, and light clue collection.
- Visual direction: minimalist near-future realism; time-stop state trends gray-blue.
- Production target: a polished vertical slice that demonstrates the full game's potential.

### 室内美术基准

2026-11-07 用户确认，后续室内沿用 Chapter 1 实验室的近未来美术方向。建筑和普通设备用低多边形大轮廓，细节集中在玩家需要辨认的关键设备。墙板色相和明度随房间用途与照明条件选择：第一房间采用压暗的暖灰，其他房间可使用正常亮度的浅色墙面。房间之间通过清晰的几何、材质和工作灯具保持一致。[第一房间 UE 实景与对照](../../../output/time-shuttler/ch1-room1-installed/index.html)

Chapter 1 的前两个房间均处在灾难之后。第一房间的破坏集中在停机的粒子机器；第二房间用被压低的风管、旧落板、爆开的滤柜和随后坠落的顶板延续事故。后续室内的损坏程度随各场景的剧情与时间点确定。[第二房间的白盒与美术预览](../Design/Chapter1/room2-environment-plan.md)

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
