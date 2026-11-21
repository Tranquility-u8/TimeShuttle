# ADS sight and wall impact alignment

Verified: 2026-11-15, UE 5.6.1.

The reported black dot is the actual wall impact decal. The first repair checked muzzle-origin stability, which did not establish alignment between a wall impact and the visible orange sight mark.

## Cause and final correction

`BP_Weapon_Pistol` uses hidden generic `FrontSight` and `RearSight` components to calculate its aiming pose. Their reference line was above the orange sights built into the visible pistol model. Shooting already used the camera trace branch; moving a projectile model could not fix this wall-impact discrepancy.

The correction lowers the shared hidden sight reference frame by 1.5 cm:

| Component | Original relative Z | Final relative Z |
| --- | --- | --- |
| FrontSight | 6.825749 | 5.325749 |
| RearSight | 0.259056 | 0.259056 |

`RearSight` is attached to `FrontSight`, so moving the parent moves both reference points once. The shared sight meshes, visible weapon geometry, firing direction, spread, damage and decal placement logic are unchanged. The corrected reference makes the native ADS pose bring the visible orange marker up to the firing line.

The speculative `BP_TimeBullet` mesh adjustment was fully reverted through the original LFS object. Its SHA-256 matches HEAD and the task baseline: `00de9f7e4fd90c9b6ad652ab5e0f2ed33a66bfaaeb0afc1e06ac896016999cf0`.

## Verification

Actual player, pistol pickup/equip and Enhanced Input `IA_Aim` / `IA_Shoot` were exercised in `Map_Test`; wall decals came from the real shot pipeline. AI was stopped and the player was temporarily invulnerable. No impact/decal was injected or repositioned for acceptance.

| Check | Result |
| --- | --- |
| One aimed shot, recoil recovery, real wall decal | Passed |
| Three aimed shot requests | Passed |
| Exit aim, re-enter aim, native BeginFire shot | Passed |
| One hip-fire shot with IsAim false | Passed |
| Reload saved assets and compile item base, player and pistol | 0 Blueprint errors / warnings |
| Pistol functional graphs before/after calibration | Identical |
| End of tests | No dirty maps or content packages |

In the 1280 x 720 resting captures, the front orange marker moved upward by about 22 pixels. The previous fixed gap above the sight is eliminated; the weapon retains its existing spread.

The editor rendered at about 3 FPS while in the background, which made the spring pose unstable. Acceptance therefore used a temporary `t.OverrideFPS 30` simulation step. This is a deterministic pose/impact check, not a performance test. The frame override and Slate throttling settings were restored afterward. Cooked builds and multiplayer were not tested in this follow-up.

Local evidence is ignored by Git under `Saved/Agent/ADSSight20261115/`: `final-review.json`, `pistol-sight-calibration.json`, `visible-marker-measurements.json`, and the `normal-hit-final`, `repeat-and-reaim-final`, and `hip-final` probe directories. Cold compiler evidence is `Saved/Agent/ADSRecoil20261114/final-compile.json`.

Before: [actual wall impact above the orange mark](../../Saved/Agent/ADSSight20261115/normal-hit-before/after-ads.png).

After: [calibrated sight and actual wall impact](../../Saved/Agent/ADSSight20261115/normal-hit-final/after-ads.png).

## Earlier origin-stability work

The previous `BP_Item_Base.CaptureShotMuzzleOrigin` camera-space reference and same-frame snapshots in `PrepareTemporalMuzzleShot` / `SpawnHitscanTrail` remain present, as does the player-side invalidation when leaving ADS. The earlier seven shot-origin tests and two re-aim checks verified that separate behavior; they were insufficient to accept visible sight alignment. Their original local evidence is under `Saved/Agent/ADSRecoil20261114/`.

## Recovery

To undo this follow-up calibration, restore only pistol FrontSight relative Z to 6.825749 through Unreal Editor. Keep RearSight relative Z at 0.259056 and preserve its attachment. The original pistol asset is backed up under `Saved/Agent/ADSSight20261115/Backup/`. Earlier locomotion and enemy weakpoint work is outside this change.
