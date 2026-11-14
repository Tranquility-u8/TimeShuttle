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
- 台词、配音和句后停顿统一在 `/Game/Data_Dialog/DT_OD01` 至 `DT_OD09`。章节专用注册表 `Event1/DT_Chapter1EscapeConversations` 保持：OD03Impact读取DT_OD03第1行，后续OD03读取第2–4行。出口第4行保留ExitSpotted；OD06第5行保留ExamineHand。
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

对白现位于 `/Game/Data_Dialog`；过渡画面保留在 `/Game/Environment/LabV39/Chapter1/Control`。OD09 的任务坐标和简报使用可替换的英文文案；具体目的地确定后在 DT_OD09 更新。

**对白分段与演出标记（2026-11-12早前实现历史；当前配音入口及OD03行映射见上文与dialog-system.md）**

本次按用户提供的 `Dialogue_ChapterOne (2).docx` 更新 OD01–OD07，发言数为 4 / 6 / 3 / 4 / 7 / 12 / 2。OD03 的惊叫仍由 `DT_OD03Impact` 单独播放，其余两段在 `DT_OD03`；OD07 已与原稿一致。既有 OD 编号、保留行的 RowName、语音和时长参数沿用。

- `DT_OD03` 的出口台词（RowName `3`）保留 `LineEventId = ExitSpotted`。`WatchEscape` 在当前已宣布播放的 OD03 台词具有该标记时发送原有出口信号。
- `DT_OD06` 的检查左手台词（RowName `5`，新版第六段）设置 `LineEventId = ExamineHand`。`ExaminePlayerHand` 仅在该标记播放时靠近，换句、完成或取消后沿用原有回位逻辑。
- 章节内纯函数 `IsChapterDialogueLineEvent` 检查管理器、活动会话、台词已宣布状态、数组边界和事件标记；`CurrentLineIndex` 只用于取当前行，不比较固定序号。编辑或调整这两句的位置时应随台词保留对应标记。
- 未修改通用 MissionSystem、DialogueManager、任务组件配置、步骤表、目标表或关卡。对话任务仍等待整段 `OnConversationEnded / Completed` 后结束。

验证：UE5.6.1 编译和独立冷进程读取通过；文稿 38 条对白逐条匹配，章节 43 个行引用有效。Map_LabV39 的 PIE 定向测试覆盖标记触发、普通台词不触发、标记临时换位、取消与结束回位；OD06 任务在全部 12 段期间保持 Running，完成后 Succeeded。测试通过临时 PIE 状态和原生播放/推进方法执行，未做全章人工通关或配音节奏验收。自动播放时长未随长段落合并重新调校。

**撤离后停止房间环境声（2026-11-12，20261112-od04-stop-escape-audio）**

Map_LabV39 中 FireAlarmSound、FireSound、FireSound2–FireSound6 共 7 个 AmbientSound 添加 Actor Tag `Chapter1.EscapeAmbience`。章节蓝图的 `BindEscapeAudioEvents` 在玩家对话管理器就绪后绑定一次 `OnConversationStarted`；`OnEscapeConversationStarted` 只接受本章节或所属任务组件发起的 OD04，立即调用 `StopEscapeAmbience`，逐个将 AudioComponent 的 Volume Multiplier 设为 0 并 Stop。触发时间为对白开始，不等待结束；原任务流、对白结束判定和声音资产不变。绑定前每 Tick 重试，绑定后立即返回；从训练返回、ChapterReturn 为 true 时也停止已撤离房间的环境声。

后续需要一起关闭的 AmbientSound，在 Actor 的 Tags 中添加同一个标签即可。关卡保存的音量和 Auto Activate 保持原值；重新开始关卡自然恢复播放。不要在运行时调用 SetAutoActivate，它在 UE5.6 注册后的组件上不会修改属性。

验证：开启声音的 UE5.6.1 Map_LabV39 PIE 定向测试 17 项通过。7 个声音在关卡开始均 Playing、Volume=1；真实 Aftermath 对话任务启动 OD04 第一段后均停止且 Volume=0；OD03、不属于本章节的 OD04、无标签的对照声音保持播放；OD04 四段期间任务 Running，结束后 Succeeded；重复停止及 ChapterReturn 临时状态测试通过。使用临时 PIE 状态进入任务，没有全章人工通关或打包测试。新增节点已局部整理、注释及编译保存。证据：文档工作区 `tmp/od04-stop-audio-20261112/{runtime-verification,final}.json`。

**受伤移动倍率（2026-11-12，20261112-escape-injury-speed）**

在 Map_LabV39 选中 `Ch1_E1_Mission`，Details 搜索 **Injury Speed Multiplier**；参数位于 `Chapter 1 | Injury Movement`，默认 **0.65**，允许 0.05–1.0。数值按进入受伤状态前的正常步行/蹲伏速度乘算；0.8 为80%，1为不减速。它是实例可编辑变量，不需要修改节点；修改后重新 Play 生效。

`BeginWalkRestriction` 调用 `ApplyInjurySpeed`，只缓存/应用一次，更新玩家 WalkSpeed、CharacterMovement.MaxWalkSpeed 和 MaxWalkSpeedCrouched；重复 Tick 不会叠加。`OnEscapeConversationStarted` 沿用本章节及任务来源筛选，在 OD04 开始时停止环境声并调用 `RestoreInjurySpeed`。北门过线的旧输入解锁本身不恢复速度，恢复严格以OD04开始为准。恢复标记防止后续再应用；ChapterReturn跳过受伤减速，EndPlay恢复本章节缓存的速度。无需修改玩家蓝图或正常速度默认值。

UE5.6.1 编译保存及13项PIE定向验证通过：自然开场410.2553→266.666 cm/s，蹲伏205→133.25；真实Aftermath任务开始OD04第一段即恢复410.2553/205。覆盖重复调用、北门输入解锁不提前恢复、OD03及其他来源OD04不恢复、OD04正常完成、既有7声源关闭、倍率0.8、训练返回跳过、真实Actor EndPlay恢复。测试用临时PIE状态进入后续任务，未做整章人工通关或打包验收。证据位于文档工作区tmp/injury-speed-20261112。


**配音引用修复（2026-11-12）**

用户要求统一使用已填写配音的Data_Dialog表。现44个章节行引用均解析到该目录，OD03第1行惊叫独立、后续第2–4行保留用户当前文本及配音，第4行ExitSpotted和OD06第5行ExamineHand经PIE回归通过。仅保存章节注册表与Data_Dialog/DT_OD03；自然开场声音自动衔接、其余已配置声音Playing、出口标记、Omen检查左手与回位、OD04环境声关闭和任务结束均已定向验证。未做完整人工通关或听感验收；空VoiceWave行仍需后续补配。细节见[对话系统当前统一入口](dialog-system.md)。
