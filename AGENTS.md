# Time Shuttler agent guidance

This repository is an Unreal Engine 5.6 Blueprint-first FPS project. Read `Docs/Knowledge/README.md` before planning project work. Treat repository state as authoritative for implementation, and the Google Drive sources listed in `Docs/Knowledge/source-manifest.yaml` as authoritative for current design intent.

## Mandatory change gate

Before any action that changes project files, Unreal assets, editor state, source control, builds, or external systems:

1. Inspect the relevant repo and knowledge sources read-only.
2. Send a **Problem definition** and **Proposed technical plan** using the template in `Docs/Agent/approval-gate.md`.
3. List assumptions, affected assets/files, risks, validation, and rollback.
4. Wait for an explicit user approval such as `确认执行`, `批准`, or `Proceed`.

Do not treat the original request, silence, or approval of a different plan as execution approval. Read-only investigation and plan refinement are allowed before approval. If scope or risk materially changes after approval, stop and request approval for the revised plan.

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
