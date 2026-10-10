# Enemy AI behavior migration

## Outcome

On 2026-10-10, the melee and ranged enemy behavior dependency closure from `EnemyAITutorial` was migrated into Time Shuttler under `/Game/EnemyAITutorial`. The stable gameplay entry paths remain:

- `/Game/Blueprints/AI/Melee/BP_MeleeNPC`
- `/Game/Blueprints/AI/Shooter/BP_ShooterNPC`

Both now use `/Game/EnemyAITutorial/Enemies/AI/AIC_Enemy_Base` and the imported behavior trees. Melee uses `BT_Enemy_Melee`; ranged uses `BT_Enemy_Ranged`. Imported behavior includes patrol, perception, target selection, movement, combat decisions, attacks, animation, weapons and their required support assets.

## Gunshot hearing

Player firearm shots now bridge into the imported perception behavior from `/Game/Blueprints/Interactables/BP_Item_Base.Fire_HitScan`. Every non-melee trace reports one `Gunshot` stimulus at the weapon Actor location with the player as instigator; melee traces do not report it. The shared controller keeps the imported hearing-to-investigation logic, configured to 2000 uu hearing range and 5 seconds max stimulus age. A heard shot sets `PointOfInterest` and enters Investigating, but does not grant `AttackTarget`; visual confirmation remains necessary for combat targeting.

Scripted PIE validation disabled sight on both formal enemies, reported a shot between them, and observed both switch from Passive to Investigating with zero PointOfInterest error. They moved from roughly 760 uu away to 41–56 uu from the sound while `AttackTarget` stayed null. A separate regression verified melee attack montage, ranged rifle montage plus TimeShuttle projectile spawning, and both enemies entering and leaving the rewind animation class.

## Compatibility bridges

- The imported shared base owns `BPC_DamageSystem.Health`. Its generic Unreal `AnyDamage` adapter forwards Time Shuttler weapon/weakpoint damage into the imported damage interface.
- The shared base carries the existing `AC_EnemyWeakPoints`, `AC_EnemyReverse` and `BPI_RewindableEnemy` integration. Rewind health reads and writes `BPC_DamageSystem.Health`.
- Ranged keeps the imported rifle model, animation and behavior-tree timing, but its shot endpoint spawns `/Game/Blueprints/AI/Shooter/Projectiles/BP_ShooterProjectile_Bullet`. Time Shuttler therefore remains authoritative for projectile collision and player damage.
- Melee keeps the imported attack choice, montage/notify timing and team filters. Its four terminal damage submissions use generic Unreal `ApplyDamage`, preserving the player's existing two-hit and invulnerability pipeline.

## Patrol routes

`Map_Test` contains two imported `BP_PatrolRoute` actors, one bound to each formal enemy. Each route is a closed four-point loop. Reload inspection confirmed that both bindings persist, both enemies use the imported controller, and placed actors auto-possess correctly.

## Cleanup

The replaced melee controller/tree/tasks and ranged controller/StateTree/EQS/interfaces/weapon chain were removed from the old AI folders. Time Shuttler's ranged projectile base and bullet were retained. A dependency reachability audit found two unused imported helpers (`BP_POI` and `NavLink_EnemyAI`); both were removed. Training AI and shared Time Shuttler combat/weakpoint/reverse systems were kept because they are separate or still referenced.

## Verification

- A fresh batch compile covered 43 relevant Blueprints with no task-related compile failures.
- Fresh logs contained no Blueprint error, montage segment mismatch or duplicate slot warning. The commandlet still reported 42 mannequin PoseAsset source-hash warnings: 14 from pre-existing Player assets and 28 from the migrated Manny/Quinn rig pose library; these did not surface as Blueprint, behavior-tree, montage or PIE runtime failures.
- Scripted PIE observed both formal enemies possessed by `AIC_Enemy_Base`, both moving along their assigned patrol routes, and two imported weapon actors spawning.
- Exercising the formal ranged attack interface produced one Time Shuttler `BP_ShooterProjectile_Bullet`.
- Generic damage changed an enemy from 100 to 90. With only the runtime player's damage gate enabled for the fixture, melee-caused generic damage changed player health from 2 to 1 through the existing AnyDamage chain.

The headless PIE fixture did not naturally acquire a player target and complete an autonomous attack, so attack initiation was exercised through the enemies' actual formal attack interface. Manual visual feel, packaged builds, networking and large-count performance remain outside this verification.

Blueprint graphs retain the imported source layout and received structured comments around the compatibility bridges. An attempted Blueprint Assist auto-format in null-rendering editor mode crashed in a platform window-size call, so auto-format is not counted as successful evidence; the assets were recompiled and saved afterward.
