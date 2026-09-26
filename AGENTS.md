# Time Shuttler agent guidance

This repository is an Unreal Engine 5.6 Blueprint-first FPS project. Read `Docs/Knowledge/README.md` before planning project work. Treat repository state as authoritative for implementation, and the Google Drive sources listed in `Docs/Knowledge/source-manifest.yaml` as authoritative for current design intent.

## Collaboration modes / 协作模式

This section is the canonical workflow for both modes. It takes precedence over conflicting approval or stop instructions in repository skills and SOPs; higher-priority platform instructions still apply. Mode changes affect task division, not asset integrity or verification standards.

### 模式选择与授权

- 用户说“懒人模式”或“你完全自主完成”时，进入懒人模式；说“节能模式”或“指挥我操作”时，进入节能模式。同一任务延续最近明确选择的模式，“继续”不重置模式或已有授权。
- 新任务未指定模式时，先继承会话中已表达的偏好；仍无法确定则采用节能模式，并简短说明，无须为模式选择单独暂停。
- “懒人模式 + 明确需求”授权该任务必要的常规可逆调查、修改、编辑器操作、修复、验证和定向保存。先说明目标、范围与验收，再直接实施，不另要求一次“确认执行”。讨论方案、询问可行性不自动构成实施请求。
- 两种模式均不把已有授权重复变成审批问题。已授权改动引起的关联实例变脏、可在范围内修复的编译错误，不是暂停理由。直接依赖的兼容性修复应在方案中纳入范围；意外发现时先说明原因和影响，常规可逆修复可继续，实质扩大功能或风险则重新确认。
- 模式选择不授权删除无关数据、丢弃用户改动、发布、推送、付费或发送外部消息。必要信息缺失时集中提问；等待期间继续不依赖答案的工作。
- 随时可说“切换懒人模式”或“切换节能模式”。记录已完成项、未保存项、验证结果与下一步，接着做，不重新调查整个任务。

### 懒人模式：用户定需求，Agent 完成实施

1. 将需求转为可观察的验收标准。检查当前分支、已有改动、相关知识与真实工具能力；确认恢复点，缺少恢复点时使用定向备份等可逆方式，不擅自重置或提交用户工作。
2. 优先读取蓝图导出文本、资产元数据和日志，整理直接依赖与关键默认值。给出简短的执行范围、验证和恢复办法后继续，不要求用户重复提供本机已有的材料。
3. 通过已验证的 Unreal-aware 工具或编辑器内 Python 执行适用操作；GUI 用于工具未覆盖的编辑及关键可视确认。用户无需承担例行点击、接线、导出或测试。
4. 自主修复本任务产生的问题，编译相关蓝图，在 PIE 中验证完整行为链；保存明确属于任务的资产与关联实例，核对 Git 范围。
5. 报告实际结果、保存状态、验证证据和未验证项。只有工具确实无法完成、必须由用户作出设计决定或涉及额外授权时才请求协助；说明具体阻碍，不暗中改成节能模式。

### 节能模式：Agent 负责判断，用户执行高成本界面操作

1. Agent 先完成文本、依赖、日志和参数分析，再按实际工具能力拆分工作：可批量且可验证的脚本和检查由 Agent 承担；反复截图定位、少量节点拖线、组件面板调整和游戏手感测试优先交给用户。
2. 每次只给一个可完成的操作批次，通常 3–7 步。写清资产/图表、节点名称、引脚连接、设置值、预期结果，以及本批次何时编译、是否保存。不只说“改一下引用”。
3. 每批只请求必要反馈：成功确认、完整编译错误文本、指定图表的文本导出或一张关键截图。已有文本足够时不追加整套截图。
4. 用户执行时，Agent 可继续独立分析，但不同时操控同一个 UE 窗口或修改同一资产。收到结果后检查再给下一批；出现错误先解释和修复当前批次，不让用户继续累积修改。
5. Agent 提供具体试玩清单，用户负责移动、瞄准、遮挡、命中和表现验收；Agent 对照日志及可用运行数据核查。明确区分用户报告与工具实测，不以“能编译”代替功能通过。
6. 完成后 Agent 复核保存范围和差异，交付结果。节能不意味着把依赖排查、技术决策或报错分析推给用户。

### 本次 ShooterNPC 迁移的经验：两种模式共同执行

- 改父类前检查依赖闭环：子类图表、父类初始化与构造逻辑、接口、Controller、StateTree/行为树任务与条件、动画蓝图、武器调用方、关卡实例。不能只检查当前蓝图；本次遗漏的 StateTree 旧相机引用直到 PIE 才暴露。
- 先记录关键组件层级、挂点、模型/动画资源、相对变换、碰撞尺寸与响应、移动/旋转、AI 占有设置及实例覆盖。改父类后逐项比较；不要假设组件复制或重设父类会保留全部默认值。
- 文本导出不是完整运行时事实。核对导出是否对应当前保存版本、是否包含继承成员、引脚连接及默认值；缺失内容定向补查，避免要求用户反复全量导出。
- 先用最小操作验证 API 行为，再批量使用。变量改名不等于引用所属类迁移；本次替换引用 API 保留旧 MemberParent，最终需要重建正确 Getter。已证实不可用的受保护图表属性或接口，不重复盲试。
- 同一 GUI 操作连续两次未取得预期结果，停止重复相同尝试：刷新窗口/焦点和截图，判断原因，再采用不同方法。节能模式可将明确的短操作交给用户；懒人模式先尝试已验证的替代手段。
- 截图只覆盖必要窗口，关键状态变化后再获取；文本输出使用摘要、差异或错误片段。不要输出截图 base64、大量重复截图或完整日志。独立读取可批量，依赖前一步结果的修改顺序执行。
- 保留可复用的已验证操作知识，临时脚本和观测数据放在忽略跟踪的本地目录。任务阶段完成后记录简短交接状态，避免长对话恢复时重做调查。
- PIE 验证拆开记录：占有、发现目标、视线遮挡、瞄准、开火、实际命中/扣血、受伤、死亡及清理。射击标志为真或看见弹丸不代表已证实玩家扣血；注入伤害测试必须注明方法。
- 按测试起止时间区分新错误、旧错误、观测脚本错误和原有警告。能修复的任务内错误继续修复；无法验证的结果明确列出，不称“全部正常”。
- 不承诺固定 token 节省比例或 Pro 可工作分钟数。若用户需要量化，在明确阶段前后读取额度快照并记录活动时长；账户共享用量不能直接归因于单一任务。

## Change gate outside explicit autonomous authorization

Apply this gate when execution has not already been authorized under the collaboration modes above. Existing approvals remain valid across turns; do not request them again for the same scope.

Before any action that changes project files, Unreal assets, editor state, source control, builds, or external systems:

1. Inspect the relevant repo and knowledge sources read-only.
2. Send a **Problem definition** and **Proposed technical plan** using the template in `Docs/Agent/approval-gate.md`.
3. List assumptions, affected assets/files, risks, validation, and rollback.
4. Wait for an explicit user approval such as `确认执行`, `批准`, or `Proceed`.

Do not treat the original request, silence, or approval of a different plan as execution approval. Read-only investigation and plan refinement are allowed before approval. If scope or risk materially changes after approval, stop and request approval for the revised plan.

An authorized Blueprint edit automatically dirtying its related level instances or World Partition external actors does not itself change the approved scope. Verify the relationship, preserve instance overrides, and continue necessary validation and saving without another approval request. Do not save unrelated assets.

## Project invariants

- Never edit `.uasset` or `.umap` bytes directly. Use Unreal Editor, an approved Unreal-aware MCP server, or Unreal Python running inside the editor.
- Preserve user changes. The worktree may contain active Blueprint and World Partition edits; never reset, revert, delete, rename, or resave unrelated assets.
- Keep changes narrowly scoped and reviewable. Prefer interfaces/components and data-driven configuration over hard coupling between Blueprints.
- Do not claim a Blueprint change succeeded without editor-visible verification, compile/save results, and the validation evidence agreed in the approved plan.
- Do not invent MCP tools or assume an Unreal MCP server is connected. Discover available tools first and follow `Docs/MCP/SOP.md`.
- Never store credentials, access tokens, personal data, generated caches, or machine-specific absolute paths in tracked files.
- Do not automatically copy all Drive binaries into Git. The curated text snapshot and source manifest are the default knowledge layer.

## Routing

- Project facts, design questions, or task planning: use `$time-shuttler-context`.
- Blueprint generation, Unreal Editor manipulation, gameplay implementation, asset mutation, or UE automation: use `$ue5-change-gate`.
- Refreshing or checking Google Drive knowledge: use `$drive-knowledge-sync`.
- New teammate onboarding and workflow maintenance: read `Docs/Agent/USER-GUIDE.zh-CN.md`.
- Team setup and MCP operation: read `Docs/Agent/TEAM-SOP.md` and `Docs/MCP/SOP.md`.

## Verification

Run `powershell -ExecutionPolicy Bypass -File Scripts/Agent/Validate-AgentWorkflow.ps1` after changing agent workflow files. For UE changes, validation is task-specific and must be agreed at the approval gate; at minimum compile affected Blueprints, inspect the Output Log, exercise the changed path in PIE, and report evidence and known gaps.
