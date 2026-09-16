# Agent approval gate

Use this gate before every mutating UE or project task. Read-only inspection does not require approval.

## Required proposal

```text
Problem definition
- Goal:
- Current behavior/evidence:
- Desired behavior and acceptance criteria:
- In scope / out of scope:

Technical plan
- Approach and rationale:
- Assets/files/editor state to change:
- Dependencies and assumptions:
- Risks (including Blueprint references, save/resave blast radius, performance):
- Validation evidence to collect:
- Rollback path:

Approval request
If this matches your intent, reply “确认执行” / “Proceed”. I will not modify the project before that confirmation.
```

## Approval semantics

- Approval is bound to the stated scope, targets, and risk level.
- A question, correction, or request for alternatives is not approval.
- If investigation reveals a materially different solution, new asset set, destructive step, plugin install, migration, or external write, present the revision and wait again.
- After approval, report deviations immediately. Do not hide compensating changes.

## Completion report

Report changed assets/files, editor compile/save results, tests or PIE scenario, observed output, remaining risks, and how to roll back. Distinguish verified behavior from inference.
