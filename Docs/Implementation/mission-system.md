# MissionSystem Blueprint refactor

Training orchestration is authored in `BP_TrainingMission` task components. `BP_MissionFlow` runs component links and reports task/flow results; it does not switch on training stage numbers. New behaviors derive from `AC_MissionTask` and implement ExecuteTask, UpdateTask and CleanupTask. FinishTask reports success or a readable failure.

The original migration used 86 task components and eight gameplay checkpoints. The 2026-10-22 tutorial dialogue update uses 99 task components and preserves those checkpoints. The Level Blueprint no longer contains its 31 Enter/Check/Complete stage functions. Existing controller mechanics, fixed layout and retry positioning remain in BP_TrainingController. Three embedded dialogue requests moved into editable dialogue components, and retry cancellation now reports CancelledByStory rather than Completed.

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

## Tutorial dialogue document migration (2026-10-22)

All active training dialogue now follows Tutorial Dialogue.docx: fifteen conversations TD01-TD15 and twenty lines in DT_TD01-DT_TD15. Existing recorded SoundWaves are retained. The central conversation table exposes the fifteen new IDs; the obsolete Energy and Arrival line tables and old conversation rows are removed after reference verification.

TD01 starts on level entry, TD02 precedes the falling-rock demonstration, and TD03 prompts Time Stop when the rocks fall. TD04 completes before movement is released. TD05 waits for the safe-zone/normal-time/landed-rock conditions. TD06 follows successful dodging and precedes the energy demonstration. TD07 follows energy recovery, before pickup practice, as confirmed by the user.

TD08 follows basic shooting completion. A background AC_Training_WaitRangeHit task snapshots the active static target before TD08 and completes on accepted health loss; joining it triggers TD09 without requiring a kill. TD10 requires TD09 completion, the static exercise completion, and the defeated target's visual disappearance, as clarified by the user. AC_Training_WaitDefeatedTargetHidden observes that existing lifecycle rather than a fixed delay or player-bullet lifetime.

TD11 follows the moving-target exercise; TD12 follows the environment kills. AC_Training_WaitCombatSpawned gates TD13 on an actual live melee enemy after the deferred spawn request completes. The melee HUD page activates before TD13. TD14 follows melee defeat; TD15 follows the final enemy clear and finishes before the exit-completion task. The falling-rock HUD completion binding now uses S1_LockBeforeRocks, after entering the trigger, instead of the movement-lock task used by the introduction.

These changes are editable task-component links and ordinary Blueprint tasks. No new runtime C++ or level-script stage calls were added. Game Instance, disabled memory/persistence, training controller mechanics and map are unchanged. Process scripts, backups and test evidence stay in Git-ignored LocalTests/TutorialDialogue20261022.

Validation of the final saved configuration: 48 full-training runtime assertions, 9 manual/cancel/retry/HUD assertions, and 69 isolated cold-load checks passed. The four affected Blueprints compile with zero errors and warnings; six new graphs were formatted/commented with semantic preservation checked and editor-visible inspection. All 20 voice bindings matched the document and all 15 conversations played in order. Later combat/range gates used disclosed hit/damage fixtures; this is not manual aiming or Cook/package acceptance. The initial stale editor-instance test failed on old row names; reloading the unchanged saved map refreshed its defaults and the final full run passed. Original animation/shadow warnings remain outside this change.
