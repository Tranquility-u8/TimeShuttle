# Implementation status

Last repo/editor observation: **2026-10-02** (targeted weakpoint update). This file records verified implementation facts, not sprint status. Drive sources were not refreshed during this local audit.

## Verified in the repository

- Enemy weakpoints use five configurable bone-attached query spheres and constrained non-repeating initialization. Per the 2026-10-02 user revision, armor/durability/break power were removed: every active hit immediately returns its tier data asset's independent `WeakPointDamage` (yellow 50, red 25 initially), with no hit-count threshold or point consumption. BodyDamage and weakpoint-only gating remain enemy component settings. A fresh 24-shot PIE matrix on both enemy types passed repeated hits, body, weakpoint-only, inactive head, walls, and independent fractional red damage (12.5 while yellow remained 50). Fixtures paused AI/pose, aligned the actual camera and removed spread; damage was not injected. This supersedes historical head=100/body=25 routing for weakpoint enemies only. Precision brackets and temporal-projectile integration remain unimplemented; rewind lifecycle integration still needs verification. See [enemy-weakpoints-plan.md](../Implementation/enemy-weakpoints-plan.md).

- UE 5.6 Blueprint project opens from `TimeShuttle.uproject`.
- Content is organized by purpose at the root: Blueprints, Animations, Maps, Data, Input and presentation resources. ProceduralFPSKIT, CombatAI and Variant_Shooter assets were migrated into these categories; the original TimeReverseSystem framework remains in use.
- Main map: `/Game/Maps/Map_Test`, with map-specific `GM_FP` and FPS player `BP_FPCharacter`. The global fallback GameMode is a different legacy FirstPerson class. See [project-architecture.md](project-architecture.md) for exact paths.
- Two gameplay enemy types: `BP_MeleeNPC` with a behavior tree and `BP_ShooterNPC` with StateTree. ShooterNPC inherits Character directly and uses its own AI weapon chain, independent of the FPS player's weapon implementation.
- Player input, weapon/inventory data, interaction and procedural animation assets are present in the migrated FPS system. Their presence does not establish completion of the planned production inventory/item design.
- Both enemies implement `BPI_RewindableEnemy` and use `AC_EnemyReverse`. Q / `IA_Reverse` drives synchronized transform, floating-point health and skeletal pose history. Reversible death retains objects until living history is exhausted; living rewind exit restarts AI and normal animation.
- Enemy reverse validation covered damage, death/revival, fractional health, repeated/short rewind, bone snapshot comparison, history trimming and eventual enemy/controller/weapon cleanup. Damage was scripted through real damage entry points; Q's action was injected through Enhanced Input. Player damage after revival was not asserted. See [EnemyReverse.md](../Implementation/EnemyReverse.md) for evidence and limitations.
- Enemy pose playback now restores actor transform before mesh world transform/pose on automatic and seek-reverse paths, preventing the attached mesh from inheriting movement twice. Melee and shooter both refresh bones while ticking pose. A 2026-09-27 PIE comparison measured zero mesh-relative position and yaw drift for both enemies throughout 179 reverse samples.
- Enemy rewind now preserves, disables and restores each Character's controller-yaw policy. This prevents the melee AI controller from inserting live-facing rotations between fixed-rate rewind samples while leaving the shooter's already-disabled policy unchanged. Three PIE reruns measured zero alternating melee yaw steps across 537 reverse samples and confirmed policy restoration after every exit.
- Player hitscan damage now reaches both gameplay enemy types through generic Unreal Damage. The shared weapon graph preserves 100 damage for the `head` bone and 25 for other bones; melee adapts `AnyDamage` to `AC_Combat`, while shooter retains its existing `Current HP` handler. PIE directly observed a melee body hit from 100 to 75 and shooter damage/death handling. A clean physical-input single-shot body/head matrix was not completed; exact head/body routing was additionally verified from the saved graph. See [EnemyDamagePipeline.md](../Implementation/EnemyDamagePipeline.md).
- Time ability stages 1–7 are implemented. T toggles a 0–100 energy-driven Normal / FullStop / BulletTime state; active energy drains uniformly, inactive energy recovers uniformly, 70 belongs to FullStop, and exhaustion auto-exits. Existing rewind and the new ability block one another in both directions. FullStop applies 0.01 global dilation while compensating the player/current weapon; BulletTime maps energy 70→0 to dilation 0.2→1.0. FullStop shooting creates up to 12 suspended `BP_TimeBullet` actors; HUD reports count/cap and `LIMIT`, and transition to BulletTime or Normal releases them at 5000 uu/s. Actual aim direction, 40 uu near-obstruction fallback, delayed one-shot body/head damage (25/100), melee/Shooter receivers, FullStop pickup interaction and generic rigid-body slow/freeze/resume were verified in PIE. See [TimeAbilityCore.md](../Implementation/TimeAbilityCore.md) and [TimeProjectileBridge.md](../Implementation/TimeProjectileBridge.md).
- FullStop first-person viewmodel sway now uses the compensated `SwaySpring` DeltaTime consistently instead of mixing it with global world DeltaSeconds. This removes the roughly 100× mouse-sway amplification caused by the 0.01 world scale while preserving the normal-time formula.
- The 2026-09-26 naming pass normalized 54 gameplay/data assets, preserving serialized compatibility through CoreRedirects. Imported/resource names have documented exceptions. See [asset-naming.md](asset-naming.md) and its per-file mapping.

## Historical planning snapshot, not current implementation evidence

- Time Rewind was marked completed in the development-plan spreadsheet.
- Character controls and melee/ranged enemy work were marked in progress at that snapshot's date; subsequent local work above supersedes this as implementation evidence.
- Area Stop, Bullet Time, item interaction, and inventory were marked not started at the snapshot date. Do not repeat these as current status without checking the current design source and repository; imported FPS systems already contain item/inventory functionality.

## Known verification boundaries

- No packaged-build, network replication or large-enemy-count certification is implied.
- Pose rewind does not replay animation notifies, sound/VFX or curves, nor resume an interrupted montage at its exact historical time. Projectile history remains a separate system.
- Area Stop/Bullet Time stages 1–7 establish player state, energy, input exclusion, HUD, global time scaling with player/current-weapon compensation, a 12-shot suspended-projectile loop, current pickup interaction and generic rigid-body behavior. Special-case interactable matrices, audiovisual effects, packaged builds, networking and broader stress certification are not yet established.
- The player-to-enemy damage pass did not certify packaged builds, networking, alternate player weapon families, post-revival damage, or a clean one-shot body/head PIE matrix for both enemies.
- Local implementation observations and Drive source freshness are separate; preserve the source manifest's actual observation date.

## Important distinction

Folder or asset presence is not proof of production readiness. Before planning integration, inspect the relevant Blueprint graphs and dependencies in Unreal Editor, compile them, and run the agreed PIE scenario. Update this file only with durable, high-confidence facts; use Jira or the current planning sheet for task status.
