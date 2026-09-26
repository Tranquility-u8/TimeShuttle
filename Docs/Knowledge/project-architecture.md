# 当前项目架构

仓库与 Unreal 5.6 实际资产核对日期：2026-09-26。本文描述实现入口；设计目标仍以 `design-snapshot.md` 和对应 Drive 来源为准。本次未刷新 Drive。

## 目录职责

`Content` 直接按用途组织，没有新增 `TimeShuttle/` 包裹层。

| 目录 | 职责 |
| --- | --- |
| `Maps/` | `Map_Test` 主关卡、`Map_Menu` 菜单 |
| `Blueprints/Player/` | FPS 玩家及相机；模板来源 ProceduralFPSKIT |
| `Blueprints/Components/Player/` | 交互、翻越、后坐力、程序动画等玩家组件 |
| `Blueprints/AI/Melee/` | 近战角色、Controller、BT / Blackboard / Tasks、Spawner |
| `Blueprints/AI/Shooter/` | 远程角色、Controller、StateTree、EQS、接口、敌人武器和弹丸 |
| `Blueprints/AI/Training/` | 模板训练/测试靶逻辑，不是第三种正式敌人 |
| `Blueprints/AI/` | `AC_Combat`、`BPI_Combat`、命中检测 NotifyState、攻击点枚举等共享战斗支持 |
| `Blueprints/TimeReverse/Enemies/` | 通用敌人回溯组件和适配接口 |
| `Blueprints/Weapons/Player/` | 玩家武器、拾取物、武器基类及数据资产类定义 |
| `Blueprints/Interactables/`、`Interfaces/`、`Types/` | 交互物、共享接口、枚举和结构体 |
| `Blueprints/GameModes/`、`SaveSystem/`、`Utilities/` | 游戏模式、存档和工具 Actor |
| `Animations/` | Player、Melee、Shooter、TimeReverse 及 Shared / Support 资源；骨架来源需逐一核对 |
| `Data/`、`Input/` | 武器数据资产实例、曲线、输入动作与映射 |
| `Weapons/`、`Characters/` | 武器与角色的模型、材质等表现资源 |
| `Environment/`、`Materials/`、`Audio/`、`VFX/`、`UI/` | 环境及各类表现资源 |
| `TimeReverseSystem/` | 仍在使用的原始反转框架及其示例/支持资源，尚未做整包迁移 |
| `FirstPerson/`、`LevelPrototyping/` | 遗留模板和原型支持；是否可删必须查真实引用 |

原 `ProceduralFPSKIT/`、`Variant_Shooter/`、`CombatAI/` 内容已归入分类目录；不能根据旧包目录不存在推断其功能被删除。所有 FPS 模板资源保留，AI 使用所需依赖保留。

## 游戏入口与依赖

- 编辑器启动地图、游戏默认地图：`/Game/Maps/Map_Test`。
- **Map_Test 自身的 GameMode Override 是 `/Game/Blueprints/GameModes/GM_FP`**；玩家为 `/Game/Blueprints/Player/BP_FPCharacter`。配置中的全局 fallback 仍是 `/Game/FirstPerson/Blueprints/BP_FirstPersonGameMode`，不能混为一谈。
- 输入：`/Game/Input/IMC_Player`；Q 对应 `/Game/Input/Actions/IA_Reverse`。玩家负责输入和启动全局反转，AI 不实现玩家输入。
- 近战：`BP_MeleeNPC` → `BP_MeleeAIController` → `BT_Melee` / `BB_Melee`；战斗组件为 `AC_Combat`，接口为 `BPI_Combat`。蓝图内部某些组件变量仍叫 `CAI_CombatComponent`，这是保留的成员名，不代表资产改名失败。
- 远程：`BP_ShooterNPC` 直接继承 Character → `BP_ShooterAIController` → `ST_Shooter` / 射击子树、`STT_Shooter_*`、EQS；武器在 AI/Shooter/Weapons，玩家武器来自独立 FPS 模板链。
- 玩家武器数据：`PDA_Item` / `PDA_ProceduralAnimValues` 是蓝图类；`Data/Weapons/Player/**/DA_*AnimationValues` 是实例，并非 DataTable。
- 存档：`Blueprints/SaveSystem` 中的 `SG_Character` / `SG_SaveSlots`。本地 `Saved/SaveGames` 不进 Git，测试前后需保护真实存档。

## 敌人回溯边界

两种敌人均添加 `EnemyReverse` 实例组件，类型为 `AC_EnemyReverse`，实现 `BPI_RewindableEnemy`。组件继续接入原全局 reverse manager，按同一采样索引记录 Transform、浮点血量、骨骼姿态、Mesh Transform 和速度。两种骨架分别使用 `Animations/TimeReverse/ABP_EnemyRewind_*`。

回溯期间停止 AI 与攻击；回到存活状态后恢复正常动画、移动与 AI，重新刷新远程感知。死亡对象保留到存活历史耗尽再清理。正常 AI 会重新决策，攻击蒙太奇不从历史帧继续执行。原示例 Status / Montage 组件硬依赖示例敌人，不要额外挂在当前两个敌人上。

详细行为、扩展入口和验证边界见 [EnemyReverse.md](../Implementation/EnemyReverse.md)。新的伤害、状态或 AI 功能应优先复用接口/组件；不要让敌人重新继承玩家蓝图。

## 维护入口

- 命名：[asset-naming.md](asset-naming.md)。
- 已验证行为及缺口：[implementation-status.md](implementation-status.md)。
- 协作与授权：仓库根 `AGENTS.md` 为唯一规则源；skills 只路由工作流程。
- 工具状态：[../MCP/SOP.md](../MCP/SOP.md)。没有已选定的 UE MCP 服务；发现本次实际工具后再选择编辑器 Python、Unreal-aware helper 或 GUI。
- 改动落地后更新受影响事实及证据日期，不能用本地架构核对冒充 Drive 来源刷新。
