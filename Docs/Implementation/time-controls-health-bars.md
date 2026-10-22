# 时间操作、瞄准与敌人血条更新

2026-10-15，UE 5.6.1；任务 `20261015-time-controls-healthbars`。按用户“懒人模式，确认执行”实施并定向保存。

## 配置与行为

| 入口 | 改动 |
| --- | --- |
| `AC_TimeAbility.RecoveryPerSecond` | 10 → **20**，单位为能量/现实秒；实测 0→100 为 5 秒 |
| `AC_TimeAbility.FullStopThreshold` | 70 → **30**；30 属于 FullStop，低于 30 进入 BulletTime |
| `AC_TimeAbility.DrainPerSecond` | 保持 15 |
| `GM_FP` → Class Defaults → `Show Enemy Health Bars` | 新增全局勾选项，内部变量 `bShowEnemyHealthBars`，默认 true |

`BP_FPCharacter` 的时间组件模板同步为 20/30。教程提示、控制帮助与 HUD 更新为 Q、30%；移除控制帮助中已无输入映射的 Q 回溯说明。保留用户原有 `IMC_Player` 修改，核对其 Q→`IA_TimeAbility`、右键→`IA_Aim`。HUD 的旧内部控件名保留，避免破坏引用，显示标签及区域尺寸已更新。

教程恢复初始化及完成判断读取当前能力的 `FullStopThreshold`，不再硬编码 70。新增节点已局部整理和注释；相关关卡文本及说明同步。

## 修复原因与实现

时停中 Aim 输入和 FOV 原本能够响应，但手部姿态 Timeline 和位置/旋转弹簧使用世界时间，在 0.01 倍率下几乎停滞。`AC_ProceduralAnimation` 的姿态 PlayRate 现为 `4 × Owner.CustomTimeDilation`，两个最终手部弹簧使用组件 Tick 存下的 `DeltaSeconds`。共享 Timeline 宏保持不变。Normal、FullStop 和 BulletTime 的进入/退出瞄准均经过检查。

`BP_Enemy_Base.RefreshHealthBarVisibility` 在血条初始化后和 Tick 检查 GameMode 开关及 `IsDead`，仅当组件可见性需要改变时调用 SetVisibility。没有全场 Actor 扫描；近战/远程子类继承此逻辑。关闭影响已有和新生成的敌人，重新开启只显示存活敌人。其他 GameMode 保持原表现。该设置属于 GameMode 默认值/当前实例，不新增存档持久化。

## 验证与边界

- 21/21 项定向 PIE 检查通过：默认参数、现有/新生成敌人、死亡隐藏、时停切换血条、三种时间模式的 Aim 进入/释放、30 与 29.9 边界、5 秒恢复、教程阈值与最终全局倍率恢复。
- Aim/时间输入通过 Enhanced Input 注入；核对真实映射。测试为隔离状态设置运行时能量，并临时停用消耗后恢复 15。死亡检查用 ApplyDamage 注入，不代表武器命中验收；敌人具有默认 Controller，隔离血条测试时停止 AI。
- 28/28 项冷加载检查通过：保存后的蓝图加载/编译、玩家组件模板、GameMode 默认值、两个敌人子类、Q 映射和提示、HUD 30 标签。此后仅纠正一处教程注释 70→30，并再次编译保存关卡。
- 相关蓝图编译无错误/警告；最终 PIE 区间无 Blueprint Runtime Error 或 Accessed None。原有动画槽/渲染警告仍在，未作为本任务缺陷修改。
- Blueprint Assist 局部整理后检查图表语义一致，并目视复核新增逻辑、注释和 HUD。未复测完整 S1–S7 通关、回溯复活、全部武器、多人或打包版本。

本机原始检查、图表导出和定向备份位于忽略跟踪的 `Saved/Agent/TimeControls/`。未提交或推送；保留用户原有输入映射改动。
