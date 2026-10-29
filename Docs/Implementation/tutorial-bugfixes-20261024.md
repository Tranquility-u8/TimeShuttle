# Tutorial bug investigation — 2026-10-24

Task: `20261024-tutorial-two-bugs`. User authorized autonomous implementation. The Dodge and teardown-error repairs are saved. The user stopped further investigation of the unreproduced weak-point launch / blocked progression.

## Dodge QTE hand presentation

`/Game/Blueprints/Components/Player/AC_TimeAbility.MaintainTutorialQTE` now calls the existing `ApplyTimeScale(0.0001, false)` instead of setting global dilation alone. The guided incoming shot retains the same world slowdown. Player and equipped-item compensation keep their presentation responsive while the stage still owns movement and input locks. Q accepts the original FullStop state and compensation.

Before the repair, the QTE world scale was 0.0001 with player custom dilation 1. Camera input could turn while the hand presentation advanced at almost zero speed, producing a catch-up movement on acceptance. Turning during the wait exposed substantial camera-relative hand displacement. After the repair, player custom dilation is 10000 during this guided wait and returns to 100 in FullStop and 1 in Normal.

Cold-editor scoped PIE validation passed ten checks: guided QTE compensation, preserved movement lock under actual movement input, real-time presentation updates, hand positions below the view while looking, actual physical first-Q acceptance, original FullStop compensation, actual movement clearing the shot path, physical second-Q restoration, real bullet passage / energy recovery / transition to S3, and final world/player dilation restoration. Stage entry was selected with a temporary mission StartStep fixture; this is not an S1–S7 playthrough. No damage or goal counters were injected for Dodge completion.

The ability compiles with zero errors/warnings. Blueprint Assist refreshed the modified node and performed selective layout, followed by an updated responsibility comment and final selective layout. A semantic audit resolves formatting reroutes and verifies unchanged connections/defaults. All fourteen unrelated ability graphs are unchanged. Only the ability asset is saved; no map, player animation, weapon or tutorial target asset was changed.

## Tutorial movement-lock teardown error

The captured runtime error was `Accessed None ... CallFunc_GetPlayerController_ReturnValue` at `BP_TrainingController.SetTutorialMovement` / `Set Ignore Move Input`. The mission teardown can release its tutorial lock after the player controller is gone.

`SetTutorialMovement` now validates the player controller before changing its input lock or updating the tutorial-owned latch. It validates the cached player and its movement component before stopping velocity on a lock request. An invalid controller is a no-op, so a failed lock acquisition cannot latch and suppress a later valid attempt. Existing state-edge checks and lock ownership remain intact.

Ten scoped checks across two PIE sessions passed: normal acquisition; repeated acquisition without stacking; preservation of an external lock on tutorial release; external owner release; missing-player lock and unlock; clean lock state in a new PIE session; removal of the local player/controller; safe acquisition without that controller; and safe release without it. Both PIE sessions were ended through normal editor teardown. An initial fixture used `DestroyActor` on the player controller, which did not remove it; its three invalid-fixture assertions are retained separately. A second fixture used `GameplayStatics.RemovePlayer`, but left pawn components ticking briefly after camera removal, producing unrelated interaction/procedural-animation camera errors. The final fixture stops those pawn/component ticks before player removal, then exercises the controller guards and editor teardown. No production gameplay logic was changed in response to either fixture problem. The final interval is checked separately from these retained earlier logs.

The final two-session interval has zero `Accessed None`, Blueprint runtime, script or Python errors. The controller compiles with zero errors/warnings and is saved. Blueprint Assist refreshed and selectively formatted the affected function, its structured ownership/teardown comment was updated, and final layout was visually reviewed. A reroute-normalized audit verifies preserved functional connections/defaults; all 84 unrelated controller graphs remain unchanged. No map was saved. Local evidence: `movement-validation.json`, `movement-saved.json`, `controller-errors-final.json`, and `movement-guard-layout.png` in the task evidence directory. The metrics Finish sample preceded the final fixture correction and verification; its time/token totals exclude that final verification work and must be presented as sampled totals.

## Weak-point burst investigation — stopped by user

The existing passive target already latches `Dying` before entering ragdoll and counts death once after its existing delay. The scoped current-branch tests did not reproduce launch or blocked progression:

- Normal pistol weak-point shots killed the static target and advanced the actual MissionSystem flow to the moving target.
- Eight actual pistol shots queued in FullStop and released together killed the moving target and advanced to the plank exercise.
- A same-frame stress fixture temporarily cleared the runtime fire gate between twelve native BeginFire calls. It killed the static target, counted it and advanced to the moving target. This deliberately bypasses normal fire cadence and is not a physical-click acceptance test.

These fixtures used temporary owned-pistol inventory and selected stage entry, with actual native weapon damage and original mission progression. They do not prove the user's reported condition is fixed. No speculative target or weapon modification was saved. The user subsequently requested stopping reproduction attempts and fixing the observed errors instead.

## Local evidence and recovery

Ignored evidence and pre-change backup: `Saved/Agent/TutorialTwoBugs/`. Key files: `dodge-validation.json`, `qte-saved.json`, `qte-layout.png`, `final-state.json`, `weak-normal-baseline.json`, `weak-temporal-baseline.json`, and `weak-stress-baseline.json`.

Early observation scripts had API/signature and stale-stage-fixture failures; these are not counted as gameplay failures or passing checks. The first investigation session also recorded an existing teardown `GetPlayerController` / movement-lock access error before the ability edit. The separate cold Dodge verification log is the acceptance interval. Packaging, networking, complete tutorial regression and the user's weak-point failure condition are not verified.

To undo either saved repair, close/unload the affected ability/controller package and restore only its targeted pre-change backup or prior version through source control. Preserve unrelated workspace changes.
