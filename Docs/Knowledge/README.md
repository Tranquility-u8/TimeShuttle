# Project knowledge hub

This directory is the fast, reviewable knowledge layer for agents and teammates. It is intentionally a curated Markdown snapshot rather than a full Google Drive mirror.

## Read order

1. `project-overview.md` — stable identity, goals, team, and technical baseline.
2. `design-snapshot.md` — current gameplay and narrative intent.
3. `implementation-status.md` — facts verified from the repo versus planned work.
4. `source-manifest.yaml` — exact Drive sources, ownership, and freshness.
5. `open-questions.md` — unresolved decisions that must not be guessed.

## Authority and conflicts

- **Implemented behavior:** the current repo and an editor/runtime check win.
- **Design intent:** the newest identified canonical Drive document wins.
- **Schedule and ownership:** the current project-management source wins; the spreadsheet snapshot here is contextual only.
- **This snapshot:** optimized for discovery, not a replacement for Drive.
- When sources conflict, surface the conflict. Do not silently merge incompatible claims.

The snapshot records when it was observed. Use `$drive-knowledge-sync` before high-impact design work when the snapshot is stale or the user says Drive changed.
