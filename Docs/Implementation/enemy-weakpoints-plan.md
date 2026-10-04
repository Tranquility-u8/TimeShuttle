# 敌人精密瞄准弱点实施方案

## 精密瞄准标识美术升级（2026-10-04）

- 弱点括号升级为参考图方向的精密瞄准标识：开放式左右箭括号、断开的六边形角线、分段内环、四向刻度和中空菱形核心。材质以像素稳定的程序化距离场绘制，96 px 左右仍保持清晰，不依赖原始生成图在缩小时的细线采样。
- 标识保留现有数据驱动颜色：黄色等级为暖黄，红色等级为高饱和红；`BracketColor`、`CoreColor`、`BracketLineWidth` 与强度/脉冲参数继续来自等级资产。`Glow`、`GlowRadius`、`LineWidth`、`Pixels`、`Opacity`、`Emphasis`、`PulseAmount`、`PulseSpeed` 均可通过动态材质调整。
- `M_WeakPointCore` 增加低幅实时呼吸与 Fresnel 边缘光；核心仍为无碰撞表现，不改变弱点碰撞、遮挡或伤害结算。
- 动态屏幕空间 `WidgetComponent` 在当前运行时不会稳定加入玩家屏幕层，因此 `AC_EnemyWeakPoints` 现在把五个标识 Widget 直接加入拥有者玩家视口，并使用骨骼附着的隐藏组件作为世界锚点，每帧投影位置、中心对齐并更新尺寸；销毁弱点视觉时同步 `RemoveFromParent` 并清空引用。
- PIE 以固定种子 4 验证 Shooter 与 Melee：两者均为五选二，索引 `[1,0,-1,-1,-1]`，红/黄标识颜色、材质、96 px 尺寸与可见性正确。Shooter 的 `shot showui` 实机截图确认红色头部和黄色躯干标识在 FullStop 中可见；四个相关蓝图最终编译 0 error / 0 warning，保存后无脏内容包或地图。
- 本机源素材保存在忽略目录 `SourceArt/UI/WeakPoints/`，运行时纹理位于 `/Game/UI/Textures/WeakPoints/T_WeakPointReticle_Mask`。恢复点位于忽略目录 `Saved/Agent/WeakPoints/VisualArtBackup_20261004/`。

## 时停瞄准、遮挡承诺与贴花修复（2026-10-03）

- FullStop 开火时立即缓存开火射线选中的目标、弱点组件、ImpactPoint/Normal 与 BoneName；悬停不伤害，释放后仍保留墙体/其他 Actor 的实际拦截，但敌人后续走位不会把已确认的弱点改判到另一肢体。
- 普通射线和时间弹统一调用 `SelectWeakPointHitComponent`。直接命中激活弱点按对应等级伤害；同一敌人的浅层肢体遮挡仅在射线位于扩展命中半径内、且遮挡深度不超过容差时放宽；深层身体和外部遮挡不放宽。视觉与伤害使用同一判定，因此标记不会再承诺一个实际不可命中的点。
- 新增可调参数：敌人弱点组件 `WeakPointAimAssistRadius=5`、`SelfOcclusionToleranceDepth=18`；时间弹 `LockedImpactTolerance=8`；时间能力 `ReleaseProjectileSpeed=30000`。单位均为 uu，可在敌人/玩家蓝图模板或实例中调整。
- 时间弹的 Character/弱点命中现在也生成 `M_Impact_Decal`，与世界表面共用一次性贴花入口；不改变弱点伤害、颜色等级或仅弱点开关。
- PIE 证据：视觉无遮挡为显示、15 uu 浅层同敌人遮挡仍选择激活弱点、30 uu 深层遮挡保留身体、外部遮挡保留外部组件，运行时墙体会隐藏标记；静止、300/600 uu/s 移动 Shooter 在主动退出和能量跨 70 两条释放路径中均为悬停 0、释放一次红点 25 Critical，且生成时间弹贴花。定向编译 7 个相关蓝图均为 0 error / 0 warning，保存后无脏内容包或地图。
- 本节替代任务 5 中“身体和手部一律遮挡”以及任务 6 中“完全按释放时实际组件结算”的旧描述；墙体、其他 Actor 与深层自身遮挡仍然优先。

## 任务 8：综合交接（2026-10-02）

任务 1–8 已完成。本节汇总最终运行规则、配置入口和阶段 8 回归证据；下方阶段记录保留实施过程，其中护甲/耐久、“击破”以及阶段未开始等旧描述均由本节和“当前规则”覆盖。

### 最终配置入口

- 在 `BP_MeleeNPC` / `BP_ShooterNPC` 的 `WeakPoints` 组件配置 `ActiveWeakPointCount`、`bWeakPointOnly`、`BodyDamage`、五个 `Candidates`、`TierRules` 与随机种子。当前默认五选二且同次不重复；BeginPlay 或显式新遭遇重置时抽取，连续命中不会重抽。固定种子只建议用于 QA。
- 每种颜色/等级在 `Data/Enemies/WeakPoints/DA_WeakPointTier_*` 独立配置 `WeakPointDamage`、括号/核心颜色、线宽和亮度。当前黄色 50、红色 25；颜色只是数据表现，不参与伤害分支，因此可继续增加等级资产并通过 `TierRules` 扩展。
- `bWeakPointVisualsOnlyDuringTimeAbility` 默认开启：Normal 隐藏，FullStop 与 BulletTime 显示；只控制括号和核心，不控制弱点碰撞或伤害。`bShowWeakPointMarkers` 是视觉总开关。
- `GM_FP.bDebugPrintEnemyDamage` 默认开启。普通部位输出 `Damage: <值>`，激活弱点输出 `CRITICAL Damage: <值>`；关闭后只停用调试文本。
- 未激活候选点按普通身体处理；`bWeakPointOnly=true` 时身体伤害为 0。项目不存在弱点护甲、耐久或击破次数。

### 阶段 8 最终验证

- 相关 63 个蓝图在最终清理后重新编译：0 errors / 0 warnings；内容包和地图均无未保存修改。两类敌人蓝图及 `Map_Test` 的现有关卡实例与组件默认配置一致，没有意外实例覆盖。
- 两类敌人的正式手枪/时间弹矩阵通过：26 项伤害与悬停、释放、遮挡、上限、近距回退等场景，加 14 项 Normal / FullStop / BulletTime 视觉门控；最终日志区间无 Error、Accessed None、Script Warning 或 Ensure。
- 回溯矩阵通过 19 个事件、194 个同步样本：弱点分配与同帧 HP/姿态同步恢复和裁剪；死亡、短回溯、复活、复活后真实手枪命中、10 项模式视觉、seek 及最终清理均通过。测试夹具已针对后台低帧率和 Shooter AI 弹丸遮挡做隔离；这些修正不改变正式资产。
- 综合闭环使用实际装备手枪命中旧 `BP_TrainingEnemy`，500→475 且仅消耗 1 发；T 进入 FullStop 后 Q 被阻止，退出 T 后全局时间倍率回到 1、武器时间弹标志清除；Normal 下 Q 可用且回溯期间 T 被阻止。退出 Q 后 Melee / Shooter 均恢复有效 Controller、运行中的 Brain、Walking、原动画类及非回溯状态。
- 阶段 8 未发现需要修改正式运行资产的新缺陷；本阶段只补充回归夹具与交接文档。最终证据位于忽略目录 `Saved/Agent/WeakPoints/`：`stage8-preflight.json`、`stage8-compile.json`、`temporal-qa-results.json`、`stage8-rewind-results.json`、`stage8-closure-results.json`。

### 验证边界

本轮认证的是编辑器 PIE、当前两类敌人、旧训练靶和装备手枪链路；其他武器家族完成编译兼容检查，但未逐把做实弹矩阵。没有声明打包构建、网络复制、所有分辨率/姿态或大量敌人压力测试通过。

## 全局伤害调试打印（2026-10-02）

- `GM_FP` 新增默认开启的 `bDebugPrintEnemyDamage`，作为当前 FPS 游戏模式下的统一调试开关；关闭后只停用屏幕/Output Log 文本，不改变命中、弱点反馈或伤害结算。
- `AC_EnemyWeakPoints.ResolveWeakPointDamage` 在返回正伤害时统一调用调试函数：身体及未激活候选点打印 `Damage: <数值>`，激活弱点打印 `CRITICAL Damage: <数值>`。仅弱点规则拦截、回溯拦截及其他 0 伤害不打印。
- PIE 使用 ShooterNPC 与实际装备手枪验证：身体 25、黄色激活点 50、仅弱点身体 0、关闭总开关后红色激活点仍扣 25。日志分别出现 `Damage: 25.0`、`CRITICAL Damage: 50.0`，后两项对应区间无伤害调试文本。直接绕过弱点解析器的脚本 `ApplyDamage` 不会被猜测为普通或 Critical。
- 组件、GameMode、武器基类、手枪、时间弹及两类敌人最终编译均为 0 errors / 0 warnings；Blueprint Assist 整理后功能连线与默认值签名未改变，定向保存后无脏内容包或地图。恢复点与本机证据位于忽略目录 `Saved/Agent/WeakPoints/DamagePrintBackup/`、`damageprint-pie.json` 和 `damageprint-finalize.json`。

## 任务 7：弱点回溯与生命周期（2026-10-02）

本节记录任务 7 完成时点；阶段 8 的最终综合交接见本文顶部。

- 新增 `Blueprints/Types/Structs/S_WeakPointRewindFrame`，保存五个位置的等级索引及初始化状态。没有护甲、耐久或击破历史。`AC_EnemyReverse.WeakPointHistory` 与现有位置、HP、姿态共用采样时机和索引，不启动独立定时器。
- `RecordEnemyState` 同步记录；`RestoreEnemyState` 同步恢复，自动 Q 回溯及 seek 两个方向都经过该入口。`TrimEnemyHistory` 同步处理滚动淘汰、自动回溯消耗和 seek 的未来历史裁剪。
- 恢复只写入 `RuntimeTierIndices` / `bInitialized` 并恢复五个命中球的激活碰撞，不重新随机、不重建视觉组件、不调用伤害/奖励入口。记录期间候选位置及 `TierRules` 顺序应保持固定；设计师配置、等级资产伤害数值不属于历史快照。
- 进入/退出回溯清除实时受击反馈与当前可见状态，后续按当前存活、遮挡和阶段 6 显示开关重新计算。不重放旧闪光。默认 `bWeakPointVisualsOnlyDuringTimeAbility=true` 保持不变，Q 回溯本身不会打开 T 能力的显示门控。
- 回溯期间已有伤害保护继续生效；新增显式重置保护，回溯中 `ResetForNewEncounter` 不销毁组件或重新抽取。退出后恢复原重置行为。没有弱点组件的目标采用空帧/安全跳过。
- 死亡对象仍由原有存活历史控制保留与清理；弱点球、括号、核心随敌人销毁，复活时沿用原组件，不叠加创建。

### 本阶段验证与边界

- `Saved/Agent/WeakPoints/rewind-qa-results.json`：Melee / Shooter 两类 PIE 测试通过。实际装备手枪黄点 100→50；显式重置产生另一组弱点后，Q 回溯恢复原种子分配；短回溯仍死亡、长回溯复活；复活后实际手枪红点 100→75。
- 逐帧核查位置、HP、姿态及弱点四组历史长度一致，存活计数等于正 HP 历史数。回溯中伤害解析返回 0，重置请求不改变分配或命中球身份。复活后每敌人仍只有五个球、五个括号、五个核心，普通时间默认隐藏。
- 保存后的 `rewind-finalqa-results.json` 再次通过完整链路，额外检查两类敌人复活后 Normal / FullStop / BulletTime、关闭门控及恢复默认门控共 10 项显示状态，括号/核心一致且不改变 HP；旧受击脉冲已衰减为 0。seek 恢复 75.5 小数血量与同帧分配，回到更早帧并裁掉未来后恢复 75。最终 PIE 区间 UTC 21:55:50–21:56:10 未出现 Error / Accessed None / Script Warning；既有手枪动画警告保留，早期测试夹具的后台低帧率退出等待已修正。
- seek 使用正式组件事件，在暂停世界的夹具中检查前后移动、同索引 HP/弱点恢复及未来裁剪；不是物理键鼠的 seek 控制验收。存活历史耗尽后，两个敌人、两个 Controller 和 30 个弱点相关组件全部失效。
- 死亡夹具使用 Unreal `ApplyDamage` 注入致死伤害；黄点及复活红点使用正式手枪 `BeginFire/StopFire`，Q 使用 Enhanced Input 注入。暂停 AI/姿态、清零散布与实际相机对齐仅用于隔离测试，不代表手感、敌人全姿态、大量敌人、打包或网络认证；未新增奖励计数器观测。
- 蓝图关键新图使用 Blueprint Assist 刷新尺寸、局部整理；新函数和原图窄接入点均补充职责/边界注释，未全图重排旧逻辑。整理前后有效连线/默认值语义一致；九个相关蓝图编译 0 errors / 0 warnings。定向保存后无脏内容包/地图，见 `rewind-finalize-report.json`。
- 本阶段前恢复点为本机忽略目录 `Saved/Agent/WeakPoints/RewindBackup/`，只备份弱点与敌人回溯组件；不回退用户已验收的阶段 5/6。临时编辑工具不是运行依赖。

### 本阶段查收（Shooter）

1. 保持默认显示开关开启；按 T 查看当前无遮挡弱点位置和颜色，然后退出 T。
2. 使用手枪射击已确认的弱点，记住血量变化；按住 Q 回到受击前再松开，血量应恢复。Q 本身不应让括号显现。
3. 再按 T 比较弱点：位置/等级应与对应历史一致，不因回溯重抽。退出 T 后再射击，伤害仍按相同等级结算。
4. 击杀后立即用 Q 回到存活时刻，松开后敌人恢复；重复开关 T，括号不应重叠或重放旧受击闪光。再次射击，弱点仍可正常扣血。
5. 另一次击杀后不回溯，等待存活历史耗尽：敌人及弱点表现应一起清理。完成后停止 PIE，无需保存试玩状态。

## 当前规则：按弱点等级直接伤害（2026-10-02 用户修订）

用户明确取消护甲概念，要求红、黄等不同弱点独立配置 `WeakPointDamage`。**本节替代下方历史方案中的耐久、破甲、Armored/Exposed、“第三枪才扣血”及敌人统一 WeakPointDamage 规则。**下方旧阶段证据保留作历史记录，不再作为当前验收标准。

- 每次命中激活弱点，立即返回该弱点等级资产的 `WeakPointDamage`，不累计命中次数，不消耗弱点、不在命中后失效。
- `PDA_WeakPointTier.WeakPointDamage` 是唯一弱点伤害配置入口：`DA_WeakPointTier_Yellow` 暂设 50，`DA_WeakPointTier_Red` 暂设 25；均支持独立小数值及 0，负数配置拒绝。这些是可调默认值，不是颜色硬编码；共享同一等级资产的敌人使用同一伤害值。
- 已移除等级 `MaxDurability`、组件 `CurrentDurability` 和组件统一 `WeakPointDamage`、武器 `WeakPointBreakPower`，结算函数也不再接收 BreakPower。只读状态为 Unavailable / Invalid / Inactive / Active。
- 敌人的 `BodyDamage`、`bWeakPointOnly`、候选位置、随机数量/种子、颜色和等级约束不变。五选 N 不重复，BeginPlay 或显式重置才抽取；不因连续命中重抽。
- 普通身体及未激活候选点：仅弱点开关开启时为 0，否则为 BodyDamage。未激活头部不恢复旧 100 点爆头。回溯进行中仍拒绝结算。
- 修改前恢复点：本机忽略目录 `Saved/Agent/WeakPoints/TierDamageBackup/`；本轮只改组件、等级类、武器分流函数和两个等级资产。前后比较确认两类敌人的数量、位置、随机和身体伤害配置没有被覆盖。
- 重新启动后的 PIE 手枪测试 **24 项通过**：两类敌人各连续红点四枪每枪 25、黄点两枪每枪 50、身体 25、仅弱点身体 0、未激活头部 25、墙遮挡 0；临时将红点伤害改为 12.5 后立即生效，同时黄点保持 50。测试恢复红点 25，不保存临时调参。证据：`tier-pie-results.json`、`tier-pie.log`。
- PIE 使用原有固定种子、暂停 AI/姿态、零散布与实际相机对齐夹具，通过真实装备手枪 BeginFire/StopFire，非注入伤害、非物理鼠标手感测试。所有有效敌人命中恰好结算一次；墙命中不调用敌人结算。最新运行未匹配到 Error / Accessed None / Script Warning。
- 重新编译组件、等级类、武器、两种敌人和手枪；本轮函数签名迁移过程曾出现旧 BreakPower 引脚的中间编译错误，重建调用后已修复，最新加载/PIE 无该错误。字段清理、最终编译/保存及布局证据见 `tier-change-report.json`、`tier-fields-verified.json`、`tier-layout-report.json`。

- 最终 Blueprint Assist 局部整理与目视检查完成，连线/有效默认值语义核对通过（忽略原生节点重建产生的等值数值序列化差异）；六个相关蓝图均 0 errors / 0 warnings。定向保存后没有脏内容包或脏地图；红色等级编辑面板确认 `Weak Point Damage=25`，无护甲字段。最终证据：`tier-handoff-report.json`。

### 新验收方式（Shooter 示例）

普通时间下使用手枪，不开 T/Q。保持等级/候选规则不变时，固定种子 4、数量 2 的已验证组合为红头、黄胸。假设敌人初始 HP=100：红点四次有效命中的血量依次 75/50/25/0；重开 PIE 后，黄点两次有效命中为 50/0。仅弱点开关开启时，无激活点的腿部不得扣血；关闭时按 BodyDamage 扣血。颜色调试球保持显示，不再有“击破”的验收步骤。

调伤害请打开对应 `Data/Enemies/WeakPoints/DA_WeakPointTier_*`，修改 `Weak Point Damage` 并保存，再重新 PIE。普通身体伤害仍在敌人 `WeakPoints` 组件中调整。括号视觉状态见下方任务 5；FullStop 实体时间弹接入尚未完成。取消耐久后后续回溯阶段应验证激活分配/等级的生命周期一致性，不再设计护甲历史。

## 任务 5：精密瞄准视觉（2026-10-02）

### 实现与配置

- 使用细线双侧括号、空心中心菱形、克制弧线/光晕以及骨骼附着的小发光核心，不包含耐久格、护甲值或击破状态。旧调试球默认关闭。
- 新资产：`/Game/UI/Widgets/WBP_WeakPointMarker`、`/Game/Materials/WeakPoints/M_WeakPointBracketUI`、`/Game/Materials/WeakPoints/M_WeakPointCore`。组件拥有五组原生 Screen-space WidgetComponent 和无碰撞核心；不修改 UI_Hud，不依赖临时编辑器工具运行。
- 等级资产的 `BracketColor`、`CoreColor`、`BracketLineWidth`、`CoreIntensity` 分别控制括号色、核心色、线宽及核心亮度；沿用红/黄独立配置和可扩展 TierRules，不按颜色硬编码伤害。
- `AC_EnemyWeakPoints` 的视觉参数：`bShowWeakPointMarkers=true`、`MarkerScale=1.45`、`MarkerMinSize=12`、`MarkerMaxSize=96`（UI 尺寸），`MarkerFadeStartDistance=2200`、`MarkerMaxDistance=3500`（UE cm），`MarkerNormalOpacity=0.85`、`MarkerBulletTimeOpacity=0.6`、`MarkerGlow=0.12`、`CoreRadiusScale=0.18`。FullStop 透明度为 1。
- 原生屏幕投影逐帧跟随骨骼；每次按距离、相机 FOV、视口宽度及 DPI 计算尺寸。`MarkerUpdateInterval=0.033` 按真实时间节流（下限 0.016），每敌人最多五条遮挡射线，不遍历全场敌人；尚未做大量敌人性能认证。
- 只显示激活、存活、在相机前方且在距离范围内的点。当前规则允许配置范围内的浅层同敌人肢体遮挡，并与伤害选择共用容差；墙、其他 Actor 和深层身体遮挡仍隐藏。超距/遮挡立即隐藏，恢复时淡入；远处渐隐。
- 显式重置前销毁旧表现组件，防止重复创建；初始化随机、命中球、伤害结算保持原规则。只读取时间模式/生命值，不写入其状态。任务 6 时间弹与命中反馈、任务 7 回溯生命周期未实施。

### 验证与恢复

- 恢复基线 `a7c3a03`；本机定向备份位于 `Saved/Agent/WeakPoints/VisualBackup/`。本次修改组件及直接关联的两个敌人/两份现有 World Partition 外部 Actor，新增一个控件和两个材质。临时绿色/青色测试已恢复原红/黄值；黄色数据资产发生定向重保存，不改变伤害规则。
- 两类敌人共 **44 项视觉 PIE 检查通过**：正反面、墙体遮挡、相机背后、距离/FOV、移动、动画跟随、独立颜色、FullStop/BulletTime、重置、隐藏和生命值可见性。生命值测试为夹具写值，不冒充完整击杀/复活验证。证据 `visual-qa-results.json`。
- 编辑器目视检查两种实际视口：1667×863（DPI 约 0.799）、2136×1296（DPI 1.2），红黄标记投影可见；证据 `visual-resolution-results.json`。尚未认证独立打包、多玩家或所有分辨率。
- 新图表使用 Blueprint Assist 刷新节点尺寸并局部整理，补充职责/边界注释；连线及有效默认值语义核对不变。组件、控件和两类敌人最终编译均 0 errors / 0 warnings，定向保存后无脏内容包/地图；证据 `visual-finalize-report.json`。
- 视觉开启后的真实手枪 **24 项 PIE 回归通过**（`visual-damage-results.json`），仍为黄 50 / 红 25，普通部位与仅弱点开关、未激活头部、墙遮挡、红 12.5 与黄 50 独立配置均通过。测试自动装备手枪、对齐相机并触发 BeginFire/StopFire，不注入伤害；测试后红值恢复 25。最新测试日志区间 UTC 20:16:17–20:16:42 未出现 Error / Accessed None / Script Warning；仍有既有动画重复 Slot、手枪 Additive 动画及 NavMesh 警告，不宣称打包验证通过。

### 本阶段人工验收

1. 打开 Map_Test，以 Shooter 为例：`WeakPoints` 保持 `bShowWeakPointMarkers=true`，`bDebugWeakPoints=false`；需要稳定样本时启用固定种子 4、数量 2（原规则下红头/黄胸）。编译、保存后 PIE。
2. 近距离观察细线括号、中心菱形与小发光核心；移动/瞄准时随骨骼更新。退远应缩小并渐隐，墙体或自身部位遮挡时不透视。
3. 切换 FullStop / BulletTime，检查标记仍跟随相机，透明度有区别。此步骤仅验收表现，不验收时间弹伤害。
4. 停止 PIE，在 Red/Yellow 等级资产修改 `BracketColor` 或 `BracketLineWidth`，重新运行确认独立生效。伤害仍分别由 `WeakPointDamage` 控制；不存在击破次数。

## 任务 6：时间弹与命中反馈、时间能力视觉开关（2026-10-02）

用户已验收任务 5。本阶段不进入任务 7 回溯适配。

### 当前行为与配置

- 敌人的 `WeakPoints` 组件新增 `bWeakPointVisualsOnlyDuringTimeAbility=true`。默认 Normal 隐藏，能力开启后的 FullStop 和 BulletTime 均显示；能量恰好 70 也显示，能力耗尽或主动退出后隐藏。判定依据是能力模式，不是单独比较能量。
- 关闭此开关可恢复普通时间显示。`bShowWeakPointMarkers` 仍是总开关；激活状态、存活、距离与遮挡规则仍生效。开关同时控制括号和发光核心，不修改命中球、随机分配、`bWeakPointOnly` 或伤害。没有显示不代表没有弱点伤害。
- `BP_TimeBullet` 悬停时不结算；释放后逐帧用上一位置到当前位置的 Camera 通道线段检测首次阻挡，并将实际 HitComponent 交给 `ResolveWeakPointDamage`。一枚弹最多提交一次伤害并销毁；释放调用有幂等保护。时间弹模型/根碰撞不再抢先触发胶囊 ActorHit，避免旧头部近似判定覆盖正式弱点。
- 两类正式敌人按等级 `WeakPointDamage` / `BodyDamage` / `bWeakPointOnly` 统一结算。无弱点组件的 Character 仍保留旧头/身体回退；非 Character 保留墙面弹孔。未修改敌人 AI 弹丸碰撞规则。
- 验证发现旧桥接方向虽来自瞄准射线、生成起点仍来自动画枪口，造成平行偏移。本轮仅将 `BP_Item_Base.Fire_HitScan` 时间弹生成位置改为同一 `TraceStart + Direction * TemporalMuzzleOffset`。40 uu 内首次遮挡的射线回退、12 发上限及原时间模式切换保持不变。
- 正伤害激活弱点命中触发短促亮度强调，不存在护甲/击破。可调 `HitFeedbackDuration=0.18` 秒、`HitFeedbackStrength=0.7`，按真实时间衰减；当前反馈突出最后命中的点。隐藏状态不会被命中强行点亮，退出能力后立即受显示门控约束。

### 验证记录

- `temporal-qa-results.json`：两类敌人共 26 项时间弹实际手枪开火测试通过；包含悬停不扣血、红/黄/身体、仅弱点、未激活头部、墙遮挡、三发/混色释放、12 发上限、第 13 发拒绝生成、近距墙/红点回退、目标移走后不预结算、独立红色 12.5。另有 14 项两类敌人的模式显示/总开关测试通过。
- `temporal-edge-results.json`：18 项显示状态检查与 6 项实际开火检查通过，补充恰好 70、能量耗尽、重复 Release 不改变已释放速度，以及墙面弹孔数量增加一次。
- `temporal-hitscan-results.json`：Normal 隐藏条件下 24 项真实手枪射线测试通过，黄 50、红 25/临时 12.5、身体及仅弱点规则不受视觉开关影响。命中脉冲即时值 0.7，并在等待后回到 0。
- `temporal-bullettime-hitscan-results.json`：整理/保存后再跑 BulletTime 可见条件下的同一 24 项射线矩阵，全部通过。
- 蓝图局部收尾完成：关键飞行、命中和视觉函数使用 Blueprint Assist 刷新尺寸并整理，其他本次新建图表采用编辑器定向布局及职责/边界注释，原武器图表未全图重排。有效连线/默认值语义比较一致；8 个相关蓝图 0 errors / 0 warnings；定向保存后无脏内容包/地图。见 `temporal-finalize-report.json`。最新实际测试区间 UTC 20:55:48–21:09:48 未出现 Error / Accessed None / Script Warning；早先失败记录包含旧枪口偏移问题及测试夹具修正，不计为最终通过证据。既有动画/导航警告不在本轮清理范围内。
- 测试夹具暂停 AI/姿态、对齐实际相机、清零散布、提高目标初始 HP，调用正式装备手枪 BeginFire/StopFire；没有注入伤害。不是物理鼠标手感、大量敌人、打包或网络认证。移动后的失靶案例验证实际命中时机，但不能代替全姿态/所有武器矩阵。
- 本机恢复点 `Saved/Agent/WeakPoints/TemporalBackup/` 保留本阶段前资产，任务 5 的既有工作不回退。临时数据资产伤害恢复红 25。主要改动为组件、时间弹、武器一处起点连线，以及直接关联敌人/关卡组件默认值；临时编辑器工具不成为运行依赖。

### 本阶段查收（Shooter）

1. 在 `BP_ShooterNPC` 的 `WeakPoints` 中搜索 `Weak Point Visuals Only During Time Ability`，保持勾选；`Show Weak Point Markers` 同样开启。关卡实例若有覆盖，以实例值为准。
2. PIE 普通时间应无括号/核心。按 T 开启能力，高于/等于 70 和低于 70 均能看到无遮挡激活点；退出或耗尽后隐藏。
3. FullStop 瞄准弱点开枪：悬停不扣血，释放命中后才按该档伤害扣血。同一弱点可重复受伤，不存在击破次数。
4. 停止 PIE，关闭新增开关再编译保存：普通时间也能看到标记，红黄伤害及身体规则不应改变。测试完可恢复默认勾选。

## 以下为历史方案与阶段记录（伤害规则及当前阶段以上文为准）

2026-10-02：按用户“一次性执行任务 3 和 4，然后等我验收”的授权，补齐子任务 2 的初始化、随机与敌人挂载，实施子任务 3/4 并取得组件测试及 20 项 PIE 射击证据。当前等待用户验收；任务 5/6/7 尚未实施。下方核查和 2A 记录为阶段历史，最新状态以本文末尾交接为准。

## 核查证据

- 起始分支 `dev/core-mechanics`，恢复基线 `cee3b74`，开始时 Git 工作区干净。
- 本轮没有运行中的交互式 Unreal 编辑器。使用独立 UE 5.6.1 Python commandlet 读取磁盘资产，没有调用资产修改、编译或保存 API。
- 七个资产均成功加载并重新导出图表：两个敌人、BP_Item_Base、BP_TimeBullet、AC_TimeAbility、AC_EnemyReverse、UI_Hud。
- 当前会话没有暴露 Unreal MCP；本机已有的临时 LocalBlueprintOps.inspect 在本轮成功读取图表。它只用于编辑器工具，不是游戏运行依赖；其写操作能力仍需按实际任务最小验证。
- 最新检查进程退出码 0，摘要 0 error / 15 warning。包含既有 Manny PoseAsset 和旧 PawnActionsComponent 警告。本轮未做显式编译或 PIE，不能将加载成功当作功能验收。
- 首次检查脚本使用了未暴露的自定义碰撞枚举，导致组件检查不全；已修正后重跑。当前已核实 Visibility / Camera 响应，Projectile 响应留待子任务 4/6 定向读取，不能由预设名推断全部响应。
- 本地证据位于忽略跟踪的 `Saved/Agent/WeakPoints/`：preflight.json、七份 *_graphs.json、inspect.log。保留为后续起点。

## 当前实现与依赖

| 入口 | 本轮发现 | 实施影响 |
| --- | --- | --- |
| BP_Item_Base.Fire_HitScan | 两个 Line Trace 节点使用 TraceTypeQuery2、非复杂射线；Select Float 仍为 100/25 | 接入统一命中解析；通道映射与实际遮挡在子任务 4 验证 |
| BP_TimeBullet | 独立 EventGraph 伤害入口、ReleaseProjectile | 实体弹实际命中时解析弱点，不能生成时提前扣耐久 |
| BP_MeleeNPC | Mesh 阻挡 Camera，胶囊忽略 Camera；两者忽略 Visibility；血条 Widget 阻挡 Visibility | 不能直接拿 Visibility 当弱点遮挡检测；血条不得拦截新检测 |
| BP_ShooterNPC | Mesh、NPC_AimMesh 与胶囊均阻挡 Camera，忽略 Visibility | 处理胶囊先拦截问题；弱点附着实际主体 Mesh，不选辅助瞄准网格 |
| 两种敌人模型 | 分别引用不同目录下的 SKM_Manny_Simple；head、spine_03、upperarm_l、lowerarm_r、hand_r、thigh_l 均存在 | 骨骼可作为候选锚点；表面偏移需在编辑器按两种敌人分别调整 |
| AC_TimeAbility | ApplyTimeState、ApplyTimeScale、UpdateTimeAbilityHUD 等图表；未发现组件内后处理材质链 | 时间状态接入可复用；灰蓝环境与扫描不得宣称已有，也不作为弱点阶段的前置条件 |
| UI_Hud | 已有 SetTimeAbilityStatus、SetTemporalProjectileStatus 及武器 UI | 增加独立 Marker 层，保持已有能量和弹丸计数 |
| AC_EnemyReverse | RecordEnemyState、RestoreEnemyState、TrimEnemyHistory、BeginEnemyRewind、EndEnemyRewind 及 seek 回放 | 弱点状态必须共用现有采样索引和历史裁剪 |

资产注册表确认两个敌人各有 Map_Test 外部 Actor 引用。Shooter 还被 Controller、StateTree 及任务/条件引用；这些列为兼容检查对象，不默认修改。BP_Item_Base 被多个武器子类、玩家、动画与 UI 引用，修改必须以弱点接口分流，保留无接口目标的旧行为。

## 配置的唯一归属

| 配置位置 | 字段和初始值 | 规则 |
| --- | --- | --- |
| 敌人 AC_EnemyWeakPoints | ActiveWeakPointCount、bWeakPointOnly、BodyDamage=25、WeakPointDamage=50 | 保留用户在敌人侧调参的约定；支持蓝图默认值和实例覆盖，不在等级资产再存相同伤害 |
| 敌人候选数组 | 五个唯一 CandidateId、BoneName、局部变换、命中形状/尺寸、标记偏移、AllowedTiers、正面分组 | 编辑位置不改变稳定 ID；碰撞尺寸与屏幕标记尺寸分开 |
| 敌人生成规则 | TierRules 数组，各项含 Tier、MinCount、MaxCount、Weight；可选固定 RandomSeed | 不硬编码 GuaranteedYellowCount 等颜色字段，新增等级只增加数据 |
| PDA_WeakPointTier 及实例 | TierId、MaxDurability、BracketColor、CoreColor、MarkerStyle、亮度、线宽、命中与击破表现 | 黄色耐久 1，红色 3；颜色不参与逻辑判断 |
| 玩家武器 | WeakPointBreakPower=1；后续其他武器可独立配置 | 一枪/三枪的承诺以标准手枪为基准；武器不再复制敌人 BodyDamage/WeakPointDamage |
| Marker 表现配置 | 距离尺寸曲线、显示距离、透明度、瞄准强调、状态淡入淡出 | 所有等级沿用参考图的细线括号，可选轻微形状差异 |
| 弱点运行时状态 | CandidateId、TierId、CurrentDurability、Inactive/Armored/Exposed | 状态变化更新视觉；回溯写回状态时不再次造成伤害或播放奖励 |

时间弹生成时保存 ShotId、发射者/武器身份与 BreakPower。敌人自身的伤害配置在实际命中时读取，不在悬浮弹上再建立一套敌人伤害默认值。首版配置在一次敌人生命周期内保持稳定；运行中调参不承诺追溯影响已发生的伤害。

## 生成与结算规则

1. 完成实例配置初始化后，从五个位置无重复选择指定数量，再分配等级。先满足等级数量和位置允许规则，再按权重填充；无解配置显示明确错误，不静默生成无敌敌人。
2. ActiveWeakPointCount 必须在 0–5；bWeakPointOnly=true 时至少为 1。检查重复 ID、缺失骨骼、空等级池、非正耐久、非正 WeakPointDamage 和不可能的 Min/Max 组合。
3. 新生或显式 ResetForNewEncounter 才重新生成；进出时间模式、回溯复活不重抽。仅弱点受伤敌人至少保留一个正面候选；是否瞬间被姿势遮挡由实际可见性决定。
4. Armored 命中减少耐久，未击破时首版不扣敌人血量。达到零的那一枪造成一次 WeakPointDamage，并进入 Exposed。后续每次命中核心仍造成 WeakPointDamage；无额外击破奖励或伤害溢出。
5. 未激活位置、普通身体及未命中核心的护壳边缘，按 bWeakPointOnly 决定 0 或 BodyDamage。头部若未激活也按身体处理，不叠加旧 100 点爆头。
6. 一个标准手枪射击最多对一次有效阻挡命中结算一次；多颗时间弹按实际到达顺序处理。世界遮挡优先，不能隔墙或穿过身体命中背面弱点。
7. 无弱点接口的训练靶、环境和其他对象保留原路径；范围外武器仍须做共享基类兼容检查，不顺带重写全部武器规则。

## 视觉范围

以用户选中的精密瞄准参考图为视觉目标：细线侧括号、中央菱形、少量圆弧、克制光晕。黄色和红色共用基本轮廓，耐久用细小刻度表示。世界核心跟随骨骼，HUD 括号使用世界坐标投影；隐藏未激活点，不做默认穿墙提示。

参考图中的重装模型不是当前项目角色。首版还原标记与核心视觉，使用现有 Manny；替换角色模型不在本任务。屏幕括号不能无限远保持大尺寸，尺寸与实际投影区域适度关联，远距离淡出，避免显示为大靶但实际无法命中。

HUD 的软光使用 UI 材质/图形实现；不承诺 UI 会直接获得场景 Bloom。世界核心的发光和后处理颜色保留要在实际渲染下验证。暂不为假定已有的灰蓝滤镜启用全局 Stencil。只有后续确实接入会改变核心颜色的后处理时，才决定是否需要 Stencil 和相关配置。

FullStop 显示完整标记，BulletTime 降低透明度；退出时给予短暂命中反馈显示期。世界内命中发生后才显示成功，悬浮子弹不提前扣格。用真实经过时间推进 UI 动画，避免 0.01 世界倍率使反馈近乎停止。

## 受影响资产

计划新增：

- `Blueprints/AI/WeakPoints/AC_EnemyWeakPoints`、`BP_WeakPointTarget`、`PDA_WeakPointTier`。
- `Blueprints/Interfaces/BPI_WeakPointTarget` 及 `Blueprints/Types/Structs/S_WeakPoint*`、所需状态枚举。
- `Data/Enemies/WeakPoints/DA_WeakPointTier_Yellow`、`DA_WeakPointTier_Red`。
- `UI/Widgets/WBP_WeakPointMarkerLayer`、`WBP_WeakPointMarker`。
- `Materials/WeakPoints/`、`VFX/WeakPoints/` 下的必要表现资源；具体数量随可见效果验证收敛。

计划定向修改：BP_MeleeNPC、BP_ShooterNPC、BP_Item_Base、BP_Weapon_Pistol、BP_TimeBullet、UI_Hud、AC_TimeAbility、AC_EnemyReverse。回溯适配若需要公开新读写契约再扩展 BPI_RewindableEnemy；不更改既有健康字段归属。

Config/DefaultEngine.ini 可能需要新增弱点检测通道。通道设计在子任务 4 先验证，再同时检查子任务 5 遮挡和子任务 6 弹丸；不全面改动 AI/相机碰撞。相关 Map_Test 外部 Actor 仅在确需保存且确认实例关联后定向保存。Controller、StateTree、动画、其他武器为依赖验证范围，不默认重保存。

## 实施阶段与验收

| 子任务 | 状态 | 交付条件 |
| --- | --- | --- |
| 1 核查与配置 | 完成 | 重新读取资产、记录依赖和缺口、固定配置归属、确认恢复点 |
| 2 候选与随机 | 已实现；动态姿势下位置待用户查收 | 五个位置、无重复随机、等级约束、初始化与显式重置；两类敌人已挂载 |
| 3 耐久状态 | 已实现并测试，待用户验收 | 黄色 1 次、红色 3 次击破；击破及暴露后命中造成弱点伤害 |
| 4 射线伤害 | 20 项 PIE 射击通过，待用户验收 | 两类敌人的护壳、核心、身体、未激活头部、仅弱点与遮挡 |
| 5 括号视觉 | 未开始 | 参考图细线风格、两色配置、动态跟随、遮挡、不同距离及分辨率可读 |
| 6 时间弹与反馈 | 未开始 | 悬停不提前结算，释放后多弹命中顺序准确；近距回退仍遵循统一规则，数量上限回归 |
| 7 回溯 | 未开始 | 自动/seek 回放、裁剪、死亡复活恢复同帧血量/耐久/状态，不重复奖励 |
| 8 综合交接 | 未开始 | 输入与时间倍率恢复、敌人 AI、旧目标、实例覆盖、保存范围和使用说明完成 |

每项蓝图改动均局部整理、结构注释、编译、Output Log 检查、定向保存，并在适用阶段 PIE 取得证据。子任务 1 无蓝图修改，不运行功能验收。打包、联网和大规模压力认证不在首版验收声明内。

## 恢复与接续

子任务 1 只新增本文和忽略跟踪的检查资料/度量。子任务 2A 新增下列六个配置资产，没有改写现有敌人或关卡。已对两个敌人建立本地定向备份，2A 收尾时原件与备份 SHA-256 一致。开始下一批前重新检查 Git 和编辑器未保存状态，保护之后新增的用户工作。

如需恢复后续改动，先核对备份/基线与当前差异，再仅恢复本任务资产；二进制资产通过安全的编辑器关闭/重载流程处理，不自动 reset 整个分支，也不创建提交。按最终依赖顺序编译和复验。

度量 TaskId 为 `20261002-weakpoints`，跨子任务复用。子任务 1 查收时 Pause，继续时 Resume，整个任务验收后 Finish。

## 子任务 2A：配置资产交接

新增并定向保存六个资产：

- `/Game/Blueprints/AI/WeakPoints/PDA_WeakPointTier`：TierId、MaxDurability、BracketColor、CoreColor、MarkerStyle、CoreIntensity、BracketLineWidth。
- `/Game/Data/Enemies/WeakPoints/DA_WeakPointTier_Yellow` 和 `DA_WeakPointTier_Red`：耐久 1 / 3，线宽 1.5，亮度 3，MarkerStyle=PrecisionBrackets。颜色为可编辑 LinearColor，逻辑不依赖颜色判断。
- `/Game/Blueprints/Types/Structs/S_WeakPointCandidate`：稳定 ID、骨骼、局部变换、球形命中半径、标记偏移、允许等级、正面标志和选择权重。首版候选采用球形；该尺寸不等于屏幕括号尺寸。
- `/Game/Blueprints/Types/Structs/S_WeakPointTierRule`：等级引用、最小/最大数量、权重。
- `/Game/Blueprints/AI/WeakPoints/AC_EnemyWeakPoints`：公开配置字段与五项 Candidates、两项 TierRules；本批没有 BeginPlay 逻辑，禁用 Tick，尚未挂到敌人。

组件默认值：ActiveWeakPointCount=2，bWeakPointOnly=false，BodyDamage=25，WeakPointDamage=50；固定种子开关默认关闭，种子值 12345。黄色 MinCount=1、红色 MinCount=0，两者 MaxCount=5、Weight=1。所有候选暂允许两种等级。

| 稳定 ID | 骨骼 | 初始半径（uu） |
| --- | --- | --- |
| Head | head | 7 |
| Chest | spine_03 | 10 |
| LeftUpperArm | upperarm_l | 7 |
| RightForearm | lowerarm_r | 7 |
| LeftThigh | thigh_l | 9 |

当前 LocalTransform 是骨骼中心的单位变换，MarkerOffset 为零，FrontCandidate 均为 true。这是待定位的初始配置，不是已验证的身体表面位置或实际可见性；两种敌人的表面偏移与正面判定需后续在编辑器分别查收。

验证与限制：

- 两个新蓝图编译均为 0 error / 0 warning。创建时浮点类型接口曾回退为整数；已定向改为 UE 的 real/double，并重新保存、重新加载核验小数线宽 1.5、浮点耐久和伤害值。
- 在不加载临时 BlueprintOps 工具的新 UE 进程中成功读取全部六项资产；逐项验证五个唯一 ID、骨骼名、半径、单位缩放、等级引用、两项规则、1/3 耐久及颜色。验证日志没有 Error/Warning 匹配项。
- 本地证据：`Saved/Agent/WeakPoints/configuration-repair.json`、`configuration-verified.json` 和对应日志。原始 configuration-report.json 是修复前记录，不作为最终类型验收结果。
- 交互式编辑器已打开 AC_EnemyWeakPoints 的 Class Defaults，目视确认绿色编译状态、All Saved、数量 2、伤害 25.0/50.0、五项 Candidates、两项 TierRules；展开首项确认 Head/head、半径 7.0、两项允许等级。界面保留在此供用户查收。
- 现有两个敌人、武器、关卡均未改动。没有新增功能图表或运行时逻辑，因此本批不声明随机抽取、碰撞、击破或 PIE 通过；后续逻辑批次仍需图表整理、注释和 PIE。
- 下一批：先完成编辑器配置面板查收，再实施无重复随机抽取、等级约束/无解检查、生命周期初始化及两种敌人挂载；仍属于子任务 2，不进入子任务 3。

## 子任务 3/4 联合交接（含子任务 2 必要前置补齐）

### 保存内容与运行入口

- `AC_EnemyWeakPoints` 已实现配置校验、约束随机、初始化/重置、五个骨骼附着 SphereComponent、耐久结算及只读状态查询。主 Mesh 为挂载对象，两类敌人分别设置表面偏移；候选 ID 和半径沿用 2A。
- 两个敌人新增 `WeakPoints` 组件。主 Mesh 阻挡 Camera；胶囊、辅助 NPC_AimMesh、血条 Widget 忽略 Camera，避免抢先遮挡弱点射线；其他物理通道不改。
- `BP_Item_Base.Fire_HitScan` 的正式目标分支接入 `ResolveShotDamage`，读取命中目标的弱点组件，然后复用原有单次 ApplyDamage。训练靶分支和无组件目标保留旧规则，近战保留 legacy 值。新增武器 `WeakPointBreakPower=1`。
- 当前不需要 `BP_WeakPointTarget` Actor 或新增 BPI：目标识别由命中 Actor 的组件承担，球体仅为 Actor 自有组件；状态名由激活索引/耐久派生。未创建额外运行时 C++ 依赖或新碰撞通道。
- 保存范围：两个敌人、BP_Item_Base、六项弱点配置/运行资产；手枪仅做依赖编译。未保存关卡、外部 Actor、Controller、StateTree、时间弹或回溯组件。

### 配置与边界

- 敌人蓝图选择 `WeakPoints` 组件，可编辑 ActiveWeakPointCount、bWeakPointOnly、BodyDamage、WeakPointDamage、Candidates、TierRules 和随机种子。当前默认数量 2、身体 25、弱点 50、仅弱点关闭。
- 等级资产决定颜色与耐久，颜色不参与伤害判断。黄色耐久 1，红色 3；黄色规则最低 1，因此默认可能抽到两个黄色，不保证每个敌人都有红色。需保证红色时将红色 MinCount 设为 1，保持约束可解。
- 当前枚举全部有效分配并加权抽取，支持 **1–4 项 TierRules**（五个位置最多 3125 种组合）。新增颜色需新增等级资产并加入候选 AllowedTiers 和 TierRules；超过四档会明确报错，不能宣称无限扩展。大量敌人同时生成的性能尚未认证。
- BeginPlay 初始化一次，重复 Initialize 不重抽。只有新实例或显式 ResetForNewEncounter 重置；先销毁旧球体再创建，不因时间模式变化重抽。配置失败记录 InitializationError 并输出诊断，不静默忽略约束。
- Armored 命中消耗 BreakPower，尚未击破为 0 点 HP 伤害；击破那枪及 Exposed 后命中为 WeakPointDamage。未激活头部与身体相同，不再沿用 100 点爆头。回溯进行中拒绝弱点结算，但耐久历史恢复仍属任务 7。
- `bDebugWeakPoints=true` 暂时每 0.1 秒绘制黄色/红色命中范围球；可关闭。它不是正式发光核心/括号，也没有击破动画或耐久刻度。当前验收要通过敌人血量和组件 CurrentDurability/GetWeakPointState 观察，不能期待球体击破时消失。

### 验证证据

- `Saved/Agent/WeakPoints/component-test.json`：两类敌人各 8 个固定种子，检查两点不重复、黄色最低数量、重复初始化稳定、无效数量拒绝、黄色 `[50,50]` / 红色 `[0,0,50,50]` 返回值、身体 25 与仅弱点 0。此处直接调用真实组件函数，**不是实际射击证据**。
- `pie-results.json`：实际 PIE 玩家装备手枪，调用 BeginFire/StopFire，20 次射击均各消耗一发弹药。两种敌人各覆盖红色前两枪 0、第三枪 50、暴露后 50、黄色第一枪 50、黄色暴露后 50、身体 25、仅弱点身体 0、未激活头部 25、墙体遮挡 0。目标命中均结算一次；墙体命中不调用敌人弱点结算。
- PIE 夹具：固定种子、暂停 AI/姿势、生成默认 Controller、临时提高初始血量、清除测试散布，在开火时对齐实际 FirstPersonCamera。扣血来自真实武器射线链，**未注入伤害**；不是物理鼠标输入/移动靶手感验收，不改正式武器的瞄准或散布默认值。
- 最新 PIE 日志完成标记 `2026.10.02-18.08.41 WEAKPOINT_PIE_FINISHED True`，未匹配到 Error、Accessed None 或 Script Warning。旧资产加载/预览警告单独保留，不宣称整个项目零警告。
- 收尾已对新增图表做布局、职责/时序/边界注释；关键结算及武器分流使用 Blueprint Assist 刷新尺寸并整理，其他新图表用编辑器内定向布局。原 Fire_HitScan 不全图重排。整理前后功能节点、默认值及有效连线比较一致（reroute 仅影响走线）。
- `final-layout-report.json`：组件、武器基类、两敌人、手枪均编译 0 error / 0 warning；定向保存后无未保存内容包/地图。编辑器目视核查新分流布局及注释；武器最终复核另见 `review-response.json` 与 `weapon-reviewed-graphs.json`。
- 本地恢复点 `Saved/Agent/WeakPoints/Stage34Backup/` 保留本轮修改前两个敌人、武器基类及 2A 组件。不得自动覆盖后续用户修改。

### 本次查收（普通时间、手枪）

1. 打开 Map_Test，进入 PIE，分别观察两类敌人活动中的黄/红命中球位置；默认每个敌人随机两个位置，未保证必有红点。
2. 命中黄色一次即进入 Exposed 并扣 50；红色前两次不扣血，第三次扣 50；之后核心命中继续扣 50。正式击破视觉尚未制作。
3. 射击普通部位扣 25；在敌人 WeakPoints 组件开启 bWeakPointOnly 后重新 PIE，普通部位不扣血。未激活头部不能一枪按旧 100 点爆头。
4. 检查墙体遮挡和实际移动瞄准体验；三处肢体候选的不同姿态/角度仍需手动验收，不能用头胸测试代替全姿态认证。

本次不推进任务 5；FullStop 实体时间弹仍走旧规则（任务 6），回溯不会恢复弱点耐久历史（任务 7）。不要把时间弹/回溯结果作为当前 3/4 的已完成承诺。训练靶和其他武器家族本轮仅保护原图表路径，完整行为回归留给任务 8。
