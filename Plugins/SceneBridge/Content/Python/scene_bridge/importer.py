"""UE 5.6 editor-side import of an owned, complete Blender snapshot.

The actor transaction is undoable. Asset imports are NOT undoable: a persisted
pending journal and stable paths make retries idempotent. No asset is deleted.
"""
import json
import os
import time
from pathlib import Path

import unreal

from .schema import (BridgeError, asset_signature, digest, object_fingerprint,
                     package_path, read_manifest, token, transforms_close)

SCENE_TAG = "SceneBridge.Scene:"
OBJECT_TAG = "SceneBridge.Object:"
OWNER_TAG = "SceneBridge.Managed"
META_SCENE = "SceneBridgeSceneId"
META_MESH = "SceneBridgeMeshId"
META_MATERIAL = "SceneBridgeMaterialId"
META_HASH = "SceneBridgeHash"
_BUSY = False
IMPORT_POLICY = "legacy-fbx-local-cm-absolute-cvar-v3"


def _import_signature(obj):
    return digest({"asset": asset_signature(obj), "import_policy": IMPORT_POLICY})


def saved_root():
    return Path(unreal.Paths.project_saved_dir()).resolve() / "SceneBridge"


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + ".tmp")
    temp.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(str(temp), str(path))


def read_json(path, default=None):
    if not Path(path).exists():
        return {} if default is None else default
    try:
        return json.loads(Path(path).read_text(encoding="utf-8-sig"))
    except (ValueError, OSError) as error:
        raise BridgeError(f"Invalid SceneBridge state {path}: {error}") from error


def is_playing():
    return unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).is_in_play_in_editor()


def editor_world():
    return unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()


def world_path():
    world = editor_world()
    return world.get_path_name().split(".", 1)[0] if world else None


def _require_non_partitioned():
    world = editor_world()
    if not world:
        raise BridgeError("No editor world is open")
    settings = world.get_world_settings()
    try:
        partition = settings.get_editor_property("world_partition")
    except Exception as error:
        raise BridgeError("Could not verify World Partition status; refusing an unbounded import") from error
    if partition is not None:
        raise BridgeError("SceneBridge 0.1 imports only non-World-Partition maps. Use a dedicated bridge test map.")


def _scene_namespace(scene_id, asset_root):
    return package_path(asset_root, "asset_root") + "/Scene_" + token(scene_id, 16)


def _mesh_path(namespace, mesh_id):
    return namespace + "/Meshes/SM_" + token(mesh_id)


def _material_key(material):
    return str(material.get("id") or material.get("name") or "Default")


def _material_path(namespace, material):
    return namespace + "/Materials/M_" + token(_material_key(material))


def _owned_asset(path, scene_id, kind, object_id, pending=None):
    if not unreal.EditorAssetLibrary.does_asset_exist(path):
        return None
    asset = unreal.EditorAssetLibrary.load_asset(path)
    if asset is None:
        raise BridgeError(f"Could not load existing asset: {path}")
    scene = unreal.EditorAssetLibrary.get_metadata_tag(asset, META_SCENE)
    ident = unreal.EditorAssetLibrary.get_metadata_tag(asset, kind)
    if str(scene) == scene_id and str(ident) == object_id:
        return asset
    # Recovery only claims a path explicitly recorded as absent before this
    # pending batch. It never takes over an asset that existed at preflight.
    if (pending and not str(scene) and not str(ident)
            and path in pending.get("new_asset_paths", [])
            and pending.get("scene_id") == scene_id):
        return asset
    raise BridgeError(f"Asset path is not owned by this scene: {path}")


def _stamp(asset, scene_id, kind, object_id, fingerprint=None):
    unreal.EditorAssetLibrary.set_metadata_tag(asset, META_SCENE, scene_id)
    unreal.EditorAssetLibrary.set_metadata_tag(asset, kind, object_id)
    if fingerprint:
        unreal.EditorAssetLibrary.set_metadata_tag(asset, META_HASH, fingerprint)


def _save_asset(asset):
    if not unreal.EditorAssetLibrary.save_loaded_asset(asset, only_if_is_dirty=False):
        raise BridgeError(f"Asset save failed: {asset.get_path_name()}")


def _tags(actor):
    return [str(t) for t in actor.get_editor_property("tags")]


def _actor_index(scene_id):
    index = {}
    scene_tag = SCENE_TAG + scene_id
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
    for actor in actors:
        tags = _tags(actor)
        if OWNER_TAG not in tags or scene_tag not in tags:
            continue
        object_ids = [t[len(OBJECT_TAG):] for t in tags if t.startswith(OBJECT_TAG)]
        if len(object_ids) != 1:
            raise BridgeError(f"Managed actor has invalid identity tags: {actor.get_actor_label()}")
        oid = object_ids[0]
        if oid in index:
            raise BridgeError(f"Duplicate managed actor identity {oid}; resolve copied UE actors before syncing")
        if not isinstance(actor, unreal.StaticMeshActor):
            raise BridgeError(f"Managed object {oid} is no longer a StaticMeshActor")
        index[oid] = actor
    return index


def _transform(actor):
    transform = actor.get_actor_transform()
    location = transform.translation
    scale = transform.scale3d
    quat = transform.rotation
    return {"location": [location.x, location.y, location.z],
            "quaternion": [quat.x, quat.y, quat.z, quat.w],
            "scale": [scale.x, scale.y, scale.z]}


def _desired_transform(obj):
    return {k: obj[k] for k in ("location", "quaternion", "scale")}


def _material_definitions(data):
    materials = {}
    for obj in data["objects"]:
        for material in obj.get("materials", []):
            key = _material_key(material)
            if key in materials and digest(materials[key]) != digest(material):
                raise BridgeError(f"Material identity {key!r} has inconsistent definitions in one snapshot")
            materials[key] = material
    return materials


def _plan(data, state, actors, namespace, policy, live):
    previous = state.get("objects", {})
    desired = {o["id"]: o for o in data["objects"]}
    plan = {"add": [], "geometry": [], "materials": [], "transform": [],
            "rename": [], "metadata": [], "delete": [], "conflicts": [],
            "unchanged": [], "live_actor_check": live}
    for oid, obj in desired.items():
        old = previous.get(oid, {})
        actor = actors.get(oid)
        changed = False
        if not old or (live and actor is None):
            plan["add"].append(oid)
            changed = True
        old_asset = state.get("assets", {}).get(obj["mesh_id"], {})
        if obj.get("mesh_id") and (old_asset.get("signature") != _import_signature(obj)
                or not unreal.EditorAssetLibrary.does_asset_exist(_mesh_path(namespace, obj["mesh_id"]))):
            plan["geometry"].append(oid)
            changed = True
        if obj.get("mesh_id") and old.get("material_hash") != obj["material_hash"]:
            plan["materials"].append(oid)
            changed = True
        current = _transform(actor) if actor else None
        # Keep an explicit UE override sticky across revisions until source_wins.
        conflict = bool(actor and old and (old.get("ue_override") or
                        not transforms_close(current, old.get("applied_transform")))
                        and not transforms_close(current, _desired_transform(obj)))
        if conflict:
            plan["conflicts"].append({"id": oid, "name": obj["name"], "resolution": policy,
                                      "ue": current, "blender": _desired_transform(obj)})
            if policy == "keep_ue" and (not old.get("ue_override") or
                                         not transforms_close(current, old.get("applied_transform"))):
                plan["metadata"].append(oid)
                changed = True
        if ((actor and not transforms_close(current, _desired_transform(obj)))
                or (not live and old.get("transform_hash") != obj["transform_hash"])):
            if not conflict or policy == "source_wins":
                plan["transform"].append(oid)
                changed = True
        if old.get("name") != obj["name"] or (actor and actor.get_actor_label() != obj["name"]):
            plan["rename"].append(oid)
            changed = True
        if old.get("fingerprint") != object_fingerprint(obj) and oid not in plan["metadata"]:
            plan["metadata"].append(oid)
            changed = True
        if not changed:
            plan["unchanged"].append(oid)
    # In live mode tags are the authority, including an interrupted prior batch.
    plan["delete"] = sorted(set(actors if live else previous) - set(desired))
    plan["counts"] = {k: len(v) for k, v in plan.items() if isinstance(v, list)}
    return plan


def _import_fbx(obj, asset_path, scene_id):
    destination, name = asset_path.rsplit("/", 1)
    options = unreal.FbxImportUI()
    options.set_editor_property("automated_import_should_detect_type", False)
    options.set_editor_property("original_import_type", unreal.FBXImportType.FBXIT_STATIC_MESH)
    options.set_editor_property("mesh_type_to_import", unreal.FBXImportType.FBXIT_STATIC_MESH)
    options.set_editor_property("import_mesh", True)
    options.set_editor_property("import_as_skeletal", False)
    options.set_editor_property("import_materials", False)
    options.set_editor_property("import_textures", False)
    options.set_editor_property("import_animations", False)
    static = options.get_editor_property("static_mesh_import_data")
    import_settings = {
        "combine_meshes": True,
        "auto_generate_collision": False,
        "one_convex_hull_per_ucx": True,
        "import_uniform_scale": 1.0,
        "convert_scene": True,
        "convert_scene_unit": True,
        "force_front_x_axis": False,
        "transform_vertex_to_absolute": True,
        "bake_pivot_in_vertex": False,
        "generate_lightmap_u_vs": False,
    }
    for key, value in import_settings.items():
        static.set_editor_property(key, value)
    existing_mesh = unreal.EditorAssetLibrary.load_asset(asset_path) if unreal.EditorAssetLibrary.does_asset_exist(asset_path) else None
    if existing_mesh:
        existing_data = existing_mesh.get_editor_property("asset_import_data")
        if not isinstance(existing_data, unreal.FbxStaticMeshImportData):
            # FbxFactory routes an existing mesh into its reimport handler before
            # it reads ImportTask.Options. Replace Interchange import metadata
            # first so that the first migration already uses the intended units.
            existing_data = unreal.FbxStaticMeshImportData(outer=existing_mesh)
            existing_data.scripted_add_filename(obj["_fbx_path"], 0, "SceneBridge")
            existing_mesh.set_editor_property("asset_import_data", existing_data)
        for key, value in import_settings.items():
            existing_data.set_editor_property(key, value)
    task = unreal.AssetImportTask()
    for key, value in {
        "filename": obj["_fbx_path"], "destination_path": destination,
        "destination_name": name, "automated": True, "replace_existing": True,
        "replace_existing_settings": True, "save": False,
        "options": options, "factory": unreal.FbxFactory(),
    }.items():
        task.set_editor_property(key, value)
    # UE 5.6 redirects even an explicit FbxFactory to Interchange while this
    # feature flag is enabled. Scope the override to the synchronous import and
    # always restore the user's previous setting, including on failure.
    cvar = "Interchange.FeatureFlags.Import.FBX"
    previous_text = unreal.SystemLibrary.get_console_variable_string_value(cvar)
    if previous_text == "":
        raise BridgeError("Cannot verify the UE 5.6 FBX importer feature flag")
    previous_value = unreal.SystemLibrary.get_console_variable_int_value(cvar)
    try:
        unreal.SystemLibrary.execute_console_command(editor_world(), cvar + " 0")
        if unreal.SystemLibrary.get_console_variable_int_value(cvar) != 0:
            raise BridgeError("Could not select the legacy FBX importer for this batch")
        unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    finally:
        unreal.SystemLibrary.execute_console_command(editor_world(), cvar + " " + str(previous_value))
    results = task.get_objects()
    meshes = [r for r in results if isinstance(r, unreal.StaticMesh)]
    mesh = unreal.EditorAssetLibrary.load_asset(asset_path)
    if not meshes or not isinstance(mesh, unreal.StaticMesh) or mesh not in meshes:
        raise BridgeError(f"FBX import did not produce expected StaticMesh {asset_path}")
    if any(r.get_path_name().split(".", 1)[0] != asset_path for r in meshes):
        raise BridgeError(f"FBX unexpectedly produced additional static meshes for {obj['id']}")
    if not isinstance(mesh.get_editor_property("asset_import_data"), unreal.FbxStaticMeshImportData):
        raise BridgeError(f"Import did not use the required legacy FBX pipeline: {asset_path}")
    imported_data = mesh.get_editor_property("asset_import_data")
    for field in ("transform_vertex_to_absolute", "convert_scene", "convert_scene_unit", "import_uniform_scale"):
        if imported_data.get_editor_property(field) != import_settings[field]:
            raise BridgeError(f"FBX import settings readback failed for {field}: {asset_path}")
    _stamp(mesh, scene_id, META_MESH, obj["mesh_id"], _import_signature(obj))
    return mesh


def _collision(mesh, obj):
    subsystem = unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)
    mode = obj["collision"]
    body = mesh.get_editor_property("body_setup")
    if body is None:
        raise BridgeError(f"Missing BodySetup on {mesh.get_name()}")
    if mode != "custom":
        subsystem.remove_collisions(mesh)
    if mode == "complex":
        flag = unreal.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE
    else:
        flag = unreal.CollisionTraceFlag.CTF_USE_SIMPLE_AND_COMPLEX
    body.set_editor_property("collision_trace_flag", flag)
    if mode == "box":
        if subsystem.add_simple_collisions(mesh, unreal.ScriptCollisionShapeType.BOX) < 0:
            raise BridgeError(f"Box collision generation failed on {mesh.get_name()}")
    elif mode == "convex":
        settings = obj.get("collision_options", {})
        hulls = max(1, min(64, int(settings.get("hull_count", 8))))
        verts = max(8, min(64, int(settings.get("max_hull_verts", 16))))
        precision = max(10000, min(1000000, int(settings.get("hull_precision", 100000))))
        if not subsystem.set_convex_decomposition_collisions(mesh, hulls, verts, precision):
            raise BridgeError(f"Convex collision generation failed on {mesh.get_name()}")
    elif mode == "custom" and subsystem.get_simple_collision_count(mesh) == 0:
        raise BridgeError(f"Custom collision requested but no UCX/UBX collision was imported: {obj['name']}")
    actual = subsystem.get_collision_complexity(mesh)
    if actual != flag:
        raise BridgeError(f"Collision complexity readback failed: {mesh.get_name()}")
    return {"policy": mode, "simple_count": subsystem.get_simple_collision_count(mesh),
            "convex_count": subsystem.get_convex_collision_count(mesh), "complexity": str(actual)}


def _material(material, path, scene_id, pending):
    key = _material_key(material)
    fingerprint = digest(material)
    asset = _owned_asset(path, scene_id, META_MATERIAL, key, pending)
    if asset and str(unreal.EditorAssetLibrary.get_metadata_tag(asset, META_HASH)) == fingerprint:
        return asset
    if asset is None:
        destination, name = path.rsplit("/", 1)
        asset = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
            name, destination, unreal.Material, unreal.MaterialFactoryNew())
    if not isinstance(asset, unreal.Material):
        raise BridgeError(f"Owned material path has the wrong asset type: {path}")
    lib = unreal.MaterialEditingLibrary
    lib.delete_all_material_expressions(asset)
    color = material.get("base_color", [.7, .7, .7, 1.0])
    rgb = lib.create_material_expression(asset, unreal.MaterialExpressionConstant3Vector, -420, 0)
    rgb.set_editor_property("constant", unreal.LinearColor(*color))
    lib.connect_material_property(rgb, "", unreal.MaterialProperty.MP_BASE_COLOR)
    for row, (prop, value) in enumerate([
        (unreal.MaterialProperty.MP_ROUGHNESS, material.get("roughness", .8)),
        (unreal.MaterialProperty.MP_METALLIC, material.get("metallic", 0.0)),
    ], 1):
        scalar = lib.create_material_expression(asset, unreal.MaterialExpressionConstant, -420, row * 120)
        scalar.set_editor_property("r", float(value))
        lib.connect_material_property(scalar, "", prop)
    transparent = color[3] < .999
    asset.set_editor_property("blend_mode", unreal.BlendMode.BLEND_TRANSLUCENT if transparent
                              else unreal.BlendMode.BLEND_OPAQUE)
    asset.set_editor_property("two_sided", transparent)
    if transparent:
        alpha = lib.create_material_expression(asset, unreal.MaterialExpressionConstant, -420, 360)
        alpha.set_editor_property("r", max(0., min(1., float(color[3]))))
        lib.connect_material_property(alpha, "", unreal.MaterialProperty.MP_OPACITY)
        asset.set_editor_property("translucency_lighting_mode", unreal.TranslucencyLightingMode.TLM_SURFACE)
    lib.recompile_material(asset)
    _stamp(asset, scene_id, META_MATERIAL, key, fingerprint)
    _save_asset(asset)
    return asset


def _apply_transform(actor, obj):
    transform = unreal.Transform(location=unreal.Vector(*obj["location"]),
                                 rotation=unreal.Quat(*obj["quaternion"]).rotator(),
                                 scale=unreal.Vector(*obj["scale"]))
    actor.set_actor_transform(transform, False, True)
    if not transforms_close(_transform(actor), _desired_transform(obj)):
        raise BridgeError(f"Actor transform readback failed: {obj['name']}")


def _assign_actor(actor, obj, mesh, scene_id, preserve_transform):
    tags = [t for t in _tags(actor) if not t.startswith((SCENE_TAG, OBJECT_TAG)) and t != OWNER_TAG]
    actor.set_editor_property("tags", tags + [OWNER_TAG, SCENE_TAG + scene_id, OBJECT_TAG + obj["id"]])
    actor.set_actor_label(obj["name"], mark_dirty=True)
    folder = "SceneBridge/" + token(scene_id, 12)
    source_folder = str(obj.get("folder") or "").replace("\\", "/").strip("/")
    if source_folder:
        folder += "/" + source_folder
    actor.set_folder_path(folder)
    component = actor.get_editor_property("static_mesh_component")
    if component.get_editor_property("static_mesh") != mesh:
        if not component.set_static_mesh(mesh):
            raise BridgeError(f"Could not assign mesh to {obj['name']}")
    component.set_mobility(unreal.ComponentMobility.STATIC)
    component.set_collision_profile_name(obj.get("collision_profile", "BlockAll"), True)
    component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION if obj["collision"] == "none"
                                    else unreal.CollisionEnabled.QUERY_AND_PHYSICS)
    component.set_simulate_physics(False)
    if not preserve_transform:
        _apply_transform(actor, obj)


def import_scene(manifest_path, target_map=None, asset_root="/Game/SceneBridge", options=None):
    """Import or dry-run a complete snapshot. See README for supported options.

    options: dry_run=False, conflict_policy='keep_ue', create_map=True,
    save=True, force=False. A map change is refused while any map is dirty.
    """
    global _BUSY
    if _BUSY:
        raise BridgeError("A SceneBridge batch is already running")
    if is_playing():
        raise BridgeError("PIE is active; the watcher will apply the latest snapshot after PIE ends")
    _BUSY = True
    journal_path = None
    journal = None
    try:
        return _import_scene(manifest_path, target_map, asset_root, options or {})
    finally:
        _BUSY = False


def _import_scene(manifest_path, target_map, asset_root, options):
    path, data = read_manifest(manifest_path)
    scene_id = data["scene_id"]
    policy = options.get("conflict_policy", "keep_ue")
    if policy not in ("keep_ue", "source_wins"):
        raise BridgeError("conflict_policy must be keep_ue or source_wins")
    state_path = saved_root() / "scenes" / (token(scene_id) + ".json")
    journal_path = saved_root() / "pending" / (token(scene_id) + ".json")
    state = read_json(state_path)
    pending = read_json(journal_path)
    target = package_path(target_map or state.get("target_map") or
                          "/Game/Maps/Map_SceneBridge_" + token(scene_id, 12), "target_map")
    namespace = _scene_namespace(scene_id, asset_root)
    if state and (state.get("scene_id") != scene_id or state.get("target_map") != target
                  or state.get("namespace") != namespace):
        raise BridgeError("This scene is already bound to a different map or asset scope")
    if pending and (pending.get("target_map") != target or pending.get("namespace") != namespace):
        raise BridgeError("A pending batch uses a different target scope; resolve it before rebinding")
    materials = _material_definitions(data)
    live = world_path() == target
    if live:
        _require_non_partitioned()
    actors = _actor_index(scene_id) if live else {}
    plan = _plan(data, state, actors, namespace, policy, live)
    report = {"scene_id": scene_id, "scene_name": data["scene_name"], "revision": data["revision"],
              "target_map": target, "asset_root": namespace, "manifest": str(path),
              "dry_run": bool(options.get("dry_run")), "plan": plan,
              "asset_imports_are_undoable": False, "warnings": []}
    if not live:
        report["warnings"].append("Target map is not currently open; live UE transform conflicts are checked after loading.")
    if options.get("dry_run"):
        report["status"] = "preview"
        return report
    required_changes = any(plan[key] for key in
                           ("add", "geometry", "materials", "transform", "rename", "metadata", "delete"))
    if (state.get("revision") == data["revision"] and not pending and not options.get("force")
            and not required_changes and not options.get("force_assets")):
        report["status"] = "unchanged_revision"
        return report
    if not live:
        dirty = unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages()
        if dirty:
            raise BridgeError("Save your currently open map before SceneBridge switches maps; no unrelated map is auto-saved")
        levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
        if unreal.EditorAssetLibrary.does_asset_exist(target):
            if not levels.load_level(target):
                raise BridgeError(f"Could not load target map {target}")
        else:
            if not options.get("create_map", options.get("create_if_missing", True)):
                raise BridgeError(f"Target map does not exist: {target}")
            if not levels.new_level(target, False):
                raise BridgeError(f"Could not create non-World-Partition map {target}")
        _require_non_partitioned()
        actors = _actor_index(scene_id)
        plan = _plan(data, state, actors, namespace, policy, True)
        report["plan"] = plan
    # A pre-existing target is supported, but only tagged SceneBridge actors are
    # touched. New scene imports do not take over or clear existing actors.
    mesh_objects = {}
    for obj in data["objects"]:
        if obj.get("mesh_id"):
            mesh_objects.setdefault(obj["mesh_id"], obj)
    new_paths = set(pending.get("new_asset_paths", []))
    for mesh_id, obj in mesh_objects.items():
        mesh_path = _mesh_path(namespace, mesh_id)
        existing = _owned_asset(mesh_path, scene_id, META_MESH, mesh_id, pending)
        if existing is None:
            new_paths.add(mesh_path)
    for material in materials.values():
        material_path = _material_path(namespace, material)
        existing = _owned_asset(material_path, scene_id, META_MATERIAL, _material_key(material), pending)
        if existing is None:
            new_paths.add(material_path)
    journal = {"scene_id": scene_id, "revision": data["revision"], "target_map": target,
               "namespace": namespace, "manifest": str(path), "started_at": time.time(),
               "status": "pending", "phase": "assets", "new_asset_paths": sorted(new_paths),
               "completed_assets": [], "plan": plan,
               "recovery": "Re-run the same snapshot; stable owned paths are idempotent. Asset imports are not undone by Ctrl+Z."}
    write_json(journal_path, journal)
    meshes, next_assets, collision_report = {}, {}, {}
    imported_count, material_updates = 0, 0
    try:
        material_assets = {}
        for key, material in materials.items():
            material_assets[key] = _material(material, _material_path(namespace, material), scene_id, journal)
        for mesh_id, obj in mesh_objects.items():
            mesh_path = _mesh_path(namespace, mesh_id)
            old = state.get("assets", {}).get(mesh_id, {})
            mesh = _owned_asset(mesh_path, scene_id, META_MESH, mesh_id, journal)
            signature = _import_signature(obj)
            # Metadata also supports finishing an asset stage after a prior error.
            mesh_fingerprint = str(unreal.EditorAssetLibrary.get_metadata_tag(mesh, META_HASH)) if mesh else ""
            force_assets = options.get("force_assets", False)
            force_this_asset = force_assets is True or (isinstance(force_assets, (list, tuple)) and mesh_id in force_assets)
            changed = mesh is None or mesh_fingerprint != signature or force_this_asset
            if changed:
                mesh = _import_fbx(obj, mesh_path, scene_id)
                collision_report[mesh_id] = _collision(mesh, obj)
                imported_count += 1
            elif old.get("signature") != signature:
                collision_report[mesh_id] = _collision(mesh, obj)
            if changed or old.get("material_hash") != obj["material_hash"]:
                for slot, material in enumerate(obj.get("materials", [])):
                    mesh.set_material(slot, material_assets[_material_key(material)])
                material_updates += 1
            if changed or old.get("material_hash") != obj["material_hash"] or old.get("signature") != signature:
                _save_asset(mesh)
            meshes[mesh_id] = mesh
            next_assets[mesh_id] = {"path": mesh_path, "signature": signature,
                                    "geometry_hash": obj["geometry_hash"], "material_hash": obj["material_hash"],
                                    "collision": obj["collision"]}
            journal["completed_assets"].append(mesh_id)
            write_json(journal_path, journal)
            if len(journal["completed_assets"]) % 25 == 0 or len(journal["completed_assets"]) == len(mesh_objects):
                progress = {"phase": "assets", "completed": len(journal["completed_assets"]),
                            "total": len(mesh_objects), "imported": imported_count, "revision": data["revision"]}
                write_json(saved_root() / "progress.json", progress)
                unreal.log(f"SceneBridge assets {progress['completed']}/{progress['total']}; imported {imported_count}")
        journal["phase"] = "actors"
        write_json(journal_path, journal)
        actor_system = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
        keep_ids = {c["id"] for c in plan["conflicts"] if policy == "keep_ue"}
        next_objects = {}
        changed_ids = set().union(*(set(plan[key]) for key in
                                    ("add", "geometry", "materials", "transform", "rename", "metadata")))
        moving_ids = set(plan["transform"]) | set(plan["delete"])
        actor_ids = {actor.get_path_name(): oid for oid, actor in actors.items()}
        detached_ids = set()
        with unreal.ScopedEditorTransaction("SceneBridge: " + data["scene_name"]):
            # Detach only affected hierarchy nodes. Unchanged actor properties
            # are not written, while moved parents cannot move a kept UE child.
            for oid, actor in actors.items():
                parent = actor.get_attach_parent_actor()
                affected_parent = False
                cursor = parent
                while cursor is not None:
                    if actor_ids.get(cursor.get_path_name()) in moving_ids:
                        affected_parent = True
                        break
                    cursor = cursor.get_attach_parent_actor()
                if parent and (oid in changed_ids or affected_parent):
                    actor.detach_from_actor(unreal.DetachmentRule.KEEP_WORLD,
                                            unreal.DetachmentRule.KEEP_WORLD,
                                            unreal.DetachmentRule.KEEP_WORLD)
                    detached_ids.add(oid)
            for obj in data["objects"]:
                oid = obj["id"]
                actor = actors.get(oid)
                if actor is None:
                    actor = actor_system.spawn_actor_from_class(unreal.StaticMeshActor,
                                                                unreal.Vector(*obj["location"]))
                    if actor is None:
                        raise BridgeError(f"Could not spawn {obj['name']}")
                    actors[oid] = actor
                if oid in changed_ids:
                    _assign_actor(actor, obj, meshes.get(obj["mesh_id"]), scene_id, oid in keep_ids)
            for obj in data["objects"]:
                pid = obj.get("parent_id")
                actor = actors[obj["id"]]
                if pid and (obj["id"] in detached_ids or obj["id"] in changed_ids):
                    actor.attach_to_actor(actors[pid], "", unreal.AttachmentRule.KEEP_WORLD,
                                          unreal.AttachmentRule.KEEP_WORLD, unreal.AttachmentRule.KEEP_WORLD,
                                          False)
                next_objects[obj["id"]] = {
                    "name": obj["name"], "mesh_id": obj["mesh_id"],
                    "geometry_hash": obj["geometry_hash"], "material_hash": obj["material_hash"],
                    "transform_hash": obj["transform_hash"], "fingerprint": object_fingerprint(obj),
                    "source_transform": _desired_transform(obj), "applied_transform": _transform(actor),
                    "ue_override": obj["id"] in keep_ids, "actor_path": actor.get_path_name(),
                }
            for oid in plan["delete"]:
                actor = actors[oid]
                tags = _tags(actor)
                if OWNER_TAG not in tags or SCENE_TAG + scene_id not in tags or OBJECT_TAG + oid not in tags:
                    raise BridgeError(f"Ownership changed before deletion of {oid}")
                if not actor_system.destroy_actor(actor):
                    raise BridgeError(f"Could not remove managed actor {oid}")
        journal["phase"] = "save_map"
        write_json(journal_path, journal)
        if not options.get("save", True):
            report["status"] = "applied_unsaved"
            report["warnings"].append("Map is intentionally unsaved; pending journal retained. State will commit after a saved sync.")
            journal["status"] = "applied_unsaved"
            write_json(journal_path, journal)
        else:
            if not unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level():
                raise BridgeError("Target map save failed; pending journal retained")
            new_state = {"schema_version": 1, "scene_id": scene_id, "scene_name": data["scene_name"],
                         "revision": data["revision"], "target_map": target, "namespace": namespace,
                         "manifest": str(path), "updated_at": time.time(),
                         "objects": next_objects, "assets": next_assets}
            write_json(state_path, new_state)
            journal["status"] = "committed"
            journal["phase"] = "complete"
            write_json(journal_path, journal)
            # Retain journal evidence while keeping pending distinct from committed.
            history = saved_root() / "history" / (token(scene_id) + "_last.json")
            write_json(history, journal)
            journal_path.unlink()
            report["status"] = "saved"
        report.update(imported_meshes=imported_count, material_assignments=material_updates,
                      object_count=len(next_objects), collisions=collision_report, state_path=str(state_path))
        report_path = saved_root() / "reports" / (token(scene_id) + "_last.json")
        write_json(report_path, report)
        unreal.log(f"SceneBridge: {report['status']}, {len(next_objects)} objects, {imported_count} meshes imported, "
                   f"{len(plan['delete'])} managed actors removed, {len(plan['conflicts'])} transform conflicts")
        return report
    except Exception as error:
        journal["status"] = "failed"
        journal["error"] = str(error)
        write_json(journal_path, journal)
        unreal.log_error(f"SceneBridge paused: {error}. Retry information: {journal_path}")
        raise
