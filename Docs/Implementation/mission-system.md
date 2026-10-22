# MissionSystem Blueprint refactor

Training orchestration is authored in `BP_TrainingMission` task components. `BP_MissionFlow` runs component links and reports task/flow results; it does not switch on training stage numbers. New behaviors derive from `AC_MissionTask` and implement ExecuteTask, UpdateTask and CleanupTask. FinishTask reports success or a readable failure.

The migrated training flow has 86 components and eight gameplay checkpoints. The Level Blueprint no longer contains its 31 Enter/Check/Complete stage functions. Existing controller mechanics, fixed layout and retry positioning remain in BP_TrainingController. Three embedded dialogue requests moved into editable dialogue components, and retry cancellation now reports CancelledByStory rather than Completed.

Reusable task types support dialogue completion, independently owned movement/look/gameplay locks, Level Sequence playback and role binding, delays, objective signals, background-task joins and checkpoint retries. Failure, cancellation, death and owner destruction clean up owned work. Sequence callbacks defer cleanup until the next task update, avoiding re-entrant MovieScene evaluation.

Project Game Instance and default memory settings are unchanged. Dialogue playback remains independent of the concrete Game Instance; global dialogue memory and persistence remain disabled. Runtime functionality uses normal Blueprints; the editor-only authoring helpers are not runtime dependencies.

## Editing

Open `Content/Environment/TrainingRoom/Mission/BP_TrainingMission`. Select a task in Components, edit its StepId, NextStep, FailureStep and its task-specific settings. Component list order does not determine execution. To insert dialogue or a Cutscene, add the corresponding task component and redirect the previous NextStep to it. Use unique IDs and set the new task's NextStep to the original continuation.

The Chinese authoring manual accompanies this implementation. Tests and preservation evidence are in `Docs/Implementation/MissionSystem/`.

## Repeat the generic runtime checks

Open `/Game/DialogSystem/Tests/L_DialogueVerification`, start PIE, then use the editor Python console to execute `Scripts/Validation/MissionSystem/run.py` and call `run('generic')`. Wait until `Saved/Agent/DialogueBlueprint/MissionFlow/runtime-generic-cold.json` reports passed/failed. Call `run('edges')` for the boundary suite. Do not run the two suites simultaneously. These scripts require the built-in Python Editor Script plugin and the checked-in Blueprint test fixtures; they do not require the temporary authoring plugins. Stop PIE after the checks.

Training verification uses actual dialogue, Q input and physical projectiles, plus explicitly recorded objective/hit/damage fixtures for later stages. It is not a manual weapon-aim playthrough. Network, split-screen and full Cook/package acceptance are outside this verification.

## Mission HUD update (2026-10-19)

The training objective panel now uses a reusable Blueprint presenter and page/step DataTables. See [mission-ui.md](mission-ui.md) for field contracts, animation behavior, source artwork and the scoped test results. The original 86 task components remain; the legacy controller no longer creates WBP_TrainingObjective.
