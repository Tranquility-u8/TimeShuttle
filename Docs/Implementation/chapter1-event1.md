# 第一章事件 1 · 逃离实验室

打开 `/Game/Maps/Map_LabV39`，从关卡的 PlayerStart 开始 Play。章节实例是 `Chapter1/Event1/Ch1_E1_Mission`，对应资产在 `/Game/Environment/LabV39/Chapter1/Event1`。

| 玩家动作 | 关卡响应 |
| --- | --- |
| 在时间粒子实验室苏醒 | OD01 开始时实验室清晰可见。Kairos 在第 0.36 秒第一次闭眼，第 0.55 秒完全睁开。随后睁眼停留 3 秒，再快速连眨两下。后两次之间只睁眼停留 0.09 秒，第 4.08 秒完全睁开。字幕显示在眼睑之上，起身后接 OD02 并开放步行、观察、蹲伏和互动。 |
| 蹲过左侧横管，沿斜面进入紫色管道 | Omen 交代目标后显示 “Leave the damaged laboratory”。两段固定路径分别指向矮洞另一侧和管道出口。低洞过线会被提前记录。 |
| 出管落稳，走向西门 | 沿用第二房间已有的门特写。交还视角后显示 “Check the exit door”，与门交互后勾选此目标并触发坍塌。 |
| 目睹落板和时停 | 惊叫由头顶落板触发。碎块冻结后播放 OD03；Kairos 说到出口时显示北门路线。玩家可以立即移动。 |
| 通过北门 | 离开危险区恢复物理。越过北门外侧区域完成撤离，解除本章行动限制，接续 “Reach the main control room”。OD04 询问刚才的异常，Edwina 和 Omen 在主控室的 OD06 讨论时间粒子与 Kairos 的结合。 |

**编辑入口**

- `M_Chapter1WakeEyelids` 控制三次眨眼的弧度、闭合时间和开合幅度。`WakePresentation` 使用抬眼演出已有的 `WakeClock`，完成第三次眨眼、提前起身和结束关卡都会清理眼睑遮罩。
- 台词和无配音时长在 `DT_OD01`、`DT_OD02`、`DT_OD03Impact`、`DT_OD03` 和 `DT_OD04`。章节专用注册表将这些行提供给现有对话系统。
- `BP_Chapter1EscapeMission` 继承 MissionFlow。任务组件的 StepId 和 NextStep 决定顺序；目标文案和出现时机分别在 `DT_Chapter1EscapeObjectives`、`DT_Chapter1EscapeSteps`。`Handoff` 把主控室目标交给 `AtriumRoute`。
- 四段引导使用 `AC_Task_GuideTo`。在地图实例的 Roles 中找到对应路径点，调整转折与落脚高度。实验室采用章节专用的箭头亮度和终点标记材质。管内点贴近管底，管口处应在角色第一人称视角复核。
- `Ch1_E1_LowPassageCrossing` 记录是否已穿过低洞。`Ch1_E1_NorthDoorMarker` 在门内侧，`Ch1_E1_NorthExitCrossing` 在门外侧；两者分别控制引导位置和任务完成。第二房间导演的 `DangerBounds` 单独控制时间恢复。
- `IMC_Chapter1Recovery` 暂时接管奔跑及主动时间能力按键。北门过线时恢复奔跑。后续 `IMC_Chapter1Unregulated` 接管主动时间能力键，直到玩家领取调节器。共享字幕和按键提示字体使用引擎自带的中文回退字形。

第二房间的原有演出参数和物理绑定见[房间演出说明](chapter1-room2-cinematic.md)，固定路点和到达信号的契约见[路径引导说明](mission-guidance.md)。

**主控室与训练往返**

从北门沿上层通道向东，走下西侧楼梯，绕过中央接待台，经 C0 自动门进入 Omen 房间。章节蓝图沿用任务组件、对白与地面引导。控制室物件在 Outliner 的 Chapter1/MainControl 下；任务仍由 Ch1_E1_Mission 驱动。

| 步骤 | 编辑位置或触发条件 |
| --- | --- |
| 进入主控室 | PresentOmen 控制冷却池镜头和球体升起。Edwina 使用带待机动画的 Quinn 占位模型，位于 C0 门内。OD05 由 Kairos 向她发问开始，随后 Omen 汇报设施受损与预测能力下降。 |
| 再次被动时停 | OD06 开场借用现有演出用时停控制器。检查左手的台词触发 Omen 俯身靠近，翻到下一句后退回冷却池。Kairos 的内心独白在字幕中标为 “Kairos (thought)”。 |
| 领取装置 | Kairos 答应出发后，PresentRegulator 升起设备台并播放 OD07。瞄准调节器并互动领取后，目标更新为 “Go to the training room”，路线沿东侧楼梯通往训练入口。 |
| 进入或离开教程 | 带 ChapterTraining 选项进入 Map_TrainingRoom。Ch1_TrainingReturn 观察原训练任务的 Completed 状态，然后播放 OD08。单独打开教程保留原有行为。 |
| 返回、简报、部署 | 带 ChapterReturn 选项返回 Map_LabV39，将玩家放在主控室内并从 FieldBrief 开始。OD09 完成后开放控制台，玩家主动部署后显示章末标题并返回主菜单。 |

新增对白及过渡画面在 `/Game/Environment/LabV39/Chapter1/Control`。OD09 的任务坐标和简报使用可替换的英文文案；具体目的地确定后在 DT_OD09 更新。
