# Enemy AI behavior migration

## Outcome

On 2026-10-10, the melee and ranged enemy behavior dependency closure from `EnemyAITutorial` was migrated into Time Shuttler under `/Game/EnemyAITutorial`. The stable gameplay entry paths remain:

- `/Game/Blueprints/AI/Melee/BP_MeleeNPC`
- `/Game/Blueprints/AI/Shooter/BP_ShooterNPC`

Both now use `/Game/EnemyAITutorial/Enemies/AI/AIC_Enemy_Base` and the imported behavior trees. Melee uses `BT_Enemy_Melee`; ranged uses `BT_Enemy_Ranged`. Imported behavior includes patrol, perception, target selection, movement, combat decisions, attacks, animation, weapons and their required support assets.

## Gunshot hearing

Player firearm shots now bridge into the imported perception behavior from `/Game/Blueprints/Interactables/BP_Item_Base.Fire_HitScan`. Every non-melee trace reports one `Gunshot` stimulus at the weapon Actor location with the player as instigator; melee traces do not report it. The shared controller keeps the imported hearing-to-investigation logic, configured to 2000 uu hearing range and 5 seconds max stimulus age. A heard shot sets `PointOfInterest` and enters Investigating, but does not grant `AttackTarget`; visual confirmation remains necessary for combat targeting.

Scripted PIE validation disabled sight on both formal enemies, reported a shot between them, and observed both switch from Passive to Investigating with zero PointOfInterest error. They moved from roughly 760 uu away to 41–56 uu from the sound while `AttackTarget` stayed null. A separate regression verified melee attack montage, ranged rifle montage plus TimeShuttle projectile spawning, and both enemies entering and leaving the rewind animation class.

## Ranged tactical cover — phase 1

`BT_Enemy_Ranged` now has a tactical-cover branch that reuses the imported `EQS_FindCover` query without replacing the existing ranged attack subtree. It can enter cover after a fresh health loss, below 35% health, or 2.5 seconds of sustained exposure. The query stores its result in the dedicated `CoverLocation` blackboard key and randomly selects within the best 25% of candidates, leaving `PointOfInterest` available for hearing and line-of-sight repositioning.

At the selected location the enemy keeps the imported 5% recovery behavior, waits a randomized 0.6–1.2 seconds, clears its transient cover flag, and starts a four-second cooldown. The existing line-of-sight and attack branches then provide the peek/reposition/fire phase. Abort handling clears transient cover state during behavior changes, death or rewind; the next entry recomputes a location. Shooter movement enables RVO avoidance with a 500 uu consideration radius to reduce same-point crowding without introducing a reservation manager in this phase.

Cold-load compilation reported zero Blueprint errors. Scripted `Map_Test` PIE applied five damage after target acquisition and observed `100 → 95`, cover activation on the next decision pass, an EQS result distinct from `PointOfInterest`, movement from about 1253 uu to 92 uu from the cover point, the 5% recovery back to 100, cover release with a four-second cooldown, no immediate re-entry, and two Time Shuttler shooter projectiles after combat resumed. Packaged builds and large-squad contention remain outside this phase.

## Ranged tactical cover — phase 2

The ranged cover branch now uses `BTT_ReserveAndMoveToCover` instead of the native Move To node. Each live Shooter publishes `HasCoverReservation`, `CoverReservationUntil` and `IsCoverOccupied` through its controller blackboard. Before movement the task scans other live Shooters; a reservation within 275 uu blocks the candidate and waits 0.35 seconds before retrying. A successful claimant marks the slot reserved before movement, upgrades it to occupied only after arrival, and clears both flags on move failure or behavior-tree abort. This keeps ownership distributed and avoids a new global manager while still covering death, rewind and branch interruption through actor removal, abort cleanup and the reservation timeout.

`BTT_CoverPeekBurst` replaces the phase-one hold-only task. After the imported 5% recovery and 0.6–1.2 second hidden pause, it compares the target direction with the pawn right vector, stores `CoverSide` as -1 or +1, writes a `CoverPeekLocation` 140 uu to that side, and physically sidesteps there. It invokes the imported Shooter attack interface twice with a 0.38 second gap, so projectile spawning and hit resolution remain in `BP_ShooterNPC` / `BP_ShooterProjectile_Bullet`. The enemy then returns to `CoverLocation`, applies the existing four-second cooldown and releases occupied, reserved and taking-cover state. Move failure and abort use the same ownership cleanup path.

Cold-load compilation of the blackboard, behavior tree, both new tasks, decorator and Shooter completed with zero Blueprint errors; the only startup warnings were the existing 14 Manny PoseAsset source-version warnings. Scripted `Map_Test` PIE used two ranged enemies and observed both enemies reserve and occupy a slot, no simultaneous claims within 275 uu (the recorded simultaneous pair was about 1108.5 uu apart), both -1 and +1 side choices, the 140 uu peek offset, seven TimeShuttle projectile spawn events, and release transitions for both enemies. The temporary Summon fixture needed its default controller and behavior tree started explicitly; teardown still exposes the pre-existing `AC_EnemyWeakPoints` player-null warning after PIE ends, which is outside this cover change.

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
