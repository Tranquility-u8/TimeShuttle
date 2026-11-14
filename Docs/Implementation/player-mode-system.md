# Player mode system

Task: `20261111-player-mode-system`. Implemented and saved in UE 5.6.1; targeted PIE checks passed. All gameplay logic is Blueprint.

## Assets and defaults

Reusable assets live in `/Game/Blueprints/Player/PlayerModes/`: `ENUM_PlayerMode`, `S_PlayerModeConfig`, `DT_PlayerModes`, `AC_PlayerModeManager`, `BFL_PlayerMode`, and `BPI_PlayerModeConsumer`.

| DataTable field | Combat | Chapter1 | SafeZone |
| --- | --- | --- | --- |
| ShowTimeEnergyUI | true | false | false |
| ShowWeaponCrosshair | true | false | false |
| ShowSafeZoneCrosshair | false | true | true |
| AllowWeaponWheel | true | true | true |
| AllowManualTimeAbility | true | false | false |
| AllowFirearmEquip | true | false | false |
| DisableAttack | false | true | true |

ShowTimeEnergyUI controls both the left panel and the reticle energy arc. The safe-zone crosshair is a centered white 4x4 circular dot. DisableAttack=true prevents hand and weapon attacks independently of firearm equip permission.

## Designer use

Connect persistent Level Blueprint BeginPlay to `BFL_PlayerMode.SetLevelDefaultMode`, with Self as Context and the desired enum. Map_LabV39 selects Chapter1. Gameplay levels without an explicit override fall back to Combat on the next tick. Generic code does not inspect map names.

Call `SetPlayerMode` from a trigger or mission to change mode at runtime. `ResetToLevelDefault` restores the level's configured mode. `GetCurrentMode` / `GetCurrentConfig` include Ready; permissions are closed before initialization. Subscribe to `OnPlayerModeChanged` for additional consumers.

To add a mode, extend the enum and add one DataTable row with the matching Mode and all seven booleans. Row names should match display names for readability; lookup uses Mode. Missing or duplicate modes reject the switch and preserve the previous valid state. Rows are cached per world: restart PIE after editing the table.

## Integration behavior

- One manager component is created on the current world's GameState. Level travel creates a new world configuration; pawn possession and HUD creation reapply the current mode.
- HUD uses the existing tutorial visibility conditions and cinematic root opacity in addition to mode permissions. Continuous HUD refresh cannot restore forbidden elements.
- Both equip requests and final equipment creation are gated. Firearm classification reads existing ItemType class defaults. Disabling firearm equip cancels pending requests and switches a held firearm to hands without removing inventory or ammunition.
- The wheel can remain openable while firearm buttons are disabled and dimmed. Disabling the wheel closes it without committing a selection on release.
- Attack input, BeginFire and direct damage commits are gated. Disabling attacks stops automatic fire and invalidates queued melee through an attack epoch. Re-enabling cannot revive an old delayed strike. Already-fired projectiles keep existing behavior.
- Manual Q and manual threat prompts obey AllowManualTimeAbility. Scripted forced stops retain ownership; cinematic release reapplies permissions after restoring its previous state.
- Newly possessed local pawns complete existing inventory/HUD initialization if needed, then register. Existing inventories are preserved.
- No runtime dependency on the Python/editor authoring helper was introduced.

## Verification and scope

Targeted PIE matrices passed 29 checks: 16 primary, 9 supplemental, 4 actual level-travel checks. Tests covered real gun/hand damage, loaded firearm and hand attack rejection, automatic fire stopping, delayed melee cancellation and fresh attacks, forced hands, pending equip rejection, wheel restrictions, manual Q, scripted stop preservation, HUD recreation, pawn replacement, missing row fallback, and level default reset.

Actual OpenLevel travel verified Lab Chapter1 -> TrainingRoom Combat -> Lab Chapter1. Damage fixtures used temporary enemies, inventory and test positions with mission activity isolated; these runtime fixtures were not saved. Five existing SaveGame files retained identical SHA256 hashes.

Twelve Blueprint/Level Blueprint compile results reported zero errors; the subsequent possession initialization fix was also compiled and saved. Fifteen asset packages were saved (six new and nine modified). Final audit found no dirty packages and no editor-helper runtime calls in the twelve Blueprints. Graph layout changes preserved graph semantics.

Local workspace evidence is under `tmp/player-mode-impl-20261111/`: `runtime-matrix.json`, `runtime-supplement.json`, `runtime-travel.json`, `compile-final.json`, `saved.json`, `savegame-check.json`, `final-audit.json`, and screenshots. This is targeted feature validation, not a complete chapter playthrough, packaged build, or multiplayer certification. No commit or push was performed.
