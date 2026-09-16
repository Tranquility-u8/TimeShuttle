# Knowledge sync policy

## Include

- Stable project identity, constraints, roles, agreed design intent, narrative outline, technical decisions, and milestone scope that improve agent decisions.
- A concise source manifest with file ID, URL, type, canonical purpose, modified time, and observation time.

## Exclude by default

- Raw Docs/Sheets/Slides exports, duplicate presentations, PDFs, images, contracts, personal details, faculty/course templates, comments, and large binaries.
- Secrets, permissions, access lists, audit metadata, and machine-local paths.
- Volatile row-by-row task status better served by Jira or the live planning sheet.

## Transform

- Summarize rather than copy long source text.
- Mark concepts, decisions, and implementation facts separately.
- Preserve uncertainty and conflicting source claims.
- Do not erase human-authored repo knowledge unless the source clearly supersedes it; show the conflict for review.
- A missing/inaccessible Drive file is not authorization to delete its knowledge immediately. Mark it unavailable and request review.
