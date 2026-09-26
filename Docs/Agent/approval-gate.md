# Agent approval gate

Use this gate when execution has not already been authorized under the collaboration modes in `AGENTS.md`. Explicit lazy-mode implementation requests and prior approvals remain valid; do not ask again for the same scope. Read-only inspection does not require approval. In authorized work, summarize scope, validation and recovery without emitting the approval-request block below.

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
- If investigation materially expands functionality/risk or requires an action outside the existing authorization, present the revision and obtain the missing permission. Routine dependency repair, approved migrations and their related instance saves remain within scope.
- After approval, report deviations immediately. Do not hide compensating changes.
- Automatic propagation of an authorized Blueprint edit to its related level instances or World Partition external actors does not require renewed approval by itself. Verify the relationship, preserve instance overrides, and save only necessary related assets. Unrelated assets remain outside scope.

## Completion report

Report changed assets/files, editor compile/save results, tests or PIE scenario, observed output, remaining risks, and how to roll back. Distinguish verified behavior from inference.
