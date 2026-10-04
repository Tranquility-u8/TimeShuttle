# Project knowledge hub

This directory is the fast, reviewable knowledge layer for agents and teammates. It is intentionally a curated Markdown snapshot rather than a full Google Drive mirror.

## Read order

1. `project-overview.md` — stable identity, goals, team, and technical baseline.
2. `design-snapshot.md` — current gameplay and narrative intent.
3. `project-architecture.md` — current folders, gameplay entry points, dependencies and extension boundaries.
4. `asset-naming.md` — canonical naming rules, legacy exceptions and safe rename procedure; consult before creating/moving assets.
5. `implementation-status.md` — facts verified from the repo versus planned work.
6. `source-manifest.yaml` — exact Drive and external technical sources, ownership, and freshness.
7. `technical-references.md` — important official vendor references and their verification boundaries.
8. `open-questions.md` — unresolved decisions that must not be guessed.

Task-specific implementation evidence lives in `Docs/Implementation/`. Current records include [EnemyReverse.md](../Implementation/EnemyReverse.md), [EnemyDamagePipeline.md](../Implementation/EnemyDamagePipeline.md), [player-melee-combat.md](../Implementation/player-melee-combat.md), [TimeAbilityCore.md](../Implementation/TimeAbilityCore.md), [TimeProjectileBridge.md](../Implementation/TimeProjectileBridge.md), and the reusable [TimeAbilityLessons.md](../Implementation/TimeAbilityLessons.md).

## Authority and conflicts

- **Implemented behavior:** the current repo and an editor/runtime check win.
- **Design intent:** the newest identified canonical Drive document wins.
- **Schedule and ownership:** the current project-management source wins; the spreadsheet snapshot here is contextual only.
- **Vendor integration details:** official vendor documentation is an important technical reference, but the installed asset version and editor/runtime checks win when they differ.
- **This snapshot:** optimized for discovery, not a replacement for Drive.
- When sources conflict, surface the conflict. Do not silently merge incompatible claims.

The snapshot records when it was observed. Use `$drive-knowledge-sync` before high-impact design work when the snapshot is stale or the user says Drive changed.

Local architecture/naming observations were refreshed on 2026-09-26. This does not update the observation time of the separate Drive design snapshot. Keep project facts here, task evidence in `Docs/Implementation/`, and procedural routing in `.agents/skills/`; do not duplicate architecture tables inside skills.
