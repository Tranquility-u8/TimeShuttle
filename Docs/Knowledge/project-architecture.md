# 当前项目架构

仓库与 Unreal 5.6 实际资产核对日期：2026-10-10。本文描述实现入口；设计目标仍以 `design-snapshot.md` 和对应 Drive 来源为准。本次未刷新 Drive。

## 目录职责

`Content` 直接按用途组织，没有新增 `TimeShuttle/` 包裹层。

| 目录 | 职责 |
| --- | --- |
| `Maps/` | `Map_Test` 主关卡、`Map_Menu` 菜单 |
| `Blueprints/Player/` | FPS 玩家及相机；模板来源 ProceduralFPSKIT |
| `Blueprints/Components/Player/` | 交互、翻越、后坐力、程序动画等玩家组件 |
| `Blueprints/AI/Melee/` | 正式近战入口 `BP_MeleeNPC` 与 Spawner；实际 AI 行为依赖位于 `EnemyAITutorial/` |
| `Blueprints/AI/Shooter/` | 正式远程入口 `BP_ShooterNPC` 与保留的 TimeShuttle 弹丸基类/子弹；实际 AI 行为依赖位于 `EnemyAITutorial/` |
| `EnemyAITutorial/` | 迁入的敌人共享基类、Controller、接口、行为树/Blackboard/任务/装饰器/EQS、PatrolRoute、动画、武器与模型支持资源 |
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

**2026-10-05 存档策略更新：** 用户要求关闭游戏自动存档与启动自动读档。`BP_FPCharacter` 启动跳过 `Load`，缓存本轮实际出生变换；`BP_AutoSavePoint` 重叠不再调用 `Save`，因此自动存档点也不再更新复活缓存。显式 Save/Load 与设置持久化保留。此更新覆盖下文历史 checkpoint 启动/触发描述；编译保存通过，PIE 待用户验证。详见 [TECH-005](../Implementation/DisableAutoSave20261005.md)。

- 编辑器启动地图、游戏默认地图：`/Game/Maps/Map_Test`。
- **Map_Test 自身的 GameMode Override 是 `/Game/Blueprints/GameModes/GM_FP`**；玩家为 `/Game/Blueprints/Player/BP_FPCharacter`。配置中的全局 fallback 仍是 `/Game/FirstPerson/Blueprints/BP_FirstPersonGameMode`，不能混为一谈。
- 输入：`/Game/Input/IMC_Player`；Q 对应 `/Game/Input/Actions/IA_Reverse`，T 对应 `/Game/Input/Actions/IA_TimeAbility`。玩家负责输入和启动全局反转，AI 不实现玩家输入。
- 近战：`/Game/Blueprints/AI/Melee/BP_MeleeNPC` → `/Game/EnemyAITutorial/Enemies/AI/AIC_Enemy_Base` → `BT_Enemy_Melee`。巡逻读取关卡中的 `BP_PatrolRoute`，攻击、动画、剑与行为树依赖均来自迁入资源。
- 远程：`/Game/Blueprints/AI/Shooter/BP_ShooterNPC` → 同一 `AIC_Enemy_Base` → `BT_Enemy_Ranged`。巡逻、感知、选位、枪械模型、动画与开火节奏来自迁入资源；开火终点改为生成 TimeShuttle 的 `BP_ShooterProjectile_Bullet`，继续沿用本项目命中与伤害判定。战术掩体复用 `EQS_FindCover` 和独立 `CoverLocation`；`BTT_ReserveAndMoveToCover` 以 275 uu 互斥半径管理分布式预约/占用并处理失败、Abort、死亡/回溯释放，`BTT_CoverPeekBurst` 依据目标方向选择左右 140 uu 侧身、短点射并归位后进入四秒冷却。Shooter 的 RVO 继续负责移动过程中的局部避让。
- 听觉：玩家枪械在 `BP_Item_Base.Fire_HitScan` 起点以武器 Actor 位置上报 `Gunshot` 听觉事件（近战分支静音）。共享 `AIC_Enemy_Base` 的 Hearing 范围为 2000 uu、刺激保留 5 秒；仅听到枪声时把该位置写入 `PointOfInterest` 并进入 Investigating，不会绕过视线直接设置 `AttackTarget`。近战与远程行为树复用同一调查分支。
- 玩家武器数据：`PDA_Item` / `PDA_ProceduralAnimValues` 是蓝图类；`Data/Weapons/Player/**/DA_*AnimationValues` 是实例，并非 DataTable。
- 存档：`Blueprints/SaveSystem` 中的 `SG_Character` / `SG_SaveSlots`。本地 `Saved/SaveGames` 不进 Git，测试前后需保护真实存档。

## 时间能力核心入口

`/Game/Blueprints/Components/Player/AC_TimeAbility` 挂载在 `BP_FPCharacter` 上，负责 0–100 能量、Normal / FullStop / BulletTime 三态、均匀消耗恢复及零能量退出。当前 `ModeIndex` 映射为 0 / 1 / 2，阈值 70 归入 FullStop。组件和玩家现有回溯输入共同形成双向互斥门禁。

`AC_TimeAbility` 在 `FullStop` 使用全局时间倍率 0.01，并用倒数补偿玩家和当前武器；在 `BulletTime` 将能量 70→0 映射为世界倍率 0.2→1.0。`/Game/UI/Widgets/UI_Hud.SetTimeAbilityStatus` 接收能量百分比和模式索引，更新画面左侧的竖向进度条、100% / 70% / 0% 阈值、当前百分比、模式文字与颜色区域；`SetTemporalProjectileStatus` 在 FullStop 显示时间弹丸数量、12 发上限及满额提示。详细范围和验证见 [TimeAbilityCore.md](../Implementation/TimeAbilityCore.md)。

## 时间停止视觉层（2026-10-03）

2026-10-11当前破碎层补充：`M_PP_TS_Facets`使用`T_TS_FacetNoise`周期随机Delaunay数据纹理（RG梯度、B高度、A诊断ID），替代下面第三轮历史的同向方格三角搜索；世界法线主轴投影、世界锚定与玩家Stencil排除保留。新增静态`NoiseSeed`偏移参数。第五轮控制器的共享线性波前与表面局部保留/淡出保持；第四轮网格已改为原生实例分块，下面Niagara描述属于第三轮历史。当前实现和第六轮证据见[时间停止特效](../Implementation/time-stop-vfx.md)。

`/Game/VFX/TimeStop/BP_TimeStopVFXController` 由 BP_FPCharacter 的 TimeStopVFX ChildActorComponent 持有。它读取 AC_TimeAbility.ModeIndex==1 的边沿，以 GetRealTimeSeconds 驱动两条向量曲线，持有独立 PostProcessComponent、三个 MID 和 Niagara 网格。State 与 Facets 均在色调映射后，优先级10/20。第三轮Facets由场景深度重建世界表面、依世界法线主轴选择投影，固定世界三角格及共享正负高度与扫描Origin分离；世界距离波带内按Pulse投影虚拟位移取色。它模拟表面凸凹折射，不修改网格、碰撞、阴影或真实轮廓，也不提供运动物体的局部空间贴附。Niagara仍为单Mesh粒子、固定局部包围盒±1600cm；退出隐藏/暂停网格，EndPlay销毁组件。

独立描边位于`/Game/VFX/TimeStop/Outline/`。目标Actor挂`AC_TimeStopOutline`后，自动登记到每世界单个`BP_TimeStopOutlineManager`；不需要修改玩家蓝图。组件负责Owner的Static/Skeletal Mesh筛选（可选Component Tag）、颜色选择器/Intensity/1–8px Thickness及`bEnabled`正式开关。Manager缓存Player0及AC_TimeAbility，Pawn变化/引用失效时重取，以ModeIndex==1门控；按帧检测，不依赖0.01倍率下的DeltaTime累计。一个后处理MID有32个float4样式参数，每组件独占Stencil 224–255之一，自己的多个Mesh共用一槽；RGB为颜色×强度，A为宽度。After Tonemapping优先级30在冷色与扫描之后绘制可见外缘和解析软光晕，后者不是引擎Bloom。

所有权边界：Manager启动扫描已有CustomDepth使用者并预留冲突槽，目标Mesh原本启用CustomDepth则跳过；借用其余Mesh时保存原Stencil/Mask，退出只在flag/ID/mask仍归本组件时恢复。bEnabled关闭、Owner/组件销毁释放槽，Manager结束清理并允许存活组件重建登记。登记容量最多32组件，已有预留会减少容量；运行中新外部Stencil占用须遵守224–255预留协议，不自动重新协商。透明材质需支持深度写入，当前仅单人Player0；原生Activate/Deactivate不是正式开关。绿色Cube、淡红Manny只是可放置示例，没有给现有敌人/弱点自动挂接。

15个视觉资产的冷加载确认无制作模块依赖、DebugWorldCells=0、CustomDepth=3、Manny默认网格和无脏包。第三轮指定冷PIE描边41项通过；补充27项验证32槽、第33组件安全拒绝、释放重试及切换Pawn时清理/重绑能力缓存；BA的16图及PlayerRef补图语义一致，对应蓝图编译0错误/0警告。表面冷PIE复测21张图、59项有效锚点比较在提案阈值内，实际启停与连续调试移动视频已归档。这不认证隐藏容量夹具的满载渲染性能、HDR、打包或最终艺术接受；现有AI空Controller日志错误单独记录，不能称全工程零错误。视觉层不写能量/倍率/输入/伤害，不改变既有弱点。详见[工程实现](../Implementation/time-stop-vfx.md)、[第三轮方案](../../../开发文档/时间停止特效/第三轮_表面扫描与独立描边方案.md)、[组件说明](../../../开发文档/时间停止特效/独立描边组件使用说明.md)和[第三轮验收记录](../../../开发文档/时间停止特效/实现验收/第三轮/验收记录.md)。

## 玩家武器对敌伤害入口

玩家武器基类 `/Game/Blueprints/Interactables/BP_Item_Base` 的 `Fire_HitScan` 使用命中结果中的 `Hit Actor` 提交通用 Unreal Damage。2026-10-02 两类正式敌人已挂载 `/Game/Blueprints/AI/WeakPoints/AC_EnemyWeakPoints`：`ResolveShotDamage` 将命中组件交给敌人结算，激活弱点直接读取对应 Tier 的 `WeakPointDamage`，再提交一次原有 Damage；不再传递武器 BreakPower，也没有护甲或击破门槛。激活球体附着主体 Mesh 骨骼、只阻挡 Camera 射线；未激活位置按身体处理，取消这些敌人的旧 100 点爆头。无弱点组件目标保留 head=100 / body=25 回退。训练靶 `BP_TrainingEnemy` 专用分支保持互斥。任务 5 已由弱点组件拥有 Screen-space WidgetComponent（`WBP_WeakPointMarker`）和无碰撞发光核心，使用 `M_WeakPointBracketUI` / `M_WeakPointCore`；原生投影跟随骨骼，真实时间节流更新遮挡、距离/FOV/DPI 和等级颜色。不修改 UI_Hud，不依赖编辑器工具运行。任务 6 时间弹和任务 7 回溯接入见下文；具体配置与验证见 [enemy-weakpoints-plan.md](../Implementation/enemy-weakpoints-plan.md)。

时间弹丸桥接同样位于 `BP_Item_Base.Fire_HitScan`。`UseTemporalProjectile=false` 时完整保留原射线伤害；启用后沿实际瞄准射线生成 `/Game/Blueprints/Weapons/Player/Projectiles/BP_TimeBullet`，起点为同一 TraceStart 加 40 uu 方向偏移，不混用动画枪口位置；40 uu 内遮挡仍回退射线结算。全局实例上限为 12。`BP_TimeBullet` 使用 `SM_GeneralBullet`，生成时移动组件不激活、碰撞关闭，通过幂等的 `ReleaseProjectile(Speed)` 延迟恢复运动。释放后以实际上一位置到当前位置的 Camera 通道线段检测首个阻挡，命中弱点敌人调用同一 `ResolveWeakPointDamage(HitComponent)`，每弹仅一次 Damage 后销毁；视觉不参与伤害。无弱点组件 Character 保留旧头/身体回退，非 Character 保留弹孔。`AC_TimeAbility` 只在 `FullStop` 开启实体弹，在进入 `BulletTime` 或退出能力时以默认 5000 uu/s 释放现存弹丸。

弱点视觉新增 `bWeakPointVisualsOnlyDuringTimeAbility=true`：Normal 隐藏，FullStop / BulletTime 显示；仍受总开关、存活、激活、距离和遮挡限制，只控制括号/核心、不关闭命中球。命中反馈按真实时间短暂强调最后命中的激活弱点，参数为 `HitFeedbackDuration` / `HitFeedbackStrength`，不会令隐藏点强制显现。进入/退出回溯清除瞬态反馈，之后按当前显示门控重新计算；Q 本身不会打开 T 能力的显示门控。

迁移后两种正式敌人都继承 `/Game/EnemyAITutorial/Enemies/BP_Enemy_Base`，真实血量统一由迁入的 `BPC_DamageSystem.Health` 持有。共享基类的 `Event AnyDamage` 将 TimeShuttle 的通用 Damage 适配到迁入的 `BPI_Damagable.TakeDamage`，并挂载原有 `AC_EnemyWeakPoints`、`AC_EnemyReverse` 与 `BPI_RewindableEnemy`；玩家武器、弱点和回溯调用方无需改写。旧实现细节仍见 [EnemyDamagePipeline.md](../Implementation/EnemyDamagePipeline.md)，当前迁移后的最终入口与验证见 [EnemyAIBehaviorMigration.md](../Implementation/EnemyAIBehaviorMigration.md)。

## 玩家近战入口

`BP_FPCharacter` 挂载 `/Game/Blueprints/Components/Combat/AC_MeleeHitDetector` 并实现 `/Game/Blueprints/Interfaces/BPI_MeleeAttackSource.RequestMeleeAttack`。接口根据第一人称相机方向和 `S_MeleeAttackSpec.Range` 生成轨迹，共享组件对 Pawn / WorldStatic / WorldDynamic 做一次球形扫掠、忽略攻击者、以首个阻挡命中提交 `Apply Point Damage`。拳头从 `BP_Weapon_EmptyHands` 传入 20 伤害、150 距离、18 半径；匕首从 `BP_Weapon_MeleeBase` 传入 25 伤害、200 距离、12 半径，`BP_Weapon_Knife` 继承该实现。

近战沿用武器原有攻击节奏：拳头即时判定，匕首在原 0.3 秒攻击时点判定；当前不是逐帧 NotifyState 扫掠。世界阻挡会先截断攻击，同一次单扫掠只解析一个 Actor。近战直接进入敌人现有 AnyDamage 链，不调用枪械弱点解析器；回溯守卫、受击和死亡仍由敌人负责。完整证据和扩展步骤见 [player-melee-combat.md](../Implementation/player-melee-combat.md)。

## 敌人对玩家伤害入口

`BP_FPCharacter` 使用现有 `Health` 作为剩余受击次数，默认值为 2。`Event AnyDamage` 将任意正伤害统一折算为一次受击；它用 `Get Real Time Seconds` 和默认 0.9 秒的 `DamageInvulnerabilitySeconds` 去重，因此多帧近战检测和全局时间倍率 0.01 都不会在同一保护窗内连续扣除。第一次受击启用 `/Game/Characters/Player/Camera/Materials/M_PlayerDamageVignette`；该后处理以屏幕矩形边缘距离生成暗红遮罩，不再产生圆形镜片边界。`/Game/Input/Actions/IA_DebugPlayerInvincibility` 在 `IMC_Player` 映射 F6，切换玩家原生 `Can Be Damaged`：开启时所有 Unreal Damage 在进入 AnyDamage 前被拒绝，关闭时恢复，状态不写入存档。第二次独立受击把 Health 置为 0、设置 `IsPlayerDead`、退出时间能力并恢复世界时间，随后锁定输入与移动、清零速度并立刻回到缓存 checkpoint；0.65 秒淡出结束后再次确认 checkpoint 变换，再恢复控制器朝向、Health、伤害接收、Walking 和输入，并清除暗角及淡出状态。

Shooter 的迁入步枪与行为树保留原有开火节奏，但射击终点生成 `/Game/Blueprints/AI/Shooter/Projectiles/BP_ShooterProjectile_Bullet`，由其父类的通用 `ApplyDamage` 进入玩家现有 AnyDamage 链。Melee 保留迁入的攻击选择、Montage/Notify 与队伍过滤，但四个最终伤害提交点已改为通用 `ApplyDamage`，同样进入玩家的两次受击、无敌帧、暗角、死亡和复活流程。checkpoint 资产和存档格式均未修改。

## 敌人回溯边界

弱点伤害的 2026-10-02 修订：`PDA_WeakPointTier.WeakPointDamage` 是每档弱点的独立伤害值（当前黄 50、红 25），每次有效激活点命中立即生效。已删除护甲耐久、击破门槛、武器 BreakPower 和敌人统一弱点伤害字段；BodyDamage 与仅弱点开关仍在 `AC_EnemyWeakPoints`。当前 GetWeakPointState 只返回激活/未激活及无效状态，没有护甲历史。

伤害调试统一由 `AC_EnemyWeakPoints` 在解析出正伤害后触发，并读取当前 `GM_FP.bDebugPrintEnemyDamage`（默认开启）。身体/未激活候选打印 `Damage: <数值>`，激活弱点打印 `CRITICAL Damage: <数值>`；0 伤害和开关关闭不打印。该开关只控制屏幕与 Output Log 文本，不进入伤害、视觉显示或回溯状态。绕过弱点解析器的直接 `ApplyDamage` 没有可靠命中上下文，因此不由此功能标记 Critical。

任务 7 使用 `/Game/Blueprints/Types/Structs/S_WeakPointRewindFrame` 保存五位置等级索引及初始化状态。`AC_EnemyReverse.WeakPointHistory` 与 HP/姿态同采样、同索引回放和裁剪，覆盖自动 Q 与 seek。恢复直接写入分配和命中球激活，不重新随机、不重建组件、不重放闪光或触发伤害/奖励。记录期间 Candidates / TierRules 顺序保持固定，设计师配置不属于快照。回溯中忽略显式重置；死亡保留期继续使用原存活历史，最终销毁敌人时清理其所有弱点组件。两类敌人的复活后手枪伤害、显示门控及历史清理已取得 PIE 证据；seek 仅验证正式组件事件，不代表物理 seek 输入验收。

迁入的共享敌人基类挂载 `EnemyReverse` 实例组件（`AC_EnemyReverse`）并实现 `BPI_RewindableEnemy`；读写血量适配到 `BPC_DamageSystem.Health`。组件继续接入原全局 reverse manager，按同一采样索引记录 Transform、浮点血量、骨骼姿态、Mesh Transform 和速度。

回溯期间停止 AI 与攻击；回到存活状态后恢复正常动画、移动与 AI，重新刷新远程感知。死亡对象保留到存活历史耗尽再清理。正常 AI 会重新决策，攻击蒙太奇不从历史帧继续执行。原示例 Status / Montage 组件硬依赖示例敌人，不要额外挂在当前两个敌人上。

详细行为、扩展入口和验证边界见 [EnemyReverse.md](../Implementation/EnemyReverse.md)。新的伤害、状态或 AI 功能应优先复用接口/组件；不要让敌人重新继承玩家蓝图。

## BP_TimeBullet 拖尾（2026-10-03）

`BP_TimeBullet.Collision` 下的 `BulletTrail` 为 `/Game/VFX/BulletTrail/AC_BulletTrail`，父类原生 StaticMeshComponent。它在 BeginPlay 设置 `SM_BulletTrailTaper` 并创建 `M_BulletTrail` 的独立 MID；TG_PostUpdateWork + Owner Tick prerequisite 确保在弹丸飞行/命中之后读取位置。长度由实际累计位移和可配上限决定，静止保持；瞬移和明显转向清零历史。世界绝对变换使厘米粗细不继承弹头缩放；组件不碰撞、不投影，Owner 销毁即清理。公开颜色、粗细、长度、强度、最小方向短尾及视觉开关；不写伤害、时间能力或输入。现有 Normal/BulletTime hitscan 保持，FullStop 生成的实体弹和后续释放使用此组件。当前仅直线弹道，未接独立敌弹类；50 项指定 PIE 检查和可视证据见 [bullet-trail.md](../Implementation/bullet-trail.md)。

同日普通射击扩展：`BP_Item_Base.Fire_HitScan` 的 UseTemporalProjectile=false 分支经 `SpawnHitscanTrail(ShotHit)` 生成 `/Game/VFX/BulletTrail/BP_HitscanTrail`，随后继续原即时伤害链。后者是独立原生 Actor 子类（不是 BP_TimeBullet），持有同一个 AC_BulletTrail；记录真实命中点/TraceEnd，按世界 DeltaSeconds 以默认5000cm/s推进、钳制终点、保持0.04游戏秒后清理。无碰撞/伤害、不计时停弹数量，FullStop 原路径保留。Normal/BulletTime 的样式入口是 BP_HitscanTrail.BulletTrail，FullStop 的是 BP_TimeBullet.BulletTrail；两模板可分别覆盖。新增42项指定PIE检查通过，旧图除单次视觉调用外语义保持；详见上述实现文档。

## DialogSystem（2026-10-12）

`/Game/DialogSystem` 保存逐句/整段 DataTable、可编辑 WBP_Dialogue、独立 Enhanced Input 与三个触发入口。`Plugins/TimeShuttleDialog` 为 UE5.6 原生 Runtime 模块，提供行结构、DialogueManager 状态机、2D语音完成回调、玩家控制锁和 GameInstance 级 DialogMemory；无需编辑器制作辅助工具运行。

BP_FPCharacter 的 DialogueManager 使用 AC_DialogueManager 项目适配子类；按下/持续输入经过 AllowGameplayInput，释放路径保留，死亡与显式主存档接入静态通知。碰撞 Trigger、继承 BP_Interaction_Base 的 NPC（现有 F 互动）和 Story 请求共享该管理器。新加玩法输入也须接门禁，禁止 ClearAllMappings 或 ResetIgnoreMoveInput 破坏其他系统状态。

跨关卡/磁盘记忆默认 false，侧车为原槽名加 `_Dialogue`，未开启自动存档/启动读档。正式台词表为空待填写，Tests 独立。84项指定运行检查、6个蓝图编译保存、插件三个目标构建及视觉证据见 [dialog-system.md](../Implementation/dialog-system.md)；不代表完整游戏已打包验收。

## 维护入口

- 实验室新版白盒：`/Game/Maps/Map_LabV39`，独立于旧 `Map_LabBridge`；建筑资源在 `Environment/LabV39`，桥接身份与旧图分离。使用 `GM_FP` 和现有角色，初始门禁为静态阻挡，尚未接入剧情解锁。2026-10-02 的构建、碰撞及角色通行证据见 [LabV39Whitebox.md](../Implementation/LabV39Whitebox.md)。默认启动地图仍为 `Map_Test`。

- 命名：[asset-naming.md](asset-naming.md)。
- 已验证行为及缺口：[implementation-status.md](implementation-status.md)。
- 协作与授权：仓库根 `AGENTS.md` 为唯一规则源；skills 只路由工作流程。
- 工具状态：[../MCP/SOP.md](../MCP/SOP.md)。没有已选定的 UE MCP 服务；发现本次实际工具后再选择编辑器 Python、Unreal-aware helper 或 GUI。
- 改动落地后更新受影响事实及证据日期，不能用本地架构核对冒充 Drive 来源刷新。
