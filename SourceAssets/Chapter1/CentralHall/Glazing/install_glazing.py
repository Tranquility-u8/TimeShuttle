"""Dress the curved city-facing curtain wall in the open Chapter 1 laboratory."""
import json
from pathlib import Path
import re
import runpy

import unreal as ue


HERE = Path(__file__).resolve().parent
DEST = "/Game/Environment/Chapter1/CentralHall/Glazing"
FOLDER = "Chapter1/CentralHall/Glazing"
TAG = "Chapter1CentralHallGlazing"
LAB = "/Game/Environment/Chapter1/ParticleLab/Materials/MI_LabShell"
FINISHES = {name: LAB + material for name, material in (
    ("Graphite", "Graphite"), ("Seal", "Seal"), ("Alloy", "Steel"), ("WallCool", "Shadow"))}
NAMES = tuple("SM_HallGlazing" + part + side for part in ("Frame", "Panes") for side in ("West", "East"))
FRAME_LABELS = {name: "Art_CH_Glazing_" + name.removeprefix("SM_HallGlazing") for name in NAMES}


def build_glass_graph(master, transmission, coverage, roughness, specular):
    # Native thin translucency transmits the city and reflects room lights independently.
    # A closed nine-centimetre pane must be single sided; otherwise each side attenuates
    # the same ray and the grazing-angle skyline darkens twice.
    edits = ue.MaterialEditingLibrary
    if master.get_editor_property("shading_model") == ue.MaterialShadingModel.MSM_THIN_TRANSLUCENT:
        master.set_editor_property("shading_model", ue.MaterialShadingModel.MSM_DEFAULT_LIT)
    edits.delete_all_material_expressions(master)
    master.set_editor_property("blend_mode", ue.BlendMode.BLEND_TRANSLUCENT)
    master.set_editor_property("translucency_lighting_mode", ue.TranslucencyLightingMode.TLM_SURFACE_PER_PIXEL_LIGHTING)
    master.set_editor_property("two_sided", False)
    master.set_editor_property("screen_space_reflections", True)
    master.set_editor_property("refraction_method", ue.RefractionMode.RM_NONE)
    master.set_editor_property("translucency_pass", ue.MaterialTranslucencyPass.MTP_BEFORE_DOF)

    def parameter(node_type, name, value, x, y):
        node = edits.create_material_expression(master, node_type, x, y)
        node.set_editor_property("parameter_name", name)
        node.set_editor_property("default_value", value)
        return node

    def output(node, prop):
        if not edits.connect_material_property(node, "", prop):
            raise RuntimeError("Unable to wire glass property " + str(prop))

    prop = ue.MaterialProperty
    scalar = ue.MaterialExpressionScalarParameter
    color = parameter(ue.MaterialExpressionVectorParameter, "PaneTransmission",
                      ue.LinearColor(*transmission, 1), -650, -340)
    cover = parameter(scalar, "CoatingCoverage", coverage, -650, -180)
    thin = edits.create_material_expression(master, ue.MaterialExpressionThinTranslucentMaterialOutput, -300, -340)
    inputs = edits.get_material_expression_input_names(thin)
    if len(inputs) != 2:
        raise RuntimeError("Unexpected thin-glass material pins: " + str(inputs))
    for source, pin in zip((color, cover), inputs):
        if not edits.connect_material_expressions(source, "", thin, str(pin)):
            raise RuntimeError("Unable to wire architectural glass " + str(pin))
    # Opacity in the thin-translucent model describes the opaque coating above the glass.
    # Setting it to zero preserves the view; CoatingCoverage controls the thin layer itself.
    no_paint = edits.create_material_expression(master, ue.MaterialExpressionConstant, -360, 240)
    no_paint.set_editor_property("r", 0.0)
    output(no_paint, prop.MP_OPACITY)
    output(parameter(scalar, "GlassRoughness", roughness, -360, 40), prop.MP_ROUGHNESS)
    output(parameter(scalar, "GlassSpecular", specular, -360, 140), prop.MP_SPECULAR)
    master.set_editor_property("shading_model", ue.MaterialShadingModel.MSM_THIN_TRANSLUCENT)
    edits.recompile_material(master)


def glass_instance(master, name, transmission, coverage, roughness, specular):
    edits = ue.MaterialEditingLibrary
    assets = ue.EditorAssetLibrary
    folder = DEST + "/Materials"
    path = folder + "/" + name
    if assets.does_asset_exist(path):
        instance = ue.load_asset(path)
    else:
        factory = ue.AssetToolsHelpers.get_asset_tools()
        instance = factory.create_asset(name, folder, ue.MaterialInstanceConstant,
                                        ue.MaterialInstanceConstantFactoryNew())
    if not isinstance(instance, ue.MaterialInstanceConstant):
        raise RuntimeError("Unable to load glass instance " + path)
    edits.set_material_instance_parent(instance, master)
    edits.set_material_instance_vector_parameter_value(instance, "PaneTransmission", ue.LinearColor(*transmission, 1))
    for parameter, value in (("CoatingCoverage", coverage), ("GlassRoughness", roughness), ("GlassSpecular", specular)):
        edits.set_material_instance_scalar_parameter_value(instance, parameter, value)
    edits.update_material_instance(instance)
    if not assets.save_loaded_asset(instance, False):
        raise RuntimeError("Could not save " + path)
    return instance


def glazing_material(transmission=(.74, .81, .85), coverage=.78, roughness=.16, specular=.34):
    """Prepare the exterior optical material; the independent guard uses the same parent."""
    assets = ue.EditorAssetLibrary
    edits = ue.MaterialEditingLibrary
    folder = DEST + "/Materials"
    if not assets.does_directory_exist(folder):
        assets.make_directory(folder)
    name = "M_HallCurtainGlass"
    path = folder + "/" + name
    if assets.does_asset_exist(path):
        master = ue.load_asset(path)
    else:
        factory = ue.AssetToolsHelpers.get_asset_tools()
        master = factory.create_asset(name, folder, ue.Material, ue.MaterialFactoryNew())
    if not isinstance(master, ue.Material):
        raise RuntimeError("Unable to load architectural glass: " + path)
    expected = {"CoatingCoverage", "GlassRoughness", "GlassSpecular"}
    complete = (master.get_editor_property("shading_model") == ue.MaterialShadingModel.MSM_THIN_TRANSLUCENT
                and expected.issubset(str(p) for p in edits.get_scalar_parameter_names(master))
                and "PaneTransmission" in [str(p) for p in edits.get_vector_parameter_names(master)]
                and edits.get_num_material_expressions(master) >= 6)
    if not complete:
        build_glass_graph(master, transmission, coverage, roughness, specular)
        if not assets.save_loaded_asset(master, False):
            raise RuntimeError("Could not save " + path)
    return glass_instance(master, "MI_HallCurtainGlass", transmission, coverage, roughness, specular)


def select_curtain_wall(actors):
    """Collect the outer curtain wall and only the glass infill of the upper guard."""
    groups = {"Glass": {}, "Mullion": {}, "Guard": {}}
    for actor in actors:
        label = actor.get_actor_label()
        match = re.fullmatch(r"Facade(Glass|Mullion)::[0-9]{3}", label)
        guard = re.fullmatch(r"Observation::[0-9]{3} Panel", label)
        if not match and not guard:
            continue
        p = actor.get_actor_location()
        group_name = "Guard" if guard else match.group(1)
        if abs(p.x) > 5000 or not -5350 <= p.y <= -3700 or abs(p.z - (595 if guard else 700)) > 1:
            continue
        group = groups[group_name]
        if label in group or not isinstance(actor, ue.StaticMeshActor):
            raise ValueError("Ambiguous facade actor: " + label)
        component = actor.static_mesh_component
        if not component.static_mesh or component.get_num_materials() != 1:
            raise ValueError("Unexpected facade mesh: " + label)
        group[label] = actor
    counts = [len(groups[group]) for group in ("Glass", "Mullion", "Guard")]
    if counts != [70, 33, 68]:
        raise ValueError(f"The surveyed facade has 70 panes, 33 mullions and 68 guard panels; found {counts}.")
    return groups


def import_frames(world, manifest, materials):
    importer = runpy.run_path(str(HERE.parent / "Environment/install_environment.py"))["import_mesh"]
    if set(manifest) != set(NAMES):
        raise ValueError("Unrecognized glass frame manifest: " + str(list(manifest)))
    for name, info in manifest.items():
        if (not (HERE / (name + ".fbx")).is_file() or len(info["pivot_cm"]) != 3
                or not set(info["slots"]).issubset(materials)):
            raise ValueError("Incomplete glass frame source: " + name)
    mesh_dir = DEST + "/Meshes"
    if not ue.EditorAssetLibrary.does_directory_exist(mesh_dir):
        ue.EditorAssetLibrary.make_directory(mesh_dir)
    # The shared importer reads the FBX material slot names via the legacy FBX factory.
    flag = "Interchange.FeatureFlags.Import.FBX"
    previous = ue.SystemLibrary.get_console_variable_int_value(flag)
    try:
        ue.SystemLibrary.execute_console_command(world, flag + " 0")
        return {name: importer(name, materials, world, manifest[name]["slots"],
                               source_dir=HERE, destination=DEST) for name in NAMES}
    finally:
        ue.SystemLibrary.execute_console_command(world, f"{flag} {previous}")


def install():
    editor = ue.get_editor_subsystem(ue.UnrealEditorSubsystem)
    world = editor.get_editor_world()
    if world.get_path_name() != "/Game/Maps/Map_LabV39.Map_LabV39":
        raise RuntimeError("Open Map_LabV39 before installing the glass frames.")
    if ue.get_editor_subsystem(ue.LevelEditorSubsystem).is_in_play_in_editor():
        raise RuntimeError("Exit play mode before installing the glass frames.")
    subsystem = ue.get_editor_subsystem(ue.EditorActorSubsystem)
    actors = subsystem.get_all_level_actors()
    facade = select_curtain_wall(actors)
    existing = {}
    for actor in actors:
        label = actor.get_actor_label()
        if label in FRAME_LABELS.values():
            if (label in existing or ue.Name(TAG) not in actor.tags
                    or not isinstance(actor, ue.StaticMeshActor)):
                raise ValueError("Another actor uses glass frame label " + label)
            existing[label] = actor
    materials = {slot: ue.load_asset(path) for slot, path in FINISHES.items()}
    if not all(materials.values()):
        raise RuntimeError("A laboratory frame finish is missing.")
    manifest = json.loads((HERE / "glass_frames.json").read_text(encoding="utf8"))
    manifest.update(json.loads((HERE / "glass_panes.json").read_text(encoding="utf8")))
    glass = ue.load_asset(DEST + "/Materials/MI_HallCurtainGlass") or glazing_material()
    guard_glass = ue.load_asset(DEST + "/Materials/MI_HallGuardLaminatedGlass")
    if not guard_glass:
        guard_glass = glass_instance(glass.get_editor_property("parent"), "MI_HallGuardLaminatedGlass",
                                     (.85, .90, .93), .67, .20, .26)
    materials["Pane"] = glass
    gallery = runpy.run_path(str(HERE / "install_gallery_edge.py"))
    frames = import_frames(world, manifest, materials)
    for mesh in frames.values():
        gallery["enable_surface_collision"](mesh)
    report = {"architecture": {}, "panes": [], "mullions": [], "guard_panes": [], "material_changes": {},
              "glass_material": glass.get_path_name(), "guard_material": guard_glass.get_path_name()}
    with ue.ScopedEditorTransaction("Dress the laboratory atrium curtain wall"):
        for group, finish, key in (("Glass", glass, "panes"), ("Mullion", materials["Graphite"], "mullions"),
                                   ("Guard", guard_glass, "guard_panes")):
            for label, actor in sorted(facade[group].items()):
                component = actor.static_mesh_component
                material = component.get_material(0)
                if material != finish or group == "Mullion":
                    actor.modify()
                    component.modify()
                if material != finish:
                    report["material_changes"][label] = material.get_name() if material else None
                    component.set_material(0, finish)
                if group == "Mullion":
                    component.set_lighting_channels(False, True, False)
                if group in ("Glass", "Mullion"):
                    # Retire both parts of the irregular bays so traces hit the visible frame or glass.
                    actor.modify()
                    component.modify()
                    component.set_visibility(False)
                    component.set_hidden_in_game(True)
                    component.set_editor_property("can_ever_affect_navigation", False)
                    component.set_collision_profile_name("NoCollision")
                    actor.set_actor_enable_collision(False)
                report[key].append(label)

        for name in NAMES:
            label = FRAME_LABELS[name]
            position = ue.Vector(*manifest[name]["pivot_cm"])
            actor = existing.get(label)
            if not actor:
                actor = subsystem.spawn_actor_from_class(ue.StaticMeshActor, position, ue.Rotator())
                actor.set_actor_label(label)
                actor.tags = [ue.Name(TAG)]
            actor.modify()
            actor.set_folder_path(FOLDER)
            actor.set_actor_location_and_rotation(position, ue.Rotator(), False, True)
            actor.set_actor_scale3d(ue.Vector(1, 1, 1))
            component = actor.static_mesh_component
            component.modify()
            component.set_static_mesh(frames[name])
            component.set_editor_property("override_materials", [])
            pane = name.startswith("SM_HallGlazingPanes")
            component.set_lighting_channels(pane, True, False)
            component.set_editor_property("cast_shadow", False)
            component.set_collision_profile_name("BlockAll")
            component.set_editor_property("can_ever_affect_navigation", True)
            actor.set_actor_enable_collision(True)
            report["architecture"][label] = frames[name].get_path_name()
    report["gallery"] = gallery["install"]()
    return report
