"""Install one collision-free, locally rendered city panorama in Map_LabV39."""
import hashlib
from pathlib import Path
import unreal as u

ROOT = Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir()))/"SourceAssets/Chapter1/CentralHall/CityVista"
BASE = "/Game/Environment/Chapter1/CentralHall"
TEX, MAT, MESH = BASE+"/Textures", BASE+"/Materials", BASE+"/Meshes"
LIB, ME = u.EditorAssetLibrary, u.MaterialEditingLibrary
COLORS = {
    "Sky": (1,1,1), "NearWall": (.022,.041,.066), "NearEnd": (.016,.031,.050),
    "NearRim": (.042,.068,.091), "MidWall": (.044,.077,.120),
    "MidEnd": (.035,.064,.101), "MidRim": (.066,.102,.142),
    "Window": (.21,.205,.158), "Glazing": (.041,.069,.104),
}


def load(path):
    return LIB.load_asset(path) if LIB.does_asset_exist(path) else None


def import_source(name,extension,destination,options=None):
    file=ROOT/(name+"."+extension)
    digest=hashlib.sha256(file.read_bytes()).hexdigest()
    path=destination+"/"+name
    obj=load(path)
    if obj and str(LIB.get_metadata_tag(obj,"CityVistaSource"))==digest:
        return obj
    task=u.AssetImportTask()
    props=dict(filename=str(file), destination_path=destination,destination_name=name,
               automated=True,save=False,replace_existing=True,replace_existing_settings=True)
    if options:
        props["options"]=options
    for k,v in props.items():
        task.set_editor_property(k,v)
    u.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    obj=load(path)
    assert task.imported_object_paths and obj, (name,task.imported_object_paths)
    LIB.set_metadata_tag(obj,"CityVistaSource",digest)
    return obj


def make_master(white):
    name="M_CH_CityVista"
    mat=load(MAT+"/"+name)
    if mat:
        return mat
    mat=u.AssetToolsHelpers.get_asset_tools().create_asset(name,MAT,u.Material,u.MaterialFactoryNew())
    assert mat,name
    mat.set_editor_property("shading_model",u.MaterialShadingModel.MSM_UNLIT)
    mat.set_editor_property("two_sided",True)
    texture=ME.create_material_expression(mat,u.MaterialExpressionTextureSampleParameter2D,-800,-100)
    texture.set_editor_property("parameter_name","VistaTexture")
    texture.set_editor_property("texture",white)
    tint=ME.create_material_expression(mat,u.MaterialExpressionVectorParameter,-800,120)
    tint.set_editor_property("parameter_name","Tint")
    tint.set_editor_property("default_value",u.LinearColor(1,1,1,1))
    mix=ME.create_material_expression(mat,u.MaterialExpressionMultiply,-550,0)
    assert ME.connect_material_expressions(texture,"RGB",mix,"A")
    assert ME.connect_material_expressions(tint,"",mix,"B")
    gain=ME.create_material_expression(mat,u.MaterialExpressionScalarParameter,-510,200)
    gain.set_editor_property("parameter_name","VistaBrightness")
    gain.set_editor_property("default_value",.8)
    out=ME.create_material_expression(mat,u.MaterialExpressionMultiply,-290,0)
    assert ME.connect_material_expressions(mix,"",out,"A")
    assert ME.connect_material_expressions(gain,"",out,"B")
    assert ME.connect_material_property(out,"",u.MaterialProperty.MP_EMISSIVE_COLOR)
    ME.recompile_material(mat)
    assert LIB.save_loaded_asset(mat,False)
    return mat


def install(brightness=460.0):
    editor=u.get_editor_subsystem(u.UnrealEditorSubsystem)
    actors=u.get_editor_subsystem(u.EditorActorSubsystem)
    world=editor.get_editor_world()
    assert world.get_path_name().split(".")[0]=="/Game/Maps/Map_LabV39",world.get_path_name()
    for folder in (TEX,MAT,MESH):
        if not LIB.does_directory_exist(folder):
            LIB.make_directory(folder)
    texture=import_source("T_CH_BlueHourCity","png",TEX)
    texture.set_editor_property("srgb",True)
    texture.set_editor_property("address_x",u.TextureAddress.TA_CLAMP)
    texture.set_editor_property("address_y",u.TextureAddress.TA_CLAMP)
    assert LIB.save_loaded_asset(texture,False)
    white=load("/Engine/EngineResources/WhiteSquareTexture")
    assert white,"Engine white texture"
    master=make_master(white)
    materials={}
    for slot,rgb in COLORS.items():
        name="MI_CH_Vista"+slot
        inst=load(MAT+"/"+name)
        if not inst:
            inst=u.AssetToolsHelpers.get_asset_tools().create_asset(name,MAT,u.MaterialInstanceConstant,
                                                                   u.MaterialInstanceConstantFactoryNew())
        ME.set_material_instance_parent(inst,master)
        ME.set_material_instance_texture_parameter_value(inst,"VistaTexture",texture if slot=="Sky" else white)
        ME.set_material_instance_vector_parameter_value(inst,"Tint",u.LinearColor(*rgb,1))
        ME.set_material_instance_scalar_parameter_value(inst,"VistaBrightness",brightness)
        ME.update_material_instance(inst)
        assert LIB.save_loaded_asset(inst,False),name
        materials[slot]=inst
    flag="Interchange.FeatureFlags.Import.FBX"
    previous=u.SystemLibrary.get_console_variable_int_value(flag)
    try:
        u.SystemLibrary.execute_console_command(world,flag+" 0")
        options=u.FbxImportUI()
        for k,v in dict(automated_import_should_detect_type=False,mesh_type_to_import=u.FBXImportType.FBXIT_STATIC_MESH,
                        import_mesh=True,import_as_skeletal=False,import_materials=False,import_textures=False,
                        import_animations=False).items():
            options.set_editor_property(k,v)
        for k,v in dict(combine_meshes=True,auto_generate_collision=False,convert_scene=True,convert_scene_unit=True,
                        force_front_x_axis=False,generate_lightmap_u_vs=False,
                        normal_import_method=u.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS).items():
            options.static_mesh_import_data.set_editor_property(k,v)
        mesh=import_source("SM_CH_CityVista","fbx",MESH,options)
    finally:
        u.SystemLibrary.execute_console_command(world,flag+" "+str(previous))
    slots=[str(s.get_editor_property("imported_material_slot_name")) for s in mesh.static_materials]
    assert set(slots)==set(materials),slots
    for i,slot in enumerate(slots):
        mesh.set_material(i,materials[slot])
    mesh.set_editor_property("allow_cpu_access",True)
    assert LIB.save_loaded_asset(mesh,False)
    label="Art_CH_CityVista"
    existing=[a for a in actors.get_all_level_actors() if a.get_actor_label()==label]
    assert len(existing)<=1, existing
    location=u.Vector(0,-2500,0)
    rot=u.Rotator(roll=0,pitch=0,yaw=0)
    actor=existing[0] if existing else actors.spawn_actor_from_class(u.StaticMeshActor,location,rot)
    actor.modify()
    actor.set_actor_label(label)
    actor.set_folder_path("Chapter1/CentralHall/ExteriorVista")
    actor.set_actor_location_and_rotation(location,rot,False,True)
    comp=actor.static_mesh_component
    comp.modify()
    comp.set_static_mesh(mesh)
    comp.set_editor_property("override_materials",[])
    comp.set_collision_profile_name("NoCollision")
    comp.set_editor_property("can_ever_affect_navigation",False)
    comp.set_editor_property("cast_shadow",False)
    comp.set_editor_property("affect_distance_field_lighting",False)
    comp.set_editor_property("affect_dynamic_indirect_lighting",False)
    comp.set_editor_property("visible_in_ray_tracing",False)
    actor.set_actor_enable_collision(False)
    return {"actor":actor.get_path_name(),"mesh":mesh.get_path_name(),"brightness":brightness}
