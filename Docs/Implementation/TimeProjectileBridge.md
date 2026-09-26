# 时间弹丸桥接

## 目的

为“高能量时停期间可开火、弹丸在枪口前悬浮、解除后保留方向并延迟释放”提供实体弹丸链路，同时不破坏正常状态下已经可用的射线武器伤害。

## 已实现资产与接口

- `/Game/Blueprints/Weapons/Player/Projectiles/BP_TimeBullet`
  - 模型：`/Game/Weapons/Bullet/General/StaticMeshes/SM_GeneralBullet`
  - `Collision`：2 uu Sphere，`Projectile` 碰撞预设。
  - `ProjectileMovement`：默认不激活、无重力；`ReleaseProjectile(Speed)` 设置本地前向速度并激活移动。
  - 生成时忽略 Owner，避免与玩家发生初始碰撞。
  - Actor Hit 时读取命中骨骼：`head` 为 100 点，其余为 25 点；提交通用 Damage 后销毁。
- `/Game/Blueprints/Interactables/BP_Item_Base`
  - `UseTemporalProjectile`：时间系统的切换入口，默认 `false`。
  - `TemporalProjectileClass`：默认指向 `BP_TimeBullet`。
  - `TemporalProjectileLimit`：默认 12；达到上限后该次射击不再生成弹丸。
  - `TemporalMuzzleOffset`：默认 40 uu。
  - 启用时间弹丸时，若射线在偏移距离内已命中遮挡，仍走原射线结算，避免把弹丸生成到墙后。

## 当前边界

- 本次只建立射线/实体弹丸的切换桥和弹丸生命周期接口，没有实现能量条、时停/子弹时间状态机或 UI。
- 默认开关关闭，因此现有正常状态射击和其他玩家武器不改变。
- 后续时间管理器应在高能量时停阶段开启 `UseTemporalProjectile`；退出完全时停或进入低能量子弹时间后，枚举现存 `BP_TimeBullet` 并调用 `ReleaseProjectile`，速度可由能量比例映射。

## 验证记录（2026-09-26）

- 冷启动重新加载并编译 `BP_TimeBullet`、`BP_Item_Base`、`BP_Weapon_Pistol`：0 error。
- PIE 通过手枪 `BeginFire` 正式链路启用时间弹丸模式，观察到 4 枚实体弹头在枪口前持续悬浮。
- PIE 读取 4 个实例的 `ProjectileMovement`，均为未激活状态；Owner 忽略碰撞修复后不再生成即销毁。
- 输出日志仍有项目原有 Manny PoseAsset 版本警告，与本改动无关。
- 未完成：面向敌人的实际释放命中、12 发上限的手感测试，以及时间能力状态机集成。
