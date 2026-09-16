---
name: ue5-change-gate
description: Plan and execute Time Shuttler Unreal Engine 5.6 Blueprint, asset, editor, gameplay, or automation changes with a mandatory user approval gate and editor-visible verification. Use for UE implementation or mutation; read-only diagnosis may proceed before approval.
---

# UE5 change gate

Every mutating task has two phases. Never collapse them.

## Phase A: define and propose

1. Read `Docs/Knowledge/README.md` and the relevant context.
2. Inspect the repo, Unreal asset metadata/graphs, references, and logs read-only. Discover actual MCP tools; do not assume names or capabilities.
3. Define desired behavior and measurable acceptance criteria. Identify ambiguities that materially change the solution.
4. Choose the least-coupled approach. Prefer Blueprint interfaces, actor components, event dispatchers, data assets/tables, and explicit subsystem boundaries when they fit; do not add abstraction without a concrete need.
5. Send the exact proposal structure from `Docs/Agent/approval-gate.md`.
6. Stop and wait for explicit approval.

## Phase B: execute after approval

Read [references/ue-execution.md](references/ue-execution.md), then:

1. Reconfirm target project/editor and approved asset list.
2. Capture pre-change evidence and current dirty assets.
3. Make only the approved changes through Unreal-aware APIs/tools.
4. Compile and save only affected assets. Stop on unexpected dirty assets or errors.
5. Run the approved PIE/editor validation and capture observable evidence.
6. Review source-control status for collateral changes.
7. Report results using the completion section of `Docs/Agent/approval-gate.md`.

Re-enter Phase A if scope, asset set, plugin/config needs, data migration, or risk changes materially.
