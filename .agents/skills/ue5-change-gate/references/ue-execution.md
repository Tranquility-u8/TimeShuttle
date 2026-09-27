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

## Blueprint layout and comments

Treat graph readability as a required final implementation pass, not optional polish.

1. Finish functional edits and establish that the intended graph connections are stable.
2. When Blueprint Assist is available and verified, refresh node sizes before formatting. Prefer selective formatting for the modified node tree; use full-graph formatting only for a new graph, a graph wholly owned by the task, or explicit user authorization to rearrange the whole graph. If the plugin is unavailable, arrange the same scope manually.
3. For new functionality, add comment boxes after the initial layout. Group nodes by responsibility and document only useful intent: purpose, important branches, timing/order, invariants, or non-obvious edge cases. Do not narrate individual nodes or replace accurate existing comments.
4. Selectively format the nodes inside the new or changed comment boxes, then inspect the graph at a readable zoom. Check comment bounds, execution flow, crossings, reroute nodes, and separation from unrelated sections.
5. Confirm formatting did not change semantic connections, pin defaults, interfaces, replication, or public behavior. Reroute-node changes are acceptable only when they preserve connectivity.
6. Compile after the layout/comment pass, save only the task assets, and capture editor-visible evidence of the final graph. Layout evidence supplements rather than replaces PIE and runtime validation.

## Evidence

- Before/after asset paths and screenshots or structured graph summaries.
- Blueprint compiler result and relevant Output Log excerpt.
- PIE steps, expected result, actual result, and edge cases exercised.
- Git status showing intended files only; note that binary diffs require editor-level review.

## Stop conditions

Do not mutate an ambiguous/wrong editor target, overwrite conflicting user changes, or perform an unapproved destructive recovery. A missing operation or locked package is a reason to diagnose and choose a verified alternative, not to repeat a failed call blindly. Check available editor Python, Unreal-aware helper or GUI support; pause only when no safe authorized route remains. Diagnose and repair compile errors introduced by the task before claiming success.

Do not pause for renewed approval merely because an authorized Blueprint edit automatically dirties related level instances or World Partition external actors. Verify their relationship, preserve instance overrides, and include only necessary related assets in validation and saving. Investigate unrelated dirty assets and leave them unsaved; request clarification only when completing the task would require changing unrelated work.
