# 时停 / 子弹时间能力：阶段 1–4

实现与 PIE 验证日期：2026-09-26。本页记录仓库中的已实现事实；当前设计意图仍以项目策划来源为准。

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
- 组件结束运行时主动恢复全局、玩家和武器时间倍率，避免退出 PIE 或销毁组件后残留时间状态。

阶段 1–4 已形成可试玩的核心闭环。交互物专项适配、视听特效、打包和联网仍不在本轮范围内。

## 资产与入口

| 资产 | 职责 |
| --- | --- |
| `/Game/Blueprints/Components/Player/AC_TimeAbility` | 能量、三态、时间倍率、玩家/武器补偿、时间弹丸开关与释放、回溯状态检查和 HUD 推送 |
| `/Game/Blueprints/Player/BP_FPCharacter` | 挂载组件、接收 `IA_TimeAbility`、为现有回溯输入增加时间能力门禁 |
| `/Game/Input/Actions/IA_TimeAbility` | 时间能力数字输入动作 |
| `/Game/Input/IMC_Player` | 将 `IA_TimeAbility` 映射到 `T` |
| `/Game/UI/Widgets/UI_Hud` | `SetTimeAbilityStatus(EnergyPercent, ModeIndex)` 及能量条/文字 |

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

- 冷启动重新加载并编译 `AC_TimeAbility`、`BP_FPCharacter`、`BP_Item_Base`、`BP_TimeBullet` 和 `UI_Hud`：0 错误；同时复核阶段 3–4 的默认参数与时间弹丸类引用。
- PIE 从 `Map_Test` 运行完整输入链：`T` 激活/退出、均匀消耗/恢复、`FullStop` 到 `BulletTime` 阈值切换、耗尽自动退出均通过。
- PIE 验证双向互斥：时间能力激活时 `Q` 被拦截；回溯激活时 `T` 被拦截。
- 阶段 3–4 PIE 实测：`FullStop` 世界倍率 `0.01`，玩家/武器补偿倍率 `100`；能量以约 10 点/现实秒消耗；进入 `BulletTime` 时世界倍率约 `0.2006`，之后随能量下降连续上升。
- 同一轮 PIE 通过正式武器开火链生成 3 枚弹丸，悬停时其移动组件均未激活；跨入 `BulletTime` 后 3 枚的移动组件均被激活，并在约 0.125 秒内各自移动约 138 uu；退出能力后全局、玩家和武器倍率均恢复为 `1`。
- PIE 日志未出现 Blueprint Runtime Error、`Accessed None` 或新增编译错误。测试前的本地存档已在测试后恢复。

`0.01` 是为保持输入、Tick 和退出能力链可靠而采用的近似完全时停，并非把全局倍率设为绝对零。本轮未做打包、联网、交互物专项矩阵或大规模弹丸压力验证。
