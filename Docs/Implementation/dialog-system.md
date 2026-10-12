# DialogSystem 使用与实现说明

日期：2026-10-12。任务 ID：P-008（对白播放）、P-058（对白 UI）、GPD-026（交互）。

状态：完整功能已实现并通过本轮 UE 编辑器与 PIE 验证，资产已保存。运行环境为 UE 5.6.1、单机本地玩家。正式剧情台词尚未提供，因此正式表为空；Tests 内的台词、语音和地图仅供验证。

## 已确认并实现的规则

- 支持碰撞空气盒、现有 NPC 互动接口、剧情强制三种入口；全部由玩家唯一的 DialogueManager 管理，无回答选项。
- 角色初始化默认自动。P 切换模式，Enter / 空格在手动模式下进入下一句；切换状态在同一角色生命周期内保留。没有跳过整段的玩家入口。
- 有配音时，自动和手动都必须等真实声音完成。自动在完成后推进；手动等待按键。按住键不会连续跳句，同一帧的多次 Next 请求只处理一次。
- 无 SoundWave 的句子只显示文字：自动等待 TextOnlyDuration，手动可立即继续。非空但加载失败、循环或无效的声音资源属于配置错误，会取消并发出错误事件，不能伪装成正常完成。
- 字幕为底部姓名＋整句文字，自动换行，无打字机、选项或头像。所有声音为 2D，不因离开 NPC 变小声。
- 整段配置 bLockPlayerMovement。锁定时保留转视角、对话控制和暂停菜单；阻止移动、跳跃、开火、互动、换枪、时间能力等输入，并清理已经启动的连射、互动、滑行及时间能力。自由移动版本保留其他游戏操作，空格在对话中专用于下一句。
- 离开碰撞区、离开或销毁 NPC 不会取消已经开始的对话。只有一个活动对话。
- Priority 为 1–3，1 最高；Story 请求的有效优先级强制为 1。新请求必须严格高于当前段才能打断；同级、低级或当前同一段返回 Busy，不排队，不自动恢复被打断的段。
- 暂停菜单暂停声音和计时，恢复后继续；死亡取消；关卡切换清理声音、UI 和本组件的输入状态。时停/子弹时间不改语速，也不延长纯文字阅读时间。回溯不回退本组件的台词索引或完成记录。
- 跨关卡及存档记忆已实现，但默认关闭；没有重新开启项目此前禁用的自动存档/自动读档。

## 资产与代码入口

| 路径 | 用途 |
|---|---|
| `/Game/DialogSystem/Data/DT_DialogueLines` | 正式逐句表，行类型 DialogLineRow |
| `/Game/DialogSystem/Data/DT_DialogueConversations` | 正式整段表，行类型 DialogConversationRow |
| `/Game/DialogSystem/Blueprints/AC_DialogueManager` | 原生运行组件的项目适配子类，已挂载 BP_FPCharacter |
| `/Game/DialogSystem/Blueprints/BP_DialogueTrigger` | 可调整盒体范围的空气碰撞触发器 |
| `/Game/DialogSystem/Blueprints/BP_DialogueNPC` | 继承 BP_Interaction_Base，接入 BPI_Interaction；可再派生并添加 NPC 模型 |
| `/Game/DialogSystem/Blueprints/AC_DialogueParticipant` | 已有 NPC/剧情 Actor 可添加的请求组件 |
| `/Game/DialogSystem/UI/WBP_Dialogue` | 可编辑 UMG 布局；姓名、正文、状态文字及安全区 |
| `/Game/DialogSystem/Input/IMC_Dialogue` | P、Enter、SpaceBar 的独立输入上下文 |
| `/Game/DialogSystem/Tests/L_DialogueVerification` | 独立验证地图，使用现有 GM_FP 与时间回溯管理器 |
| `Plugins/TimeShuttleDialog/Source/TimeShuttleDialog/` | UE5.6 C++ 生命周期、语音、输入、数据行结构和记忆；全部提供 Blueprint 接口 |

原生插件已在 TimeShuttle.uproject 启用。新机器需要对应 UE5.6 C++ 工具链构建模块；本机已构建。行结构和枚举是原生反射类型，在 DataTable/蓝图编辑器中直接可选，不另造功能重复的 S_/ENUM_ 资产。编辑器自动化辅助工具仅用于本次制作与验证，不是游戏运行依赖。

## 填写 DataTable

先在逐句表添加行，再在整段表的 Lines 数组按播放顺序引用这些行；不依赖 DataTable 显示排序。

| DialogLineRow 字段 | 类型／默认值 | 说明 |
|---|---|---|
| SpeakerId | Name | 可选的稳定说话者标识 |
| SpeakerName | Text | 必填，字幕姓名，可本地化 |
| DialogueText | Text | 必填，完整字幕，可本地化 |
| VoiceWave | Soft SoundWave | 可空；非空则异步预加载整段的语音 |
| TextOnlyDuration | Float，3 秒 | 无配音的自动阅读时间，至少 0.1 秒 |
| PostLineDelay | Float，0 秒 | 自动模式的句后停顿；有配音时从声音完成后开始计时。手动模式不增加这个等待 |
| LineEventId | Name | 可选的剧情事件标识，随句开始/自然结束事件发出 |

| DialogConversationRow 字段 | 类型／默认值 | 说明 |
|---|---|---|
| ConversationId | Name | 必填的稳定整段 ID；用于事件和一次性记录，不随表行重排变化。不同表也应保持项目内唯一 |
| Lines | DataTableRowHandle 数组 | 有序逐句引用，可复用台词 |
| Priority | Int，3 | 1 最高、3 最低；运行时也验证范围 |
| bLockPlayerMovement | Bool，false | 整段是否限制为仅转视角 |
| bPlayOnce | Bool，false | 自然完成后禁止重复；取消、死亡、优先级打断均不计完成 |

ValidateConversation 可供制作工具/蓝图预检；RequestDialogue 也会验证空表、错行类型、缺行、空姓名/正文、非法时间和同表重复 ID。声音加载超时及异常播放会通过 OnDialogueError 返回 LastError。

## 三种接入方式

1. **碰撞盒**：把 BP_DialogueTrigger 放进关卡；设置 Conversation 的 DataTable 与 RowName；在 TriggerBox 调整 Box Extent。仅本地玩家 Pawn 可触发。Busy 不消耗一次性标记，离开后重新进入可重试。
2. **NPC**：把 BP_DialogueNPC 或其子类放进关卡并配置 Conversation，沿用现有 InteractionArea、UI_Interaction 与玩家互动键 F（也保留现有手柄映射）。对于已有 NPC，添加 AC_DialogueParticipant，并从它原有的互动事件调用 Interact(Player)，避免另写一套抢占按键的距离轮询。
3. **剧情**：取得玩家 DialogueManager，调用 RequestDialogue(Conversation, Story, SourceActor)；或调用触发器/参与组件的 TriggerStory(Player)。根据返回值区分 Accepted、Busy、AlreadyCompleted、InvalidData、PlayerUnavailable、ReentrantRequest。

监听 OnConversationStarted、OnLineStarted、OnLineEnded、OnConversationEnded、OnDialogueError 接剧情。OnConversationEnded 带结束原因与来源；只有 Reason=Completed 才按剧情完成处理。中途取消不补发句自然结束。回调中需要衔接另一段时放到下一 Tick 请求，避免正在状态转换时重入。

CancelDialogue 是剧情/生命周期接口，没有绑定玩家跳过键。不要用 Stop Voice 充当 Next：停止音频也可能触发 UE 的 OnAudioFinished。

## UI 与输入扩展

WBP_Dialogue 提供可编辑 Widget Tree。保留 SpeakerLabel、DialogueLabel、StatusLabel 三个 TextBlock 名字可继续使用原生更新；样式默认值在父类 Dialogue|Style 分类。UI 不抢键盘焦点，整个 Widget 不参与命中测试。字幕上移留出原 HUD 的弹药区域。

Manager 只添加/移除自己的 IMC，不 ClearAllMappings。输入组件由 PlayerController 持有并推入输入栈，避免 Pawn 的自动枚举造成重复分发。BP_FPCharacter 的按下/持续输入路径有门禁，释放路径保留；以后新增 Gameplay Input 时也接入 AllowGameplayInput。移动锁使用成对的 SetIgnoreMoveInput，不用 ResetIgnoreMoveInput，也不会强行恢复 Walking。

## 一次性记忆：已实现，默认关闭

- bPlayOnce 的本角色生命周期记录可使用；只有自然完成才写入。
- 跨关卡与磁盘持久化开关为 AC_DialogueManager 的 Enable Persistent Memory，当前 false。也可由游戏初始化逻辑取得 DialogMemory 子系统并显式 SetMemoryEnabled(true)，运行时启用会跨关卡保留。
- 启用后，DialogMemory 在 GameInstance 中保留完成 ID。BP_FPCharacter 现有显式成功存档和成功读档路径已接 SavePlayerMemory / LoadPlayerMemory。
- 对话记录使用“原游戏槽名 + `_Dialogue`”的独立 SaveGame，不覆盖原存档结构。主存档失败则不写对话记录；旧存档没有侧车时清空旧的完成集合，正常作为无记录读取。坏存档/版本不符返回 false。
- 读档先取消活动对话并清空本角色一次性记录，再按已启用的持久化策略读取。未做播放到半句的存档恢复：读取后处于 Idle，而不是重新播放旧音频。
- 测试仅使用独立的 DialogSystem_QA_20261012 槽。正式自动存档和自动读档仍保持原有关闭状态。

## 验证与恢复点

最终验证结果见本文件后续“交付证据”及本地 `Saved/Agent/DialogSystem/` 报告。编译成功、文件存在、PIE 行为、键位注入和目视截图分别记录，不能互相替代。测试语音是本机离线合成的两条测试声音，不是正式剧情配音。

范围：DialogSystem 新资产、TimeShuttleDialog 插件、TimeShuttle.uproject 插件启用项、BP_FPCharacter 对话组件/输入门禁/死亡/显式存档接入，以及本说明与共享知识记录。原有 VFX、训练室等改动不属于本任务。

玩家原始资产有定向备份 `Saved/Agent/DialogSystem/Backup/BP_FPCharacter.uasset`，初始图表导出为 player_before.json。仅在确认没有后续玩家改动后才可按工程规则恢复，不直接覆盖新的用户工作。

## 网络调查与参考选择

所有链接于本轮打开或搜索核查。仅阅读可访问文本，不声称完整观看视频或运行示例工程。

| 资料 | 本轮核实内容 | 本项目采用方式与限制 |
|---|---|---|
| [Curtision：Designing a Data-Driven Dialogue System in Unreal Engine 5](https://curtision.com/2025/05/24/%F0%9F%8C%BF-designing-a-data-driven-dialogue-system-in-unreal-engine-5/) | 作者文章覆盖结构体、DataTable、管理器、UMG 与事件派发；示例含选择分支 | 参考数据与 UI 分离结构；文章是概念教程，未完整解决声音结束、清理与输入恢复，不直接照抄分支或可运行性声明 |
| [Grogger：Blueprint Dialogue System](https://forums.unrealengine.com/t/blueprint-dialogue-system/29427) | 作者介绍 Blueprint/UMG、Actor Component、DataTable、线性/分支、语音与事件；附文档和视频教程入口 | 与工程蓝图路线接近，可参考组件边界；帖子标注 UE4 4.9–4.19，不能视为 UE5.6 已验证模板，视频入口访问失败 |
| [NotYetGames/DlgSystem](https://github.com/NotYetGames/DlgSystem) | 源码仓库、MIT；作者 README 列 UE5.6/5.7/5.8 支持 | 主要生命周期参考；本轮没有下载、安装、编译该插件 |
| [DlgSystem 使用手册](https://github.com/NotYetGames/DlgSystem/wiki/Dialogue-Manual) | 参与者接口、上下文、Speech Sequence、声音字段、开始/结束事件；UI 与序列化由游戏提供 | 参考线性序列、参与者和完成/取消边界，不照搬 Dialogue Asset 图编辑器替换用户要求的 DataTable |
| [NotYetDlgSystemExample](https://github.com/NotYetGames/NotYetDlgSystemExample) | 实际示例仓库含 Content、Plugins、uproject、MIT；当前打开分支为 5.2，附逐步教程 | 可参考的完整示例工程；示例分支不是 5.6，不直接迁入项目，不把插件支持版本误写为示例版本 |
| [steelx/DTDialogueSystem](https://github.com/steelx/DTDialogueSystem) | 当前可见仓库只有 README 与 gitignore，README 给三张表与 GameplayTag 流程 | 仅作为文档参考；未取得实现源码，不称其为可直接复刻的开源模板 |
| [Epic UAudioComponent API](https://dev.epicgames.com/documentation/en-us/unreal-engine/API/Runtime/Engine/UAudioComponent) | 完成委托既可能来自自然结束，也可能来自 Stop | 实际推进必须有状态保护、取消顺序和过期回调防护；网页默认版本为5.8，另做本机5.6源码核查 |
| [Epic Data Driven Gameplay](https://dev.epicgames.com/documentation/en-us/unreal-engine/data-driven-gameplay-elements-in-unreal-engine) | DataTable 与结构化数据工作流 | 用于字段、行引用和内容制作方式参考；网页默认版本为5.8 |

结论：参考 DlgSystem 的生命周期/事件及上述 DataTable 教程，自行实现数据驱动的运行组件及可编辑蓝图内容层。未找到经本轮运行验证、能原样覆盖全部需求的现成模板，因此不能承诺整包迁移即可完成。

本地采用 skills：项目 time-shuttler-context、ue5-change-gate，以及扩展库 ue-data-driven-design、ue-audio-and-metasounds（后两者标注5.8）。音频 Skill 中“SoundWave 不直接播放”的绝对表述与本机接口不符，不采用：5.6.1 SoundWave.h 中 USoundWave 继承 USoundBase；AudioComponent.h 的 SetSound 接受 USoundBase。

本机5.6.1头文件证据：AudioComponent.h 449–451行说明 OnAudioFinished 包含 Stop，484行为 SetSound，578行为 Stop，586行为 SetPaused；SoundWave.h 416行为继承关系。这仅证明接口，不是当前游戏运行证据。

## 交付证据

2026-10-12 最终结果：**84 项指定运行检查通过，6 个受影响蓝图编译通过并成功保存**。逐项结果保存在 [verification.json](DialogSystem/verification.json)。最后检查没有未保存的内容或关卡包；持久化默认值为 false，独立 QA 存档已删除。

| 验证组 | 结果与范围 |
|---|---|
| 冷启动后核心回归 | 57 项通过：实际声音完成、自动/手动、文字时长、暂停、0.01/0.2 世界倍率、输入锁、优先级、碰撞、NPC 接口、一次性与清理 |
| 跨关卡／存档 | 9 项通过：OpenLevel 重新加载验证地图产生新 World/Pawn，已完成 ID 保留；切图释放输入锁；侧车保存/加载、旧存档无侧车清空记录；测试结束关闭记忆 |
| 实际键位与项目系统 | 17 项通过：P/Enter/Space 映射、项目 FullStop 保持语速、锁定时结束已有时间能力、W/T 被挡而视角保留、Escape 打开原暂停菜单、无效行拒绝、真实角色死亡分支取消 |
| NPC 完整交互链 | 1 项通过：面向实际 InteractionArea，向 PlayerController 注入 F 按下/释放，经原 AC_Interaction 触发 TEST_NPC |
| 原生构建 | UnrealEditor Development、UnrealGame Development、UnrealGame Shipping 插件目标构建成功；后两项不代表完整游戏已 Cook/打包或运行 |
| 蓝图与布局 | BP_FPCharacter、Manager、Participant、Trigger、NPC、Widget 均 UpToDate、0 编译错误、保存返回 true；Blueprint Assist 整理后补充注释并目视复核 |

测试方法边界：按键由 PlayerController / Enhanced Input 注入，不冒充人工 OS 键盘试玩。死亡测试将 PIE 实例设为可受伤、剩余一次命中并清除测试保护时间，再调用真实 ApplyDamage；未改正式角色默认血量或无敌设置。存档读写测试使用独立 QA 槽，主存档蓝图接入另经图表审计。

玩家 21 张原有图表审计：原有功能节点位置不变；穿过新增门禁/通知与 reroute 后，原有连接端点保持；3 个未连接的输出 Key 引脚由空值序列化为 None，实际 Caps Lock 等按键事件没有改键。新增节点在原有空白处独立成组，未全图重排。

日志没有宣称全工程零警告：无效行测试会主动产生预期的 DialogSystem 错误；原暂停菜单仍记录 Non-Focusable Widget 焦点错误，原动画蓝图有重复 DefaultSlot 警告，本轮未修改这两个系统。早期测试夹具、工具 API 探测及编辑器辅助构建错误已与最终通过结果分开记录。

目视证据：[游戏字幕](DialogSystem/dialogue-ui.png)、[NPC 接入](DialogSystem/npc-layout.png)、[锁定适配](DialogSystem/manager-layout.png)、[输入门禁](DialogSystem/player-input-layout.png)、[死亡清理](DialogSystem/player-death-layout.png)、[显式存档](DialogSystem/player-save-layout.png)。

本轮未做：完整游戏 Cook/打包运行、所有正式关卡与分辨率的视觉验收、正式剧情台词/配音制作。系统功能已完成；这些内容与发布阶段验证不能由测试台词替代。

## 开始制作正式对话

1. 打开 `/Game/DialogSystem/Data/DT_DialogueLines`，添加姓名、正文和可选 SoundWave；没有声音时设置 TextOnlyDuration。
2. 在 `DT_DialogueConversations` 新建唯一 ConversationId，按顺序填写 Lines；设置 Priority、Lock Player Movement 和 Play Once。
3. 碰撞触发放置 BP_DialogueTrigger，NPC 使用 BP_DialogueNPC 子类或 Participant 接入现有互动，分别指定刚建立的整段行。剧情通过 RequestDialogue 的 Story 入口调用。
4. 可先打开 `/Game/DialogSystem/Tests/L_DialogueVerification` 运行，测试表已提供声音、纯文字、锁定和优先级样例。NPC 继承的是交互基类，需要按项目角色另加外观模型。
5. 玩家初始自动；P 切换手动，语音结束后 Enter/空格继续。持久化保持关闭，等需要正式接入一次性存档时再显式开启。

新机器若缺少原生模块二进制，需要使用匹配的 UE5.6 与 C++ 工具链构建 TimeShuttleDialog 插件。编辑器制作辅助 DLL 位于本机临时目录，不应加入项目依赖或分发。

