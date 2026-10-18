# Lab R17 运行证据索引

日期：2026-10-17。目标地图：`/Game/Maps/Map_LabV39`。维护源见[门与 Omen 蓝图维护目录](../../../../SourceAssets/LabV39/R17/runtime_authoring/README.md)。本目录保留通过的最终功能检查和图片，不收录失败重试、缓存或大日志。

| 证据 | 实际结果与边界 |
| --- | --- |
| [门蓝图编译](door_build_result.json) | 两份蓝图各 0 错误/0 警告。这份记录产生于功能测试之前，记录内“尚未试玩”不是后续测试状态。 |
| [真实输入与门行为](door_pie_qa.json) | `done=true`、`passed=true`，32/32 项通过。使用项目实际 AC_Interaction 聚焦与 EnhancedInput Action；普通/锁定/1.2 m 门、占门保护、C0 两侧自动感应、真实时停输入与恢复。不是物理键盘按键测试。 |
| [78 扇门全开净空](all_door_fit.json) | 78/78 通过。用项目玩家胶囊扫掠各门洞；测试临时命令门全开，仅证明尺寸/碰撞净空，不代替 F 输入验证。 |
| [Omen PIE 采样](omen_pie_check.json) | 278 个样本，全部 21 项检查通过。左右注视、离开回位、回位中重新进入、模型位置/缩放保持和子件同步。使用测试位置设置，不是导航路线测试。 |
| [C0 广角捕图与恢复](door_c0_wide_capture.json) | 两张 PNG 已验证落盘；临时 FOV 120°，完成后恢复原 90°。只改 PIE 活动摄像机，不改相机资产默认值。归档仅将图片路径换成本目录相对路径，测量值未改。 |

门时停测试确实通过项目 `IA_TimeAbility` 将全局时间缩放降至约 0.01，门仍能响应 F 并完成动画，最后缩放恢复为 1。门控制仍只有实例锁定参数；43 扇初始锁门继承阶段门表，没有新增剧情解锁。

## 已回看的运行图片

- [锁门 F 反馈](images/01_Locked_F_feedback.png)：`LOCKED` 清晰可见。
- [普通门 F 打开](images/02_Normal_F_open.png)：通道无遮挡。
- [C0 自动打开近景](images/03_Omen_automatic_double_open.png)：可见通往大厅的开放门洞。
- [C0 双叶打开中](images/04_Omen_double_leaves_opening_wide.png)：两片门叶向两侧分离。
- [C0 全开门框](images/05_Omen_full_open_frame_wide.png)：两叶退入侧墙，完整门洞开放。
- [Omen 注视左侧玩家](images/Omen_Look_Left.png)、[Omen 注视右侧玩家](images/Omen_Look_Right.png)：原模型 Eye/Pupil 随对应玩家方向转动。

## 蓝图原生图形回读

[原生图形与逐图回读索引](graphs/README.md)收录本次 10 张图的报告和 17 张精选 PNG。每张图均检查至少一张 100% tile 或 1:1 小图总览；抽查未见节点实体重叠，注释已恢复功能意图。捕图前后源图哈希一致，排版前后及后续编译后语义一致。本项不代替上面的实际输入与运行测试。

这些证据支持本次实现和各自明确的检查范围。

## 最终重启与保存

辅助插件 `LabAuthoring` 关闭后重新启动 UE 5.6.1，直接加载原 `Map_LabV39`，再完成以下检查：

- [插件确实未加载](no_helper_restart.json)。
- [重启后的门输入链](door_pie_after_restart.json)：32/32，通过。
- [重启后的 Omen 追踪](omen_pie_after_restart.json)：21/21，通过。
- [最终地图保存和引用核查](final_save_reload_result.json)：78 扇门实例尺寸/位置/权限与门表一致；Omen 六件模型和引用保持；没有未保存内容包或地图；备份存在；运行蓝图无编辑工具模块依赖。

PIE 已退出，UE 保持打开工作地图，后台节流恢复原值，任务临时轮询已注销。重启后的报告单独归档，保留早期通过报告对应的截图与测量数据，不混用不同运行的误差数值。
