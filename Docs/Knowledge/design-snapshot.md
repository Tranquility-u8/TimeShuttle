# Design snapshot

Observed from Google Drive on **2026-09-17**. This is a synthesis, not a verbatim mirror.

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
- The ability is toggled with `T`. Time Rewind and this ability are mutually exclusive in both directions; either may start only while the player is otherwise in Normal state.
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
