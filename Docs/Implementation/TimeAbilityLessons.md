# 时停 / 子弹时间实施经验与踩坑记录

记录日期：2026-09-26。本文保存阶段 1–7 中可复用的工程经验，避免后续扩展武器、敌人、交互物或表现层时重复调查。功能事实和参数以 [TimeAbilityCore.md](TimeAbilityCore.md) 与 [TimeProjectileBridge.md](TimeProjectileBridge.md) 为准。

## 1. 架构选择

### 保留普通射线，FullStop 单独桥接实体弹丸

原玩家武器的伤害链是射线判定，枪口表现主要是粒子；单靠延迟射线或冻结粒子无法提供可碰撞、可计数、可释放的悬浮弹丸。因此采用混合方案：

- Normal 和 BulletTime 保留原 `Fire_HitScan`，避免破坏现有武器手感和伤害链。
- 仅在 FullStop 将一次有效射击桥接为 `BP_TimeBullet`。
- `AC_TimeAbility` 只负责模式、时间倍率、武器开关和离开 FullStop 时的统一释放；武器仍负责瞄准/开火入口，弹丸负责命中结算。

这一边界比把所有武器永久改成实体弹更窄，也便于后续逐个武器家族验证。

### 使用近似时停而非绝对零

全局时间倍率使用 `0.01`，没有设为 0。绝对零会让依赖 Tick 的输入、退出能力、HUD 和状态过渡难以继续。玩家和当前武器设置为世界倍率的倒数，使其主观速度接近正常：FullStop 时为 100，BulletTime 时随世界倍率变化。

能量消耗必须按现实时间观察。不能仅看到一个 Delta Seconds 节点就假设速率正确；最终 PIE 实测约为 10 点/现实秒。

第一人称程序动画也必须使用同一条“补偿后时间”语义。`AC_ProceduralAnimation.SwaySpring` 原先用组件 Tick 的补偿后 `DeltaTime` 积分弹簧，却用全局 `Get World Delta Seconds` 归一化鼠标摆动；FullStop 的 `0.01 × 100` 补偿会令后者比前者小约 100 倍，从而把手臂/武器横向摆动放大并造成左右震荡。现已统一使用 `SwaySpring` 的 `DeltaTime` 输入；正常时间下数值不变，FullStop 下不再重复放大。后续相机抖动、后坐力、武器惯性等第一人称表现若混用全局与 Actor/组件 DeltaTime，也应按同样方式审计。

武器 Actor 的 `Custom Time Dilation` 不能补偿潜伏动作 `Delay` 或 TimerManager。手枪单发链原本用未经换算的 `WeaponFireRate` 延迟复位 `IsFire`；FullStop 世界倍率为 `0.01` 时，现实等待时间被放大约 100 倍，表现为第一枪后直到能量跌入 BulletTime 才能再次开火。现将单发 Delay、连发与自动射击 Timer 的间隔统一改为 `WeaponFireRate × Get Global Time Dilation`：在 Normal 中结果不变，在 FullStop/BulletTime 中抵消世界减速。凡是需要随被补偿玩家保持现实节奏的冷却、Timer、Timeline 或潜伏动作，都应单独审计，不能只看所属 Actor 的自定义倍率。

### 模式边沿只释放一次

持续 Tick 中反复扫描并调用释放会产生重复激活和难以追踪的状态。组件用 `WasFullStop` 记录前一帧，只在 `FullStop → 其他模式` 的边沿释放现存弹丸并关闭武器桥接。

## 2. 弹丸实现踩坑

### 枪口模型旋转不等于玩家实际瞄准方向

最初按武器/枪口旋转生成弹丸时，瞄准敌人身体的弹丸仍可能沿模型朝向飞向头部高度。武器模型、程序动画和相机射线不保证完全一致。

修复原则：用命中结果的 `TraceStart → TraceEnd` 计算 Look At Rotation，生成旋转和 40 uu 前移都沿这条真实瞄准射线。后续任何“子弹从准星飞向目标”的系统都应优先复用射线方向，而不是直接读取枪口世界旋转。

### Character 胶囊命中通常没有骨骼名

时间弹丸首先撞到 Character Capsule 时，HitResult 的 `HitBoneName` 可能为 None。只判断 `head` 会让所有实体弹都结算身体伤害，即使视觉上命中头部。

当前可靠补偿：保留真实 `HitBoneName == head`，同时比较弹道直线到角色 Mesh 的 `head` 与 `pelvis` 骨骼位置的距离；离 head 更近则按头部伤害，否则按身体伤害。验证时不要只看准星或碰撞事件，必须记录悬停弹丸的轨迹、两个骨骼到轨迹的距离和实际血量差。

这是一种适配当前两类 Character 敌人的判定。若未来角色没有 `head` / `pelvis`、使用复杂弱点组件或非人形骨架，应改为显式弱点接口/碰撞体，而不是继续堆高度阈值。

### 悬浮弹丸会与 Owner 和其他弹丸互撞

只把 ProjectileMovement 停掉并不足够：弹丸仍可在生成瞬间撞到玩家、武器或前一颗悬浮弹，导致立即销毁或释放时互相清零速度。

当前处理包括：生成时忽略 Owner、Collision 忽略 Projectile 通道，并在 Hit 入口跳过 `BP_TimeBullet`。三层保护都需要保留。

### 近距遮挡必须在生成前处理

若墙面距离小于枪口前移距离，直接生成会把弹丸放到墙后。当前先使用既有射线结果判断距离；40 uu 内有阻挡时回退到原即时射线结算，不生成时间弹丸。验证要专门放置近距阻挡，不能只在开阔场地射击。

### 伤害成功与命中反馈是两条独立证据链

实体时间弹丸最初在 `Event Hit` 中已经能对 Melee 和 Shooter 提交通用 Damage，但非 Character 分支没有复用普通射线的墙面弹孔。结果是敌人测试可实际扣血，而射墙时只看到弹丸消失，玩家很容易把“缺少贴花”判断为“没有命中”。修复时保留既有伤害与销毁顺序，单独在非 Character 命中上根据 `HitComponent`、`ImpactPoint`、`ImpactNormal` 生成 `M_Impact_Decal`。以后验证弹丸应分别记录碰撞/销毁、伤害差值和表现对象数量，不能用其中一项替代另外两项。

### 上限策略必须明确

初版选择固定全局 12 发：第 13 发拒绝，不替换最旧弹丸。HUD 在 FullStop 中显示 `当前数 / 12`，满额显示 `LIMIT`。计数目前只在 FullStop 更新，并使用小规模全局查询；12 发上限下可接受。若未来变为高射速、大规模或多人系统，应改为组件维护注册表/对象池。

## 3. 交互物与物理

- 现有拾取链是玩家交互射线命中 `InteractionArea` 后同步调用接口。玩家被时间倍率补偿，因此 FullStop 下无需为拾取蓝图增加专用豁免。
- 验证拾取时必须瞄准实际 `InteractionArea` 子 Actor，而不是只把模型中心放在相机前；否则“无法聚焦”只是测试摆放错误。
- 通用刚体依靠全局时间倍率自然减速，并保留 Physics Linear Velocity。退出能力后不需要手工重新注入速度。
- 临时物理测试体必须设置 `Mobility = Movable`、启用 Simulate Physics、唤醒刚体；Static Mobility 即使写入速度也不会移动，容易被误判为时停成功。
- 当前只验证了正式武器拾取和通用刚体。门、机关、爆炸物、约束、布料、Niagara、音频和自定义 Timeline 仍需各自的专项矩阵。

## 4. PIE 与自动化验证经验

### 编译通过不等于玩法通过

本功能至少拆成以下可观察链：输入互斥、能量变化、FullStop 倍率、玩家/武器补偿、弹丸生成、悬停、数量上限、HUD、模式边沿释放、移动、命中、扣血、物理恢复和最终时间恢复。每项都需要运行数据，而不是只看蓝图编译。

### 测试中 Summon 的 AI 必须拥有正式 Controller

直接 Summon 近战 AI、但不执行 `SpawnDefaultController`，会让 `AC_Combat` 和 `AC_EnemyReverse` 访问空 Blackboard/AIController，产生 `Accessed None`。这属于测试夹具错误，不是时间弹丸错误，但会污染最终日志。最终干净回归在伤害前为测试敌人生成了默认 Controller。

### 要区分测试夹具失败和功能失败

本轮出现过两类典型假失败：StaticMeshActor 仍是 Static Mobility 导致任何模式都位移 0；拾取模型对准相机但 InteractionArea 未对准，导致玩家没有 Focus。修复测试搭建后，正式逻辑无需改动。

### 保存、冷启动和恢复点

- `.uasset` 只通过 Unreal-aware helper / Editor Python 修改并定向保存。
- 每轮关键改动后重新加载并冷编译相关蓝图，避免只验证内存中的热状态。
- PIE 前备份真实 `Saved/SaveGames/Saved.sav`，结束后恢复并比较 SHA-256；不要把测试存档当作项目资产提交。
- 最终检查 Git 范围，确认没有关卡、World Partition External Actor 或无关蓝图被保存。

## 5. 已验证矩阵

| 场景 | 结果 |
| --- | --- |
| T 激活/取消、Q/T 双向互斥 | 通过 |
| 70 阈值、低能量连续减速、零能量退出、恢复 | 通过 |
| FullStop 世界 0.01、玩家/武器补偿 100 | 通过 |
| FullStop 能量仍高于 70 时连续单发 3 次 | 通过，三次均生成弹丸且每次间隔前 `IsFire` 已复位 |
| 3 发悬停后在 BulletTime 释放移动 | 通过 |
| 12 发上限、第 13 发拒绝、HUD `LIMIT`、12 发全部释放 | 通过 |
| Melee 身体 25 / 头部 100，悬停阶段不扣血 | 通过 |
| Shooter 身体 25，悬停阶段不扣血 | 通过 |
| FullStop 弹丸命中墙体后生成普通射击同款弹孔 | 通过，DecalComponent +1 |
| Normal 原射线即时伤害且不生成时间弹丸 | 通过 |
| BulletTime 原射线即时伤害且不生成时间弹丸 | 通过 |
| 40 uu 内近距遮挡 | 通过，不生成时间弹丸 |
| FullStop 武器拾取 | 通过真实交互射线与输入链 |
| 刚体正常 / FullStop / BulletTime / 恢复 | 通过，速度保留 |
| 9 个相关蓝图冷启动编译 | 0 error |
| 最终干净 PIE 日志 | 无 Blueprint Runtime Error / Accessed None |

## 6. 后续扩展入口与风险

- 美术可读取 `AC_TimeAbility` 的能量、模式和当前世界倍率，以及 `UI_Hud` 的状态更新入口；当前没有专用 VFX Event Dispatcher。增加后应由模式边沿驱动，不要让每个特效自行轮询世界倍率。
- 若生产版改为局部时停，不能只替换全局倍率：需要 Actor 纳入/退出集合、初始速度缓存、生成中 Actor 注册、销毁清理、重叠边界和回溯互斥策略。
- 非 Character 弱点、爆炸物连锁、移动平台、Chaos 约束、布料、音频 Pitch、Niagara 和 Timeline 可能不完全遵循相同时间语义，必须分系统验证。
- 打包、联网、对象池和更高数量压力尚未认证。当前实现应视为单机可玩切片，而不是最终通用时间框架。
