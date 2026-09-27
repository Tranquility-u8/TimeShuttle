---
name: ue5-change-gate
description: Inspect, implement and verify Time Shuttler UE 5.6 Blueprint, asset, gameplay and editor changes under the collaboration mode and authorization in AGENTS.md. Use for Unreal mutation and automation; preserve asset integrity and editor-visible evidence.
---

# UE5 change gate

Resolve collaboration mode and existing authorization from `AGENTS.md` first. An explicitly authorized lazy-mode task proceeds through investigation, implementation and verification without another confirmation request. The proposal/approval template applies only when execution is not already authorized. Read-only diagnosis may always precede approval.

For implementation tasks, include the standard Start/Finish metrics step in `Docs/Agent/workflow-metrics.md`; reuse an existing task record when continuing. Missing measurements never replace or block gameplay validation.

## Phase A: define and propose

1. Read `Docs/Knowledge/README.md` and the relevant context.
2. Inspect the repo, Unreal asset metadata/graphs, references, and logs read-only. Discover actual MCP tools; do not assume names or capabilities.
3. Define desired behavior and measurable acceptance criteria. Identify ambiguities that materially change the solution.
4. Choose the least-coupled approach. Prefer Blueprint interfaces, actor components, event dispatchers, data assets/tables, and explicit subsystem boundaries when they fit; do not add abstraction without a concrete need.
5. Read `Docs/Knowledge/project-architecture.md` and `asset-naming.md` when locating, adding or moving assets; consult task implementation notes for existing contracts.
6. State scope, acceptance criteria and recovery path. If execution is not already authorized, use `Docs/Agent/approval-gate.md` and wait; otherwise continue.

## Phase B: execute after approval

Read [references/ue-execution.md](references/ue-execution.md), then:

1. Reconfirm target project/editor and approved asset list.
2. Capture pre-change evidence and current dirty assets.
3. Make only the approved changes through Unreal-aware APIs/tools.
4. Compile and save only affected assets. If an authorized Blueprint edit automatically dirties its related level instances or World Partition external actors, inspect the relationship and preserve instance overrides, then continue within the task without another approval request. This propagation alone is not a scope change. Investigate other unexpected dirty assets without saving unrelated work; stop on errors that cannot be resolved within the authorized task.
5. Run the approved PIE/editor validation and capture observable evidence.
6. Review source-control status for collateral changes.
7. Report results using the completion section of `Docs/Agent/approval-gate.md`.

Explain newly discovered dependencies and repair routine reversible issues within the authorized task. Seek additional authorization only for materially expanded functionality/risk or actions outside the user's permission; a directly related asset becoming dirty is not itself such an expansion. Update the knowledge documents when verified architecture or naming changes.
