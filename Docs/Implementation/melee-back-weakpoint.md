# Melee enemy back weakpoint

Verified on 2026-11-14 in UE 5.6.1.

`/Game/Blueprints/AI/Melee/BP_MeleeNPC` now places its fixed yellow weakpoint on the middle back. In the `WeakPoints` component, candidate 0 changed from bone `neck_01` to `spine_04`, with bone-local translation `(-0.406344, -12.905250, 5.411969)` cm. The reference-pose center is 31.316 cm below the former rear-neck position, 14 cm behind the spine anchor.

The legacy internal candidate ID `BackNeck` is preserved. Candidate count, tier eligibility, radius setting (5), damage, selection rules, marker settings and all other candidates remain unchanged. Source graph connections, pins and layout were compared across all five authored graphs and remain unchanged. Compiler-generated intermediate graphs are excluded from that source comparison.

Validation:

- Saved and reloaded the targeted asset; native Blueprint compilation reports `errors=0 warnings=0`.
- Ordinary PIE in `Map_TrainingRoom` uses the real player, tutorial pistol pickup, and `BeginFire`/`StopFire`; no damage injection. The test enemy has its default controller, stopped AI, disabled movement and frozen pose for aiming.
- Runtime assignment remains one yellow point, attached to `spine_04`. Its center is below the old neck and behind the torso.
- One shot at the former rear-neck position produced no weakpoint damage (100 HP remained). One shot at the new back point consumed one round and reduced HP from 100 to 50, with `CRITICAL Damage: 50.0` in the Output Log.
- Time stop reveals the back marker. The visual core remains attached to the new hit sphere with its existing camera-facing skin offset (0.7 × radius = 3.5 cm); the core is intentionally not at the exact sphere center. Marker and collision follow a 30 cm actor translation together. The position was also checked visually in PIE.

Local evidence and recovery copy are in `Saved/Agent/MeleeBack20261114/`: `inspection.json`, `verification.json`, `compile.json`, `pie.json`, `final.json`, before/after Blueprint text exports, and `Backup/BP_MeleeNPC.uasset`. Restore with Unreal-aware asset recovery while the editor is closed, preserving any subsequent user work. The temporary compile helper is editor-only and is not added as a project dependency.

This is a targeted position change. A complete combat playthrough and packaged-build validation were not performed.
