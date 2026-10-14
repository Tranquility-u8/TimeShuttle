# Training Room tutorial implementation

## Current implementation: ordinary Blueprints — 2026-10-14

`TimeShuttleTraining` has been removed from the active Plugins directory and project descriptor. Its unused native-derived `BP_TrainingRoomSupport` asset was deleted after a reference audit. Runtime mechanics now live in ordinary `/Game/Environment/TrainingRoom/Tutorial/` assets: `BP_TrainingController` (Actor; 45 gameplay functions, Construction Script and EventGraph), `AC_TrainingVisual` (ActorComponent; four functions), `BPI_TrainingShot`, `BFL_TrainingImpact`, and `WBP_TrainingObjective`. The original 31 Level Blueprint graphs retain stage ownership. Both weapon impact adapters call the Blueprint function library, which routes via the interface and returns false outside registered training targets. No game graph calls the temporary authoring tool.

The 16 dissolve mappings are parallel `MaterialOriginals` / `MaterialDissolves` arrays on controller defaults and the placed instance. All first-shot-only 2A/2B rules, death/current-step retry, Home reset, session-only progress, S1 dialogue/outline, shared layouts and original combat/weapon integration are retained. Existing `TimeShuttleDialog` is retained.

After removal, cold-start single-player PIE completed S1–S7B plus optional S6 practice through actual movement/interaction/reload/time/fire inputs; the fixture sets aim only and does not inject goal counters, damage or progression for completion. All 13 records were present. Real exit travel reached Map_LabBridge; the shot adapter returned false outside the tutorial and time dilation was 1. Separate death verification applies actual damage twice per death (the existing player accepts one health point per hit) and checks two same-stage respawns with four, not duplicated, enemies. Home, immediate Backspace and layout/dissolve boundary fixtures also passed. A final ordinary launch without either old plugin or temporary helper passed the initial PIE smoke test.

Blueprint Assist processed 90 changed graphs, followed by visible review and semantic equivalence checks over 105 exported graphs. Compile/save and zero native-plugin-reference checks passed. The final cold gameplay log has no Blueprint Runtime Error, Accessed None or illegal component destruction; existing animation/rendering warnings remain. Packaging, multiplayer, all weapons and long-duration performance are unverified.

Portable evidence: [Blueprint migration validation](TrainingRoomTutorial/validation_blueprint_migration.json). Local evidence: `Saved/Agent/TutorialBlueprint`; original backups remain there under Backups. The sections describing native plugin development or earlier test runs below are historical, superseded by this migration. No commit or push was made.

Verified 2026-10-14 on UE 5.6.1. Task: `20261014-tutorial-flow`; related workspace IDs: LEVEL-002, DOC-001. Map: `/Game/Maps/Map_TrainingRoom`.

The current S1–S7 guide and the user's explicit dissolve/checkpoint requirements supersede the historical three-stage tutorial plan. This change implements the tutorial in the already populated room. It does not certify the rest of the laboratory, a packaged build, multiplayer, or final difficulty tuning.

## Stage 2B update — 2026-10-14

Task `20261014-tutorial-s2b-clear` applies the same first-single-bullet rule to 2B. `Enter_S2B` calls the new `StartIndependentProjectileClearRound`, which reuses `StartProjectileClearRound` and disables QTE. `Check_S2B` prioritizes `DodgePlayerHurt`: retry step 3 with full shared player-state restoration. Otherwise a fired-and-destroyed first bullet records completion and enters step 4 (2C). No time-stop, displacement or manual-resume gate remains in 2B. Retry retains S1/2A completion and arms a new first shot. HUD text now describes this condition. 2A and 2C behavior are unchanged by this update.

Cold-loaded single-player PIE without the temporary authoring plugin passed S1, S2A and all 11 scoped assertions: QTE stays disabled; no pre-shot completion; two consecutive actual projectile injuries automatically retry 2B; health 2/energy 100/checkpoint position and facing/damage presentation/protection timer restore; previous progress remains; a frozen live first bullet blocks completion; Backspace retry works; normal-time sidestep and natural disappearance of the sole `BP_ShooterProjectile_Bullet_C_4` complete 2B into 2C. The S2 segment took 36.34 seconds. No health, progression or projectile-destruction injection obtained the pass; the fixture sets aim and sends real inputs.

Only `Enter_S2B` and `Check_S2B` changed; the other 29 level graphs compare exactly equal. BA refresh/format/comments/local-format, visual review, compile/save passed with zero errors/warnings. Win64 Development Editor build succeeded. Final editor state is clean, PIE stopped, all 101 stage actors hidden/noncolliding and all 16 material pairs retained. The cold test log contains no Blueprint Runtime Error, Accessed None or Python Error; existing animation/rendering warnings remain. See [S2B validation](TrainingRoomTutorial/validation_s2b.json) and `Saved/Agent/TutorialS2B`. S2C–S7 and packaging were not rerun. No commit or push was made.

## Stage 2A update — 2026-10-14

Task `20261014-tutorial-s2a-clear` implements the user's new rule and supersedes the old 2A control sequence. `Enter_S2A` starts `StartProjectileClearRound`; the support actor fires and tracks only the first single bullet in each attempt. `bClearVolleyFired` blocks additional shots until a retry; `DodgeProjectilesGone` requires that this first bullet actually spawned and was destroyed. A frozen or impacted-but-alive bullet still counts. Waiting before the first shot cannot pass. Retry clears the old reference and arms a new first shot. The existing six-game-second projectile lifetime remains. This matches the user's subsequent explicit first-shot-only clarification; the test tracked exactly `BP_ShooterProjectile_Bullet_C_3` in the passing attempt.

`Check_S2A` gives `DodgePlayerHurt` priority: current Health below 2 calls `PrepareRetry(false)` and re-enters step 2 with its existing checkpoint. Otherwise, `DodgeProjectilesGone` records completion and enters 2B. There is no time-stop, movement-distance or manual-resume requirement in 2A. Its HUD explains the new condition and automatic retry. That 2A-only update left 2B/C unchanged; the subsequent 2B update above supersedes the old 2B contract.

The shared tutorial retry already restored health/energy and cleared old threats. It now also resets `LastAcceptedDamageRealTime` to -1000, zeros only the existing player damage-vignette blendable, stops the held damage camera fade, and restores checkpoint facing. Other camera blendables and the F6 invincibility preference are preserved. Movement velocity is stopped by the existing retry path; lethal damage continues through the existing player death/respawn chain.

Cold-loaded UE 5.6.1 PIE without the temporary authoring plugin passed: S1; no pre-shot completion; two consecutive real projectile injuries and automatic retries; health 2/energy 100/checkpoint/facing/presentation reset; prior progress retention; a frozen live bullet blocking completion; Backspace retry; normal-time sidestep and natural first-bullet disappearance completing 2A. The original 2B sequence also reached 2C at 33.56 seconds in the scoped test. No health, projectile-destruction or completion-counter writes obtained the pass. The test sets aim and uses real controller inputs. Both edited graphs passed Blueprint Assist refresh/format/comments/local-format, visible review, compile and save; the other 29 level graphs compare exactly equal. Build succeeded. See [scoped validation](TrainingRoomTutorial/validation_s2a.json) and `Saved/Agent/TutorialS2A`.

The initial script-started PIE test had no active gameplay viewport, so its S1 movement fixture timed out; it is retained under `FixtureAttempts`. A later PIE session ended after the retry checks; the final run started through the editor Play button and passed all requested S2A checks, then ended during extra S2C regression. The raw combined test correctly reports incomplete, while `s2a_contract_passed` records the completed scoped assertions. No reason for the external session end is inferred. S2C–S7 were not fully rerun for this scoped update; the original complete-flow results below remain evidence of the earlier version. Packaging and user playtesting remain outstanding.

## Stage ownership

The map's Level Blueprint owns progression through 31 graphs: EventGraph, EnterExercise, CheckCurrentExercise and the Enter/Check pair for each step. Blueprint `BP_TrainingController` exposes mechanics and observations; it never chooses the next step.

| Step | Exercise | Completion contract |
|---|---|---|
| 1 | S1 falling rocks | Existing Omen intro, trigger, automatic locked time stop, full capsule in safe zone, restored time and landed rocks, arrival dialogue |
| 2 | S2A avoid the shot | The first single bullet actually fired and destroyed while current Health is 2; injury immediately retries 2A and resets player state. QTE enabled; time stop is optional |
| 3 | S2B avoid the shot independently | The first single bullet actually fired and destroyed while current Health is 2; injury immediately retries 2B with restored state. No QTE; time stop is optional |
| 4 | S2C two threats | Observe side shooter, dodge both threats, then actually exhaust energy and recover to 70% |
| 5 | S3 supplies / aiming | Separate pistol and ammo interactions, real manual reload, four actual target kills |
| 6–8 | S4 moving armor | Three sequential weakpoint-only targets; first requires a temporal hit and manual resume |
| 9 | S5 environment kill | Temporal link hit, manual resume, rock landing and three footprint kills; body shots rejected |
| 10 | S6 free solution | Five targets; guns, temporal shots and rock kills allowed; Enter continues, O starts optional practice |
| 14 | Optional moving rock | Moving link/rock, visible landing result; Enter can always leave, success never blocks the main line |
| 11 | S7A melee preview | One real melee NPC on the player side; existing damage/death system determines completion |
| 12 | S7B combat | Table removed, five covers, one melee plus three ranged NPCs with staggered AI activation; all four dead while player survives |
| 13 | Complete | Stop training threats, unlock Training Exit to Map_LabBridge |

S7A's one-enemy completion contract fills an underspecified section of the guide. S7A/B training resource defaults are health 2, energy 100, reserve ammo 120 and 12 magazine rounds only when empty; these are implementation choices, not guide-specified balance numbers.

## Player controls and progress

- Existing WASD, mouse, T, F, R and firing/aiming controls are retained.
- Backspace retries the current exercise; hold Home for 2 real seconds to reset the entire tutorial. Legacy F8/F9 aliases remain, but the HUD uses Backspace/Home to avoid PIE shortcut conflicts.
- H supplies an extra hint and marks that exercise as guided. S6 uses Enter to continue and O for optional practice.
- A fresh stage caches the current player transform. Ordinary transitions do not teleport the player. Death uses the existing player respawn chain and `RespawnFallbackTransform`, then resets only the current step. S4 checkpoints each target.
- Full reset clears completion records, cancels old dialogue/threats, restores entrance, initial equipment and layout orientation, and locks the exit again. Holding reset does not repeatedly restart.
- `CurrentStep`, `Phase`, checkpoint and `CompletedExercises` are level-local memory only. No tutorial SaveGame or local progress file is written. Leaving the map or ending PIE discards this session.
- Guided/Independent grading distinguishes scripted or explicitly prompted exercises from independent exercises. `gun/rock/temporal` observations count tutorial dummy/link actions; S7 NPC deaths use the original damage system, so zero dummy counters do not mean no weapon/time use.

## Scene presentation and supply

`/Game/Environment/TrainingRoom/Tutorial/BP_TrainingController` holds 16 original-to-dissolve mappings as parallel arrays, configured both on the Blueprint CDO and the placed actor instance. Material clones retain original appearance/instance parameters, use Masked blend, and call the existing `/Game/Dissolve/Materials/MaterialFunctions/MF_PlaneMask`. Original Dissolve resources and the global MPC are unchanged.

Each actor receives independent MIDs. `TS_PlanePosition` travels from its world lower bound to upper bound for bottom-up reveal and reverses for top-down removal; default duration is 1.4 real seconds. Authored stage actors are saved hidden with collision disabled. Outgoing threats stop before dissolve, and incoming collision activates after reveal. NPC movement is disabled until their meshes finish materializing; the pistol pickup does not fall through the table during reveal.

Shared table, barrier and ammo remain continuously active from S3 through S7A. S7B stops supply and removes uncollected ammo/table, preserving the equipped weapon. If the player finishes S2 on the far side, subsequent shooting layouts reflect about the table line. Occupied incoming tables/covers wait with a HUD prompt instead of moving the player. The table blocks pawns while preserving shooting paths.

The placed support actor exposes `DissolveSeconds`, `AmmoRespawnSeconds` (5), `AmmoPerPack` (24), material pairs, existing NPC/projectile/pickup/outline classes and conversation table. Existing instance overrides must be checked when changing defaults. Ammo slots refill only when empty and add reserve ammo; R still reloads manually.

## Existing-system adapters

- `BP_Item_Base.ResolveShotDamage` calls `HandleTrainingShot` for real hits. Only registered tutorial targets/links consume the impact; other actors retain the original damage path.
- `BP_TimeBullet.ResolveTemporalImpact` and `ResolveLockedTemporalImpact` use the same gate for actual released temporal projectiles, avoiding duplicate regular damage.
- `AC_TimeAbility.ToggleTimeAbility` checks `TutorialForceStop`. Only the S1 auto-demonstration sets it; safe-zone entry, retry and EndPlay clear it.
- S1 reuses `AC_TimeStopOutline` with red threat color. Existing TS11/TS12 dialogue recordings remain; TS12 movement locking is disabled so the player can reach the safe zone.
- New TS13 arrival conversation contains the two requested arrival sentences as text-only lines, 3 and 4 seconds respectively, since matching recorded audio was absent. Existing five recordings were not recreated or rewritten.
- `BP_TrainingController` uses the existing dialogue component. The former `TimeShuttleTraining` plugin is removed. The temporary TSVFXEditor authoring helper is outside Plugins, absent from the descriptor, and not a runtime dependency.

## Verification and evidence

The full-flow evidence below belongs to the original version before the subsequent S2A/S2B rule updates; their current scoped validation is recorded above.

The final saved Runtime/Editor modules built successfully for Win64 Development Editor. The final cold-start PIE ran without TSVFXEditor and completed S1 through S7B in one uninterrupted run, including S6 optional practice, through actual movement/interaction/reload/time/fire inputs. The test driver sets aim direction, but does not set goal counters, enemy health or progression to obtain completion. All 13 exercise records were present; `TUTORIAL_COMPLETE` was logged at 16:03:41 UTC with player health 2. S7A+B took 24.66 seconds under automation, not a representative human play time.

Earlier targeted tests also covered mirrored placement, retained table/collision, real dissolve intermediate frames, repeated actual deaths and current-step respawn without duplicate enemies, actual exit travel to Map_LabBridge, and the no-op shot adapter/time-scale cleanup outside the tutorial. Isolated test setups explicitly invoked stage entry; those fixtures are not the final end-to-end completion evidence.

Home full reset passed with one reset per continuous hold, empty initial equipment slots and cleared records. Backspace retry is independently checked after the intro movement lock finishes. Each changed graph received Blueprint Assist size refresh, scoped formatting, structured comments and visible review before compile/save. Semantic comparison of 62 graphs preserved all functional nodes, pin defaults and connections after ignoring reroute routing. Four narrow comments use short visible titles and detailed hover text to avoid covering nodes.

Portable evidence: [validation.json](TrainingRoomTutorial/validation.json). Full local raw evidence and task scripts are under `Saved/Agent/TutorialFlow/`: `final_cold_complete.log`, stage result JSONs, `boundary_result.json`, `exit_result.json`, reset/retry results, `format_result.json`, `graph_semantics_result.json`, final build log and screenshots. Failed fixture attempts remain separate from final passing results.

The final completion log contained no Blueprint Runtime Error, Accessed None or Python Error. Existing missing recoil-curve, additive pistol animation, Manny pose/slot and virtual-shadow-page warnings remain. This is not a project-wide clean-log or cooked-build claim. One post-save editor shutdown hit a Blueprint preview-scene assertion; the saved content was subsequently cold-loaded and the complete playable flow verified.

## Scope and follow-up

Changed assets are the training map, new Tutorial assets/materials/arrival table, the three shared Blueprint adapters, conversation table, project plugin descriptor and training plugin source. No other map or original Dissolve source was saved as part of this change. Original task backups are retained in `Saved/Agent/TutorialFlow/Backups`; no commit or push was made.

Next validation is user playtesting of pacing, difficulty and final VFX/audio quality. Packaging, all-weapon coverage, multiplayer and long-duration performance are unverified. The two arrival lines still require recorded audio if voiced delivery is desired. Update stage tags, material pairs, checkpoint logic and tests together when changing the room layout.
