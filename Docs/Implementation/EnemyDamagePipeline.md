# Player weapon damage to gameplay enemies

Implemented and inspected in UE 5.6 on 2026-09-26. This document records the current player-hit damage path for the two gameplay enemies, the defect that was fixed, and the limits of the available PIE evidence. It is repository/editor implementation evidence, not a Google Drive design refresh.

## Runtime damage path

The player weapon base is `/Game/Blueprints/Interactables/BP_Item_Base`. Its `Fire_HitScan` function performs the weapon trace and derives damage from the hit result:

- hit bone `head`: 100 damage;
- every other hit bone: 25 damage.

The selected value is sent to `GameplayStatics.ApplyDamage` with the trace's `Hit Actor` as `Damaged Actor`. The two gameplay enemies receive that generic Unreal damage event through different health implementations:

| Enemy | Damage entry | Health storage and handling |
| --- | --- | --- |
| `/Game/Blueprints/AI/Melee/BP_MeleeNPC` | `Event AnyDamage` | Forwards the event's floating-point `Damage` value to the existing `CAI_CombatComponent.Apply Damage` function. The retained member name refers to the `AC_Combat` component. |
| `/Game/Blueprints/AI/Shooter/BP_ShooterNPC` | Existing `Event AnyDamage` | Updates the shooter's `Current HP` and continues its existing hit/death behavior. |

`/Game/Blueprints/AI/Training/BP_TrainingEnemy` remains a template/training target, not a third gameplay enemy. Its pre-existing specialized damage branch is retained. The specialized cast-success branch and the new generic cast-failure branch are mutually exclusive, so a hit is not deliberately submitted to both damage nodes.

## Defect and repair

Before this change, the active damage node in `Fire_HitScan` was reachable only after `Cast To BP_TrainingEnemy`. Both gameplay enemies fail that cast, so their collision could be hit and impact effects could continue without the player weapon submitting damage to them.

The repair added a generic `Apply Damage` node on the training-enemy cast-failure path:

1. `Cast To BP_TrainingEnemy.Cast Failed` executes the generic node.
2. The trace's `Hit Actor` supplies `Damaged Actor`.
3. The existing head/body `Select Float` supplies `Base Damage`, preserving 100/25.
4. The generic node continues into the existing impact/effect flow.
5. The training-enemy cast-success path keeps its original node and does not traverse the generic node.

`BP_MeleeNPC` previously had no generic Unreal damage-event adapter even though its real health mutation belonged to `AC_Combat`. `Event AnyDamage` was added as that adapter. At the time of that repair, `BP_ShooterNPC` already had a compatible health/death event and required no asset change; that statement did not imply that Shooter had a hit-reaction animation.

## Player melee extension (2026-10-04)

Player fist and knife attacks now reach the same two AnyDamage receivers through `Apply Point Damage`. `BP_FPCharacter` supplies a camera-aligned segment through `BPI_MeleeAttackSource`, and `AC_MeleeHitDetector` performs a first-blocking sphere sweep over pawn and world objects. `BP_Weapon_EmptyHands` submits 20 damage; `BP_Weapon_MeleeBase` / `BP_Weapon_Knife` submit 25. This path does not call `AC_EnemyWeakPoints.ResolveShotDamage`, so firearm weakpoint multipliers remain isolated from melee.

No receiver change was needed. PIE verified Shooter hit reaction, Melee health mutation, wall obstruction, rewind rejection/resumption and lethal cleanup. The shared trace-and-Point-Damage boundary is also the intended extension point for a later `MeleeNPC -> player` implementation; details and required multi-frame deduplication are recorded in [player-melee-combat.md](player-melee-combat.md).

## Shooter hit reaction (2026-10-02)

Repository history and the saved pre-change graph both show that `BP_ShooterNPC.Event AnyDamage` previously ended its surviving-damage branch after updating `Current HP`; it did not call a montage, animation sequence, hit state, or combat-component reaction. This was therefore an existing omission rather than a regression from the weakpoint work.

Shooter now plays `/Game/Characters/Mannequins/Anims/Rifle/HitReact/MM_HitReact_Front_Lgt_01` as a dynamic montage on a dedicated `HitReact` slot in `/Game/Animations/Shooter/Blueprints/ABP_TP_Rifle`. The sequence uses Shooter's own `SK_Mannequin` skeleton, lasts 0.7 seconds, has no root motion, and blends back to the unchanged locomotion/rifle-aim output (`0.08` seconds in, `0.12` seconds out). The existing damage order is preserved:

- rewind-active and already-dead guards still run before health mutation;
- lethal damage follows the original `Die` branch and does not play the reaction;
- only a surviving damage event plays the reaction;
- the animation is presentation-only and does not alter weakpoint damage, body damage, health, AI state, or rewind data.

Final editor verification compiled `BP_ShooterNPC`, `ABP_TP_Rifle`, and `BP_Weapon_Pistol` with zero errors and zero warnings. A controlled PIE run observed health `100 → 75`, an active transient montage immediately and at `0.25 s`, no montage after completion, unchanged `ABP_TP_Rifle` ownership, no damage/montage while rewind-active, and no hit montage on lethal damage. The run submitted Unreal Damage through the production `AnyDamage` entry; final visual feel under active combat movement remains a player acceptance item.

## Verification evidence

The affected and directly dependent Blueprints were opened and compiled successfully in the editor:

- `BP_Item_Base`;
- `BP_MeleeNPC`;
- unchanged receiver `BP_ShooterNPC`;
- player child `BP_Weapon_AutomaticBase`.

Only `BP_Item_Base.uasset` and `BP_MeleeNPC.uasset` were saved for the repair.

Graph inspection after saving confirmed the exact links described above and confirmed that the shared selector still contains 100 for head and 25 for non-head hits. A controlled PIE run using the player's pistol firing action recorded a melee body hit changing health from 100 to 75. A shooter PIE run emitted its `take damage` messages and reached destruction/cleanup.

The automated Enhanced Input test did not provide a clean single-shot assertion for every body/head combination. Injected fire could remain active or be observed after the sampling point, producing delayed or repeated shots. Consequently:

- the melee 25-point body hit is direct runtime evidence;
- shooter damage reception and cleanup are direct runtime evidence, but not a reliable per-shot damage-count assertion from that run;
- the 100-point head value and the common 100/25 routing are verified from the saved Blueprint graph;
- a physical-input, one-shot PIE pass for body and head on both enemies remains the preferred final gameplay acceptance test.

Do not summarize the last three points as “all four shots were fully PIE-verified.”

## Reusable debugging lessons

### Inspect both the weapon and the receiver

A valid collision hit does not prove that damage is submitted, and a working `AnyDamage` handler does not prove that the weapon can reach it. Trace from the weapon's hit result through its execution gates, then inspect each enemy's actual health owner.

### Do not treat a training target as the enemy contract

The original cast to `BP_TrainingEnemy` silently made one template class the damage gate for unrelated enemies. New gameplay enemies should receive generic damage through a shared contract or adapter; class-specific casts should be reserved for genuinely specialized behavior.

### Preserve real health ownership

The melee enemy owns combat mutation through `AC_Combat`, while the shooter owns `Current HP` in its character Blueprint. A common incoming damage event should adapt to those existing owners rather than duplicating health variables or forcing a new inheritance relationship.

### Separate graph proof from runtime proof

Blueprint export/inspection can prove node values, targets and mutually exclusive execution paths. It cannot prove collision responses, the actual hit bone, input timing, death cleanup or rewind interaction. Record those claims separately.

### Treat injected fire as stateful test input

An injected Enhanced Input value may not behave like a single physical click. For shot-count assertions, explicitly observe action release, weapon state, health timestamps and event timestamps; use a fresh PIE session when necessary. Ammo counters alone are not sufficient proof that `Fire_HitScan` did or did not run.

### Spawned test actors must satisfy their runtime dependencies

Summoning a melee enemy without its normal controller caused `AC_EnemyReverse` to report missing-controller runtime errors. Those errors came from the test setup, not from the damage adapter. Spawn the default controller or use a normal level instance before judging the product log.

### Attribute logs to a bounded test window

Separate pre-existing animation warnings, helper-script/Python errors, intentionally malformed test actors and new Blueprint runtime errors. Record the PIE start/end time and the actor instance involved; do not call the log clean merely because the affected Blueprints compiled.

## Extension and regression checklist

When adding another damageable enemy:

1. Confirm the player trace channel blocks on the intended capsule/mesh and returns the expected bone names.
2. Receive generic Unreal damage and adapt it to the enemy's real health owner.
3. Preserve floating-point damage; do not truncate values used by rewind history.
4. Gate damage during rewind through the existing enemy rewind contract.
5. Compile the weapon base, the new enemy and at least one real player weapon child.
6. In PIE, verify body hit, head hit, lethal cleanup, rewind guard and post-revival damage separately.
7. Check the scoped Output Log and save only the approved assets.

Packaged builds, networking, alternate player weapon families, post-revival player damage, and a clean physical-input four-shot matrix were not certified by this task.
