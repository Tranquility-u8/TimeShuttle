# SceneBridge UE editor plugin

An editor-only, content/Python plugin for Unreal Engine 5.6. It consumes a complete
Blender export bundle, imports stable static-mesh assets, and maintains managed
actors in a dedicated, non-World-Partition map. It has no runtime dependency or
C++ build requirement.

## Installation and first import

Copy `SceneBridge/` into the target project's `Plugins/` directory and enable it.
Its dependencies are Python Editor Script Plugin and Editor Scripting Utilities.
Restart the editor after enabling the plugin. This registers **Tools → SceneBridge**.

From the editor Python console (the paths below are examples):

```python
import scene_bridge
scene_bridge.configure(
    "D:/MyExports/Lab/manifest.json",
    target_map="/Game/Maps/Map_LabBridge",
    conflict_policy="keep_ue",
)
scene_bridge.sync_configured(dry_run=True)
scene_bridge.sync_configured()
scene_bridge.start_watch()
```

When loading the Python package directly before installing/enabling the plugin,
call `scene_bridge.startup()` once to register the menu in the running editor.
The installed plugin runs this automatically from `Content/Python/init_unreal.py`
on subsequent editor starts. If the Tools menu is not ready yet, registration is
deferred to the first available editor tick. Watch is opt-in: choosing Watch
remembers that choice and resumes it on subsequent editor starts; choosing Stop
clears it. After restart it still waits for the configured map and never switches
the user's current map automatically.

The same actions are available from Tools → SceneBridge: **Preview changes**,
**Sync Blender scene**, **Watch saved Blender snapshots**, **Stop watching**.
Configuration, import reports, collision counts, recovery journals and sync state
are local to `<project>/Saved/SceneBridge/`; no machine path is embedded in the
plugin or tracked project configuration.

`Watch` polls complete manifest snapshots once per second on the editor thread.
Blender must publish a snapshot on save or export; the UE plugin does not read
`.blend` files itself. During PIE, changes stay queued. When the target map is not
open, Watch waits without switching the user's map. On failure it pauses that
revision and records the error; manual Sync or a new exported snapshot retries.
Stopping Watch does not remove imported assets or actors.

## Python API

```python
report = scene_bridge.import_scene(
    "D:/MyExports/Lab/manifest.json",
    target_map="/Game/Maps/Map_LabBridge",
    asset_root="/Game/SceneBridge",
    options={
        "dry_run": False,
        "conflict_policy": "keep_ue",  # or "source_wins"
        "create_map": True,           # create_if_missing is also accepted
        "save": True,
        "force": False,
        "force_assets": False,       # True or an explicit list of mesh IDs
    },
)
```

Dry-run validates the complete manifest and calculates changes without importing,
switching maps, or writing state. If the target map is closed, its live transform
conflicts cannot be checked until a real sync loads it; the report states this.
A scene ID is bound to one target map and asset namespace. A different target
requires an intentionally separate Blender scene identity.

Source-owned names, collection folders, geometry, material assignments and
collision policy are updated. Actor identity is retained through renaming and
movement. Transforms use `keep_ue` by default: a detected UE transform edit becomes
a persistent override and is reported. `source_wins` explicitly reapplies the
Blender transform. This is a one-way bridge, not a two-way scene editor.

## Supported snapshot contract

- `schema_version: 1`, stable `scene_id`, `scene_name`, string/integer `revision`,
  `complete: true`, `unit: "cm"`, and a full `objects` list.
- Each object has stable `id`, display `name`, `object_type` (`MESH` or `EMPTY`),
  optional exported `parent_id`, collection `folder`, UE world `location`,
  quaternion `[x,y,z,w]`, `scale`, and `transform_hash`.
- Meshes have stable `mesh_id`, `geometry_hash`, `material_hash`, optional
  `collision_hash`, a relative FBX path, collision policy and PBR material list.
- The FBX contains geometry in normalized local space. The exporter converts its
  metric units to the FBX unit system. UE imports with scale 1 and applies the FBX
  node/unit conversion (`transform_vertex_to_absolute=True`); world placement is
  applied only from the manifest. Asset import settings are included in the cache
  signature so importer policy changes invalidate old mesh imports.
- EMPTY objects become an empty StaticMeshActor, which has a root component for
  transform hierarchy. No render mesh or collision is assigned to these nodes.
- Shared IDs, missing parents, cyclic hierarchy, path escapes, zero scale,
  non-finite transforms and inconsistent shared material definitions are rejected.
  Mirrored transforms are supported through signed scale and require the same
  collision verification as other imported geometry.

This release synchronizes mesh geometry and EMPTY transform hierarchies. It does
not import Blender cameras, lamps, procedural shader graphs, animation, armatures,
geometry-node instances that have not been realized, or arbitrary game logic.
UE lighting, PlayerStart, triggers and gameplay actors are authored in UE and
remain outside the bridge's managed actor set. Evaluated mesh modifiers are baked
by the Blender exporter before FBX is written.

Stable generated mesh paths use scene and mesh identity, never display labels:
`<asset_root>/Scene_<scene hash>/Meshes/SM_<mesh ID hash>`. Geometry or custom
collision changes reimport that same asset; transform-only changes update the
actor without reimporting its mesh. Material-only changes update material assets
and slots. Ordinary PBR colors, roughness, metallic and alpha are supported;
Blender node graphs are not translated. Alpha below 1 produces a translucent,
two-sided material, independently of its collision policy.

## Collision policies

| Policy | Imported result | Intended use |
| --- | --- | --- |
| `complex` | Use Complex Collision As Simple | Static architecture with concave openings |
| `box` | Generated box simple collision | Simple rectangular static props |
| `convex` | Bounded convex decomposition | Convex/simple prop approximations |
| `custom` | Imported UCX/UBX, required to be present | Authored hulls, stair ramps |
| `none` | Actor collision disabled | Helpers and intentionally nonblocking geometry |

Every mesh actor uses its declared collision preset (default `BlockAll`). All
bridge geometry is static and physics simulation is disabled. This version does
not convert objects into interactive Blueprint doors, elevators or rigid bodies.
The collision report verifies generated shape counts and complexity settings;
it is not proof that a game character, line trace, projectile or NavMesh can use
the level correctly. Validate those using the target game's actual classes and
channels, including both simple collision sweeps and complex weapon traces.

## Ownership, deletion and recovery

Managed actors are marked with `SceneBridge.Managed`, `SceneBridge.Scene:<id>` and
`SceneBridge.Object:<id>`. Only actors bearing all matching tags may be updated or
removed. Actors the UE designer adds remain outside the bridge. Import paths carry
scene/mesh metadata; a pre-existing unowned asset at a generated path is rejected.
Removing a Blender object removes its managed UE actor on the next complete sync;
its static mesh asset is retained, preserving other references and recovery data.

Each import writes a pending journal before importing assets. The actor edits use
an editor transaction, but **FBX imports are not undone by Ctrl+Z**. If interrupted,
rerun the same snapshot: existing owned assets and actors are reused. State commits
only after the target map saves. Asset bytes are never edited directly, no assets
are deleted, and unrelated content packages are never saved. Switching maps is
refused while a map is dirty. A successful sync saves its target map, so ordinary
edits already made in that target map are included in that map save.

Use project source control/backups for recovery to an earlier asset revision.
Undoing actor changes does not roll back imported static-mesh contents. A follow-up
Sync reconciles the owned actors with the desired snapshot.

World Partition targets are deliberately rejected in this initial release. The
first validation map is ordinary and isolated; integration into a World Partition
production level needs a separately verified ownership/loading/saving strategy.
