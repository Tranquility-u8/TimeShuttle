# Design snapshot

Observed from Google Drive on **2026-09-17**. This is a synthesis, not a verbatim mirror.

## Tutorial design read back from the user-edited local plan on 2026-10-15

The [R5 readback record](../Design/training-room-tutorial-r5-readback-2026-10-15.md) records the user's local Word edits and the completed synchronization of 7B entry wording across text and diagram. It supersedes earlier same-day R2–R4 tutorial summaries. This is design intent, not verified UE behavior or a Google Drive refresh.

- Active time stop and impending-hit QTE both use Q. The QTE stays enabled throughout the game and appears when the threat condition is met. Older implementation records with T require separate verification; no new rewind key is established here.
- S1 prompts the player to activate time stop while rocks are falling, teaches energy drain/recovery and uses the enlarged danger area around a central safe zone.
- Use **S2A and S2B**. Both use the designated 4 × 4 m region and immobile normal enemies; attacks start only after the player's whole body is inside. Each substage begins/retries with restored health. S2A has one enemy; S2B refreshes two enemies at the far corners. Two uninjured successes/rounds pass. First injury retains earlier successes; death resets only the current substage. S2A to S2B restores health.
- S3A uses four normal enemies with body damage and requires pistol/ammo pickup and a manual reload. S3B remains provisionally two moving targets with ordinary damage, without repeating pickup/reload gates. The historical progression bug is not diagnosed by this document review.
- S4 uses three laterally moving enemies. Weakpoints are visible only in time stop, but hits remain valid in any time state, including normal shots and released temporal bullets. Non-weakpoint hits do no damage; all three must die to weakpoint damage.
- S5 permits ordinary shots to break the connection and guarantees that the falling device kills all three targets below. Show and settle that result before advancing; this is a reliable environmental-kill demonstration.
- S6 retains the high-hung slab with two independent connections. One-side release leaves it hanging vertically; recommended Q use stores two shots to help release a broad footprint. Passing requires all three designated targets to actually die in **the same main slab impact**, with no separate time-gap, angle or Q-use gate. Do not accumulate rolling/bouncing/follow-up kills. An incomplete hanging state can continue; a failed impact or abnormal fully released slab rebuilds the local attempt. Geometry and outcome grouping still need implementation validation.
- S3A through S6 retain the full-width blocking weapon table and reserve-ammo replenishment. Remove them before S7A. One melee enemy then spawns in front of the player; its death while the player survives advances to 7B preparation. Player death retries 7A; mutual death is failure.
- **7B entry is unified across the plan: first entry uses waypoint guidance so the player walks to P, without teleporting or forcing facing. Only a death retry automatically resets position and facing.** First arrival is followed by health/energy recovery, time-mode exit, old-projectile/combat-state cleanup, pistol/ammo preparation and scene generation. Enable attacks only after that preparation; no attacks during guidance. A death retry repositions first, then performs the same preparation. The former introduction/flow/diagram inconsistencies are fixed in the unified version.
- 7B retains full health/energy preparation, the same pistol picked up in S3A, a full standard magazine and 24 additional reserve rounds. Its original formalized layout has four high and four low covers, L2 horizontal, one melee and three ranged enemies, and a central falling-rock device with passable ground below. Enemy activity may pass beneath it; this is no longer restricted to one ranged enemy. Four enemies dead and player alive passes, with any valid combat method. Death retries only 7B.
- Other ordinary stage transitions preserve player position/facing and dissolve props. The separate optimized S7B layout remains a proposal, not the accepted main diagram. Exact layout coordinates, S3B target parameters and S6 physical dimensions retain their proposed or unverified status.

The [R2](../Design/training-room-tutorial-revision-2026-10-15.md), [R3](../Design/training-room-tutorial-r3-2026-10-15.md) and [R4](../Design/training-room-tutorial-r4-2026-10-15.md) tutorial records are historical. Their S2C naming, slab trays, break-interval gate and demonstration-only S6 deaths must not override the latest user decisions. Older implementation records remain evidence of the older build.

## Core combat and movement

- Required FPS verbs: move, aim, shoot, sprint, crouch, reload, knife, and pistol.
- Explicitly out of current scope in design discussion: climbing and sliding.
- Ammunition is intended to be effectively unlimited, narratively supported by recreating items from earlier timelines.
- Enemy archetypes: a fully armored melee enemy with three red weak points and a lightly armored ranged enemy with one red weak point.
- Weak points become a key target during stopped time. Some armored enemies may require time to resume before an opening appears; this interaction remains a design detail to validate.

## Time abilities

- **Area Stop:** freeze objects and enemies in a local range.
- **Bullet Time:** slow the environment.
- **Time Rewind:** record object state and replay/restore it in reverse.
- The left-arm device displays an energy bar and percentage.
- Current concept: full stop from 100% to 50% energy; below 50%, time moves slowly as control degrades.
- Detached moving objects may retain momentum for roughly 0.5–1 second before stopping. This is a concept, not a verified implementation requirement.
- Intended emergent play includes shooting chains, explosives, projectiles, or physics objects during stopped time to set up consequences when time resumes.

### Time ability vertical-slice decisions confirmed by the user on 2026-09-26

This subsection records direct decisions made during the implementation conversation. It is newer than the 2026-09-17 Drive observation, but it is not a Drive refresh and does not silently rewrite the broader GDD.

- The first playable version uses a single 0–100 energy resource. Energy drains uniformly while active and recovers uniformly while inactive; both default to 10 points per real second.
- Energy `100–70` is FullStop. Below 70 is BulletTime, with world speed continuously approaching normal as energy approaches zero. Zero energy automatically exits the ability.
- At the time of this 2026-09-26 slice, the ability was toggled with `T` (superseded as design intent by R3's unified Q; migration is not yet verified). Time Rewind and this ability are mutually exclusive in both directions; either may start only while the player is otherwise in Normal state.
- In FullStop, the player remains fully controllable and may fire. Each shot becomes a visible projectile that stops a short distance in front of the muzzle, preserves its trajectory/momentum, and releases when FullStop ends.
- The initial projectile policy is a fixed global cap of 12. At the cap, further shots are rejected rather than replacing an older projectile.
- Existing pickup interaction remains available during FullStop. Generic world physics follows the current time mode and retains velocity across stop/slow/resume transitions.
- The first version does not require a new VFX pass. HUD must distinguish Normal, FullStop and BulletTime, show energy, and show suspended-projectile count/cap in FullStop.
- The implemented vertical slice currently applies time scaling level-wide rather than within a local radius. Whether the production Area Stop becomes spatially local remains a separate design decision.

These decisions supersede the earlier `100–50` threshold for this implemented slice. They do not resolve the final production scope, spatial radius, VFX language or balance values.

## Interaction and inventory

- Pick up objects and readable notes; show descriptions in UI.
- Highlight interactable objects.
- Maintain a simple collection inventory focused on clues rather than RPG depth.
- Recreate collected objects into a radial toolbar operated by holding the middle mouse button.

## World and narrative

- Laboratory hub: Omen dialogue/mission room, teleport platform, separate training area, player bedroom, and hidden puzzles.
- Chapter 1: laboratory exposition and combat tutorial.
- Chapters 2–3: escalating combat and time-mechanic mastery, including anti-time armor.
- Chapter 4: laboratory combat and narrative transition.
- Chapter 5: rewind/environment interaction, story interaction, and fighting the player's past self.
- Chapter 6: puzzles and information collection across a past-bound route and laboratory.
- Chapter 7: return to the present and final confrontation with Omen using items obtained in the past.

## Presentation goals

- Time activation begins with an environmental scan and transitions into a gray-blue world state.
- Pistol muzzle flash and solid-color bullet trails support readability.
- UI includes crosshair, time-device energy, item descriptions, collection inventory, and radial toolbar.
