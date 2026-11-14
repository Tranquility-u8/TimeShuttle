# Tactical minimap and QTE threat directions

Implemented on 2026-11-07 under the user's autonomous authorization for style 1.

## Player-facing behavior

- A compact square map stays at the top-left, with 28 logical-unit left and plot-top offsets. The plot-top offset was raised from 52 to 28 to keep the existing time-energy title readable; map size remains 224. The player stays centered; map-up is world +X and map-right is +Y. The cyan chevron follows camera yaw. Camera pitch and roll are discarded so looking vertically cannot collapse the map arrow or distort horizontal threat directions.
- The default map covers approximately 50 m across. Nearby floor surfaces and body-height obstacles use different gray-blue fills. Geometry comes from the current level's visible StaticMesh components that block Pawn, with overhead ceilings excluded by a height slice around the player's feet. Blocking bounds that contain the player are treated as enclosing/concave shells: only actual edges inside the visible range are outlined. This prevents the laboratory's 560 × 460 m terrain component from filling the entire map and does not invent walls at the crop boundary.
- While the native projectile QTE window or FullStop is active, all qualifying production enemy bullets are displayed. Outlined orange-red diamonds with bright cores indicate their current positions; short contrasting tails indicate their actual flight directions. Off-map threats are clamped to the inner map edge. The footer counts all qualifying bullets; there is no UI count cap.
- The same bullets produce camera-relative filled directional darts and tapered inner crescents around the crosshair. Faceted shading, hot rims, restrained glow and dark contrast edges retain readability over the scene. This includes left, right and rear threats. Large height differences retain UP/DN map annotations.
- Visual eligibility follows the existing QTE's relative-motion prediction window, separate capsule XY/Z tolerances, projectile radius and `Projectile`-profile occlusion trace. The projectile's move-ignore list and itself are ignored as in the native detector. A projectile already consumed by the QTE remains visible while it is still approaching; consumption only prevents repeat triggering.
- Normal state hides the threat overlay. Destroyed, receding, missing or occluded bullets disappear on the next visual refresh. FullStop does not stall HUD refreshes because scheduling uses real time.

## Assets and ownership

| Asset | Responsibility |
| --- | --- |
| `/Game/Blueprints/Components/UI/AC_TacticalMinimap` | Local-player widget creation and EndPlay cleanup. `Enabled` is the startup opt-out. |
| `/Game/UI/Minimap/WBP_TacticalMinimap` | Terrain discovery/cache, real-time refresh, world-to-map projection, threat classification and native UMG painting. |
| `/Game/UI/Minimap/WBP_IncomingThreatCue` | A retained-mode material image for one threat; a child of the minimap canvas, never a separate viewport owner. |
| `/Game/UI/Minimap/Materials/M_IncomingThreatCue` | Analytic, antialiased UI dart / crescent material with per-threat parameters and self-contained glow. |
| `/Game/Blueprints/Player/BP_FPCharacter` | Adds one `TacticalMinimap` component. Existing gameplay graphs remain unchanged. |

Runtime logic uses Blueprints and a standard Unreal UI material. The temporary authoring helper, Python, Blueprint Assist and LabAuthoring are not runtime dependencies. No new input, map, render target, scene capture, damage or energy asset is required. Existing QTE/weapon Blueprints are not modified.

Widget class defaults expose `MapRange` (2500 cm half-range), `MapSize` (224 logical units), `TerrainRefreshSeconds` (0.35 real seconds), `ThreatRefreshSeconds` (0.025 real seconds) and `RingRadius` (105 logical units). Since the art pass, each centered cue canvas is `4.2 × RingRadius` square; the material places its tapered arc inside its dart. The current footer's 50 m text corresponds to the default range; update that text if changing the range. Local geometry / centered canvas anchors keep map placement and directional cues consistent with DPI and aspect ratio.

Terrain references are collected at widget construction. Moving existing meshes, including door leaves, are resampled. New streamed/spawned mesh components are not automatically registered in this first version; a new player/widget rebuilds the cache. Terrain uses conservative world-axis component bounds, so curved/rotated/irregular meshes are approximations rather than an exact floor-plan raster. Landscape-only terrain and instanced mesh per-instance outlines are not certified.

The map panel is hidden by default. Enable **Show Map Panel** in the class defaults of `WBP_TacticalMinimap` to restore its terrain, labels and map markers. The incoming projectile arrows around the reticle use child widgets and stay available with either setting.

The current threat integration covers the game's existing production enemy-projectile QTE. It does not introduce melee prediction, reveal every enemy, or infer falling-object/explosion danger regions. Those require explicit threat-source contracts rather than treating every nearby actor as dangerous.

## Verification and evidence

The user's subsequent top-left placement correction changes only the minimap widget's horizontal anchor, plot-top default and associated comments/unused calculation nodes. `Saved/Agent/MinimapTopLeft/` preserves the pre-change package, graph inventories, clean compile/save result, seven targeted PIE checks and actual HUD/layout captures. Existing widget size and threat behavior are retained. Other worktree changes present at this follow-up were preserved.

Evidence and recovery files are local-only under `Saved/Agent/TacticalMinimap/`.

- `runtime.json`: 54/54 PIE assertions pass using the actual player and production enemy projectiles. Covers eight azimuths, four simultaneous bullets, occlusion, misses, receding bullets, capsule-height offsets, off-map clamping, consumed-projectile visibility, destruction cleanup, native FullStop, real-time refresh and restoration to Normal. The fixture temporarily disables player movement and damage at an isolated altitude; it is not an aiming/damage playthrough.
- `widget-final-graphs.json`, `component-final-graphs.json`, `final-save.json`: Blueprint Assist node-size refresh/format, structured comments, final selective format, semantic equality of all functional nodes/pins/defaults, and targeted save. Player, component and widget compile with zero errors and zero warnings. No unrelated maps/packages were saved.
- `visual-four-directions00000.png`: editor-visible native rendering of four map markers and four crosshair chevrons in FullStop. This is an isolated visual fixture; a separate ordinary-level capture demonstrates terrain.
- `lab-fixed00000.png`: actual laboratory floor/obstacle layout after the enclosing-terrain correction. `refresh-threats-layout.png` captures the final commented, formatted Blueprint graph with its clean compile indicator.
- `map-suite-warm.json`: 12/12 assertions across Map_Test, Map_TrainingRoom and Map_LabV39, including map transitions, one component/widget, visible terrain and on-screen anchoring. Three targeted calls per level measured approximately 0.20–0.27 ms, 0.62–0.74 ms and 8.09–8.31 ms for a terrain refresh respectively on this workstation; the laboratory cached 2736 mesh components. These are narrow editor measurements, not a frame-rate or stress certification. `map-suite.json` is the final repetition in the ordinary editor without the authoring helper.
- `cold-load.json` confirms clean loading/compilation without BlueprintOps or LabAuthoring. `cold-native.json` passes 16/16 native runtime checks in that process, including four-direction QTE detection, consumed-primary visibility, native FullStop/exit, real-time refresh, restored global dilation, and stable horizontal heading when the camera pitches to 80 degrees.
- The final ordinary-editor `map-suite.json` passes 12/12 checks after the enclosure/yaw corrections. `final-audit.json` confirms no custom authoring-module package dependencies, no dirty content/maps, PIE stopped, and the editor returned to Map_Test. The recovery player package SHA-256 matches the pre-task Git LFS object.

Final map/cold-load checks are recorded in the same evidence directory. Cook, packaged builds, networking, large streaming worlds and a full manual combat playthrough remain outside this first-version acceptance.

## Incoming-threat art pass — 2026-11-07

The user's Apex screenshot is the visual reference for a broad inward dart plus a separate curved direction indicator. [EA's official description](https://www.ea.com/able/resources/apex-legends/pc/features) distinguishes 2D and 3D incoming-damage arrows; [Activision's HUD reference](https://support.activision.com/servlet/servlet.FileDownload?file=00PU0000004ZRV7MAO&retURL=%2Fapex%2Fmanuals) describes a red directional damage marker. This implementation adapts that visual language to predicted incoming projectiles. It does not claim to reproduce either game's internal renderer, or turn a prediction into an actual-damage signal. Existing damage-vignette ownership is preserved.

`RegisterThreatVisual` allocates an actor-keyed child widget / dynamic material only when no reusable slot exists. `UpdateThreatVisuals` runs after the existing Tick collection: 100 ms ease-in, real-time pulse, bounded travel-time urgency, and a 160 ms exit fade followed by collapse and actor-reference release. Peak-concurrency slots are retained for reuse, including their MIDs. Invalid / destroyed actors retain their last bearing during fade. FullStop keeps the red danger body with a narrow cold rim; real-time parameters keep animation responsive. Child widgets inherit the minimap's travel / EndPlay cleanup. No new gameplay state, input, trace or terrain collection is introduced.

Material inputs are `Direction` (camera-yaw-relative screen XY), `Urgency` (0–1), `RealTime`, `Age`, `Presence` and `Frozen`. The material itself contains the complete shader; [the readable HLSL source](../../SourceAssets/UI/Threats/incoming-threat-cue.hlsl) is an authoring reference, not a runtime include. Glow is composited in the UI material and does not depend on scene bloom. The default `Presence=0` keeps uninitialized cues hidden.

Local recovery, scripts, graph exports, native captures and verification results are under ignored `Saved/Agent/ThreatArt/`. The original terrain, map anchoring, native-matched eligibility and collection graphs are unchanged. Both affected Widget Blueprints compile with zero errors / warnings. Graphs received layout and structured lifetime / presentation comments, with functional pin equality checked after layout. Initial material-output wiring was corrected before acceptance; temporary observation-script issues and overlapping projectile test fixtures were corrected separately from production logic.

The warm pass includes 54 existing eligibility / map assertions and 48 art assertions: four bearings and rotated camera bearings, pitch rejection, FullStop real-time animation, proximity urgency, exit fade, actor-reference cleanup, slot reuse, 12 simultaneous valid bullets without a display cap, moving production bullets triggering native QTE, and EndPlay during QTE. Art geometry / fade cases temporarily hold production bullet movement while retaining their native velocity; the QTE / EndPlay cases use actual moving bullets. All fixture changes are PIE-only. The ordinary-level art capture uses stationary production projectiles and a transient longer QTE window so the visual can be inspected; timing regressions use saved defaults.

All 123 recorded checks pass: `runtime.json` (54), `art-runtime.json` (48), and `cold-native.json` (21). The cold pass runs in an ordinary editor without BlueprintOps or LabAuthoring and verifies native moving-projectile QTE, material widgets, FullStop, fade completion, actor-reference cleanup and restored time scale. Scoped final warm / cold logs contain no Blueprint runtime errors or `Accessed None`. `incoming-threats-gameplay00000.png` is the native ordinary-level art capture; `material-update-layout.png` records the reviewed Blueprint layout. PIE is stopped and no content or map packages are dirty. Cook / packaged rendering, networking and a full manual combat playthrough remain unverified.

## Recovery and diagnostic boundaries

The initial worktree was clean on `dev/wingshing`. `Recovery/BP_FPCharacter.uasset` preserves the pre-change player package. Restore through version control or the preserved package only with the editor/package unloaded; never edit asset bytes. Removing the task's player component and the two new assets through the editor also removes this integration.

Preparation encountered a malformed temporary authoring-function signature and a reentrant multi-map test callback. Both caused editor exits before final acceptance; saved feature assets and unrelated maps were preserved. The signature and callback were corrected. One temporary compiler warning disappeared after a clean reload; final feature compiles are clean. Fixture/authoring errors and pre-existing animation/controller warnings are separate from final feature runtime results.
