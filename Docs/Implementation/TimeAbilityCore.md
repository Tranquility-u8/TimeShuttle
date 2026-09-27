# 时停 / 子弹时间能力：阶段 1–7

实现与 PIE 验证日期：2026-09-26。本页记录仓库中的已实现事实；当前设计意图仍以项目策划来源为准。

## 决策来源与设计边界

本轮阈值、切换、互斥、12 发上限、拾取交互和初版不增加特效等规则，由用户在 2026-09-26 的实现会话中直接确认。它们已记录到 `Docs/Knowledge/design-snapshot.md` 的后续决策段落。旧 Drive 快照中的 `100–50` 阈值和“局部 Area Stop”描述没有被删除：当前可玩切片以 70 为阈值并使用全局时间倍率，生产版是否恢复局部范围仍待确认。

## 已实现范围

- 玩家按 `T` 切换时间能力；再次按下退出。
- 能量范围为 0–100，初始 100。
- 激活时以每秒 10 点均匀消耗；未激活时以每秒 10 点均匀恢复。
- 能量 `>= 70` 时为 `FullStop`，能量 `< 70` 时为 `BulletTime`；耗尽后自动退出并回到 `Normal`。
- 时间能力与现有回溯双向互斥：只有玩家处于正常状态时才能启动其中一项。时间能力激活时 `Q` 不启动回溯；回溯激活时 `T` 不启动时间能力。
- 现有 HUD 底部中央增加能量进度条、百分比和模式文字。`Normal`、`FullStop`、`BulletTime` 使用不同颜色区分。
- `FullStop` 使用 `0.01` 的全局时间倍率实现工程上的近似完全时停；玩家和当前武器使用其倒数作为自定义时间倍率，因此仍能正常移动、瞄准和开火。
- `BulletTime` 将能量从 70 到 0 线性映射到全局时间倍率 `0.2` 到 `1.0`：能量越低，世界越接近正常速度；玩家和当前武器继续保持补偿。
- 只有 `FullStop` 开启当前武器的 `UseTemporalProjectile`。此时射击生成实体弹丸并停在枪口前；转入 `BulletTime` 或退出能力时，所有现存 `BP_TimeBullet` 以 5000 uu/s 恢复运动。
- `FullStop` 的时间弹丸全局上限为 12；HUD 同步显示 `当前数量 / 上限`，达到上限显示 `LIMIT`，第 13 次开火不生成弹丸。
- 时间弹丸沿实际瞄准射线生成和释放，而不是沿武器模型朝向；近于 40 uu 的遮挡继续走即时射线结算，避免弹丸生成到墙后。
- 时间弹丸命中 Character 胶囊时，以弹道直线到 `head` / `pelvis` 骨骼位置的距离判定头部或身体；身体 25、头部 100，只在释放命中后结算一次。
- 组件结束运行时主动恢复全局、玩家和武器时间倍率，避免退出 PIE 或销毁组件后残留时间状态。

阶段 1–7 已形成可试玩的核心闭环。现有拾取交互在 `FullStop` 下保持可用；普通物理物体由全局时间倍率统一进入近似冻结/慢速/正常恢复，不额外改写其速度。视听特效、打包和联网仍不在本轮范围内。

## 阶段交付映射

| 阶段 | 已交付内容 |
| --- | --- |
| 1 | 三态、能量、均匀消耗/恢复、阈值与耗尽退出 |
| 2 | `T` 输入、与 `Q` 回溯双向互斥、基础 HUD |
| 3 | FullStop / BulletTime 世界倍率、玩家和当前武器补偿 |
| 4 | FullStop 实体悬浮弹丸、模式边沿释放、动量恢复 |
| 5 | 12 发固定上限与 HUD、真实瞄准方向、近距遮挡、身体/头部延迟伤害 |
| 6 | FullStop 拾取交互和通用刚体冻结/慢速/恢复验证 |
| 7 | 两类敌人、普通射线、互斥、耗尽、上限、物理、日志与冷启动全量回归；知识文档收口 |

详细实现经验、失败尝试和测试陷阱见 [TimeAbilityLessons.md](TimeAbilityLessons.md)。

## 资产与入口

| 资产 | 职责 |
| --- | --- |
| `/Game/Blueprints/Components/Player/AC_TimeAbility` | 能量、三态、时间倍率、玩家/武器补偿、时间弹丸开关与释放、回溯状态检查和 HUD 推送 |
| `/Game/Blueprints/Player/BP_FPCharacter` | 挂载组件、接收 `IA_TimeAbility`、为现有回溯输入增加时间能力门禁 |
| `/Game/Input/Actions/IA_TimeAbility` | 时间能力数字输入动作 |
| `/Game/Input/IMC_Player` | 将 `IA_TimeAbility` 映射到 `T` |
| `/Game/UI/Widgets/UI_Hud` | `SetTimeAbilityStatus(EnergyPercent, ModeIndex)`、`SetTemporalProjectileStatus(CurrentCount, Limit, ModeIndex)` 及能量条/文字 |

`ModeIndex` 当前约定为：`0 = Normal`、`1 = FullStop`、`2 = BulletTime`。后续若其他系统大量消费该状态，可在不改变行为的前提下迁移为专用枚举。

## 默认参数

| 参数 | 默认值 |
| --- | ---: |
| `MaxEnergy` | 100 |
| `Energy` | 100 |
| `FullStopThreshold` | 70 |
| `DrainPerSecond` | 10 |
| `RecoveryPerSecond` | 10 |
| `FullStopTimeScale` | 0.01 |
| `MinimumBulletTimeScale` | 0.2 |
| `ReleaseProjectileSpeed` | 5000 |

## 验证证据

- 冷启动重新加载并编译时间能力、玩家、武器、时间弹丸、HUD、拾取/交互和两类正式敌人共 9 个蓝图：0 错误；同时复核阈值、倍率、弹速、12 发上限、40 uu 近距保护及 25/100 伤害默认值。
- PIE 从 `Map_Test` 运行完整输入链：`T` 激活/退出、均匀消耗/恢复、`FullStop` 到 `BulletTime` 阈值切换、耗尽自动退出均通过。
- PIE 验证双向互斥：时间能力激活时 `Q` 被拦截；回溯激活时 `T` 被拦截。
- 阶段 3–4 PIE 实测：`FullStop` 世界倍率 `0.01`，玩家/武器补偿倍率 `100`；能量以约 10 点/现实秒消耗；进入 `BulletTime` 时世界倍率约 `0.2006`，之后随能量下降连续上升。
- 同一轮 PIE 通过正式武器开火链生成 3 枚弹丸，悬停时其移动组件均未激活；跨入 `BulletTime` 后 3 枚的移动组件均被激活，并在约 0.125 秒内各自移动约 138 uu；退出能力后全局、玩家和武器倍率均恢复为 `1`。
- 2026-09-27 修复 FullStop 重复开火门控：武器单发 Delay、Burst/Auto Timer 的间隔改为 `WeaponFireRate × Get Global Time Dilation`。PIE 在能量约 92 和 88（均高于 70）时连续完成第二、第三次单发，三次均生成悬浮弹丸，且每次开火前 `IsFire` 已复位。
- 12 发上限 PIE：第 13 次开火被拒绝，HUD 显示 `FULL STOP  12 / 12  LIMIT`，进入 `BulletTime` 后 12 发全部恢复运动。
- 命中 PIE：近战敌人身体弹在悬停阶段不扣血、释放后扣 25；头部弹悬停阶段不扣血、释放后扣 100。ShooterNPC 身体弹同样延迟结算 25 点；普通状态下原射线仍即时伤害且不生成时间弹丸。
- 交互/物理 PIE：`FullStop` 下玩家真实交互射线锁定拾取区域并完成狙击枪拾取。同一 600 uu/s 物理方块在约 0.56 秒内位移分别为正常 354、FullStop 3.4、50 能量 BulletTime 165、退出后 340 uu，且线速度始终保留。
- 近距遮挡 PIE：40 uu 内的阻挡不生成时间弹丸。最终回归日志未出现 Blueprint Runtime Error、`Accessed None` 或新增编译错误。测试前的本地存档已在测试后恢复。

`0.01` 是为保持输入、Tick 和退出能力链可靠而采用的近似完全时停，并非把全局倍率设为绝对零。物理验证覆盖通用刚体与现有武器拾取，不等于所有特殊交互物的专项认证。本轮未做打包、联网或超过 12 发的大规模压力验证。
