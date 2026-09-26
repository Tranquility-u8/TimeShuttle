# Team SOP: using agents in Time Shuttler

## One-time setup

1. Clone/open the repository and trust the project only after reviewing `AGENTS.md`.
2. Connect the approved Google Drive connector if you need live design documents.
3. Configure an approved Unreal-aware MCP server only after the team chooses one; follow `Docs/MCP/SOP.md`.
4. Open `TimeShuttle.uproject` in Unreal Engine 5.6 for Blueprint inspection or mutation.
5. Run `Scripts/Agent/Validate-AgentWorkflow.ps1` to check the checked-in workflow structure.

## Normal task flow

1. Choose lazy/autonomous mode or energy-saving/guided mode as defined in `AGENTS.md`; an ongoing task inherits its mode and authorization.
2. The agent inspects current assets and relevant knowledge, then explains scope, acceptance criteria and recovery.
3. For an explicitly authorized lazy-mode implementation request, proceed without another confirmation. For read-only proposals or work not yet authorized, use `approval-gate.md` and obtain the missing permission.
4. Keep Unreal Editor available for verification. In guided mode, do not operate the same editor concurrently.
5. Review completion evidence and Git diff/status before committing; consult `Docs/Knowledge/project-architecture.md` and `asset-naming.md` for the current entry points and conventions.

Suggested prompt:

```text
Use $ue5-change-gate to investigate <problem>. Do read-only diagnosis first, then present the required problem definition and technical plan. Wait for my explicit confirmation before changing anything.
```

## Knowledge refresh

Use `$drive-knowledge-sync` when Drive has changed, before milestone planning, or when `source-manifest.yaml` is stale. Review the proposed diff before allowing the snapshot update. Do not commit confidential contracts, personal information, large exports, or duplicate binary presentations.

## Review checklist

- Mutation was covered by explicit task/mode authorization or a subsequently approved proposal.
- Only approved files/assets changed.
- Blueprint assets compile without new errors.
- PIE validation covers the acceptance criteria.
- No unrelated World Partition/external actor saves appeared.
- Drive-derived claims include source and observation time.
- Secrets and local paths are absent.
