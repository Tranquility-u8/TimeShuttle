# Implementation status

Last repo/editor observation: **2026-09-26**. This file records verified implementation facts, not sprint status. Drive sources were not refreshed during this local audit.

## Verified in the repository

- UE 5.6 Blueprint project opens from `TimeShuttle.uproject`.
- Content is organized by purpose at the root: Blueprints, Animations, Maps, Data, Input and presentation resources. ProceduralFPSKIT, CombatAI and Variant_Shooter assets were migrated into these categories; the original TimeReverseSystem framework remains in use.
- Main map: `/Game/Maps/Map_Test`, with map-specific `GM_FP` and FPS player `BP_FPCharacter`. The global fallback GameMode is a different legacy FirstPerson class. See [project-architecture.md](project-architecture.md) for exact paths.
- Two gameplay enemy types: `BP_MeleeNPC` with a behavior tree and `BP_ShooterNPC` with StateTree. ShooterNPC inherits Character directly and uses its own AI weapon chain, independent of the FPS player's weapon implementation.
- Player input, weapon/inventory data, interaction and procedural animation assets are present in the migrated FPS system. Their presence does not establish completion of the planned production inventory/item design.
- Both enemies implement `BPI_RewindableEnemy` and use `AC_EnemyReverse`. Q / `IA_Reverse` drives synchronized transform, floating-point health and skeletal pose history. Reversible death retains objects until living history is exhausted; living rewind exit restarts AI and normal animation.
- Enemy reverse validation covered damage, death/revival, fractional health, repeated/short rewind, bone snapshot comparison, history trimming and eventual enemy/controller/weapon cleanup. Damage was scripted through real damage entry points; Q's action was injected through Enhanced Input. Player damage after revival was not asserted. See [EnemyReverse.md](../Implementation/EnemyReverse.md) for evidence and limitations.
- The 2026-09-26 naming pass normalized 54 gameplay/data assets, preserving serialized compatibility through CoreRedirects. Imported/resource names have documented exceptions. See [asset-naming.md](asset-naming.md) and its per-file mapping.

## Historical planning snapshot, not current implementation evidence

- Time Rewind was marked completed in the development-plan spreadsheet.
- Character controls and melee/ranged enemy work were marked in progress at that snapshot's date; subsequent local work above supersedes this as implementation evidence.
- Area Stop, Bullet Time, item interaction, and inventory were marked not started at the snapshot date. Do not repeat these as current status without checking the current design source and repository; imported FPS systems already contain item/inventory functionality.

## Known verification boundaries

- No packaged-build, network replication or large-enemy-count certification is implied.
- Pose rewind does not replay animation notifies, sound/VFX or curves, nor resume an interrupted montage at its exact historical time. Projectile history remains a separate system.
- Area Stop/Bullet Time design readiness and the next damage-system feature are not established by this audit.
- Local implementation observations and Drive source freshness are separate; preserve the source manifest's actual observation date.

## Important distinction

Folder or asset presence is not proof of production readiness. Before planning integration, inspect the relevant Blueprint graphs and dependencies in Unreal Editor, compile them, and run the agreed PIE scenario. Update this file only with durable, high-confidence facts; use Jira or the current planning sheet for task status.
