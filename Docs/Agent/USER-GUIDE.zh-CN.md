# Time Shuttler Agent 用户与维护指南

本文面向第一次接触本项目的同事，说明仓库内 Agent 能做什么、如何安全地使用，以及如何维护它的知识与规则。

## 1. 先理解这套工作流

本项目是 Unreal Engine 5.6 Blueprint-first FPS。Agent 工作流由四层组成：

| 层级 | 位置 | 作用 |
|---|---|---|
| 仓库总规则 | `AGENTS.md` | 规定审批门、安全边界、Skill 路由与最低验证要求 |
| 项目 Skill | `.agents/skills/` | 告诉 Agent 在特定任务中采用哪套专业流程 |
| 项目知识库 | `Docs/Knowledge/` | 保存可检索、可审查的项目与设计摘要 |
| SOP 与校验 | `Docs/Agent/`、`Docs/MCP/`、`Scripts/Agent/` | 说明团队操作方式并检查工作流是否完整 |

基本原则：Agent 可以先做只读调查，但任何会修改文件、UE 编辑器状态、资产、Git、构建或外部系统的操作，都必须先提交问题定义和技术方案，并等待用户明确批准。

## 2. 新同事首次使用

### 2.1 准备项目

1. 克隆仓库，并确认当前工作分支正确。
2. 使用 Codex 将仓库根目录作为本地项目打开，不要只打开单个文件。
3. 阅读根目录的 `AGENTS.md` 和本文。
4. 如果任务涉及 Blueprint 或 UE 资产，使用 Unreal Engine 5.6 打开 `TimeShuttle.uproject`。
5. 如果需要读取最新设计文档，连接团队批准的 Google Drive Connector。
6. 运行工作流校验：

```powershell
powershell -ExecutionPolicy Bypass -File Scripts/Agent/Validate-AgentWorkflow.ps1
```

看到 `Agent workflow validation passed` 表示仓库级文件与三个 Skill 均已被发现。知识快照过期警告不会令校验失败，但提示你应在高影响决策前刷新资料。

### 2.2 开始第一个任务

建议先让 Agent 调查，不要直接要求它立即修改：

```text
请先只读调查这个问题，说明你对问题的理解、当前证据、技术方案、影响范围、风险、验证方式和回滚方式。得到我的明确确认后再修改。
```

Agent 应先返回方案。检查目标、影响文件/资产和验证方式无误后，再回复：

```text
确认执行
```

批准只对已陈述的范围有效。如果目标资产、风险、依赖或方案发生实质变化，Agent 必须停下并重新申请确认。

## 3. 三个项目 Skill 怎么选

通常可以直接描述任务，Agent 会自动选择 Skill；也可以用 `$skill-name` 明确指定。

### `$time-shuttler-context`

用于理解项目，而不是修改项目，例如：

- 查询玩法、叙事、技术基线或当前实现状态。
- 分析需求、拆分功能、讨论架构与里程碑。
- 区分“设计文档计划实现”和“仓库中已验证实现”。

示例：

```text
使用 $time-shuttler-context，说明 Area Stop 的现有设计意图、仓库中已验证的实现状态，以及仍需团队确认的问题。不要修改文件。
```

### `$ue5-change-gate`

用于任何 UE5、Blueprint、关卡、资产、编辑器或 gameplay 实现任务。它强制分为两阶段：

1. 只读调查并提交方案。
2. 用户明确批准后，通过 Unreal-aware 工具执行、编译、保存和验证。

示例：

```text
使用 $ue5-change-gate 调查敌人冻结后仍会旋转的问题。先检查相关 Blueprint 和日志，给出问题定义与技术方案，等待我确认后再修改。
```

不得用文本编辑器或二进制工具直接修改 `.uasset`、`.umap`。也不要把“资产存在”当作“功能已经完成”。

### `$drive-knowledge-sync`

用于检查 Google Drive 资料是否比仓库知识快照更新，或在批准后刷新快照。默认只读取 Drive，不上传、移动、分享或删除文件。

示例：

```text
使用 $drive-knowledge-sync，只读检查设计资料是否有更新。列出新增、变化、缺失或不可访问的来源，并先给出拟更新的仓库文件，不要直接写入。
```

## 4. 日常任务的标准流程

### 第一步：只读调查

Agent 应检查相关仓库文件、知识来源、UE 资产元数据或日志，同时保护工作区里其他同事尚未提交的改动。

### 第二步：审查方案

方案必须包含：

- 目标、当前证据和验收标准。
- 范围内与范围外事项。
- 将修改的文件、资产和编辑器状态。
- 依赖、假设、风险与性能影响。
- 验证证据和回滚方式。

模板位于 `Docs/Agent/approval-gate.md`。

### 第三步：明确批准

只有 `确认执行`、`批准`、`Proceed` 等明确表达才算批准。提问、沉默、修改要求或对另一套方案的批准都不算。

### 第四步：执行与验证

Agent 只能修改已批准目标。UE 任务至少应提供：

- 实际修改的资产路径。
- Blueprint 编译与保存结果。
- Output Log 中相关结果。
- PIE 操作步骤、预期结果与实际结果。
- Git 状态，以及是否出现意外 dirty asset。

### 第五步：审查与提交

提交前确认：

- 暂存区只有本任务文件。
- 没有无关的 World Partition / External Actor 文件。
- 没有密钥、个人信息、缓存或机器绝对路径。
- 二进制资产已有编辑器侧验证证据。
- 按团队分支策略提交；除非明确要求，不要自动 push。

## 5. 常用提示词

### 查询项目事实

```text
使用 $time-shuttler-context 回答这个问题。请区分仓库已验证事实、Drive 中的设计计划和你的推断，并标明资料时间。
```

### 规划一个新功能

```text
先只读调查 <功能>。给出玩家体验目标、验收标准、可选实现方案、建议方案、受影响资产、风险、验证与回滚。先不要修改。
```

### 修改 Blueprint

```text
使用 $ue5-change-gate 调查 <问题>。确认目标项目和资产，先给出审批方案。得到我确认后，只修改批准的资产，并提供编译、日志和 PIE 验证结果。
```

### 刷新知识库

```text
使用 $drive-knowledge-sync 比较 Drive 与 Docs/Knowledge/source-manifest.yaml。先报告变化和拟修改文件，得到确认后再更新最小范围的知识快照。
```

### 审查现有改动

```text
只读审查当前改动，重点检查功能回归、Blueprint 引用、World Partition 意外保存和缺少的验证证据。不要修改或提交。
```

## 6. 如何维护项目知识库

`Docs/Knowledge/` 是为 Agent 和团队准备的受控文字快照，不是 Google Drive 的完整镜像。

- `project-overview.md`：稳定的项目身份、团队、目标与技术基线。
- `design-snapshot.md`：玩法、叙事和表现层设计意图。
- `implementation-status.md`：经过仓库或编辑器验证的实现事实。
- `open-questions.md`：仍需团队决定、Agent 不得猜测的问题。
- `source-manifest.yaml`：Drive 来源 ID、链接、职责和观察时间。

维护规则：

1. Drive 仍是设计意图的权威来源；仓库与编辑器验证是实现状态的权威来源。
2. 只更新受变化影响的最小章节，不要整批复制 Drive 文档。
3. 长文应总结，不应逐字镜像；保留来源链接、时间和不确定性。
4. 设计计划不得写成已实现事实。
5. 来源冲突时明确记录冲突，不要自行合并结论。
6. 不提交合同、个人资料、访问列表、评论、大型导出文件或重复二进制材料。
7. 更新后运行工作流校验，并人工审查 Markdown diff。

## 7. 如何维护 Skill 和规则

修改 `AGENTS.md`、`.agents/skills/` 或相关 SOP 前，先确认这是长期、可复用的团队规则，而不是某一次任务的临时偏好。

### 修改现有 Skill

1. 保持 `SKILL.md` 的 `name` 和文件夹名一致，使用小写字母、数字和连字符。
2. `description` 要说明能力、触发场景和重要边界，避免吸引无关任务。
3. 通用流程留在 `SKILL.md`；只在特定模式下需要的细节放入 `references/`。
4. `agents/openai.yaml` 的展示名称、简述和默认提示词必须与 Skill 一致。
5. 默认允许自动发现；只有团队明确要求时才改成仅显式调用。
6. 不要创建空目录、占位文件或重复 README。

### 新增 Skill

只有当一类任务具有可复用、非显然的决策流程时才新增 Skill。新增后应：

- 在 `AGENTS.md` 中加入清晰路由。
- 在本指南中说明适用场景和示例。
- 将 `SKILL.md` 加入 `Validate-AgentWorkflow.ps1` 的必需文件清单。
- 验证 frontmatter、引用路径、UI 元数据和实际行为。

### 修改审批或安全边界

审批语义、UE 二进制资产边界、外部写入权限和 Git 安全规则属于高影响规则。修改时应说明原因、影响范围和迁移方式，并由团队负责人审查。

## 8. MCP 和外部连接维护

MCP 提供工具，Skill 规定工具如何被安全使用。连接成功不代表 Agent 获得所有写权限。

- Google Drive：默认 read-first，只读取共享项目资料。Drive 写入需要单独方案与批准。
- Unreal Editor：团队目前尚未选定标准 Unreal MCP。选定后，在 `Docs/MCP/SOP.md` 登记实现、版本、负责人、连接方式、允许工具和健康检查。
- 每次会话先枚举真实可用工具，不要根据文档猜测工具名。
- 工具应分类为只读、修改、破坏性或外部写入。
- 遇到连接中断、目标编辑器错误、编译错误或意外 dirty asset 时立即停止，不要盲目重试。
- 凭据和令牌只能放在团队批准的本地配置中，绝不能提交进仓库。

## 9. 常见问题排查

### Agent 没有发现项目 Skill

- 确认 Codex 打开的是仓库根目录。
- 确认 `.agents/skills/<skill-name>/SKILL.md` 存在。
- 运行 `Validate-AgentWorkflow.ps1`。
- 重新加载项目或新建任务，使仓库配置重新发现。

### Agent 引用的设计信息可能过期

- 检查 `source-manifest.yaml` 的 `observed_at`。
- 使用 `$drive-knowledge-sync` 做只读 freshness audit。
- 对负责人、排期和状态，优先查看当前项目管理来源。

### Unreal 修改无法验证

- 确认打开的是正确的 UE 5.6 项目和编辑器实例。
- 检查 MCP 是否真实连接并暴露所需工具。
- 不要退回到直接编辑二进制资产。
- 缺少编译、日志或 PIE 证据时，将结果标记为未验证。

### Git 状态出现无关资产

- 立即停止保存和提交。
- 不要 reset、revert 或删除他人的改动。
- 记录意外文件，检查是否由关卡保存、World Partition 或“Save All”产生。
- 只精确暂存本任务批准的文件，并向负责人报告其余改动。

## 10. 维护检查表

每次修改 Agent 工作流后确认：

- [ ] `AGENTS.md` 的路由和实际 Skill 一致。
- [ ] 所有 `SKILL.md` 名称、描述和引用路径有效。
- [ ] `agents/openai.yaml` 与对应 Skill 一致。
- [ ] 中文指南、团队 SOP 和 MCP SOP 没有互相矛盾。
- [ ] 知识来源包含 ID、链接和观察时间。
- [ ] 没有密钥、个人资料、大型二进制镜像或机器路径。
- [ ] `Validate-AgentWorkflow.ps1` 通过。
- [ ] `git diff --check` 通过。
- [ ] 暂存区仅包含本次批准的文件。

## 11. 需要进一步阅读时

- 总规则：`AGENTS.md`
- 审批模板：`Docs/Agent/approval-gate.md`
- 团队简版 SOP：`Docs/Agent/TEAM-SOP.md`
- MCP 规范：`Docs/MCP/SOP.md`
- 知识库入口：`Docs/Knowledge/README.md`
- 三个 Skill：`.agents/skills/`

如果文档与实际工具或项目状态不一致，以当前仓库、编辑器验证结果和最新批准方案为准，并把差异作为维护任务记录下来。
