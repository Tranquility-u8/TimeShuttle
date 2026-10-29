# 玩家出拳与时停手臂动画修复

2026-10-28，经用户确认实施。协作模式：节能；本轮不是 Drive 设计刷新。前两节是合入分支前的初次修复记录；最终实现与验证见末尾“Wingshing 同步与最终修正”。

## 原因与改动

当前资产与调查导出文本的 SHA-256 一致。修改前的 PIE 复现了 FullStop 世界倍率约 0.01、玩家倍率 100 时，出拳后 1.14 现实秒 `IsFire` 与 `LeftHandAlpha` 仍为 true / 1。

- `BP_Weapon_EmptyHands` 原来的世界时间 `Delay 0.2` 同时释放攻击门禁与手部覆盖。两段拳动画实际各长约 0.667 秒：正常时间下覆盖清除过早，FullStop 下则需约 20 现实秒。现在保留原 0.2 现实秒的攻击间隔，并以 `Play Animation.PlayLength` 更新独立的现实时间姿态截止点。仅在攻击活动期间逐帧等待；连续出拳读取最新截止点，旧拳不会提前清除新拳的覆盖。
- 空手武器 `EndPlay` 在引用有效时清除共享 `LeftHandAlpha`。切换武器会销毁旧武器并取消潜伏等待，清理因此独立于等待是否完成。
- `AC_ProceduralAnimation` 的起停、移动强度、前后步行循环、前行混合、冲刺/左手 IK 六处 timeline 保留原曲线和速率，将速率乘以玩家当前 `CustomTimeDilation`。宏内部的世界 DeltaTime 因而与被补偿玩家一致；没有修改共享 `ML_Timeline`。
- `ABP_FP_ArmsProcedural` 缓存本次动画更新的原生 `DeltaTimeX`，用于左手 IK 与视图 Roll 的插值，替代全局世界 DeltaTime。原生动画更新已含玩家时间补偿，不再额外乘一次倍率。

只保存上述三个资产。`BP_FPCharacter`、`ABP_Manny`、`AC_TimeAbility` 的文件哈希保持不变；伤害、输入绑定、世界倍率及教程流程不变。

## 验证与边界

- 三个资产最终编译均为 0 errors / 0 warnings；定向保存成功，无残留 dirty content / map。
- 38/38 PIE 检查通过：Normal、FullStop、BulletTime；0.2 秒攻击解锁、拳动画中段姿态、连续拳截止点、结束复位、动画中切换时间模式、冲刺姿态参数进入/退出、玩家动画 DeltaTime、武器销毁中断清理。冲刺姿态这一组通过组件参数驱动，并非真实按键试玩。
- 13/13 输入回归通过：通过 Enhanced Input 装备手枪、持续瞄准、开火扣除一发、三态下真实移动/跑步以及最终全局倍率恢复。各轮将玩家移回同一测试起点，防止上一轮移动到墙边污染下一轮速度检查。
- 布局与注释后比较节点引脚、默认值、对象引用及连接，功能签名一致；局部脚本排版保留无关节点。Blueprint Assist 局部操作尝试未产生可核实的节点位置变化，不计作格式化成功。已留编辑器图表截图，完整视觉收尾仍可由用户在试玩反馈时复核。
- 独立无 BlueprintOps 辅助插件的磁盘冷加载编译成功：0 errors，14 条原有 Manny PoseAsset 过期警告，见本机 `cold.json` / `cold-final.log`。第一次冷检查脚本读取受保护的 Blueprint Status 被拒绝，已删除该读操作，保留首次日志 `cold.log`，不将观测脚本失败归为资产编译失败。
- 最终测试窗口未发现新的 Blueprint Runtime Error / Accessed None。已有重复 `DefaultSlot`、手枪 additive 动画用于 SingleNodeInstance 和导航警告单独保留；不宣称项目日志全部无警告。初期观测脚本错误与启动时 Zen 缓存服务故障不计为玩法失败。
- 教程关卡真实鼠标操作下的出拳外观、时停奔跑及其切换，仍待用户试玩确认；未做打包或联网验证。

本机证据、定向备份和可重跑脚本在忽略跟踪的 `Saved/Agent/FistStopArms20261028/`：`preflight.json`、`baseline.json`、`qa.json`、`regression.json`、`regression-fixture-failure.json`、`save.json`、`cold.json`、`layout-fist.png`。恢复使用本次三份原始资产备份，不回退无关工作。

任务度量 ID：`20261028-fist-stop-arms`；等待用户试玩时 Pause，收到反馈后 Resume，验收完成再 Finish。

## 普通启动崩溃跟进

2026-10-28 用户报告重新打开引擎崩溃。最近两份 crash context 与启动日志均指向 `DerivedDataBackends.cpp:208`：本机 Zen 服务不可达，默认磁盘节点为 DeleteOnly，导致默认缓存图没有可写节点。崩溃发生于内容加载前；上一轮临时启动参数仅绕过缓存服务，没有修复普通启动。

本机改用项目 `Config/UserEngine.ini` 的用户覆盖：缓存层级跳过 ZenLocal，沿用引擎默认磁盘缓存位置并启用写入。该文件通过 `.git/info/exclude` 忽略，不提交共享配置、缓存或机器路径。该用户配置层由安装版引擎 `ConfigHierarchy.h` 明确支持；不使用可能被重新生成而丢失的 `Saved/Config/WindowsEditor/Engine.ini` 作为持久设置。没有删除缓存、修改系统代理或改动动画资产。

第一次不带缓存参数的普通启动已加载教程地图，界面为 All Saved；正常关闭后的第二次普通启动也通过，日志确认磁盘 Local 节点 Writable、教程地图加载及 Startup complete，未出现该缓存致命错误。持久用户配置仍在，普通启动未携带缓存参数。若后续 Zen 服务恢复，可撤销这份本机用户覆盖及对应本地排除条目。

## Wingshing 同步与最终修正

用户随后要求将 `dev/wingshing` 的功能同步到本地 `dev/Dialogue`，保留动画修复。调查确认：2026-10-28 18:22 的 checkout 将工作区从 `dev/wingshing` 切到未同步的旧 Dialogue `0af9ffae`；放松奔跑位于 `2c983a76`，QTE 运行时 Q 提示修复位于 `b819deae`，此前均未包含在本地 Dialogue。远程最新 Dialogue 已另行合入 Wingshing，但还包含本任务未选择引入的主菜单及章节内容。

本次合入来源固定为 `dev/wingshing` 的 `3b3dd629`。先备份并暂存原有未提交修复；合入全部来源提交，仅两份知识文档出现文本冲突，双方记录均保留。来源涉及的 33 个内容资产在重放修复前全部通过 SHA-256 一致性检查。保留 Dialogue 自己的对话提交，不推送远程。恢复点为本地 `codex/backup-dialogue-before-wingshing-20261028`、命名 stash 及 `Saved/Agent/WingshingSync20261028/PreSync/`。

最终逻辑：

- 恢复 Wingshing 的 `GetHandsRelaxed`、`ABP_Manny.EmptyArms` / `Anim_Character_FistSprint`、`IsRunOrSprint` 切换、H 收枪/拔枪、换枪队列与弹药保留。保留来源的一现实秒出拳战斗姿态保持，结束后回到放松移动。
- 空手武器只使用独立的 0.2 现实秒攻击解锁，不再依赖世界时间 Delay。最初新增的“保持 LeftHandAlpha 至拳动画结束”方案经画面检查被否定：拳动画已含 IK 目标，额外的 hand_l → ik_hand_l 复制会令右拳时的护手抬高。临时对照中，护手相对眼睛高度在 0.25 秒由约 +22 cm 变为 −19 cm；最终拳头保持 `LeftHandAlpha=0`，删除不再需要的姿态截止变量/等待循环，保留销毁时安全清理。没有修改拳动画资源或骨骼关键帧。
- `BP_FPCharacter.RunSprintTapControl` 的双击时间戳改用现实时间，保持 0.3 秒判定阈值。0.15 秒松键缓冲改为只在松键待处理时运行的现实时间截止点；FullStop 中不再拖成约 15 秒，时间模式切换也不残留 Shift 状态。未改移动速度、碰撞或跑步/冲刺的输入语义。
- 保留前述六处程序移动 timeline 的玩家补偿，以及动画实例原生 DeltaTime 驱动的手臂插值。HUD 使用来源已修复的 Q 文本，实际子弹威胁触发链已验证。

本次在来源上额外修改四个蓝图：`BP_FPCharacter`、`BP_Weapon_EmptyHands`、`AC_ProceduralAnimation`、`ABP_FP_ArmsProcedural`。玩家除 `RunSprintTapControl` 外的图表与来源一致，空手武器的原战斗姿态保持及非事件图表保持一致。新节点局部排版并加职责注释，未重排无关图表。

本机分轮证据位于 `Saved/Agent/WingshingSync20261028/`：来源哈希检查、20 蓝图编译、40 项装备/输入核心回归、38 项拳时序回归、36 项真实放松奔跑/出拳恢复、12 项跑步输入边界、3 项 QTE 文本/实际威胁、36 项三态左右拳姿态检查。姿态检查按四个动画时点测量护手低于眼线、出拳前伸、肢体长度、额外 IK 关闭及回到放松状态；左右拳的索引由夹具指定，调用正式 BeginFire，未注入伤害。

最终核心检查 165 项通过，另有 6 项教程启动检查通过，合计 171 项。实际运行截图复核了普通/FullStop 奔跑、左右拳及恢复状态，`VisualBeforeIK/` 保留修正前画面。20 个相关蓝图编译为 0 errors / 0 warnings；最终定向保存后没有未保存的内容或地图包。独立进程不加载 BlueprintOps，重新从磁盘加载并编译同一批蓝图；冷编译日志中的 Manny PoseAsset 过期警告与本次逻辑分开记录。

最终冷编译为 0 errors / 14 条原有 PoseAsset 警告。`punch-final-*.png` 在实际运行到目标动画帧后临时暂停 PIE 再截图，避免异步截图跨过动画结束；暂停只用于拍摄，165 项运行检查均来自独立未暂停测试。最终来源哈希复核中，33 个来源资产仅玩家与空手武器两项存在本次预期修正差异，其余 31 项保持来源一致；另两项时间补偿资产保留本轮已有修复。

教程启动另行验证 `BP_TrainingMission` 编译无错误/警告，实际地图保留唯一任务实例和 Dialogue 的 99 个任务组件，默认空手、放松状态、正常时间与 HUD 均初始化成功；运行日志无 Blueprint Runtime Error / Accessed None。该六项启动检查不代表完整教程通关。蓝图已局部整理并完成注释、功能签名复核，编辑器布局证据为 `layout-run-clock.png`。本地形成合并提交固定已验证结果，未推送远程。

移动使用 Enhanced Input，测试地面及隔离位置为临时 PIE 夹具，不保存到地图。保留了最初的夹具假设失败、真实世界时间缺陷失败及 IK 播放路径对照；不把失败计入通过。正常和 FullStop 的实际窗口截图另行复核。本轮未认证完整教程通关、打包或联网，也不把 Wingshing 其他功能的资产一致性/编译检查当作逐项试玩通过。
