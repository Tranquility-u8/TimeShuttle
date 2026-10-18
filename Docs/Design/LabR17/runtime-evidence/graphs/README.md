# Lab R17 蓝图原生图形回读

日期：2026-10-17。本次回读覆盖 `BP_LabRoomDoor` 的 9 张图和 `BP_OmenObserver` 的 EventGraph，共 10 张图。归档 17 张实际查看过的原生 PNG，每张图均至少检查一张 100% tile 或 1:1 小图总览。图片均取自本次 `capture_reports.json`，没有选取目录内旧批次遗留 tile。

在这些视图中未发现节点实体重叠；注释已显示对应功能意图，不再是默认的 `Comment`。门 EventGraph 的初始化、自动感应、F 交互、Tick 动画分区可辨，Omen 的初始化、区域判定和转向处理分区可辨。部分共享数据线仍交叉；本结论是实际视图抽查，不代表每根线都无交叉。

## 逐图索引

| 蓝图 / 图 | 已回读的原尺寸视图 | 总览 / 补充 |
| --- | --- | --- |
| RoomDoor / ConfigureDoor | [100% 尺寸与组件初始化](BP_LabRoomDoor_ConfigureDoor_tile_01_01.png) | [全图](BP_LabRoomDoor_ConfigureDoor.png) |
| RoomDoor / ApplyDoorPose | [100% 门叶位置计算](BP_LabRoomDoor_ApplyDoorPose_tile_01_01.png) | [全图](BP_LabRoomDoor_ApplyDoorPose.png) |
| RoomDoor / WakeDoor | [1:1 全图](BP_LabRoomDoor_WakeDoor.png) | 更新时间基准并唤醒 Tick。 |
| RoomDoor / SetDoorOpen | [1:1 全图](BP_LabRoomDoor_SetDoorOpen.png) | 设置目标开合状态并唤醒动画。 |
| RoomDoor / ShowDoorPrompt | [100% 双侧提示与计时](BP_LabRoomDoor_ShowDoorPrompt_tile_01_01.png) | 后续节点延续到相邻 tile；此处保留阅读样本。 |
| RoomDoor / DoorwayOccupied | [1:1 全图](BP_LabRoomDoor_DoorwayOccupied.png) | 玩家与安全区重叠判定。 |
| RoomDoor / CheckAutomaticDoor | [100% 自动门判定](BP_LabRoomDoor_CheckAutomaticDoor_tile_01_01.png) | 靠近感应和目标状态处理。 |
| RoomDoor / UserConstructionScript | [1:1 全图](BP_LabRoomDoor_UserConstructionScript.png) | 构造时配置尺寸并应用门叶状态。 |
| RoomDoor / EventGraph | [100% 初始化与自动感应](BP_LabRoomDoor_EventGraph_tile_01_01.png)、[F 交互](BP_LabRoomDoor_EventGraph_tile_02_01.png)、[实时动画计算](BP_LabRoomDoor_EventGraph_tile_03_02.png) | [全图](BP_LabRoomDoor_EventGraph.png) |
| OmenObserver / EventGraph | [100% 初始化与区域判定](BP_OmenObserver_EventGraph_tile_01_01.png)、[转向插值](BP_OmenObserver_EventGraph_tile_02_03.png) | [全图](BP_OmenObserver_EventGraph.png) |

总览用于定位分区；宽图中的文字应打开 100% tile 阅读。单张 tile 边缘可能截断继续到相邻 tile 的节点，这不代表源图丢失节点。部分自调用节点显示 `Target is Lab Graph Capture …`，来自用于离屏渲染的临时蓝图副本，不是生产蓝图改名或运行时类型变化。

## 验证记录与范围

- [原始捕图报告](capture_reports.json)：完整保留本次 10 图报告及全部输出帧清单，文件内容未改。绝对路径是当时的源输出位置；本目录只精选归档上表 17 张图，便携图片路径见下项。
- [精选图片与视觉回读记录](visual_review.json)：记录本目录相对路径、缩放、所属图和 SHA-256。已验证每张图至少有一个 100% 阅读样本，且每张归档 PNG 与源文件哈希一致。
- [排版与语义验证摘要](presentation_result_summary.json)：保留两份蓝图的结果字段与原始报告 SHA-256，省去重复完整节点快照。门图检查 192 个节点、调整 182 个；Omen 调整 6 个注释节点。排版前后语义一致，后续编译后语义也一致。

捕图使用 UE 原生 `SGraphEditor` / `FWidgetRenderer` 渲染临时副本。10 图均记录 `source_unchanged=true`、捕图前后图哈希一致、源包均未变脏。排版调用本身的 `compiled=false` 是保留的原始字段；之后主任务执行了编译和保存，摘要中的 `post_compile_status=3` 与 `post_compile_semantic_unchanged=true` 对应后续步骤，不能将前者误读为“最终未编译”。本轮回读没有修改 spec 或 UE。

运行行为证据仍以[上一级索引](../README.md)中的 PIE 检查为准；原生图形回读用于验证可读性与排版结果。
