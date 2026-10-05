# 时间弹丸桥接

## 目的

为“高能量时停期间可开火、弹丸在枪口前悬浮、解除后保留方向并延迟释放”提供实体弹丸链路，同时不破坏正常状态下已经可用的射线武器伤害。

## 已实现资产与接口

### 2026-10-03 瞄准承诺与命中反馈修复（当前规则）

FullStop 开火时，`BP_Item_Base` 先用与普通射线相同的弱点选择规则确定目标 Actor、命中组件、位置、法线与骨骼，再交给 `BP_TimeBullet.InitializeLockedImpact` 缓存。悬停阶段仍不造成伤害；离开 FullStop 后，弹丸用飞行扫掠保留墙体和其他 Actor 的真实拦截，但到达原始目标或穿过锁定位置时按开火瞬间缓存的组件结算一次。这样敌人释放后的走位不会把玩家在时停中已经确认的弱点瞄准改判到其他肢体。

弱点组件新增共享选择函数：直接命中弱点球时保持精确命中；首个阻挡是同一敌人的浅层肢体时，只有射线仍落在弱点扩展半径内且遮挡深度不超过容差才重定向到激活弱点；深层身体和外部遮挡继续阻挡。视觉显隐和普通/时间弹伤害共用这一规则，避免“标记显示可打、实际却算身体”的错误引导。当前默认参数为 `WeakPointAimAssistRadius=5`、`SelfOcclusionToleranceDepth=18`、`LockedImpactTolerance=8`（uu）。

释放速度现为 `30000 uu/s`。普通射线和时间弹统一为 Character、弱点及世界表面生成 `M_Impact_Decal`；不再把 Character 命中排除在时间弹贴花之外。PIE 已覆盖静止与 300/600 uu/s 移动 Shooter、主动退出与能量跨入 BulletTime 两种释放边沿、浅/深自身遮挡、外部墙体以及贴花生成；悬停伤害均为 0，红色锁定弱点释放后均为一次 25 点 Critical 伤害。

### 2026-10-02 弱点接入更新（替代下方旧碰撞/伤害描述）

`BP_TimeBullet` 现在在释放后使用上一位置到当前位置的 Camera 通道线段检测真实首次阻挡，根碰撞在初始化时关闭，悬停不检测/不扣血。命中带 `AC_EnemyWeakPoints` 的敌人时统一解析实际命中组件：激活弱点读对应等级的 `WeakPointDamage`，其他部位读 `BodyDamage` 并受 `bWeakPointOnly` 控制；弱点视觉显隐不参与伤害。无弱点组件的 Character 保留旧头/身体回退，非 Character 保留弹孔。每弹只处理一次命中，重复释放无效。

本轮同时修正旧时间弹起点平行偏移：生成位置与方向均来自同一真实瞄准射线，即 `TraceStart + Direction * 40`，不再混用动画枪口位置。40 uu 内遮挡回退射线、12 发上限、FullStop 悬停及离开时释放保持不变。26 项两类敌人实际手枪时间弹测试与边界补测通过，详见 [弱点任务 6](enemy-weakpoints-plan.md)。下方 2026-09-26/27 记录仅作为历史证据。

- `/Game/Blueprints/Weapons/Player/Projectiles/BP_TimeBullet`
  - 模型：`/Game/Weapons/Bullet/General/StaticMeshes/SM_GeneralBullet`
  - `Collision`：2 uu Sphere，`Projectile` 碰撞预设。
  - `ProjectileMovement`：默认不激活、无重力；`ReleaseProjectile(Speed)` 设置本地前向速度并激活移动。
  - 生成时忽略 Owner，避免与玩家发生初始碰撞。
  - 忽略 `Projectile` 碰撞通道，并在命中保护中跳过其他 `BP_TimeBullet`，避免悬浮弹丸堆叠或释放时互相销毁、清零速度。
  - Actor Hit 对 Character 使用弹道直线到 `head` / `pelvis` 骨骼位置的距离补足胶囊 HitResult 不提供骨骼名的情况；头部为 100 点、身体为 25 点，提交通用 Damage 后销毁。非 Character 阻挡走身体伤害并销毁。
  - 非 Character 阻挡同时使用命中的 `HitComponent`、`ImpactPoint` 和 `ImpactNormal` 生成 `M_Impact_Decal`，尺寸、附着方式和 15 秒寿命与普通射线武器的墙面弹孔一致；该表现与既有身体伤害链并行执行。
- `/Game/Blueprints/Interactables/BP_Item_Base`
  - `UseTemporalProjectile`：时间系统的切换入口，默认 `false`。
  - `TemporalProjectileClass`：默认指向 `BP_TimeBullet`。
  - `TemporalProjectileLimit`：默认 12；达到上限后该次射击不再生成弹丸。
  - `TemporalMuzzleOffset`：默认 40 uu。
  - 启用时间弹丸时，若射线在偏移距离内已命中遮挡，仍走原射线结算，避免把弹丸生成到墙后。
  - 弹丸的生成旋转和 40 uu 偏移沿瞄准射线的 `TraceStart → TraceEnd`，不依赖武器模型自身旋转。

## 时间能力集成

- `/Game/Blueprints/Components/Player/AC_TimeAbility` 已接入该桥：只在 `FullStop` 开启当前武器的 `UseTemporalProjectile`。
- 进入 `BulletTime`、主动退出能力或组件结束运行时关闭该开关；离开 `FullStop` 的边沿只触发一次全量释放，当前默认速度为 30000 uu/s。
- 正常状态与 `BulletTime` 仍走原射线伤害；只有 `FullStop` 使用实体悬浮弹丸，因此不改变其他状态下已经可用的射击链。
- 全局实例上限仍为 12，达到上限后不能继续生成时间弹丸。
- `UI_Hud.SetTemporalProjectileStatus` 在 `FullStop` 显示当前时间弹丸数与 12 发上限，满额时显示 `LIMIT`。

## 验证记录（2026-09-26）

- 冷启动重新加载并编译 `BP_TimeBullet`、`BP_Item_Base`、`BP_Weapon_Pistol`：0 error。
- PIE 通过手枪 `BeginFire` 正式链路启用时间弹丸模式，观察到 4 枚实体弹头在枪口前持续悬浮。
- PIE 读取 4 个实例的 `ProjectileMovement`，均为未激活状态；Owner 忽略碰撞修复后不再生成即销毁。
- 2026-09-27 阶段 4 集成验证通过：正式武器链连续生成 3 枚悬浮弹丸；跨入 `BulletTime` 后 3 枚均自动激活移动，并在约 0.125 秒内各自前进约 138 uu。
- 2026-09-27 修复 FullStop 单发门控被世界减速拖慢的问题：单发 Delay 与 Burst/Auto Timer 使用全局时间倍率换算射击间隔。PIE 在能量仍为约 92、88 时成功生成第 2、3 枚悬浮弹丸，`IsFire` 均已按现实射速复位。
- 阶段 5–7 回归：12 枚可悬停，第 13 发被拒绝，HUD 满额提示正确，12 枚在模式切换后全部释放。
- 近战敌人身体/头部释放命中分别实测 25/100 点，悬停阶段均不提前扣血；ShooterNPC 身体释放命中实测 25 点。普通射线伤害保持即时，近距遮挡不生成时间弹丸。
- 2026-09-27 命中反馈修复回归：FullStop 单发分别命中 `BP_MeleeNPC` 与 `BP_ShooterNPC`，释放后均从 100 降至 75；命中 Movable `BlockAll` 测试墙后弹丸销毁且 DecalComponent 数量增加 1。Normal 与 BulletTime 均继续走射线，身体命中各造成 25 点且不生成 `BP_TimeBullet`。
- 输出日志仍有项目原有 Manny PoseAsset 版本警告，与本改动无关。
- 未完成：所有武器家族、所有特殊碰撞体的完整命中矩阵，以及打包、联网和压力验证。
