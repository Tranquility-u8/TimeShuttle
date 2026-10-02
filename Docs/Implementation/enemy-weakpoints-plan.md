# 敌人精密瞄准弱点实施方案

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

调伤害请打开对应 `Data/Enemies/WeakPoints/DA_WeakPointTier_*`，修改 `Weak Point Damage` 并保存，再重新 PIE。普通身体伤害仍在敌人 `WeakPoints` 组件中调整。正式括号视觉与 FullStop 实体时间弹接入尚未完成；不把这些路径算作本次已验证能力。取消耐久后后续回溯阶段应验证激活分配/等级的生命周期一致性，不再设计护甲历史。

## 以下为历史方案与阶段记录（伤害规则以上文为准）

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
