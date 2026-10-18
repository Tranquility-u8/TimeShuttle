# Lab R17 门的使用与维护

本目录是项目内维护源，spec 和门表从本目录读取；临时执行报告输出至 `Saved/Agent/LabR17/doors`。已完成的验收结果见[正式运行证据](../../../../../Docs/Design/LabR17/runtime-evidence/README.md)，重建调用方式见[总说明](../README.md)。

这套门用于《Time Shuttler》的 `Map_LabV39`。当前共放置 **78 扇门，其中 43 扇初始锁定**。这些锁定值继承 R17 门表的阶段计划；本次没有新增剧情解锁规则，也没有自动把阶段标签实现成任务系统。

## 蓝图与操作

| 资产 | 行为 |
| --- | --- |
| `/Game/Environment/LabR17/Blueprints/BP_LabRoomDoor` | 普通双叶滑门，玩家瞄准门并按 **F** 开关；`bLocked` 为真时显示 `LOCKED`。 |
| `/Game/Environment/LabR17/Blueprints/BP_LabOmenDoor` | 普通门的子类，`bAutomatic = true`。用于 Omen 的 C0 门，玩家从任一侧靠近自动打开，离开后关闭；不接受手动 F 切换。 |

普通门继承项目已有 `BP_Interaction_Base`，继续使用玩家的 `AC_Interaction`、`IA_Interact` 和 `BPI_Interaction.Interface_Interact`。现有输入映射中的键位是 **F**，没有另建输入绑定或 Mapping Context。

关门时，玩家站在 `SafetyBounds` 中会阻止关闭并显示 `DOORWAY BLOCKED`；正在关闭的门检测到玩家进入后会重新打开。两扇门叶始终保留碰撞。安全检测针对玩家，未扩展为任意敌人、物理道具的通用检测。

`LOCKED` / `DOORWAY BLOCKED` 使用门两侧各一个 `TextRenderComponent`，显示两秒真实时间。它们是可随游戏打包的组件，不是开发用 `PrintString`。门动画和反馈采用受限的真实时间差，因此玩家时停时仍能操作实验室门。

## 修改某一扇门

在 Outliner 的 `LabV39/R17/InteractiveDoors/A` 或 `B` 中找到 `LabR17_Door_<门编号>`。例如 `LabR17_Door_C0` 是 Omen 自动门。每个实例带有 `LabR17.InteractiveDoor` 和 `LabR17.DoorID:<编号>` 标签。

| 参数 | 用途 |
| --- | --- |
| `bLocked` | 实例锁定状态。关闭锁定后，普通门等待玩家按 F；自动门由距离检查决定开关。 |
| `DoorWidth` / `DoorHeight` | 门洞净宽与净高，单位 **cm**；应与该处真实洞口匹配。 |
| `DoorThickness` | 门叶厚度，当前 16 cm；不是墙体厚度。 |
| `OpenSeconds` | 开关动画时间，普通默认 0.8 秒。 |
| `AutoDistance` | 自动感应范围沿门法线方向的半深度；只对自动门有实际意义。 |
| `LeafClearance` | 每片门叶完全打开后的额外让位距离，默认 4 cm。 |

实例放在**门洞底边中心**，Actor Scale 保持 `(1,1,1)`：局部 X 为墙面法线，局部 Y 沿门洞宽度，Z 向上。修改宽高后 Construction Script 会重新配置叶片、交互区域、感应区域和提示位置。不要通过整体缩放去适配门洞，也不要重复添加门框；R17 建筑已经包含门框。

当前落位使用每个门洞的实际尺寸，包含 1.2 m 净宽训练连通门和 8 × 4.8 m 的 C0 门。普通蓝图的 240 × 300 cm、自动子类的 420 × 420 cm 只是创建新实例时的默认值。

## 接入后续任务与关卡逻辑

组员应在已有阶段或任务逻辑中持有目标门实例引用，并按设计设置 `bLocked`。门蓝图不判断任务完成、不读取剧情阶段，也不自行解锁其他门。

`SetDoorOpen(WantsOpen)` 是供明确外部控制使用的函数，会直接设置开关目标并唤醒动画；它不是权限判断函数。外部逻辑应先确认自己的开门权限，不能依赖该函数替代锁定判定。普通门已打开时单独设置锁定，不会突然关闭；自动门锁定后会请求关闭，并保留玩家占门保护。

`bDoorOpen` 是目标状态，`OpenAlpha` 是动画进度，后者到 1 才表示完全打开。不要把目标状态立即变化误当作门洞已经完全可通行。

自动距离检查使用 10 Hz 定时器。门的 Tick 只在动画或提示需要更新时工作，静止时关闭。关键函数分为 `ConfigureDoor`、`ApplyDoorPose`、`CheckAutomaticDoor`、`DoorwayOccupied`、`SetDoorOpen`、`ShowDoorPrompt` 和 `WakeDoor`；事件图分开标注初始化、自动门事件、F 交互与 Tick 四部分。

## 生成脚本与重复执行

这一目录是编辑器维护工具和验证记录，游戏运行不依赖这些 Python 脚本。

1. `inspect_contract_after_helper.py`：只读回查真实父类、交互接口和组件契约。
2. `build_door_specs.py`：本地生成两个 JSON 蓝图规格，不接触 UE。
3. `apply_doors.py`：只创建、编译并选择性保存两份门蓝图；不摆放实例、不保存地图。已有资产默认阻止覆盖，明确重建时才改 `ALLOW_EXISTING`。
4. `prepare_door_placement.py`：从 R17 几何与建筑报告生成 `door_placement_plan.json`，检查来源哈希一致。
5. `spawn_doors.py`：按门表放置实例，只替换带本任务管理标签且门编号匹配的门，不改其他原有内容；地图由执行者检查后保存。

如果已在 UE 中手改实例，重新运行摆放脚本会按门表重建这些受管理实例。应先将需要保留的调整同步到来源数据或明确保留实例，避免用旧门表覆盖团队修改。不要同时运行多个编辑器写入、玩家输入或相机控制脚本。

编辑工具在 `Plugins/LabAuthoring`，只包含 **Editor 模块**。生成的门是普通蓝图，运行节点来自原生 Engine 与项目已有交互体系，没有新增运行时 C++ 类依赖。

## 验证记录

两份蓝图均已编译并保存，**0 个错误、0 个警告**；78 个实例落位成功。见 `door_build_result.json`、`door_placement_plan.json`、`door_placement_result.json`。

`qa_doors_pie.py` 的最新完整运行已通过 **32 / 32 项检查**，`door_pie_qa.json` 中 `done=true`、`passed=true`、`error=null`。验证内容包括真实交互聚焦、普通门 F 开关、锁门文字、1.2 m 门洞胶囊通行、占门拒关、关门中进入后反开、C0 两侧自动感应，以及实际时停期间的门动画和 F 交互。时停由真实 `IA_TimeAbility` 输入触发，全局时间缩放从 1 变为约 0.01，最后恢复为 1。

输入验证通过 EnhancedInput 注入项目已有 Action，并核对 F 映射，**没有直接调用门的交互接口或开门函数伪造通过结果**。这是实际 PIE 输入链验证，不等同于物理键盘按键测试。测试覆盖代表性门型与尺寸，没有逐一手动走过全部 78 扇门。

`visual_capture_doors.py` 必须在 QA 完成后独立运行。它使用真实 F 输入和自动门接近行为，保存锁门提示、普通门打开、C0 双叶打开三张当前 PIE 视角 PNG 到 `Previews/`。检查 `door_visual_capture.json` 的完成状态及文件落盘结果，并人工查看 PNG 后再作为视觉验收证据。脚本会恢复玩家原位置和视角，不保存 PIE 状态到地图。

首轮三张 PNG 已落盘并回看：`LOCKED` 文字清晰，普通门的打开通道无遮挡，C0 打开后的门洞连通大厅。C0 近景不能同时展示退入侧墙的两叶，因此另提供 `visual_capture_c0_wide.py`：临时将 PIE 活动相机组件设为 120°，分别记录开启中双叶和全开门框，完成后恢复原 FOV。它不改相机资产默认值；补图结果以 `door_c0_wide_capture.json` 和对应 PNG 为准。

广角补图已通过并回看，报告确认原 FOV 恢复为 90°。正式图片见[双叶打开中](../../../../../Docs/Design/LabR17/runtime-evidence/images/04_Omen_double_leaves_opening_wide.png)与[全开门框](../../../../../Docs/Design/LabR17/runtime-evidence/images/05_Omen_full_open_frame_wide.png)。
