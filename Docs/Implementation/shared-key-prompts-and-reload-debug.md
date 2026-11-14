# Shared key prompts and reload debug policy

Updated 2026-11-07 in UE 5.6.1.

## Shared presentation

Gameplay key prompts use the existing `AC_KeyPrompt` queue, `DT_KeyPrompts` rows and single `WBP_KeyPromptHUD` / `WBP_KeyPrompt` renderer. The cyan open corners, native text, Designer-owned dimensions and screen placement are unchanged.

- Ordinary and guided projectile QTE retain `AC_TimeAbility` detection, window timing and Q input. The existing `UI_Hud.SetProjectileThreatPrompt(Visible, Progress)` API now submits / clears the `TimeStop` row, with the HUD object as its source. `Progress` remains an accepted compatibility input; the former separate QTE panel and its progress bar are retired.
- `UI_Hud.SetGuidedThreatKey` remains callable for existing callers and performs no separate rendering. Both guided and ordinary QTE resolve the same Q / Time Stop row.
- Reload uses the shared R / Reload row and the same reserve-availability function as firearm reload input.
- Custom interaction providers (`BPI_KeyPrompt`, then `AC_KeyPromptInfo`) retain precedence and their `Available` decision. When no provider exists, the resolved native target must implement `BPI_Interaction` to receive the shared F / Interact fallback. This covers existing pickups without map-specific registrations. Interaction-area permission checks remain in the existing focus path.
- `UI_Interaction` retains world-space item information and hold-progress feedback; its old standalone F TextBlock is collapsed. The retired `UI_Hud.ProjectileThreatPanel` is also collapsed in Designer.

The manager still uses the existing interaction trace and source-keyed queue. No new prompt Tick, trace, input binding, map-name branch or duplicated style asset was introduced. Forced falling-rock prompts keep their original priority and clear-on-confirmed-FullStop contract.

## Explicit reload configuration

`GM_FP.DebugInfiniteReload` defaults to false. New child `GM_FP_Test` overrides only that bool to true, and `Map_Test` selects this child in World Settings. The inherited pawn and other gameplay classes are unchanged. Tutorial and ordinary maps using `GM_FP` use finite reserve.

Each firearm calls `BP_Item_Base.LoadReloadDebugConfig` after native spawn setup and copies the GameMode option into its inherited `DebugInfiniteReload` value. Change the GameMode default before starting PIE; already initialized weapons retain their copied value.

`BP_Item_Base.GetReloadAvailability` is the common pure policy: `Available = DebugInfiniteReload || MaxAmmo > 0`; `Empty` is its inverse. Automatic reload entry, shotgun entry / shell continuation, and the R prompt all call this function.

`BP_Item_Base.TransferReloadAmmo(RequestedRounds)` caches the positive transferable count before changing ammo. Finite mode limits it to available reserve and subtracts that count; debug mode leaves reserve unchanged, including at zero. Automatic weapons supply their native effective capacity minus current magazine, including the existing akimbo calculation. `AN_ReloadShotgun` supplies one round at the production animation-notify timing, then persists native ammo data. Firing still consumes magazine rounds in both modes.

The earlier automatic-weapon reserve-decrement bypass and both firearm bases' unconditional full-magazine / reserve=120 initialization were removed. Ammo from native pickup / saved item data is preserved. Tutorial stage locks, deliberate lesson supply / resource preparation and ability guidance remain owned by the tutorial controller; they do not own alternative player prompt or reload implementations.

## Verification and recovery

Local recovery copies, graph exports, scripts, runtime results and screenshots are under the ignored `Saved/Agent/SharedKeyPrompts/` directory. Nine affected Blueprints compile with zero errors / warnings. The layout audit flattens reroutes and confirms formatting preserved functional pins, defaults and links. Player, shared visual widgets, time ability, interaction component, training controller and native pickup assets match their task-start file hashes.

All 101 recorded checks pass. [Validation data](SharedKeyPrompts/validation.json) includes the compile reports, layout audit, unchanged-asset checks and final editor state.

| Scope | Passed checks | Method |
|---|---:|---|
| Shared ammo transfer / prompt queue | 15 | PIE function calls, reserve boundary cases, Q → R restoration and one renderer |
| Automatic / shotgun reload | 44 | Native pickup and Enhanced Input reload/fire actions; finite, insufficient, zero, repeated debug and FullStop cases |
| Ordinary QTE | 8 | Production incoming projectile, native time-ability action, saved window duration and expiry cleanup |
| Guided tutorial QTE | 9 | Native tutorial shooter / bullet; physical Q enters FullStop and withdraws the shared hint |
| Tutorial interaction / finite reserve | 11 | Existing interaction ray, native F / R actions, old F visibility, finite reserve consumption and forced-source priority |
| Helper-free cold editor | 14 | Saved classes loaded / compiled; native zero-reserve reload, Q/R/F queue, cleanup and clean stopped PIE |

The ordinary-QTE screenshot used a transient longer threat window to allow capture; the separate input / expiry checks used the saved default duration. The interaction fixtures moved a native pickup's real interaction area onto the existing ray and disabled fixture physics. They did not introduce map assets or an extra trace.

Final scoped tutorial and helper-free runtime Output Log segments contain no Blueprint runtime errors, Accessed None, Python errors or assertions. Earlier fixture initialization / result-writing issues were corrected and rerun. The first production editor exit hit the previously observed `PreviewScene.GetWorld()` assertion after assets were saved; later shutdowns, saved-version loading and gameplay verification succeeded. A final state-observer ordering issue was corrected before verifying the restored camera and original viewport-play preference. Existing animation-slot / source-asset warnings were not expanded into unrelated asset repairs.

PIE is stopped, Map_Test and the original editor camera / viewport-play preference are restored, and no content or map packages are dirty. The final editor has no temporary Blueprint helper loaded. Nothing was committed or pushed. Cook, multiplayer and a complete tutorial playthrough are outside the targeted regression scope.

Native game-preview evidence: [ordinary QTE](SharedKeyPrompts/map-test-qte.png), [R / Reload](SharedKeyPrompts/map-test-reload.png), [F / Interact](SharedKeyPrompts/map-test-interact.png), [guided tutorial QTE](SharedKeyPrompts/tutorial-guided-qte.png). Blueprint evidence: [shared availability policy](SharedKeyPrompts/layout-availability.png), [native shell notify](SharedKeyPrompts/layout-shotgun-notify.png).

## HUD teardown guard — 2026-11-07

An actual TrainingRoom PIE shutdown reported `Accessed None` in `UI_Hud.SetProjectileThreatPrompt`: the owning pawn had disappeared before the pure `GetComponentByClass` lookup. The component validity check ran after that lookup and could not protect it. An execution branch now validates the owning pawn before evaluating the existing prompt flow; an invalid owner returns safely. Valid-owner request / clear behavior and QTE timing remain unchanged. Only `UI_Hud` was saved for this repair.

The guarded function compiles with zero errors / warnings. Ten warm PIE checks passed, including real unpossess / possess, shared Q request / clear, a production incoming projectile activating QTE, and EndPlay while QTE was active. Eleven further checks passed in a freshly opened editor without the authoring helper: PIE MainMenu world → native OpenLevel into TrainingRoom → invalid-owner calls → restored owner → EndPlay. The map transition was invoked through GameplayStatics, rather than a menu-button input test. Neither scoped runtime log contains Blueprint runtime errors or `Accessed None`; PIE stopped with no dirty content or map packages. Existing animation warnings remain outside this repair. Local backup, before / after graph exports, results and layout evidence are in the ignored `Saved/Agent/HUDThreatNull/` directory.
