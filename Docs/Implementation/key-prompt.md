# Open-corner key prompt (P-106, PNG revision)

Current gameplay integration (2026-10-28): the player now owns AC_KeyPrompt and DT_KeyPrompts. Forced falling-rock, normal reload and configurable interaction prompts are integrated; the old RELOAD advice is retired. See [Blueprint rules and setup](key-prompt-rules.md) and [validation](KeyPromptRules/validation.md). The PNG revision history below describes the earlier visual-only verification scope.

Updated 2026-10-28 in UE 5.6.1. Current implementation: two ordinary UMG Blueprint widgets plus four imported white-alpha PNG textures. No C++ plugin or runtime class was added.

Assets: `/Game/UI/KeyPrompt/WBP_KeyPrompt`, `WBP_KeyPromptHUD` and `Textures/T_KeyCorner_TL/TR/BL/BR`. All four source PNGs are 80x80 RGBA and are under `SourceArt/UI/KeyPrompt/`. Brushes directly reference these textures. Q and Time Stop remain native TextBlocks using existing F_MM_Roboto.

All corners share the single CornerColor variable. SetUniformCornerColor applies it to all four Images. Per-corner color variables, override switch, SetIndividualCornerColors, ApplyCorner, dynamic materials and parameter updates were removed. The previous four material instances and mask material were reference-checked, backed up locally and deleted.

CornerLength now scales the whole PNG (default 20x20 UMG units); stroke is baked into the PNG (16 pixels at 80x80, equivalent to 4 units at default display size). CornerStroke was removed. To change stroke independently, edit and reimport the PNG. No UV clipping, direction flipping or shape generation happens in the Widget.

Text/font settings, dimensions, text gap, overall scale/opacity and screen offset remain configurable. SetPrompt and RefreshStyle retain their public use. Existing layout/text/lifecycle graphs were preserved. Defaults remain key 88x80, Q 40 Bold, action 22 Bold, gap 16, wrapper offset (0,148). Widget does not bind Q, change input mode, activate abilities or automatically track remapping. Tutorial triggers were not changed.

Validation: two widgets compiled with 0 errors/0 warnings. Five unrelated core graphs stayed identical; three changed graphs were formatted/commented with Blueprint Assist and all 11 remaining graphs preserved semantics through formatting. Refresh chain visually inspected in editor. 33 PIE checks in Map_TrainingRoom passed, including PNG Texture2D references, shared default/changed color, removed parameters and retained text/font behavior. Native gameplay screenshots show uniform red during the test and uniform cyan after restoration. This was a transient test widget, not permanent tutorial integration. SaveGames hashes did not change.

A normal editor restart without TSVFXEditor confirmed cold loading/compilation, texture dependencies, removed material assets and absence of per-corner parameters. Existing missing MK18 curve warnings appeared during level loading; unrelated references were not changed. Cook/packaging and input remapping were not tested.

Unsaved WBP_KeyPrompt edits were saved before refactoring and backed up separately from the initial disk version. Machine-local scripts/backups/evidence: `Saved/Agent/KeyPromptPNG/` (Git ignored). Chinese handoff: shared workspace `开发文档/按键提示/开放角框Widget使用说明.md`; current evidence: `开发文档/按键提示/验证_PNG优化/`. Previous evidence in `验证/` describes the superseded material implementation.

## 2026-10-29 Designer ownership
Native TextBlock fonts, KeyBox/corner SizeBoxes and TextSpacer now control sizes and gap without Blueprint overrides. WBP_KeyPromptHUD ScreenOffset and its SetPosition chain are removed; select Prompt in Designer and drag it or edit Canvas Slot Position. Saved position (0,148), centered anchors/alignment retained. RefreshPlacement retains visibility only. Compiled and saved; no PIE or further checks per user request. User performs acceptance testing.

