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
