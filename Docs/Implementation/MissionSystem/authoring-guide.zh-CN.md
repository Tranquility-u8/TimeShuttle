# 任务流程蓝图使用说明

适用于本次 MissionSystem 重构。运行逻辑使用普通蓝图；编辑器制作脚本不参与游戏运行。

## 在哪里配置训练流程

打开 `Content/Environment/TrainingRoom/Mission/BP_TrainingMission`。左侧 Components 中的任务组件就是流程配置。组件名称按阶段和步骤编号排序，实际执行顺序由 `NextStep` 决定，组件列表顺序不决定执行顺序。

关卡中放置的 `Training Mission - edit task components in Blueprint` 实例使用该配置。关卡蓝图不再包含 Enter/Check 阶段函数。原 `BP_TrainingController` 保留敌人、机关、能量教学、目标显示和检查点恢复等玩法操作。

当前配置有八个玩法检查点：S1、S2、S3、静止弱点、移动弱点、木板、近战预演、最终战斗。完成后执行原有训练结束逻辑。历史上未使用的旧分支没有重新加入流程。

## 新增或调整一个步骤

1. 在流程蓝图中使用 Add Component 添加所需任务组件，例如 `AC_Task_Dialogue`、`AC_Task_ControlLock`、`AC_Task_Cutscene`。
2. 选中组件，在 Details 的 Mission 设置中填写唯一的 `StepId`，例如 `Intro_Dialogue`。
3. 设置任务自己的参数。将前一步的 `NextStep` 改成这个 ID，再把新任务的 `NextStep` 指向原来的后续步骤。
4. 最后一步的 `NextStep` 留为 `None`。若修改第一步，同时修改流程 Class Defaults 的 `StartStep`。
5. Compile、Save，然后运行验证。重复 ID、空 ID、找不到的起点和后续 ID 会使流程拒绝开始，并记录 `LastError`。

复制组件后必须修改 StepId。删除组件时也必须修改指向它的 NextStep、FailureStep 和 WaitForStep。

| 通用参数 | 用途 |
|---|---|
| StepId | 当前任务的唯一名称 |
| NextStep | 成功后的步骤；None 表示没有后续 |
| FailureStep | 失败后的步骤；None 表示停止流程并报告错误 |
| bCheckpoint | 进入该步骤时记录重试入口 |
| bBackground | 启动后继续后续步骤，当前任务在后台运行 |
| TimeoutSeconds | 任务超时后失败；0 表示不设置超时 |

`NextStep` 不表示“等待固定时间后继续”。异步任务只有报告成功后才会推进。后台任务也需要成功结束，整个流程才能完成。

## 对话

添加 `AC_Task_Dialogue`，在 `Conversation` 中选择整段对话 DataTable 和 Row Name，不能填单句台词表。`Trigger` 控制请求类别；Story 使用现有最高优先级规则。

任务自动把自身作为 Source，并且只接受与本次请求对应的正常结束事件。对话被拒绝、抢占或取消时任务失败，不会因为播放器空闲而误判成功。`LastRequestResult` 和 `LastEndReason` 可在运行时查看。

`bAcceptPreviouslyCompleted` 默认关闭；只有明确希望把“曾经完成过”当作成功时才打开。全局对话记忆及持久化仍保持关闭。

现有播放规则保持：默认自动；P 切换自动/手动；Enter 或 Space 下一句；有语音时必须等待语音完成，纯文字按阅读时长自动推进，手动模式可立即推进。

需要“语音播放时允许玩家完成目标”时，将对话设为 `bBackground=true`，后接目标任务，再添加 `AC_Task_WaitForTask`，将 `WaitForStep` 指向该对话。训练 S1 已使用这种配置。

## 角色控制锁

添加 `AC_Task_ControlLock`：

- `AcquireLock=true`：获取锁；false：解除锁。
- `LockToken`：同一流程内用于配对的名称，例如 `IntroControls`。
- `LockMovement`：禁止移动和跳跃。
- `LockLook`：禁止转动视角。
- `LockGameplay`：禁止开火、交互、换武器和时间能力等经过玩家输入入口的操作。

例如，“只能转动视角”设置 Movement=true、Look=false、Gameplay=true。之后用另一个 ControlLock 任务设置相同 Token、AcquireLock=false 来恢复。

锁按拥有者与名称配对。同名锁在不同流程之间独立，解除一个不会清除其他拥有者的锁。流程取消、失败、结束或销毁时清理其持有的锁；Cutscene 单独持有自身的锁。暂停菜单仍然可以使用。新增加的玩家玩法输入应继续经过现有输入检查入口。

## Cutscene

添加 `AC_Task_Cutscene`，将 `Sequence` 指向 Level Sequence 资产。它创建临时播放器，正常播放一次后成功；外部提前 Stop 会失败。结束与取消会恢复序列保存的场景/镜头状态，清理临时播放器并释放自身控制锁。

Movement、Look、Gameplay 三个选项分别控制演出期间的输入，默认全部锁定。没有为训练关卡擅自增加新的演出内容；你可以把此任务插入任意两个步骤之间。

需要复用序列并替换角色时：

1. 在 Sequencer 中为要替换的对象绑定设置 Binding Tag，例如 `Speaker`。
2. Cutscene 组件的 `BindingTags` 填 `Speaker`，对应位置的 `BindingRoles` 填流程角色名，例如 `Omen`。两个数组长度必须相同。
3. 在关卡中选中流程 Actor，在其 `Roles` Map 中把 `Omen` 指向实际场景 Actor。

内置 `Player` 角色对应流程玩家，`Context` 对应 ContextActor。缺少 Sequence、标签、角色绑定或数组不匹配时，任务报告失败，不静默跳过。序列的时间来源由 Sequence 自身设置决定；不要在演出资产中使用无限循环或另一个自动播放入口与任务播放器竞争。

## 目标、等待和失败处理

- `AC_Task_Delay`：等待 Seconds，使用流程的现实时间，游戏暂停期间不计时。
- `AC_Task_WaitForTask`：等待指定任务成功；目标失败或取消时自身失败。
- `AC_Task_WaitSignal`：等待外部蓝图调用 `ReceiveSignal`。只有匹配 ExpectedSignal 且任务正在运行时才接受。
- `AC_Task_RetryCheckpoint`：重新开始当前检查点；RestartWholeFlow=true 则重启整个流程。

例如，交互机关完成后，可以通过流程的 `FindTask(StepId)` 找到 WaitSignal 组件，Cast 后调用 `ReceiveSignal(ObjectiveDone)`。信号不提前缓存；目标还没激活时返回 false，调用方应按自己的玩法决定是否记录目标状态。

训练专用任务位于 `Content/Environment/TrainingRoom/Mission/Tasks`。它们暴露具体玩法参数，例如 SetObjective 的文字、StartTargets 的分组和护甲模式、WaitTargets 的击杀数量及拾取/换弹/时停条件。它们不决定整个训练的阶段顺序。

训练支持原有 Backspace/F8 重试、Home/F9 长按重置。失败时界面显示错误和重试提示。检查点 ID 由执行器保存，训练的物理位置、生命、能量和机关恢复由训练适配逻辑执行。

## 新建其他流程与扩展任务类型

新建 `BP_MissionFlow` 的子蓝图，添加所需任务组件并设置 StartStep。默认自动启动，等待玩家可用；关闭 bAutoStart 后可从触发器、交互或剧情蓝图调用 `StartFlow`，返回值表示是否接受。`StopFlow` 用于取消，`RestartFlow` 用于重新运行。Roles 和 ContextActor 可在关卡实例中配置。

要新增能力，创建 `AC_MissionTask` 的子蓝图：

1. 重写 `ExecuteTask`，读取自己的可编辑参数并开始工作。
2. 同步操作完成时调用 `FinishTask(true, "")`。异步操作等待真实完成事件后调用；失败时传 false 和可读错误说明。
3. 需要逐帧检查时重写 `UpdateTask(DeltaSeconds)`。不需要自己额外启动 Tick。
4. 重写 `CleanupTask(Cancelled)`，解绑事件、停止自己拥有的工作并释放资源。完成、失败、超时和取消都应正确清理。
5. 把这个组件加入流程并配置链接。执行器不需要新增类型枚举或 Switch。

`TaskPlayer`、`TaskContext` 是运行时上下文。基类的 Handled 输出是覆写函数的形式参数，任务成败以 `FinishTask` 为准。不要通过修改 TaskState 变量代替生命周期 API，也不要让每个任务硬编码整个关卡的下一个阶段。

`OnStepStarted`、`OnCheckpointReached`、`OnFlowFinished` 可供 UI、日志或其他蓝图监听。调试时选择 PIE 中的流程实例，查看 FlowState、CurrentTask、PendingStep、CheckpointId、LastError，再查看对应组件的 TaskState 和 LastError。

## 验证范围

此说明描述实现接口。最终通过数量、冷启动结果和未验证项以配套验收记录为准。流程测试中使用的目标观察值和伤害夹具不等于人工武器瞄准通关；本次未宣称网络、分屏或完整打包验收。

