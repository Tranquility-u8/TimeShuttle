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
- 输入：`/Game/Input/IMC_Player`；Q 对应 `/Game/Input/Actions/IA_Reverse`，T 对应 `/Game/Input/Actions/IA_TimeAbility`。玩家负责输入和启动全局反转，AI 不实现玩家输入。
- 近战：`BP_MeleeNPC` → `BP_MeleeAIController` → `BT_Melee` / `BB_Melee`；战斗组件为 `AC_Combat`，接口为 `BPI_Combat`。蓝图内部某些组件变量仍叫 `CAI_CombatComponent`，这是保留的成员名，不代表资产改名失败。
- 远程：`BP_ShooterNPC` 直接继承 Character → `BP_ShooterAIController` → `ST_Shooter` / 射击子树、`STT_Shooter_*`、EQS；武器在 AI/Shooter/Weapons，玩家武器来自独立 FPS 模板链。
- 玩家武器数据：`PDA_Item` / `PDA_ProceduralAnimValues` 是蓝图类；`Data/Weapons/Player/**/DA_*AnimationValues` 是实例，并非 DataTable。
- 存档：`Blueprints/SaveSystem` 中的 `SG_Character` / `SG_SaveSlots`。本地 `Saved/SaveGames` 不进 Git，测试前后需保护真实存档。

## 时间能力核心入口

`/Game/Blueprints/Components/Player/AC_TimeAbility` 挂载在 `BP_FPCharacter` 上，负责 0–100 能量、Normal / FullStop / BulletTime 三态、均匀消耗恢复及零能量退出。当前 `ModeIndex` 映射为 0 / 1 / 2，阈值 70 归入 FullStop。组件和玩家现有回溯输入共同形成双向互斥门禁。

`AC_TimeAbility` 在 `FullStop` 使用全局时间倍率 0.01，并用倒数补偿玩家和当前武器；在 `BulletTime` 将能量 70→0 映射为世界倍率 0.2→1.0。`/Game/UI/Widgets/UI_Hud.SetTimeAbilityStatus` 接收能量百分比和模式索引，更新画面左侧的竖向进度条、100% / 70% / 0% 阈值、当前百分比、模式文字与颜色区域；`SetTemporalProjectileStatus` 在 FullStop 显示时间弹丸数量、12 发上限及满额提示。详细范围和验证见 [TimeAbilityCore.md](../Implementation/TimeAbilityCore.md)。

## 玩家武器对敌伤害入口

玩家武器基类 `/Game/Blueprints/Interactables/BP_Item_Base` 的 `Fire_HitScan` 使用命中结果中的 `Hit Actor` 提交通用 Unreal Damage。2026-10-02 两类正式敌人已挂载 `/Game/Blueprints/AI/WeakPoints/AC_EnemyWeakPoints`：`ResolveShotDamage` 将命中组件交给敌人结算，激活弱点直接读取对应 Tier 的 `WeakPointDamage`，再提交一次原有 Damage；不再传递武器 BreakPower，也没有护甲或击破门槛。激活球体附着主体 Mesh 骨骼、只阻挡 Camera 射线；未激活位置按身体处理，取消这些敌人的旧 100 点爆头。无弱点组件目标保留 head=100 / body=25 回退。训练靶 `BP_TrainingEnemy` 专用分支保持互斥。任务 5 已由弱点组件拥有 Screen-space WidgetComponent（`WBP_WeakPointMarker`）和无碰撞发光核心，使用 `M_WeakPointBracketUI` / `M_WeakPointCore`；原生投影跟随骨骼，真实时间节流更新遮挡、距离/FOV/DPI 和等级颜色。不修改 UI_Hud，不依赖编辑器工具运行。任务 6 时间弹和任务 7 回溯接入见下文；具体配置与验证见 [enemy-weakpoints-plan.md](../Implementation/enemy-weakpoints-plan.md)。

时间弹丸桥接同样位于 `BP_Item_Base.Fire_HitScan`。`UseTemporalProjectile=false` 时完整保留原射线伤害；启用后沿实际瞄准射线生成 `/Game/Blueprints/Weapons/Player/Projectiles/BP_TimeBullet`，起点为同一 TraceStart 加 40 uu 方向偏移，不混用动画枪口位置；40 uu 内遮挡仍回退射线结算。全局实例上限为 12。`BP_TimeBullet` 使用 `SM_GeneralBullet`，生成时移动组件不激活、碰撞关闭，通过幂等的 `ReleaseProjectile(Speed)` 延迟恢复运动。释放后以实际上一位置到当前位置的 Camera 通道线段检测首个阻挡，命中弱点敌人调用同一 `ResolveWeakPointDamage(HitComponent)`，每弹仅一次 Damage 后销毁；视觉不参与伤害。无弱点组件 Character 保留旧头/身体回退，非 Character 保留弹孔。`AC_TimeAbility` 只在 `FullStop` 开启实体弹，在进入 `BulletTime` 或退出能力时以默认 5000 uu/s 释放现存弹丸。

弱点视觉新增 `bWeakPointVisualsOnlyDuringTimeAbility=true`：Normal 隐藏，FullStop / BulletTime 显示；仍受总开关、存活、激活、距离和遮挡限制，只控制括号/核心、不关闭命中球。命中反馈按真实时间短暂强调最后命中的激活弱点，参数为 `HitFeedbackDuration` / `HitFeedbackStrength`，不会令隐藏点强制显现。进入/退出回溯清除瞬态反馈，之后按当前显示门控重新计算；Q 本身不会打开 T 能力的显示门控。

两种正式敌人不共享血量存储：`BP_MeleeNPC.Event AnyDamage` 将浮点伤害转交现有 `CAI_CombatComponent.Apply Damage`，`BP_ShooterNPC.Event AnyDamage` 继续更新自身 `Current HP`。Shooter 的非致命受伤分支会通过 `ABP_TP_Rifle` 的专用 `HitReact` Slot 播放同骨架、无 Root Motion 的 `MM_HitReact_Front_Lgt_01` 动态 Montage；回溯/已死亡守卫仍在前，致命伤仍直接走原 `Die` 分支。该表现不参与伤害和回溯数据。新增敌人应复用通用伤害事件并适配真实血量所有者，不应再把训练靶类型转换作为通用伤害门。详细实现、证据与测试限制见 [EnemyDamagePipeline.md](../Implementation/EnemyDamagePipeline.md)。

## 敌人回溯边界

弱点伤害的 2026-10-02 修订：`PDA_WeakPointTier.WeakPointDamage` 是每档弱点的独立伤害值（当前黄 50、红 25），每次有效激活点命中立即生效。已删除护甲耐久、击破门槛、武器 BreakPower 和敌人统一弱点伤害字段；BodyDamage 与仅弱点开关仍在 `AC_EnemyWeakPoints`。当前 GetWeakPointState 只返回激活/未激活及无效状态，没有护甲历史。

伤害调试统一由 `AC_EnemyWeakPoints` 在解析出正伤害后触发，并读取当前 `GM_FP.bDebugPrintEnemyDamage`（默认开启）。身体/未激活候选打印 `Damage: <数值>`，激活弱点打印 `CRITICAL Damage: <数值>`；0 伤害和开关关闭不打印。该开关只控制屏幕与 Output Log 文本，不进入伤害、视觉显示或回溯状态。绕过弱点解析器的直接 `ApplyDamage` 没有可靠命中上下文，因此不由此功能标记 Critical。

任务 7 使用 `/Game/Blueprints/Types/Structs/S_WeakPointRewindFrame` 保存五位置等级索引及初始化状态。`AC_EnemyReverse.WeakPointHistory` 与 HP/姿态同采样、同索引回放和裁剪，覆盖自动 Q 与 seek。恢复直接写入分配和命中球激活，不重新随机、不重建组件、不重放闪光或触发伤害/奖励。记录期间 Candidates / TierRules 顺序保持固定，设计师配置不属于快照。回溯中忽略显式重置；死亡保留期继续使用原存活历史，最终销毁敌人时清理其所有弱点组件。两类敌人的复活后手枪伤害、显示门控及历史清理已取得 PIE 证据；seek 仅验证正式组件事件，不代表物理 seek 输入验收。

两种敌人均添加 `EnemyReverse` 实例组件，类型为 `AC_EnemyReverse`，实现 `BPI_RewindableEnemy`。组件继续接入原全局 reverse manager，按同一采样索引记录 Transform、浮点血量、骨骼姿态、Mesh Transform 和速度。两种骨架分别使用 `Animations/TimeReverse/ABP_EnemyRewind_*`。

回溯期间停止 AI 与攻击；回到存活状态后恢复正常动画、移动与 AI，重新刷新远程感知。死亡对象保留到存活历史耗尽再清理。正常 AI 会重新决策，攻击蒙太奇不从历史帧继续执行。原示例 Status / Montage 组件硬依赖示例敌人，不要额外挂在当前两个敌人上。

详细行为、扩展入口和验证边界见 [EnemyReverse.md](../Implementation/EnemyReverse.md)。新的伤害、状态或 AI 功能应优先复用接口/组件；不要让敌人重新继承玩家蓝图。

## 维护入口

- 命名：[asset-naming.md](asset-naming.md)。
- 已验证行为及缺口：[implementation-status.md](implementation-status.md)。
- 协作与授权：仓库根 `AGENTS.md` 为唯一规则源；skills 只路由工作流程。
- 工具状态：[../MCP/SOP.md](../MCP/SOP.md)。没有已选定的 UE MCP 服务；发现本次实际工具后再选择编辑器 Python、Unreal-aware helper 或 GUI。
- 改动落地后更新受影响事实及证据日期，不能用本地架构核对冒充 Drive 来源刷新。
