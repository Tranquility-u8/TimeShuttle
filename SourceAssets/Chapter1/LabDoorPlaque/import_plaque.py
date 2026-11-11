"""Import the door plaque frame using UE's FBX importer and the chapter's surface master."""
import hashlib
from pathlib import Path

import unreal as ue


ROOT = "/Game/Environment/Chapter1/LabDoorPlaque"
MATERIALS = ROOT + "/Materials"
SURFACE = "/Game/Environment/Chapter1/ParticleLab/Materials/M_LabSurface"
LIB = ue.EditorAssetLibrary
EDIT = ue.MaterialEditingLibrary
TOOLS = ue.AssetToolsHelpers.get_asset_tools()


def save(asset):
    if not LIB.save_loaded_asset(asset, only_if_is_dirty=False):
        raise RuntimeError("Could not save " + asset.get_path_name())
    return asset


def surface(name, rgb, metallic, roughness):
    asset_name = "MI_Plaque" + name
    instance = LIB.load_asset(MATERIALS + "/" + asset_name) if LIB.does_asset_exist(MATERIALS + "/" + asset_name) else None
    if instance is None:
        instance = TOOLS.create_asset(asset_name, MATERIALS, ue.MaterialInstanceConstant, ue.MaterialInstanceConstantFactoryNew())
    parent = LIB.load_asset(SURFACE)
    if not parent or not instance:
        raise RuntimeError("Missing laboratory surface or plaque material instance: " + name)
    EDIT.set_material_instance_parent(instance, parent)
    EDIT.set_material_instance_vector_parameter_value(instance, "Tint", ue.LinearColor(*rgb, 1))
    EDIT.set_material_instance_vector_parameter_value(instance, "Emission", ue.LinearColor(0, 0, 0, 1))
    EDIT.set_material_instance_scalar_parameter_value(instance, "Metallic", metallic)
    EDIT.set_material_instance_scalar_parameter_value(instance, "Roughness", roughness)
    EDIT.update_material_instance(instance)
    return save(instance)


def backpainted_glass():
    # Back-painted signage needs two specular lobes but transmits no view of the wall.
    name = "M_PlaqueSmokedGlass"
    path = MATERIALS + "/" + name
    if LIB.does_asset_exist(path):
        return LIB.load_asset(path)
    mat = TOOLS.create_asset(name, MATERIALS, ue.Material, ue.MaterialFactoryNew())
    mat.set_editor_property("shading_model", ue.MaterialShadingModel.MSM_CLEAR_COAT)
    prop = ue.MaterialProperty
    tint = EDIT.create_material_expression(mat, ue.MaterialExpressionConstant3Vector, -400, -170)
    tint.set_editor_property("constant", ue.LinearColor(.013, .052, .056, 1))
    assert EDIT.connect_material_property(tint, "", prop.MP_BASE_COLOR)
    # The native clear coat defaults give the polished outer face a 0.1 roughness.
    for index, (target, value) in enumerate(((prop.MP_METALLIC, .08), (prop.MP_ROUGHNESS, .19))):
        node = EDIT.create_material_expression(mat, ue.MaterialExpressionConstant, -400, index * 110)
        node.set_editor_property("r", value)
        assert EDIT.connect_material_property(node, "", target)
    EDIT.recompile_material(mat)
    return save(mat)


def build():
    project = Path(ue.Paths.convert_relative_path_to_full(ue.Paths.project_dir()))
    source = project / "SourceAssets/Chapter1/LabDoorPlaque/SM_LabDoorPlaque.fbx"
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    materials = {
        "FrameGraphite": surface("FrameGraphite", (.038, .046, .049), .65, .34),
        "SmokedGlass": backpainted_glass(),
        "PolishedGlassEdge": surface("GlassEdge", (.051, .193, .193), .08, .18),
        "ClipAlloy": surface("ClipAlloy", (.45, .47, .47), .84, .28),
    }
    path = ROOT + "/" + source.stem
    mesh = LIB.load_asset(path) if LIB.does_asset_exist(path) else None
    if not mesh or str(LIB.get_metadata_tag(mesh, "PlaqueSourceSHA256")) != digest:
        options = ue.FbxImportUI()
        options.set_editor_property("automated_import_should_detect_type", False)
        for k, v in dict(mesh_type_to_import=ue.FBXImportType.FBXIT_STATIC_MESH, import_mesh=True,
                         import_materials=False, import_textures=False, import_animations=False, import_as_skeletal=False).items():
            options.set_editor_property(k, v)
        data = options.static_mesh_import_data
        for k, v in dict(combine_meshes=True, auto_generate_collision=False, convert_scene=True,
                         convert_scene_unit=True, force_front_x_axis=False, generate_lightmap_u_vs=True,
                         normal_import_method=ue.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS).items():
            data.set_editor_property(k, v)
        task = ue.AssetImportTask()
        for k, v in dict(filename=str(source), destination_path=ROOT, destination_name=source.stem,
                         automated=True, replace_existing=True, replace_existing_settings=True,
                         save=False, options=options).items():
            task.set_editor_property(k, v)
        world = ue.get_editor_subsystem(ue.UnrealEditorSubsystem).get_editor_world()
        flag = "Interchange.FeatureFlags.Import.FBX"
        original = ue.SystemLibrary.get_console_variable_int_value(flag)
        ue.SystemLibrary.execute_console_command(world, flag + " 0")
        try:
            TOOLS.import_asset_tasks([task])
        finally:
            ue.SystemLibrary.execute_console_command(world, flag + " " + str(original))
        mesh = LIB.load_asset(path)
    assert isinstance(mesh, ue.StaticMesh), path
    slots = [str(slot.get_editor_property("imported_material_slot_name")) for slot in mesh.static_materials]
    assert len(slots) == len(materials) and set(slots) == set(materials), slots
    for i, name in enumerate(slots):
        mesh.set_material(i, materials[name])
    bounds = mesh.get_bounds()
    extent = bounds.box_extent
    assert abs(extent.y - 30) < .2 and abs(extent.z - 9) < .2 and 0 < extent.x < 1.7, bounds
    assert abs(bounds.origin.x - extent.x) < .12 and abs(bounds.origin.y) < .12, bounds
    LIB.set_metadata_tag(mesh, "PlaqueSourceSHA256", digest)
    save(mesh)
    ue.log("LAB_PLAQUE_MESH_READY %s tris=%s slots=%s bounds=%s" % (path, mesh.get_num_triangles(0), slots, bounds))
    return mesh


if __name__ == "__main__":
    build()
