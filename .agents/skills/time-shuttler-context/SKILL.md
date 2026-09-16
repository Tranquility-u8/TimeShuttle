---
name: time-shuttler-context
description: Ground Time Shuttler design, planning, and implementation questions in the repo knowledge snapshot and verified Unreal project state. Use for project planning, feature analysis, requirements, architecture, or status questions; do not treat Drive plans as proof of implementation.
---

# Time Shuttler context

Read `Docs/Knowledge/README.md`, then only the routed knowledge files needed for the task.

## Workflow

1. Classify the question as design intent, implementation state, schedule/ownership, or a mix.
2. For design intent, use `design-snapshot.md` and the matching entry in `source-manifest.yaml`.
3. For implementation state, inspect the repo and relevant Unreal assets read-only; `implementation-status.md` is a starting point, not proof.
4. For schedule or ownership, treat repo snapshots as potentially stale and request/live-read the current planning source when the answer affects assignments or deadlines.
5. State source and freshness. Separate `verified`, `Drive-reported`, and `inferred` claims.
6. Surface conflicts and `open-questions.md`; do not resolve them by guessing.

If the task will mutate anything, hand off to `$ue5-change-gate` and obey the repository approval gate.
