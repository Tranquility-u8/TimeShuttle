# 落石教学安全区 Box Trigger

关联任务：P-008 / LEVEL-002 / P-106。日期：2026-10-28。

## 场景对象名称

打开 **`Map_TrainingRoom`**，在 World Outliner 搜索 **`S1_SafeZone`**。

- 对象类型：UE 原生 **TriggerBox**。
- Outliner 文件夹：`Training / S1`。
- 移动对象即可改变安全区位置。
- 在其 CollisionComponent 的 **Shape → Box Extent** 调整大小，也可以缩放对象。Box Extent 是半尺寸，例如 X=100 代表 X 方向总宽度 200 cm。
- 这是三维范围，Box 的底面与顶面也必须容纳玩家胶囊。
- 初始位置沿用原安全区地面范围；Box 中心 `(0, -607.295, 120)`，Box Extent `(498, 216.875, 130)`。这些是可编辑场景数据，不是蓝图中的坐标常量。

## 蓝图接线位置

`BP_TrainingController` 新增一个实例可编辑变量：**`SafeZone`**，类别 `Training | Safety`。教学场景中的 `Training Controller (Blueprint)` 已引用 `S1_SafeZone`。

`UpdateObservations` 调用 **`IsPlayerFullyInSafeZone`**，将返回值写入原来的 `PlayerInSafeZone`。删除原先安全区固定坐标的计算节点；其余检测保留。

判断函数使用 Box 的真实位置、旋转、缩放和尺寸，以及玩家胶囊的中心、方向、半径和半高。将 Box 内边界收缩一个胶囊半径，再检查胶囊两端半球球心是否均在范围内，确保整个胶囊进入；普通边缘 Overlap 不会通过。区域未指定时返回 false。

没有新增管理器、Actor 蓝图、额外 Tick、定时器或任务类型。运行逻辑全部由普通蓝图节点实现，无新增 C++ 插件。

## 后续流程保持

**最新修改（2026-10-28，替代本节下方历史顺序）：** 用户要求进入 Box 立即播放 TD05。保留胶囊完整进入条件，通过后恢复时间、完成安全区目标、锁定移动并立即启动 TD05，不再先等待落地。TD05 结束后检查落石落地，满足后进入 S2。只修改三个任务组件的 NextStep：S1_21 → S1_23；S1_24 → S1_22；S1_22 → S2_00_Checkpoint。功能测试由用户执行，未运行 PIE。以下为修改前调查记录。

`S1_19_WaitPlayerInSafeZone` 通过后，仍按原链执行：解除强制时停 → HUD 完成安全区目标 → 等待落石全部落地 → 锁定移动 → TD05 对话 → 第二阶段。没有修改任务组件、落地计算、对话或按键提示逻辑。

2026-10-28 补充调查：TD05（用户称 DT05）不是由 Box 的 BeginOverlap 直接触发。真正的对话任务为 `S1_24_S1_3`，前置门槛是 `S1_22_WaitRocksLanded` 等到控制器 `RocksLanded=true`，再经过 `S1_23_SetTutorialMovement`。落地变量来自 UpdateRocks 对教学落石的高度检查，非固定延时或碰撞事件。因此完整进入 Box 后不会必然立刻播放；这保留了用户此前要求不改动的后续流程。此次核对保存配置与上次静态证据，没有运行 PIE，也未证明用户这次实机是否卡在安全区或落地步骤。

## 功能测试由用户执行

按照用户要求，本次不运行 PIE，不将编译成功表述为功能测试通过。建议自行验证：

1. 角色擦到 Box、或胶囊仍有部分在外面时，安全区目标不完成。
2. 胶囊完全进入后，正常恢复时间，等待落石落地和 TD05，随后进入第二阶段。
3. 在编辑器移动 `S1_SafeZone` 或修改 Box Extent，再次进入教学；判定应跟随新范围，原位置不再生效。

控制器编译结果为 0 错误、0 警告，控制器与教学地图已保存；任务配置和原有后续流程图未改动。静态核对见 [验证记录](rock-safe-zone-box-validation.json)。功能结果等待用户测试。
