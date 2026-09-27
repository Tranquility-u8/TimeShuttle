# 轻量任务度量

目标：降低完成合格功能的总成本。质量与必要验证优先，不能靠省略测试、美化返工次数或更换统计口径改善指标。

## 标准执行步骤

适用于实施、修复、迁移、工作流维护任务；普通问答和只读方案讨论不建账。每个独立任务一个 TaskId，同任务跨轮继续沿用。无需新增 skill、常驻服务或定时轮询。

1. 开始实施前调用 Start，记录任务类别、lazy/guided 模式，以及已知的模型名；模型未知用 unknown，不猜。Start 输出 tokens_available，失败也继续开发。
2. 长任务可在调查完成、实施完成时调用 Checkpoint；短任务只有 Start/Finish。需要等待用户、停止工作或隔夜交接前 Pause；继续时 Resume。工具执行、UE 启动与编译等待仍计入任务经过时间。
3. 完成验收与保存后调用 Finish，填写 Outcome、ReworkCount 和最多一句主要浪费原因或改进。最后回复附一行统计，不打印原始日志。
4. 同一 Finish 重试不重复记账；已有未结束记录应先 Resume/Finish，不重新 Start。新会话承接任务时另开记录，并在 Note 引用前一 TaskId；不要把另一会话计数接到原基线上。
5. 如账户用量工具可用，仅在任务前后各读取一次；将同一个额度桶的百分比、窗口分钟数和重置时间传给脚本。不可用则略过，不反复排查。不要保存账号 ID 或完整账户响应。

PowerShell 示例（仓库根目录执行；TaskId 每项任务唯一）：

```powershell
$meter = 'Scripts/Agent/Measure-AgentTask.ps1'
& $meter -Action Start -TaskId '20260927-enemy-hit' -Title 'Enemy hit reaction' -TaskType feature -Mode lazy -Model unknown
& $meter -Action Checkpoint -TaskId '20260927-enemy-hit' -Note 'Dependency inspection complete'
& $meter -Action Pause -TaskId '20260927-enemy-hit' -Note 'Waiting for user decision'
& $meter -Action Resume -TaskId '20260927-enemy-hit'
& $meter -Action Finish -TaskId '20260927-enemy-hit' -Outcome passed -ReworkCount 1 -Note 'Missed animation dependency; add preflight check'
& $meter -Action Report
```

可选账户参数：`-UsedPercent 40 -WindowMinutes 10080 -ResetsAt '<实际重置时间>'`。已知期间有其他任务使用同账户时加 `-ConcurrentUsage`，并发事实在 Finish 也需补记。窗口重置、计数下降、窗口不一致或已知并发时不计算额度差；即使计算成功，它仍只是账户变化，不能归因成任务账单。

## 统计口径

| 字段 | 含义 |
| --- | --- |
| wall_seconds | Start 到 Finish 的总墙钟时间 |
| active_elapsed_seconds | active 区间之和，包含工具/编译/测试等待；不是模型纯计算时长 |
| paused_seconds | 明确 Pause 排除的时间；遗漏暂停会高估工作时长，应在 Note 注明，不能暗中修数 |
| token_status | observed：所有区间都有可用计数；partial：部分区间缺失；unknown：无可用差值 |
| tokens | 当前会话累计计数的区间差值，Pause/Resume 分段排除暂停期间用量 |
| token_cutoff | 最后可见用量事件时间；最终回答及尚未落盘用量不包含在内 |
| account_percentage_points | 可比较额度窗口的账户百分点差，非 token、非费用 |
| outcome | passed / partial / failed / cancelled / unknown，以实际验收为准 |
| rework_count | 首轮实现进入验证后，由缺陷导致再次修改并重验的次数；一次修复多个同源报错计一次，正常设计迭代不计 |
| collector_ms | 本次采集脚本耗时，用于检查机制自身开销 |

Token 数据源是当前 `CODEX_THREAD_ID` 匹配的本机会话日志，使用 `session_meta.id` 校验归属。只解析累计计数事件，不保存提示词、工具正文或截图。首次定位日志文件，之后复用路径；每次最多读取末尾 4 MiB，避免全量解析大日志。字段或日志不可用、累计计数回退、会话不匹配时降级，不用字数推算 token。该日志格式是本机已验证的适配方式，不保证未来版本不变。

`input_tokens` 已包含缓存输入，`output_tokens` 包含其推理输出子项；不能再次相加。展示总量时同时说明缓存量，不能按总 token 直接推算订阅额度或 API 账单。不自动合并其他会话、子代理或后台工作；有这些工作时必须注明统计覆盖不完整。模型/模式中途改变应在 Checkpoint/Note 记录，本任务不可当作单一模型基准。

## 低开销复盘

- 先积累 5–10 项实施任务建立基线。每约 5 项同类任务完成后，在正常收尾中用 Report 读取最近摘要；只有需要同类比较时才用本地脚本筛选更多记录，不把整个日志送入上下文。
- 分开比较任务类型、规模、协作模式和模型；小样本只给观察，不宣布固定节省比例。
- 每次最多试一项改进，记录原因、预期、后续同类任务结果。确实有效才精简合并进 SOP/skill；无效则撤回。不能自动改变用户授权、安全边界或最低验收要求。
- `workflow-improvements.md` 只保留可复用结论，统计原始记录留本机。跨机器需自行携带忽略文件；仓库克隆不会自带历史度量。
- 采集失败不阻塞任务；本轮标记未知，避免为了统计反复调用模型或排查工具。

## 文件与检查

- `Scripts/Agent/Measure-AgentTask.ps1`：无外部依赖的采集脚本。
- `Saved/Agent/Metrics/<TaskId>.json`：任务状态、区间和事件；本机路径仅保存在此。
- `Saved/Agent/Metrics/tasks.jsonl`：每个结束任务一条摘要；Report 默认最多输出最近十条。
- `Scripts/Agent/Test-AgentTaskMetrics.ps1`：隔离的合成数据测试，不混入真实账本。
- 修改后运行上述测试及 `Validate-AgentWorkflow.ps1`。

最终回复格式：`度量：工作经过 X 分钟（暂停 Y 分钟）；token X（截至采样，缓存输入 Y）/未知；返工 N 次；验收结果。` partial 必须注明仅覆盖部分区间。当前任务首次启用机制时，明确它只覆盖启用后的阶段，不追溯补造起点。
