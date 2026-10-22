# Blueprint mission HUD

The training HUD uses a right-anchored title strip and a list of objective rows. All player-facing strings are English. Runtime presentation and integration use Blueprint/UMG assets; no project C++ runtime module or authoring plugin is required.

## Authoring

- `Content/Environment/TrainingRoom/Mission/Data/DT_TrainingObjectives`: edit each page's Title and Objectives. An objective has a stable Id, Label, Goal, ShowCount, optional Marker, ProgressChannel, Current and State. Author initial Current/State as 0. State values are pending 0, active 1, complete 2, failed 3.
- `DT_TrainingObjectiveSteps`: each row name is a mission StepId. Page selects the objective table and row; ActiveIndex is zero-based. All earlier rows are complete and all later rows pending. An index equal to the number of rows completes the page. Reset reloads initial progress for a fresh attempt. CompletePrevious controls whether the outgoing page receives completion feedback.
- `BP_TrainingMission.MissionObjectives`: the `AC_TrainingObjectives` component listens to the mission flow and uses the binding table. Existing task links still control gameplay order. Changing the HUD does not require adding stage switches to the level Blueprint.
- `AC_MissionObjectives`: reusable presenter. Public Blueprint functions are ShowMission, SetProgress, SetObjectiveState and ResetTracker. StepBindings, WidgetClass, PollInterval and CompleteHoldSeconds are editable. Derive a Blueprint component and override PollProgress to read another game's counters, or call SetProgress from gameplay events.
- `WBP_MissionTracker`: edit panel placement, title and native UMG animations in Designer. `WBP_MissionObjectiveRow`: edit row layout, label, optional diamond marker, check and gradient animations. These are ordinary editable Widget Blueprints.

`TargetsDestroyed` is the training target counter. `CombatantsDefeated` is configured goal minus the existing remaining-enemy count, read only after combat preparation finishes. Polling runs at 0.1 real-second intervals while the flow is running and sends updates only when the count changes. It does not alter damage, weapons, target death, time ability or mission success conditions.

The eight training pages cover falling rocks, incoming fire, shooting, stationary weak point, moving weak point, environmental kills, melee and final combat. Shooting/combat rows contain only `Defeat enemies current/goal`. Dialogue still teaches the detailed controls. Seventeen step bindings select pages and active rows; the 86 original task components remain.

## Visual and motion specification

Design space is 1920×1080: right margin 68, top margin 72, panel width 480, title height 48, title-to-list gap 8, row height 64, checkbox 24, optional marker 36, right accent 3. Native project DPI scaling applies. Width accommodates the longer training titles and the reference's longer multi-row pages; this is a measured visual reconstruction, not access to the original game's layout files.

The palette is blue `#2AA9FF`, near-black `#05090F`, white active labels and dim pending/completed labels. The header fades from transparent on the left to black on the right. Active rows fade into a blue gradient and right edge. Completed rows retain a bright filled check, dim the label and play a brief blue pulse. Pending rows retain an empty, dim check. Failure marks the active row with an X.

Motion is authored as native UMG animations: approximately 0.3-second slide/fade from the right on first appearance; approximately 0.22-second row activation; approximately 0.42-second completion pulse; 0.65-second outgoing completion hold followed by roughly 0.16-second fade out and 0.18-second fade in. The playback range includes the final keyframe. Final success holds for 1.2 seconds before hiding. These curves and durations are reconstruction parameters, not extracted source values.

Live count changes update existing rows without replaying page entry. Rapid page requests coalesce to the newest pending snapshot. Retry immediately replaces stale state. Cancellation hides immediately; owner EndPlay removes the widget and event bindings. Page transition timing is independent of gameplay time dilation.


## Assets and ownership

Eight original transparent PNGs are in `SourceAssets/MissionUI/Art`, with a manifest; the offline generator is kept locally under `LocalTests/MissionUI/SourceAssets/MissionUI`. Runtime textures are in `Content/MissionSystem/UI/Textures`, set to UI compression and no mipmaps. They are generated geometry, not extracted THE FINALS textures.

The title uses an embedded Roboto Bold Condensed Italic face supplied with Unreal Engine; its font file and license are included with the source assets. No fonts are loaded through a machine-specific runtime path. Body text uses the engine Roboto font.

The former `WBP_TrainingObjective` asset remains available for reference, but BP_TrainingController no longer creates it. Its legacy Present function is a compatibility no-op. The Game Instance, dialogue memory defaults, persistence, player controls and level layout are unchanged.

## Verification

Final test results and screenshots are local-only in `LocalTests/MissionUI/Docs/Implementation/MissionUI/` (including `validation.json`); these are not included in a repository clone. Full-flow verification uses real dialogue, Q input, the rock/QTE/projectile sequence, and explicit target/hit/damage fixtures for later encounters. It is not a manual weapon-aim playthrough. Network/split-screen, full Cook/package and final art approval are not certified by these tests.


Final scoped results (2026-10-19): 30 visible-window UI assertions, 31 final saved training-flow assertions, 20 ordinary-editor cold state assertions, and 77 related Blueprint cold loads/compiles. Three observed viewport sizes were 1280×720, 1920×1080 and 2304×972. Twenty-four graphs were formatted/commented; 108 graph semantic comparisons passed and 82 unrelated controller graphs were preserved. No runtime error lines occurred during the final warm training test interval. Existing curve/animation/shadow warnings and authoring-tool shutdown issues are not represented as game runtime failures.

The hidden embedded cold viewport did not paint/tick UMG animations; that attempted animation test is retained as a failed harness attempt and is not counted as a pass. Cold data/state/lifetime checks passed independently. Run `LocalTests/MissionUI/Scripts/Validation/MissionUI/run.py` in a **visible** training PIE session to repeat the presentation suite. After testing, PIE was stopped, no content/map packages were dirty, no temporary authoring helper was loaded, and pre-test save files were restored. Nothing was committed or pushed.

Local tooling policy (2026-10-19): the 33 Python files introduced during mission HUD development were moved to the Git-ignored LocalTests/MissionUI directory. They are not game runtime dependencies and are not distributed with a repository clone. PNG/font source assets, Unreal assets and existing verification evidence remain in their original locations. This relocation did not rerun gameplay tests; file hashes verified that runtime assets and configuration were unchanged.

Evidence archive (2026-10-19): all 21 files formerly in Docs/Implementation/MissionUI were relocated without content changes to the Git-ignored local evidence directory. Runtime assets were not modified and no new gameplay test was performed.
