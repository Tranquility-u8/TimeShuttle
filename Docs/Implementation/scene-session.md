# 场景测试与主线会话

2026-11-21：场景加载与主线启动分离。关卡仍保存建筑、普通交互和剧情所需的锚点；是否启动章节任务、剧情镜头和章节玩家限制，由独立的会话入口决定。

## 使用方法

- **自由测试**：直接打开 `Map_LabV39`，Play 或右键 **Play From Here**。默认不启动第一章，可移动、观察场景并使用 Combat 模式允许的玩家能力。小地图沿用独立测试默认开启的规则。
- **预览主线**：在 LabV39 的 Outliner 中选择 `Session/SceneSession`，勾选 **Preview Main Story**，停止后重新 Play。测试开场建议从 PlayerStart 出生；剧情中的正常镜头和位置控制仍然生效。取消勾选后重新 Play 即恢复自由测试。仓库保存值为关闭。
- **正常游戏**：从主菜单点击新游戏，仍进入主线。教学进入与返回继续沿用原流程，小地图仍在进入教学后解锁。
- **其他场景**：没有 SceneSession 配置和主线旅行参数时，默认不属于主线会话。可放置 `BP_SceneSession` 提供同样的预览开关；开关不会凭空生成该场景没有的章节内容。

切换开关针对下一次运行，不在已开始的会话中热切换。自由测试不会删除剧情物件或自动打开全部门，也不会自动给背包添加武器；需要测试某处场景时可直接 Play From Here。

## 实现入口

| 资产 / 入口 | 职责 |
| --- | --- |
| `/Game/Blueprints/Core/Session/BP_SceneSession` | 仅保存实例可编辑的 `PreviewMainStory`，默认 false，不运行 Tick。 |
| `/Game/Blueprints/Core/Session/BFL_SceneSession.IsMainStorySession` | 集中解析旅行参数与可选场景配置；不依赖地图名称或 GameInstance 残留状态。 |
| `BFL_SceneSession.ApplyScenePlayerMode` | 根据会话选择传入的 StoryMode / TestMode，调用既有玩家模式系统。 |
| LabV39 Level Blueprint | 使用上述适配入口：StoryMode=Chapter1，TestMode=Combat。 |
| `BP_Chapter1EscapeMission` | BeginPlay 缓存 `MainStoryActive`。自由测试跳过原父类启动及章节初始化，关闭 Tick，并跳过没有资源所有权的章节 EndPlay 清理。 |
| `BP_Chapter1Room2Sequence` | 同样缓存会话并门控初始化、Tick、EndPlay；`TriggerCollapse` 也检查缓存，防止门交互绕过入口启动剧情。 |
| `BP_MainMenuController.CommitNewGame` | 旅行参数为 `MainStory?HideMinimap`，显式进入主线并保留小地图解锁顺序。 |
| 旧 `UI_MainMenu` 的旅行节点 | 新游戏和读档旅行补充 `MainStory`，保留原目的地与存档读取方式。 |

判定优先级：

1. 存在 `Sandbox` 参数：自由测试，优先于其他参数和预览开关。
2. 存在 `MainStory`、`ChapterTraining` 或 `ChapterReturn`：主线会话。
3. 否则读取场景内唯一 `BP_SceneSession.PreviewMainStory`；没有配置则返回 false。

例如程序旅行可使用 `OpenLevel(Map_LabV39, Options="MainStory?HideMinimap")`；临时自由测试可使用 `Options="Sandbox"`。这些都是 Unreal 旅行 Options，不是新的控制台命令。

新增主线导演或章节任务时，应在首次获得输入、镜头、对白、HUD 或场景物件控制权之前查询并缓存同一策略，同时保护对外的剧情触发入口。普通交互、敌人和场景自身逻辑不应统一套上主线门控。其他关卡如需区分玩家权限，调用 `ApplyScenePlayerMode` 并传入该场景的两种模式。

## 验证与范围

本次不改变章节内部任务顺序、对白数据、演出参数、场景碰撞、背包或存档格式；也未实现新的章节检查点存档系统。旧菜单读档仅补充会话参数，其原有恢复能力不因此扩展。

七个相关蓝图（含关卡蓝图）编译零错误、零警告；布局前后语义比较一致。68 项目标断言通过，覆盖自由测试、实际右键 Play From Here、主菜单至教学往返、预览主线、Sandbox 优先级、Map_Test 默认模式、无制作插件冷启动和普通编辑器重编译后再次运行。

教学往返通过既有出发/返回方法加速；主线演出入口包含直接调用 `TriggerCollapse` 的 PIE 定向测试。扩展自动行走走到 TubePath 后在管道出口卡住，未计为全章通关。旧菜单读档只检查旅行参数与编译，没有完整读档回归；未做打包或性能基准。初次新建蓝图的内存临时类曾导致崩溃，保存后冷重载以及普通编辑器重编译/PIE 均通过。

本地验证记录位于 Git 忽略的 `Saved/Agent/SceneSession/verification.json` 和 `验证记录.md`。测试使用隔离存档目录；交付时编辑器重新打开普通用户目录的 LabV39，预览开关关闭，没有未保存资产。
