# 设计师固定路径引导

2026-10-24，UE 5.6.1。当前版本使用设计师手动布置的固定路径点，替代此前的动态寻路。早期终端、F 交互和动态导航的测试记录仅为历史，不代表当前功能。

## 试玩

打开 `/Game/MissionSystem/Guidance/Map_GuidanceDemo` 并 Play。固定路径依次连接 PathStart → Turn01 → Turn02 → Turn03 → Exit；共约 32 m、64 个贴地条带。玩家移动、传送或偏离路线不改变路径起点、转折或长度。

示例控制台 Actor、GuideConsole 交互任务、Console 角色绑定及 `BP_GuidanceDemoTerminal` 资产已移除。示例任务从 EnterExit 开始，到达出口区域后通过现有 MissionFlow 完成并清理路径。角色、玩家、输入映射、正式训练关卡及默认启动地图未修改。

## 设计师配置

1. 在关卡中放置 `BP_GuidanceWaypoint`，手动设置起点和每个中间转折点。折线直连这些点；路径方向由列表顺序确定。
2. 在当前 MissionFlow 实例的 `Roles` 中绑定这些 Actor。
3. 给流程添加 `AC_Task_GuideTo`，在 `WaypointRoles` 中按顺序填写 **固定起点、其后各中间点**。列表至少一个有效起点，不要把玩家位置填作起点。
4. `TargetRole` 绑定最终终点 Actor。终点既可以是 `BP_GuidanceWaypoint`，也可以是需要指向的物体；不要在列表末尾重复同一终点。
5. 需要独立的物体锚点时，在终点 Actor 添加 `AC_GuidanceTarget`，用 `PathOffset` / `PathComponentTag` 设置地面端点，用 `MarkerOffset` / `MarkerComponentTag` 设置标记位置。偏移是物体本地坐标。
6. 通过 StepId、NextStep、FailureStep 接入现有流程。`WaitForSignal=false` 按终点区域到达完成；`true` 等待实际玩法调用 `ReceiveGuidanceSignal(ExpectedSignal)`，默认信号名 ObjectiveDone。

示例保留的 `WaypointRoles` 字段现在表示固定起点及中间点，不再表示必须踩中的检查点。玩家经过某个点不会消耗它，也不会裁掉路径前半段。UseNavigation、RepathInterval 和必要点到达参数已移除。

## 固定路径行为

- 激活时读取全部点的世界位置，逐段直连，再以 50 cm 间距做有界地面采样。不查询 NavMesh，不绕障碍，不读取玩家位置选择起点。
- 运行时不自动重建。设计师在运行中移动点后，需明确调用拥有该路线的 `BP_GuidancePath.RebuildRoute` 才应用更改；仅移动玩家不会触发它。
- 路径点列表为空、首点失效或中间点缺失时隐藏路径，不回退到玩家位置，不显示残留的部分路线。相邻点距离不足 1 cm 时跳过零长度边。
- 设计师负责让路线可通行，绕开墙体、封闭区域和不应穿越的地形。地面探测及正常深度测试保留；不存在的地面、过陡表面和被实体遮住的部分不会强制穿墙显示。
- 全路径从固定起点显示。默认 RevealDistance=100000 cm，最多 128 个条带，按默认采样距离约能承载 64 m；更长的设计路线需调整数量预算或采样间距。预算始终从固定起点计算，与玩家位置无关。
- 玩家脚底仅用于任务终点到达判定：默认 XY 半径 110 cm，独立高度容差 100 cm。它不会改变几何；任务仍激活时保持整条线。任务结束、取消或目标失效后淡出约 0.35 秒并清理。

## 表现

青蓝底线约 8 cm，LineIntensity=0.30，承载条带宽 30 cm；双箭头约 14 cm，间距 150 cm，速度 120 cm/现实秒，ArrowIntensity=7。Additive / Unlit、柔光、转角斜接和循环箭头沿用已修复的材质，暂停冻结，时停与子弹时间不改变现实秒速度。

组件和 MID 使用池复用。更新条带位置明确刷新 SplineMesh，避免旧渲染参数/包围盒导致移动视角断裂。箭头使用连续坐标计算抗锯齿，避免循环接缝横线。材质源码见 `SourceAssets/Guidance/`，运行时无需制作插件或 C++ 模块。

## 验证与恢复

最终保存版本通过 43 项 PIE 检查；5 个相关蓝图编译均为 0 错误、0 警告。检查覆盖无导航数据生成、玩家移动/传送/偏离后的几何稳定、显式重建、无效点、箭头现实时间、暂停、时停/子弹时间、跨楼层到达及任务完成/重试/取消清理。测试用的导航数据删除和镜头均仅发生在 PIE，不保存进关卡。

本机证据位于 `Saved/Agent/Guidance/`：`fixed-validation.json`（固定路线、无导航数据、位置无关、显式更新、边界与任务链），`fixed-layout-verification.json`（布局和语义），`fixed-terminal-removal.json`（终端清理），`fixed-delivery.json`（保存及编译）。历史的 dynamic route / F / locator 测试文件保留，不计入当前验收。

修改前保存版本的定向恢复副本位于忽略跟踪的 `Saved/Agent/Guidance/FixedRecovery/`；资产修改和删除通过 Unreal 编辑器 API 执行。未提交或推送。未认证完整 Cook/打包、多人和正式关卡的全部设计路径。
