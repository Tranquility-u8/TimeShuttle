# LabAuthoring — editor-only Blueprint preparation

This plugin has one `Editor` module and no runtime module or assets. It authors standard K2 nodes; generated game Blueprints must never call `LabAuthoringLibrary` at runtime. Engine: UE 5.6.

Prepared for Lab R17. The final UE 5.6 Win64 editor plugin build passed on 2026-10-17 (`Saved/Agent/LabR17/helper_presentation_build.log`). Editor load, generated-Blueprint compilation and PIE behavior were separately verified. Building/restarting UE is an explicit maintenance action; preparation scripts do not invoke either.

Python API (all return a JSON string):

- `unreal.LabAuthoringLibrary.inspect_class(class_path)` — functions, parameters, inherited properties and defaults.
- `inspect_blueprint(asset_path)` — graph/node/pin/link/component/variable inventory.
- `apply_spec(json.dumps(spec))` — create, populate, compile, optionally save one Blueprint.
- `apply_graph_presentation(json.dumps(patch))` — validate existing graph/node identities and old positions, then change only positions/comment styling. Returns before/after inventories and semantic equality; does not compile or save.
- `unreal.LabBlueprintCaptureLibrary.capture_blueprint_graph(asset, graph, png, width, height, tiles)` — render native Slate graph widgets on a transient Blueprint duplicate; verify source graph hash and dirty state remain unchanged.

The plugin is **disabled by default** for ordinary project use. Generated doors and Omen tracking do not depend on it. To author or inspect graphs, build the editor plugin against the matching UE 5.6 engine, enable it deliberately and restart the editor. For a Blueprint-only project, use an external UBT/RunUAT plugin build; do not add a runtime class merely to host this tool. Binaries are local build products and are not committed.

Spec:

```json
{
  "asset_path": "/Game/Environment/LabR17/Blueprints/BP_Example",
  "parent_class": "/Script/Engine.Actor",
  "allow_existing": false,
  "variables": [{"name":"Enabled","type":"bool","default":"true","instance_editable":true}],
  "components": [{"name":"Bounds","class":"/Script/Engine.BoxComponent","parent":"DefaultSceneRoot","properties":{"BoxExtent":"(X=200,Y=200,Z=200)"}}],
  "defaults": {"PrimaryActorTick.bCanEverTick":"true"},
  "graphs": [{"name":"EventGraph","kind":"event","clear":true,"nodes":[],"links":[]}],
  "compile": true,
  "save": false
}
```

Property values use UE ImportText. Object values may use `{"object":"/Engine/BasicShapes/Cube.Cube"}`. Nested struct properties use dot paths. Variables support bool/int/string/name/text/float (double)/float32/vector/rotator/transform/object/class/struct and optional arrays. Object/class/struct types supply `class`.

Node fields: `id`, `kind`, `x`, `y`, optional `defaults` dictionary and `split_pins`. Kinds: `call` (class/function; omit class for self function), `call_parent`, `event` (class/function), `custom_event` (name/inputs), `get`/`set` (variable, optional external class), `branch`, `sequence` (outputs), `self`, `entry`, `result`, `comment` (text/width/height/color). Graph links are `[source_id, source_pin, target_id, target_pin]`. Pin names are native UFUNCTION names, not display labels. `inspect_*` and failed apply reports expose pins for diagnosis.

Function graphs use `kind:function`, `inputs`/`outputs` arrays with the same type syntax, optional `pure`. All signatures are declared before self calls. Existing graphs are cleared only with `clear:true`; function entry/result nodes are retained. Existing target assets require explicit `allow_existing:true`. A failed operation may leave an unsaved partial asset: inspect or undo it; never report it as finished. No maps are changed by this API.

Result: `ok`, `errors`, `compile_errors`, `compile_warnings`, `compile_messages`, optional `saved`, and complete `blueprint` inventory. A compile failure prevents selective save. Blueprint compile may still expose errors in a source edit; coordinator must inspect the report, fix, compile, and play-test.

Maintained scripts and specs: `SourceAssets/LabV39/R17/runtime_authoring/`. First run the read-only contract inspection, then the appropriate guarded apply script. Door authoring creates only `BP_LabRoomDoor` / `BP_LabOmenDoor` and saves their packages after both compile. Placement is a separate task. Existing team edits must be reconciled before any explicit rebuild.
