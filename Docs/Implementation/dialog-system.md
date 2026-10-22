# DialogSystem 蓝图对话系统

更新：2026-10-18。UE 5.6.1，单机本地玩家。任务 ID：P-008 / P-058 / GPD-026。

完整对话运行逻辑现由普通蓝图实现。`TimeShuttleDialog` 运行插件已从项目目录和 `.uproject` 移除，行结构与枚举也已迁到内容资产。玩家、NPC、触发器、现有训练控制器及七张对白表已迁移。原对白表逻辑内容、路径和行名保持一致。

本次范围是替换对话底层并保留现有接入；训练关卡的 Enter/Check、Phase/NextStep 和阶段编排尚未改为通用任务执行器。后续任务、角色锁定与 Cutscene 编排应以对话事件接入，不能把本次交付当作整个任务系统重构完成。

## 改动计划与完成顺序

1. 盘点原插件、资产引用、玩家与训练室调用；定向备份。
2. 创建蓝图结构体/枚举、完整状态机、语音及输入会话、UMG、触发器与记忆模块。
3. 保留原数据与外部行为，迁移玩家/NPC/训练调用及工程 GameInstance 配置。
4. 确认原生引用为零后移走旧插件，以新进程冷启动验证。
5. 完成 PIE 功能与边界回归、真实跨关卡和训练室接入，整理图表，更新独立 Word 使用手册。

## 蓝图职责与扩展入口

除项目通用 Game Instance 位于 `/Game/Blueprints/Core/` 外，下列对话运行资产都在 `/Game/DialogSystem/`，没有自定义 C++ 运行父类。

| 资产 | 基类与职责 |
|---|---|
| `Blueprints/AC_DialogueManager` | ActorComponent；26 个函数完成请求、优先级、状态、逐句推进、语音结束、控制锁与清理。原项目控制锁适配保留在 EventGraph。 |
| `Blueprints/BP_DialogueSession` | Actor；每段独立的异步声音预加载与 Enhanced Input 事件；带请求代次校验，结束后销毁。 |
| `Blueprints/BFL_Dialogue` | BlueprintFunctionLibrary；查找管理器、读取/校验表、玩法输入门禁、死亡与显式存档接口。 |
| `/Game/Blueprints/Core/BP_TimeShuttleGameInstance` | 项目通用 GameInstance；对话记忆作为 `Dialogue|Memory` 分类内的一项功能，持久化默认关闭。 |
| `Blueprints/BPI_DialogueMemory` | 可选记忆接口；服务缺失或关闭时不阻止播放。 |
| `Blueprints/SG_DialogueMemory` | SaveGame；版本 1 的已完成 ID 集合。 |
| `Blueprints/AC_DialogueParticipant` | ActorComponent；已有 NPC/剧情 Actor 的可复用请求入口。 |
| `Blueprints/BP_DialogueTrigger` | Actor；Box 组件的玩家碰撞入口及剧情请求入口。 |
| `Blueprints/BP_DialogueNPC` | 保留 BP_Interaction_Base 与现有 F 互动接口，可派生角色外观。 |
| `UI/WBP_Dialogue` | UserWidget；Designer 可编辑姓名、整句正文与模式状态，ShowLine/ShowStatus 蓝图更新文本。 |
| `Types/S_DialogueLine`、`S_DialogueConversation` | 蓝图结构体；逐句与整段表结构。 |
| `Types/ENUM_DialogueTrigger/State/EndReason/RequestResult` | 四个蓝图枚举，可在蓝图分支和事件中使用。 |

`BP_FPCharacter.DialogueManager` 的组件模板保留 WidgetClass、IMC_Dialogue 和两项 InputAction 配置。工程 `GameInstanceClass` 保留 BP_TimeShuttleGameInstance。对话播放通过 BPI_DialogueMemory 访问可选记忆服务，不依赖该具体类；更换 GI 或不实现接口时仍可播放，仅缺少跨关卡/磁盘记忆。当前通用 Game Instance 直接继承 Engine.GameInstance，没有继承旧的对话专用蓝图；未来项目级功能可作为其他分类加入。

新增剧情效果可绑定 `OnConversationStarted`、`OnLineStarted`、`OnLineEnded`、`OnConversationEnded`、`OnDialogueError`。句事件传递 `LineEventId`，任务/演出只在结束原因是 `Completed` 时按成功处理。取消、死亡和优先级打断不能视为任务完成。新增管理器行为可直接编辑或派生蓝图，字幕布局在 Designer 编辑；不要把具体任务条件写入播放状态机。

## 保持的行为规则

- 碰撞盒、NPC 互动、Story 三种入口共用玩家的一个管理器，没有玩家回答选项。
- 初始自动播放，P 切换自动/手动。Enter 与 Space 在手动模式下前进；有声音必须等待真实 AudioFinished。没有玩家跳过整段入口。同帧多次 Next 合并，按住不会重复跳句。
- 无 SoundWave 为正常纯文字。自动按 TextOnlyDuration 计时，手动可立即前进；PostLineDelay 只作用于自动模式。语音不以阅读秒数估计结束。
- 2D 声音与底部姓名＋整句字幕，不随距离衰减，没有逐字效果。离开或销毁触发来源不取消当前对话。
- Priority 为 1–3，1 最高；Story 有效优先级为 1。只有严格更高优先级能打断。同级、低级和同一段请求返回 Busy，不排队、不恢复被打断段。
- bLockPlayerMovement 为真时阻止移动、跳跃、开火、互动、换枪、时间能力，并停止已经启动的相关动作；转视角、对话控制及暂停仍可用。自由移动对话保留玩法操作，Space 在对话期间专用于下一句。
- 暂停菜单同时暂停声音与阅读计时；恢复不补算暂停时间。时停/子弹时间不改变语速或阅读时间。死亡取消，关卡切换清理声音、UI、独立输入会话和自己拥有的移动锁；保留其他系统的锁，不使用 ClearAllMappings/ResetIgnoreMoveInput。
- BeginPlay/EndPlay、加载代次与状态转换保护阻止过期回调复活已取消对话。异步预加载超时 30 秒；丢失语音报 InvalidData。循环或异常播放在资源时长加 10 秒后取消并报 AudioFailed；纯蓝图不依赖受保护的 SoundWave.bLooping 属性预检。
- OnLineEnded 在实际前进离开当前句时发出，手动等待期间不提前发，取消不补发。转换回调内再请求返回 ReentrantRequest；需要衔接时安排到下一 Tick。CancelDialogue 不接受 Completed 原因。

## 数据与触发用法

当前整段表：`/Game/Data_Dialog/DT_DialogueConversations`。现有逐句表包括 `DT_TS1_01`、`DT_TS1_02`、`DT_TutorialEnergy` 及训练目录中的 `DT_TutorialArrival`。不要再使用旧文档中已不存在的 DialogSystem/Data 路径。

| S_DialogueLine 字段 | 类型 / 默认值 | 说明 |
|---|---|---|
| SpeakerId | Name | 可选稳定说话者标识。 |
| SpeakerName | Text | 必填，支持本地化。 |
| DialogueText | Text | 必填，整句正文与自动换行。 |
| VoiceWave | Soft SoundWave | 可空；整段开始前异步预加载。 |
| TextOnlyDuration | Float / 3 | 纯文字自动阅读秒数，至少 0.1。 |
| PostLineDelay | Float / 0 | 自动句后停顿，非负。 |
| LineEventId | Name | 句开始和自然前进事件携带的剧情标识。 |

| S_DialogueConversation 字段 | 类型 / 默认值 | 说明 |
|---|---|---|
| ConversationId | Name | 非空、稳定且项目内唯一。 |
| Lines | DataTableRowHandle 数组 | 逐句表与行名，数组顺序就是播放顺序。 |
| Priority | Int / 3 | 1–3。 |
| bLockPlayerMovement | Bool / false | 整段控制限制。 |
| bPlayOnce | Bool / false | 自然完成后记录；取消不消耗完成资格。 |

剧情调用：`Get Player Pawn → BFL_Dialogue.FindDialogueManager → Is Valid → RequestDialogue`。Conversation 输入 `Make Data Table Row Handle`（整段表＋整段 RowName）；Trigger=Story；Source=发起事件的 Actor。RowName 与 ConversationId 都须正确填写，它们不是同一个字段。

返回值：Accepted / Busy / AlreadyCompleted / InvalidData / PlayerUnavailable / ReentrantRequest。Accepted 表示请求被接收，异步加载仍可能失败；以实际句开始和结束事件作为后续依据。查看 LastError 定位数据错误。

碰撞触发放置 BP_DialogueTrigger，配置 Conversation 和 Box 范围。NPC 放置 BP_DialogueNPC 派生类并配置 Conversation；已有 NPC 可添加 AC_DialogueParticipant，再从原互动事件调用 Interact(Player)。初始化前的请求须先确认 Pawn 与管理器有效，不用固定短 Delay 猜测加载时间。

## 存档与迁移

跨关卡/存档记忆仍默认关闭，项目原有自动存档/自动读档未开启。关闭时 bPlayOnce 只在当前玩家组件生命周期内记录。以后显式打开组件的 Enable Persistent Memory，或调用 BFL_Dialogue.EnableDialogueMemory(true)；当前不启用。

主存档成功后调用 BFL_Dialogue.SavePlayerMemory，bPrimarySaveSucceeded 必须传真实结果；读档使用 LoadPlayerMemory。对话侧车槽为原槽名加 `_Dialogue`。主存档失败不写侧车，缺少侧车按空记录读取，异常版本返回失败。读档取消当前播放、清空角色局部记录，不恢复半句进度。

旧原生 `DialogMemorySave` 的磁盘文件不能靠 ClassRedirect 自动变成蓝图 SaveGame。本机仅发现一个本次 QA 旧格式槽，已先备份再一次性转换；完成集合与版本逐字段相等，并在旧插件移除的游戏进程重新读取通过。其他机器带来的旧格式存档仍需同样转换，不能声称可以直接加载。转换进程临时加载备份的旧插件，仅用于读取旧文件；游戏与正式工程不再依赖它。转换脚本与备份位于下述本地证据目录，未恢复任何自动保存功能。

## 项目通用 Game Instance 后续调整（2026-10-18）

按用户要求，将对话专用 Game Instance 通过 UE 资产改名/移动迁为 `/Game/Blueprints/Core/BP_TimeShuttleGameInstance`，更新 DefaultEngine.ini、AC_DialogueManager、BFL_Dialogue 及实际引用者；旧类路径引用为零。对话的七个记忆函数和两个状态变量归入 `Dialogue|Memory`，保留公开函数签名、SaveGame 类和版本，不引入第二套存档。资产默认与玩家组件的持久化开关均为 false，未启用自动保存或加载。

重启编辑器后，59/59 基础检查（含实际 Game Instance 类与默认关闭断言）、15/15 真实跨关卡及训练室阶段对白检查通过；显式开启仅发生于测试实例，完成后关闭。无制作工具的独立 UE 进程加载/编译11个蓝图并核对旧类及原插件/辅助模块引用为零。48张受影响图表忽略类名、路径和布局后语义相同，六处改名节点做了局部布局检查。此次没有再修改播放规则，也没有重跑上一轮28项边界检查或全游戏打包。

本轮最终报告见 [ProjectGameInstance20261018](DialogSystem/ProjectGameInstance20261018/)，完整日志、截图和本轮恢复点在 `Saved/Agent/DialogueBlueprint/ProjectGameInstance/`。最初的 BlueprintMigration20261018 证据保持原样，代表改名之前的版本。独立 Word 手册同步新路径，九页渲染已核对。

## 可选记忆接口解耦（2026-10-18）

最新实现保留通用 GI，解除 AC_DialogueManager/BFL_Dialogue 对其具体类型的直接引用。通过 BPI_DialogueMemory 提供六个记忆操作；BFL_Dialogue 负责接口发现、有效性和启用检查。缺失/关闭的服务不影响对话、局部一次性记录与清理；显式存读返回 false，LoadPlayerMemory 仍按原契约取消播放并清除局部记录。原有 GI 函数和存档格式保持，持久化默认 false。

本轮 基础 59/59、跨关卡/训练接入 15/15、默认原生 GI 无记忆服务 21/21、接口开关 11/11 全通过；4 个改动蓝图编译零错误零警告，无工具冷加载 12 个运行蓝图通过。43 张无关图表保持，15 张实现图表整理注释。详见 [本轮证据](DialogSystem/MemoryDecouple20261018/README.md)。以下表格保留迁移阶段历史结果，不混作本轮重测。

## 验证证据与范围

可随工程共享的最终报告与字幕截图位于 [BlueprintMigration20261018](DialogSystem/BlueprintMigration20261018/)。完整本地证据目录：`Saved/Agent/DialogueBlueprint/`。测试均在 UE 5.6.1 实际编辑器/PIE 执行；输入由 PlayerController 或 Enhanced Input 注入，不冒充人工 OS 键盘试玩。

| 检查 | 结果与证据 |
|---|---|
| 基础行为 | 57/57，插件移除后冷进程再次通过；runtime_tests.json。实际语音结束、自动/手动、输入映射、纯文字、优先级、移动锁、暂停、时间膨胀、碰撞、NPC 接口、死亡和记忆开关/保存读取。 |
| 边界行为 | 28/28；edge_tests.json。事件重入、开始/结束次数、取消语义、真实 Enter/Space/P 输入、同帧去重、无效表/行/ID/语音、循环音频超时、加载期死亡、来源销毁、旧存档转换后读取、主存档失败与字幕截图。 |
| 真实跨关卡及训练接入 | 15/15；travel_tests.json。真实 OpenLevel 保留启用的 GI 记录、清掉旧音频/字幕/Session/移动锁，关闭记忆时局部记录不跨地图；加载 Map_TrainingRoom，等待既有一秒初始化，通过现有 BeginStage1EnergyIntro 阶段入口播放 TSS1_Energy 并自然完成。未据此声称本轮重跑完整 S1–S7 通关。 |
| 冷加载与依赖 | cold_compile.json：10 个核心/玩家/训练蓝图 0 错误、0 警告，旧模块引用为零。另以不加载两套临时制作工具的独立 UE 进程编译 11 个运行蓝图并核对三种模块引用，见 ordinary_cold_load.json / ordinary_cold_load_final.log。 |
| 数据保留 | 原七张表 JSON 规范化逐字段相等；checkpoint.json 与 final_table_equality.json。 |
| 图表可维护性 | 60 张图表经 Blueprint Assist 整理并添加职责注释；70 张图表整理前后语义对比一致，包含默认值与穿过 reroute 后的真实连接；format_result.json、format_semantics.json 与 graph_*.png。 |
| 存档转换 | legacy_save_conversion.json，原始文件备份及 SHA-256、转换后记录数与逐字段校验。 |

本轮发现并修复了重设父类后玩家组件模板缺失 Widget/InputAction 引用、异步加载完成时的回调重入保护等迁移问题。测试脚本的失效 Python 对象引用、训练室初始化时序和 UE 受保护属性探测异常与最终通过报告分开保留；这些不属于最终运行错误。

原动画重复 DefaultSlot、既有 VFX 加载提示等非本模块日志不等同于本轮新增问题。不宣称全工程零警告；没有完整 Cook/打包、全分辨率及全部正式关卡验收。本次功能测试使用独立 QA 存档与测试数据，不改正式进度。

## 保存范围与恢复

项目改动包含 DialogSystem 蓝图/类型/测试资产、七张原对白表的行结构迁移、BP_FPCharacter、BP_TrainingController 调用类型、DefaultEngine.ini、TimeShuttle.uproject 及旧插件删除。没有更改训练关卡阶段规则，没有替换别的项目系统。

原内容/配置/插件在 `Saved/Agent/DialogueBlueprint/Backup/`；移走的旧插件在 `Saved/Agent/DialogueBlueprint/RemovedPlugin/`。这些是本机忽略跟踪的恢复材料，不能代替 Git 提交。切分支/协作时应把上述关联资产与插件删除作为完整的一组保留；不要只合并 BP 而遗漏 Types、表结构或工程配置。恢复前检查是否存在后续人工编辑，禁止直接覆盖较新的用户工作。

独立 Word 手册位于文档工作区 `开发文档/对话系统/DialogSystem 对话系统使用说明.docx`，已更新为本版并通过九页渲染检查。2026-10-12 原生实现说明保留在本地 Backup/Docs，仅供历史参考，其原生类型、空表路径和 84 项旧测试数字不代表当前蓝图版本。

## 设计参考

原调查参考了 Grogger Blueprint Dialogue System 的组件/UMG/表驱动结构，以及 NotYetGames DlgSystem 的参与者、语音及结束事件边界；没有安装它们。旧示例的引擎版本不能代替本项目 UE 5.6.1 验证。

- https://forums.unrealengine.com/t/blueprint-dialogue-system/29427
- https://github.com/NotYetGames/DlgSystem
- https://github.com/NotYetGames/DlgSystem/wiki/Dialogue-Manual
- https://dev.epicgames.com/documentation/en-us/unreal-engine/blueprint-communication-usage-in-unreal-engine?application_version=5.6
