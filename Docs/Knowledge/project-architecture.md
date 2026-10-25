# 当前项目架构

- Tutorial dialogue document migration (2026-10-22, P-008/LEVEL-002/P-106): BP_TrainingMission now configures 99 tasks across the existing eight checkpoints. Fifteen TD01-TD15 conversations contain twenty document lines with retained audio. Entry, valid-hit, defeated-enemy disappearance and actual melee-spawn gates replace old/missing calls. TD07 timing and TD10 enemy-disappearance wording follow explicit user confirmation. Old Energy/Arrival tables are removed after reference checks; two HUD timing bindings are synchronized. Final runtime 48/48, manual/cancel/retry/HUD 9/9, independent no-authoring-plugin cold checks 69/69 pass; four affected Blueprints compile cleanly. Map/controller/player/GI and disabled memory/persistence unchanged. Scripts and evidence are Git-ignored under LocalTests/TutorialDialogue20261022. Later combat uses native hit/damage fixtures, not a manual aiming playthrough. See [mission implementation](../Implementation/mission-system.md).

- Mission HUD (2026-10-19, LEVEL-002/P-106): AC_MissionObjectives and AC_TrainingObjectives drive ordinary UMG widgets from 8 page rows and 17 StepId bindings. English blue/black title/list UI replaces creation of WBP_TrainingObjective. Runtime is Blueprint-only; existing 86 flow tasks, level layout, Game Instance and disabled memory/persistence remain. Validation: 30 visible-window UI, 31 final training and 20 cold state assertions; 77 cold Blueprint compiles; three viewport sizes. Hidden embedded cold animation timing was not counted as passed. See [HUD implementation](../Implementation/mission-ui.md) and local-only evidence at `LocalTests/MissionUI/Docs/Implementation/MissionUI/validation.json`.

- MissionSystem Blueprint refactor (2026-10-18, LEVEL-002/P-008/P-058/P-106): BP_TrainingMission now authors 86 task components across eight checkpoints; removed 31 hardcoded Level Blueprint stage functions. Dialogue, owned control locks, role-bound Cutscenes, signals, background joins and failure/retry routes are extensible Blueprint tasks. 70 functional checks pass, followed by 44 ordinary-editor cold regression checks and five training startup checks; 73 Blueprints cold-compile without Blueprint warnings/errors. Preserved 189 original scene actors, 80 unrelated controller graphs and existing save files. Memory/persistence remain off. Later training objectives use disclosed fixtures; no manual aim, network or Cook acceptance. See [implementation](../Implementation/mission-system.md) and [validation](../Implementation/MissionSystem/validation.zh-CN.md).

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
- 输入（2026-10-15）：`/Game/Input/IMC_Player` 的 Q 对应 `/Game/Input/Actions/IA_TimeAbility`；用户已移除该映射上下文中的 `IA_Reverse` 绑定。右键对应 `IA_Aim`。玩家负责输入，AI 不实现玩家输入。
- 蹲起（2026-10-15）：`BP_FPCharacter.IA_Crouch` 的 Started 调用 `ToggleCrouch`，C 键按一次下蹲、再按一次站起，释放不改变姿态；切换读取原生 `bWantsToCrouch`，与冲刺/复活保持同步。CharacterMovement 管理碰撞与低顶重试，`UpdateCrouchView` 在 Mesh 更新后、SpringArm 更新前按实际时间平滑并校正视点。站立/蹲姿视点为胶囊底部上方 160/95 cm，蹲姿胶囊高 110 cm、速度 205 cm/s。快跑/冲刺先检查完整站立空间，复活恢复站起请求；Shooter 用 `GetActorEyesViewPoint` 瞄准。参数、教程低掩体验证与边界见 [FPS 蹲起](../Implementation/fps-crouch.md)。
- 近战：`/Game/Blueprints/AI/Melee/BP_MeleeNPC` → `/Game/EnemyAITutorial/Enemies/AI/AIC_Enemy_Base` → `BT_Enemy_Melee`。巡逻读取关卡中的 `BP_PatrolRoute`，攻击、动画、剑与行为树依赖均来自迁入资源。
- 远程：`/Game/Blueprints/AI/Shooter/BP_ShooterNPC` → 同一 `AIC_Enemy_Base` → `BT_Enemy_Ranged`。巡逻、感知、选位、枪械模型、动画与开火节奏来自迁入资源；开火终点改为生成 TimeShuttle 的 `BP_ShooterProjectile_Bullet`，继续沿用本项目命中与伤害判定。战术掩体复用 `EQS_FindCover` 和独立 `CoverLocation`；`BTT_ReserveAndMoveToCover` 以 275 uu 互斥半径管理分布式预约/占用并处理失败、Abort、死亡/回溯释放，`BTT_CoverPeekBurst` 依据目标方向选择左右 140 uu 侧身、短点射并归位后进入四秒冷却。Shooter 的 RVO 继续负责移动过程中的局部避让。
- 听觉：玩家枪械在 `BP_Item_Base.Fire_HitScan` 起点以武器 Actor 位置上报 `Gunshot` 听觉事件（近战分支静音）。共享 `AIC_Enemy_Base` 的 Hearing 范围为 2000 uu、刺激保留 5 秒；仅听到枪声时把该位置写入 `PointOfInterest` 并进入 Investigating，不会绕过视线直接设置 `AttackTarget`。近战与远程行为树复用同一调查分支。
- 玩家武器数据：`PDA_Item` / `PDA_ProceduralAnimValues` 是蓝图类；`Data/Weapons/Player/**/DA_*AnimationValues` 是实例，并非 DataTable。
- 敌人血条（2026-10-15）：`GM_FP` 的 `bShowEnemyHealthBars`（编辑器显示 `Show Enemy Health Bars`）默认开启。共享 `BP_Enemy_Base.RefreshHealthBarVisibility` 在血条初始化后及 Tick 读取当前 GameMode，仅在可见性变化时更新组件；同时要求敌人未死亡。现有及后来生成的近战/远程敌人均遵循该设置，时停中可切换。详见 [本次参数与修复记录](../Implementation/time-controls-health-bars.md)。
- 存档：`Blueprints/SaveSystem` 中的 `SG_Character` / `SG_SaveSlots`。本地 `Saved/SaveGames` 不进 Git，测试前后需保护真实存档。

## 时间能力核心入口

`/Game/Blueprints/Components/Player/AC_TimeAbility` 挂载在 `BP_FPCharacter` 上，负责 0–100 能量、Normal / FullStop / BulletTime 三态、均匀消耗恢复及零能量退出。当前 `ModeIndex` 映射为 0 / 1 / 2，阈值 **30** 归入 FullStop；`RecoveryPerSecond=20`，`DrainPerSecond=15`，按现实时间计量。组件和玩家现有回溯逻辑共同形成双向互斥门禁。

`AC_TimeAbility` 在 `FullStop` 使用全局时间倍率 0.01，并用倒数补偿玩家和当前武器；在 `BulletTime` 将能量 30→0 映射为世界倍率 0.2→1.0。`/Game/UI/Widgets/UI_Hud.SetTimeAbilityStatus` 接收能量百分比和模式索引，更新画面左侧的竖向进度条、100% / 30% / 0% 阈值、当前百分比、模式文字与颜色区域；`SetTemporalProjectileStatus` 在 FullStop 显示时间弹丸数量、12 发上限及满额提示。`AC_ProceduralAnimation` 的手部姿态过渡速率乘玩家 CustomTimeDilation，位置/旋转弹簧读取组件 Tick 的 DeltaSeconds，使时停中的瞄准进入/退出保持响应。详细范围和验证见 [TimeAbilityCore.md](../Implementation/TimeAbilityCore.md)。

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

2026-10-12命中清理补充：敌弹 `On Projectile Hit` 先执行 `StopFlightTrail`，有效性检查后销毁自身 `BulletTrail`，随后保持原命中表现。敌弹Actor延迟销毁（默认6秒）不再作为拖尾唯一清理时机。冷加载、编译和保存已核对；PIE未执行，详见[残留修复记录](../Implementation/bullet-trail.md)。

2026-10-12追加：敌人 `BP_ShooterProjectile_Bullet.CollisionComponent` 下已接入同一个 `AC_BulletTrail`，组件名为 `BulletTrail`。编译与定向保存成功，原有图表及类默认属性核对不变；本轮未启动PIE，敌弹运行视觉仍待验收。下面“未接独立敌弹类”为10/03历史范围，见[最新接入说明](../Implementation/bullet-trail.md)。

`BP_TimeBullet.Collision` 下的 `BulletTrail` 为 `/Game/VFX/BulletTrail/AC_BulletTrail`，父类原生 StaticMeshComponent。它在 BeginPlay 设置 `SM_BulletTrailTaper` 并创建 `M_BulletTrail` 的独立 MID；TG_PostUpdateWork + Owner Tick prerequisite 确保在弹丸飞行/命中之后读取位置。长度由实际累计位移和可配上限决定，静止保持；瞬移和明显转向清零历史。世界绝对变换使厘米粗细不继承弹头缩放；组件不碰撞、不投影，Owner 销毁即清理。公开颜色、粗细、长度、强度、最小方向短尾及视觉开关；不写伤害、时间能力或输入。现有 Normal/BulletTime hitscan 保持，FullStop 生成的实体弹和后续释放使用此组件。当前仅直线弹道，未接独立敌弹类；50 项指定 PIE 检查和可视证据见 [bullet-trail.md](../Implementation/bullet-trail.md)。

同日普通射击扩展：`BP_Item_Base.Fire_HitScan` 的 UseTemporalProjectile=false 分支经 `SpawnHitscanTrail(ShotHit)` 生成 `/Game/VFX/BulletTrail/BP_HitscanTrail`，随后继续原即时伤害链。后者是独立原生 Actor 子类（不是 BP_TimeBullet），持有同一个 AC_BulletTrail；记录真实命中点/TraceEnd，按世界 DeltaSeconds 以默认5000cm/s推进、钳制终点、保持0.04游戏秒后清理。无碰撞/伤害、不计时停弹数量，FullStop 原路径保留。Normal/BulletTime 的样式入口是 BP_HitscanTrail.BulletTrail，FullStop 的是 BP_TimeBullet.BulletTrail；两模板可分别覆盖。新增42项指定PIE检查通过，旧图除单次视觉调用外语义保持；详见上述实现文档。

## DialogSystem（2026-10-18）

`/Game/DialogSystem` 现为完整普通蓝图运行系统。AC_DialogueManager（ActorComponent）负责状态、优先级、语音完成和锁定清理；BP_DialogueSession 负责异步预加载及输入；BFL_Dialogue 提供查找、数据校验、输入门禁、死亡及存档接口；WBP_Dialogue 为可编辑 UMG。Types 中的两种 S_ 结构体与四种 ENUM_ 替代原生类型。TimeShuttleDialog 插件已从工程移除，无运行时制作工具依赖。

BP_FPCharacter 的 DialogueManager 组件及全部既有调用已迁移；原七张对白表内容逐字段保持，现有对白位于 Data_Dialog 与 Tutorial/Dialogue。碰撞、NPC 互动及 Story 仍共享唯一管理器。任务/Cutscene 通过开始、句事件及带结束原因的结束事件接入；仅 Completed 表示成功。训练关卡的阶段编排未在本轮重构。

最新解耦：对话管理器和函数库通过 `/Game/DialogSystem/Blueprints/BPI_DialogueMemory` 访问可选记忆，具体 GI 类直接引用为零。服务缺失或关闭时正常播放并保留局部一次性记录，显式存读失败安全返回；持久化仍关闭。本轮 基础 59/59、跨关卡/训练接入 15/15、默认原生 GI 无记忆服务 21/21、接口开关 11/11 通过，独立冷加载12蓝图通过，见 [记忆解耦](../Implementation/DialogSystem/MemoryDecouple20261018/README.md)。

GameInstanceClass 为 `/Game/Blueprints/Core/BP_TimeShuttleGameInstance`，直接继承 Engine.GameInstance，是项目通用入口；对话记忆作为 `Dialogue|Memory` 分类的一项功能，未来其他项目级服务另行加入。改名后冷进程59项基础＋15项跨关卡/训练接入回归通过，旧类路径引用为零；持久化默认 false，SG_DialogueMemory 侧车槽为原槽名加 `_Dialogue`，自动保存/读档仍未开启。旧原生存档需一次性转换，本机已备份并转换 QA 旧槽。验证：57 基础＋28 边界＋15 跨关卡/训练接入均通过；无辅助插件进程冷加载/编译 11 个运行蓝图，旧模块和两种制作模块引用为零。证据、恢复点及范围见 [dialog-system.md](../Implementation/dialog-system.md)，不代表全游戏打包或 S1–S7 完整通关复测。

## Training Room tutorial（2026-10-14）

2026-10-17（体验修复）：S1 开场自由行走，进入落石区域才触发对话并锁移动；落石预演中显示能量条与 Q 引导，玩家成功按 Q 后才播放 “In this state / Now, move” 的后续对话；结束后解锁移动，不耗能到安全区并自动恢复时间。S2 为单段（内部 step 2 → S3 的 step 5）：原 `BP_ShooterNPC` 真实动画开一枪 → Q 图标 → 第一次 Q 时停 → 玩家移出实际弹道 → 系统锁移动并提示再次 Q → 第二次 Q 恢复 → 确认真实弹丸经过且未受伤后进入 S3。`AC_TimeAbility.PollGuidedQInput` 在教学窗口单独处理物理 Q 边沿，普通 QTE 保留原 T 显示/超时；`SetTutorialMovement` 按拥有状态边沿管理锁，重试不叠加。旧静态射手保留在隐藏的 `LegacyS2` 分组。细节与验证见 [教程实施记录](../Implementation/training-room-tutorial.md)。

`/Game/Maps/Map_TrainingRoom` 的 Level Blueprint 拥有 S1～S7 的 Enter/Check 图表、CurrentStep/Phase 和阶段调度。原 `TimeShuttleTraining` 插件已移除。普通 `BP_TrainingController` 提供供弹、时间/位置观察及真实目标/战斗机制，不自行选择下一阶段；`AC_TrainingVisual` 处理独立Dissolve和碰撞，`WBP_TrainingObjective` 显示提示，`BPI_TrainingShot` / `BFL_TrainingImpact` 接入真实武器。资产均在 `/Game/Environment/TrainingRoom/Tutorial`；控制器的16组并行材质数组必须同时检查 CDO 与已放置实例覆盖。

每对象独立 MID 的 TS_PlanePosition 驱动原 MF_PlaneMask；S3～S5 公共桌与供弹连续保留，进入 S7A 近战预览时撤除。S5 常态射击连接体即可完成落石击杀，随后直接进入 S7A；旧 S6/可选入口重定向 S7A。S7A 出生点固定在实验室正前方；2026-10-18 已移除自动射击布局镜像，所有阶段使用编辑器摆放的固定初始变换。S7 敌人定位代理仅保留出生变换，已移除废弃静态机器人网格。共享接入点为 BP_Item_Base.ResolveShotDamage、BP_TimeBullet 的两种实际命中处理，以及 AC_TimeAbility / UI_Hud 的教学输入门控、能量条显隐与 T 提示等待模式。未登记目标走原伤害链；阶段/检查点记录仅在关卡实例内，不写教学存档。Backspace 重试当前小段，长按 Home 重置全教程。

S3 为四个固定的敌人骨骼模型，每人一个胸部弱点；S4 收为一个有左右行走动画的弱点敌人（step 6 → 9）。S7 使用原有近战/远程 NPC 及伤害系统，动态导航支持变动掩体。S7B 按提供的平面图布置四高四低掩体和中央悬石机关；首次自行到 P 后才补满生命/能量、12 发弹匣及 24 发备弹并生成敌人，死亡重试回 P 面向场内。机关落点下方可通行，真实连接体命中后落石可伤害范围内的真实敌人。完整冷启动真实输入通关、死亡重试、原地换场、实际离场和重置证据见 [training-room-tutorial.md](../Implementation/training-room-tutorial.md)。本次不改变默认启动地图或其他实验室的完成状态。

## 维护入口

2026-10-19 shared AI target selection: `AIC_Enemy_Base.IsEligibleAttackTarget` filters sight/damage candidates and final attack assignment. Hidden actors and unregistered non-player Pawns are excluded; the possessed player remains eligible without `BPI_EnemyAI`, and explicit combatants keep the original team comparison. This fixes enemies aiming at hidden range Characters instead of the player, without changing layout or mesh rotation. See [AI implementation and verification](../Implementation/EnemyAIBehaviorMigration.md#shared-attack-target-eligibility--2026-10-19).

2026-10-19 tutorial spawn facing: S7A/S7B retain fixed editor-authored spawn positions, but `BP_TrainingController.ResolveCombatSpawnFacing` supplies upright player-facing world yaw to deferred spawning on first entry and retry. This supersedes the 2026-10-18 proxy-rotation rule for these native enemies; stage-layout mirroring remains removed. See [tutorial implementation](../Implementation/training-room-tutorial.md#2026-10-19-final-combat-initial-facing).

- 实验室新版白盒：`/Game/Maps/Map_LabV39`，独立于旧 `Map_LabBridge`；建筑资源在 `Environment/LabV39`，桥接身份与旧图分离。使用 `GM_FP` 和现有角色，初始门禁为静态阻挡，尚未接入剧情解锁。2026-10-02 的构建、碰撞及角色通行证据见 [LabV39Whitebox.md](../Implementation/LabV39Whitebox.md)。默认启动地图仍为 `Map_Test`。

- 命名：[asset-naming.md](asset-naming.md)。
- 已验证行为及缺口：[implementation-status.md](implementation-status.md)。
- 协作与授权：仓库根 `AGENTS.md` 为唯一规则源；skills 只路由工作流程。
- 工具状态：[../MCP/SOP.md](../MCP/SOP.md)。没有已选定的 UE MCP 服务；发现本次实际工具后再选择编辑器 Python、Unreal-aware helper 或 GUI。
- 改动落地后更新受影响事实及证据日期，不能用本地架构核对冒充 Drive 来源刷新。

2026-10-17 tutorial target follow-up: `Environment/TrainingRoom/Tutorial/BP_TrainingTarget` is a passive Character with ShooterNPC mesh/materials, the original `AC_EnemyWeakPoints`, and the standard health-read interface backed by tutorial visual life state. Internal steps 5 → 6 → 7 → 9 teach ordinary static kills, static native weak-point hits, moving native weak-point stop-shot/resume, then the rock. `BP_TrainingController.StartTargets` selects actors and enables native presentation; `ResolveTrainingShot` asks the original resolver instead of checking a synthetic tutorial sphere tag. Production NPC and weapon defaults are unchanged. See [tutorial implementation](../Implementation/training-room-tutorial.md).

2026-10-17 range/plank revision: `BP_TrainingTarget` is the no-weakpoint body/rock-victim base with 100 health and hit/death animation state. `BP_TrainingWeakTarget` adds native weak points; both use controller-owned visual references. `BS_TrainingStrafe` blends local signed velocity through idle while keeping facing stable. `BP_TrainingController` owns support timing and slab geometry; it sets `PlankRetryRequested` and the Level Blueprint alone calls `EnterExercise` for retries, avoiding a private map reference. Final combat begins directly in `Enter_S7B`. Original production NPC, weapon and time-ability assets remain unchanged by this follow-up.

2026-10-17 visibility/contact repair: `BP_TrainingTarget.UpdateRangeTarget` applies the FullStop marker gate to both stationary and walking weak-point lessons. The final-arena rock footprint is unchanged; link base Z615 overlaps rock top Z620, stem bottom Z682 overlaps link top Z685, with link/stem aligned at Y−998. Native damage resolution remains unchanged.

2026-10-17 container/health follow-up: `Map_TrainingRoom.EnterExercise` invokes controller `RestoreStageHealth` before either routing branch, restoring Health/LastPlayerHealth to the current native full value 2. The final falling actor keeps its stable ID but uses `Stages/Meshes/SM_TS_SuspendedContainer`; user-adjusted root `(0,-1100,490)` is retained. Link/stem share Y−958 and overlap the container top at Z640. Final landing damage uses the revised 450×300 cm footprint plus capsule allowance.

2026-10-17 energy teaching: S1 phase 8 introduces the gauge before the falling-rock/Q preview. S2 adds protected cost dialogue, a bounded real-drain demonstration, the existing second-Q wait, then a safe-pass recovery explanation before Stage3. `DT_TutorialEnergy` supplies three replayable text-only conversations through the existing registry. Controller `EnergyDrainDemoActive` narrowly exempts the demonstration from the existing forced-stop top-up; cleanup clears it and restores gauge scale and saved rates. `UI_Hud.SetTutorialEnergyFocus` implements the short gauge-size pulse. Native time-ability input and rates are unchanged; see [tutorial implementation](../Implementation/training-room-tutorial.md).

2026-10-18 tutorial supply/death: `BP_TrainingAmmoPickup` subclasses native `BP_Item_Pickup`; `BP_TrainingController.UpdateNativeAmmoSupply` owns four native pickups and cooldowns using the retained slot transforms. Native interaction owns F focus and ADD AMMO (reserve comes from ItemData.MaxAmmo). `BP_TrainingTarget.BeginRangeRagdoll` matches `BP_Enemy_Base.Die` mesh physics death; ResetRangeRagdoll restores the live mesh and MaintainRangeHiddenPhysics stops hidden corpse simulation. Production NPC/pickup assets are unchanged. See [tutorial implementation](../Implementation/training-room-tutorial.md).

2026-10-18 combat reveal follow-up: `AC_TrainingVisual.HandleNativeDeath` owns the tutorial-only 2.2-game-second corpse hold/fade boundary, and `PreserveRagdollCollision` protects visible bodies from the generic actor-collision gate. `BP_TrainingController.RefreshWorldRevealRange` caches stage union bounds after layout selection; `AddVisual` assigns that interval to late native spawns. Thirteen tutorial material parents use `MF_TutorialWorldZReveal`, preserving the original Dissolve source and production materials. See [tutorial implementation](../Implementation/training-room-tutorial.md).

2026-10-18 fixed layout: `BP_TrainingController` no longer has `MirrorShootingLayout` or `bLayoutMirrored`. `SetLayout` selects stage visuals without player-position-based transform rewriting, and `PrepareRetry` restores the original visual cache without an inverse reflection. `UpdateCombat` uses the placed spawn-proxy rotation, retaining the existing capsule-height offset and later normal AI movement/turning. See [tutorial implementation](../Implementation/training-room-tutorial.md).

### Main menu city camera scene — 2026-10-25

`/Game/Maps/Map_MainMenu` now uses native-parent Blueprints GM_MainMenu, BP_MainMenuController and BP_MainMenuCameraRig with a CineCameraComponent. MainMenuScene was removed from Plugins and .uproject. The 68 saved actors comprise the original 67 plus one rig; original transforms are unchanged. Camera preview now follows real button hover through a reversible 1.2 s orbit; the earlier L path is retired (see the revision below). After repairing persisted CDO defaults, a fresh editor without MainMenuScene or TSVFXEditor passed 11 checks across 270 samples using built-in cross-frame L key simulation (not a claimed human keyboard test). All 62 city/character/endpoint transforms stayed fixed. No custom runtime dependency remains. UI/Niagara integration is implemented, and Win64 Development cold packaged camera/page/Quit/New Game regression passed. Final editor has no dirty packages and original saves are unchanged. Native UMG plus built-in Niagara needs no new runtime plugin. Pixel-identical art acceptance and Shipping/low-end validation remain open. See [implementation and evidence](../Implementation/main-menu-scene.md).


### Main menu hover-camera revision — 2026-10-25

Current Blueprint behavior supersedes the earlier L/dissolve flow: real mouse hover on New Game requests the front camera; OPTIONS/CREDITS/QUIT request side; empty space retains the last target. Keyboard/default focus does not request a camera, and the old L handler is a documented no-op. BeginNewGame keeps the empty-save-slot guard and locks menu input. If the rig is transitioning, phase 1 waits for OnViewSettled before CommitNewGame; if stable, commit immediately. There is no extra UI dissolve phase. TransitionSeconds remains editable on the level rig (1.2 s).

Controller, Button and Root compile/save; 64 scope/default checks pass, formatting preserves 31 graphs, authoring/cold hover runs each pass 37 checks. Three actual mouse-click travels reach Map_TrainingRoom with BP_FPCharacter, no visible menu or FX remnants; 62 fixed scene transforms stay identical. Cold editor has no TSVFXEditor, MainMenuScene is absent, .uproject hash is unchanged this task. Original five saves restored byte-for-byte after archiving test metadata; final world Map_MainMenu, PIE ended, zero dirty packages. One outdated comment was corrected; a cold test obscured by the BA welcome page was retained and rerun with the game viewport active. No font tests or new packaged build this revision; earlier Development package evidence is historical.

Canonical inspection record: `C:/Users/jason/Desktop/Capstone计划/开发文档/主界面/主界面UI.md`. Local scripts: `C:/Users/jason/Desktop/Capstone计划/tmp/main-menu-ui`; evidence: `Saved/Agent/MainMenuUI/hover_delivery_summary.json`. Runtime remains Blueprint/UMG/Niagara, without Python or custom runtime plugin dependencies.
