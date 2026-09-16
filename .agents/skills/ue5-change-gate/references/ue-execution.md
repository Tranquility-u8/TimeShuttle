# UE execution rules

## Tool order

1. Dedicated read/write operations from the approved Unreal MCP server.
2. Unreal Python executed in the target editor when no dedicated operation exists and the API supports the task.
3. Text edits for source/config files, followed by Unreal regeneration/reload as appropriate.
4. UI automation only for gaps that cannot be addressed safely above, with extra screenshots/state checks.

Never use raw binary editing for Unreal assets.

## Blueprint quality

- Preserve public pins, callable interfaces, replication semantics, input ownership, save data, and exposed defaults unless the plan explicitly changes them.
- Avoid logic-heavy Tick paths. Prefer events/timers and document any unavoidable per-frame cost.
- Check null/invalid references, latent action lifetime, world context, and teardown behavior.
- For time manipulation, explicitly define actor eligibility, physics/velocity handling, timers, animation, AI/state trees, projectiles, audio/VFX, UI, and restoration order.
- Make repeated activation/deactivation idempotent and test interrupted transitions.

## Evidence

- Before/after asset paths and screenshots or structured graph summaries.
- Blueprint compiler result and relevant Output Log excerpt.
- PIE steps, expected result, actual result, and edge cases exercised.
- Git status showing intended files only; note that binary diffs require editor-level review.

## Stop conditions

Stop without improvising if the editor/project target is wrong, the required tool is absent, an asset is locked, a referenced asset is missing, compile errors appear, unrelated assets become dirty, source control conflicts exist, or recovery would require an unapproved destructive action.
