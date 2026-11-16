"""Install the finishes at both glass-side links into the open Map_LabV39."""
import json
from pathlib import Path
import runpy

import unreal as ue


HERE = Path(__file__).resolve().parent
DEST = "/Game/Environment/Chapter1/CentralHall/GlassSideLinks"
FOLDER = "Chapter1/CentralHall/GlassSideLinks"
TAG = "Chapter1CentralHallGlassSideLinks"
HALL = "/Game/Environment/Chapter1/CentralHall/Environment/Materials/MI_Hall"
LAB = "/Game/Environment/Chapter1/ParticleLab/Materials/MI_LabShell"
MATERIALS = {
    "Floor": HALL + "Paving",
    "FloorAlt": HALL + "PavingInset",
    "Joint": HALL + "Seam",
    "Panel": LAB + "Panel",
    "WallCool": LAB + "Shadow",
    "Graphite": LAB + "Graphite",
    "Seal": LAB + "Seal",
    "Alloy": LAB + "Steel",
}


def import_finishes(world, manifest):
    importer = runpy.run_path(str(HERE.parent / "Environment" / "install_environment.py"))["import_mesh"]
    materials = {slot: ue.load_asset(MATERIALS[slot]) for info in manifest.values() for slot in info["slots"]}
    if not all(materials.values()):
        raise ValueError([MATERIALS[slot] for slot, value in materials.items() if not value])
    for name in manifest:
        if not (HERE / (name + ".fbx")).is_file():
            raise FileNotFoundError(HERE / (name + ".fbx"))
    if not ue.EditorAssetLibrary.does_directory_exist(DEST + "/Meshes"):
        ue.EditorAssetLibrary.make_directory(DEST + "/Meshes")
    flag = "Interchange.FeatureFlags.Import.FBX"
    previous = ue.SystemLibrary.get_console_variable_int_value(flag)
    try:
        ue.SystemLibrary.execute_console_command(world, flag + " 0")
        return {name: importer(name, materials, world, info["slots"], source_dir=HERE, destination=DEST)
                for name, info in manifest.items()}
    finally:
        ue.SystemLibrary.execute_console_command(world, f"{flag} {previous}")


def place(subsystem, existing, actor_type, name, location, rotation):
    label = "Art_CH_GlassSide_" + name
    actor = existing.get(label)
    if actor:
        if not isinstance(actor, actor_type) or ue.Name(TAG) not in actor.tags:
            raise ValueError("Another actor already uses " + label)
    else:
        actor = subsystem.spawn_actor_from_class(actor_type, location, rotation)
        actor.set_actor_label(label)
        actor.tags = [ue.Name(TAG)]
        existing[label] = actor
    actor.modify()
    actor.set_folder_path(FOLDER)
    actor.set_actor_location_and_rotation(location, rotation, False, True)
    return actor


def add_bounce(subsystem, actors, name, position, target, size, lumens, color, reach):
    location = ue.Vector(*position)
    rotation = ue.MathLibrary.find_look_at_rotation(location, ue.Vector(*target))
    actor = place(subsystem, actors, ue.RectLight, name, location, rotation)
    light = actor.rect_light_component
    light.modify()
    light.set_mobility(ue.ComponentMobility.MOVABLE)
    light.set_lighting_channels(False, True, False)
    light.set_source_width(float(size[0]))
    light.set_source_height(float(size[1]))
    light.set_attenuation_radius(float(reach))
    light.set_intensity_units(ue.LightUnits.LUMENS)
    light.set_intensity(float(lumens))
    light.set_light_color(ue.LinearColor(*color, 1.0), False)
    light.set_cast_shadows(False)
    # These lights represent diffuse light returning from the existing room and glazing.
    light.set_editor_property("specular_scale", 0.0)
    light.set_editor_property("indirect_lighting_intensity", 0.0)
    return actor.get_actor_label()


def install():
    world = ue.get_editor_subsystem(ue.UnrealEditorSubsystem).get_editor_world()
    if world.get_path_name().split(".")[0] != "/Game/Maps/Map_LabV39":
        raise ValueError(world.get_path_name())
    if ue.get_editor_subsystem(ue.LevelEditorSubsystem).is_in_play_in_editor():
        raise RuntimeError("Exit play mode before installing the links")
    subsystem = ue.get_editor_subsystem(ue.EditorActorSubsystem)
    actors = {}
    for actor in subsystem.get_all_level_actors():
        label = actor.get_actor_label()
        if label.startswith("Art_CH_GlassSide_") and label in actors:
            raise ValueError("Duplicate glass-side finish: " + label)
        actors[label] = actor
    manifest = json.loads((HERE / "glass_links.json").read_text(encoding="utf8"))
    expected = {"SM_HallGlassLink" + part + side for part in ("Wall", "Floor") for side in ("West", "East")}
    if set(manifest) != expected:
        raise ValueError(sorted(manifest))
    benches = {}
    for index in range(26, 30):
        label = f"R17_Furniture_{index:03}_bench"
        actor = actors.get(label)
        if not isinstance(actor, ue.StaticMeshActor) or not actor.static_mesh_component.static_mesh:
            raise ValueError("Missing window bench: " + label)
        benches[label] = actor
    meshes = import_finishes(world, manifest)
    report = {"architecture": {}, "local_lights": {}, "window_benches": []}
    with ue.ScopedEditorTransaction("Finish the glass-side hall connections"):
        for name, mesh in meshes.items():
            pivot = ue.Vector(*manifest[name]["pivot_cm"])
            actor = place(subsystem, actors, ue.StaticMeshActor, name.removeprefix("SM_HallGlassLink"),
                          pivot, ue.Rotator())
            actor.set_actor_scale3d(ue.Vector(1, 1, 1))
            component = actor.static_mesh_component
            component.modify()
            component.set_static_mesh(mesh)
            component.set_editor_property("override_materials", [])
            component.set_editor_property("cast_shadow", False)
            component.set_editor_property("can_ever_affect_navigation", False)
            component.set_collision_profile_name("NoCollision")
            actor.set_actor_enable_collision(False)
            # Use the same indoor receivers as SM_HallAtriumFloor across the joint at x=±1884.
            component.set_lighting_channels(False, True, False)
            report["architecture"][actor.get_actor_label()] = mesh.get_path_name()

        for label, bench in benches.items():
            bench.modify()
            component = bench.static_mesh_component
            component.modify()
            component.set_lighting_channels(False, True, False)
            report["window_benches"].append(label)

        for side, sign in (("East", 1), ("West", -1)):
            # Inner return lights run along the elevator door faces. The outer
            # glazing lights overlap the existing floor and taper down the curved walk.
            for level, source_z, target_z, strength in (("Lower", 435, 97, .62), ("Upper", 1190, 687, 1.0)):
                for zone, xy, aim, size, flux, tint, reach in (
                        ("LiftReturn", (1270, -3540), (2300, -3970), (600, 122),
                         43000, (.95, .91, .85), 1750),
                        ("WindowReturn", (3180, -4630), (3230, -4140), (1180, 165),
                         88000, (.82, .90, 1.0), 2160)):
                    position = (sign * xy[0], xy[1], source_z)
                    target = (sign * aim[0], aim[1], target_z)
                    lumens = round(flux * strength)
                    label = add_bounce(subsystem, actors, side + level + zone, position, target,
                                       size, lumens, tint, reach)
                    report["local_lights"][label] = {"position": list(position), "lumens": lumens}
    return report
