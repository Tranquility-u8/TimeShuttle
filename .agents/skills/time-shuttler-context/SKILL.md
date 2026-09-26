---
name: time-shuttler-context
description: Ground Time Shuttler design, planning, and implementation questions in the repo knowledge snapshot and verified Unreal project state. Use for project planning, feature analysis, requirements, architecture, or status questions; do not treat Drive plans as proof of implementation.
---

# Time Shuttler context

Read `Docs/Knowledge/README.md`, then only the routed knowledge files needed for the task.

- Architecture, asset location or implementation: read `Docs/Knowledge/project-architecture.md` and `implementation-status.md`; verify current assets before relying on paths.
- Asset creation, rename or folder organization: read `Docs/Knowledge/asset-naming.md`. Use its type prefixes and recorded legacy exceptions.
- Enemy time rewind: read `Docs/Implementation/EnemyReverse.md` for adapter contracts and verified limits.
- Keep these facts in the knowledge/implementation documents, not copied into this skill. A local repository refresh is not a Drive freshness refresh.

## Workflow

1. Classify the question as design intent, implementation state, schedule/ownership, or a mix.
2. For design intent, use `design-snapshot.md` and the matching entry in `source-manifest.yaml`.
3. For implementation state, inspect the repo and relevant Unreal assets read-only; `implementation-status.md` is a starting point, not proof.
4. For schedule or ownership, treat repo snapshots as potentially stale and request/live-read the current planning source when the answer affects assignments or deadlines.
5. State source and freshness. Separate `verified`, `Drive-reported`, and `inferred` claims.
6. Surface conflicts and `open-questions.md`; do not resolve them by guessing.

For UE mutation, apply `$ue5-change-gate` and the current collaboration mode in `AGENTS.md`. Existing autonomous authorization remains valid; do not invent an additional approval step.
