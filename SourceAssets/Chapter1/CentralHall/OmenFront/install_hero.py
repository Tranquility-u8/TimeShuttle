"""Install the four Omen entrance assets in the currently open Map_LabV39.

Call install() from UE editor Python. The caller controls the final map save.
"""
import hashlib
import json
from pathlib import Path

import unreal as ue

ROOT = Path(ue.Paths.convert_relative_path_to_full(ue.Paths.project_dir())) / "SourceAssets/Chapter1/CentralHall/OmenFront"
DESTINATION = "/Game/Environment/Chapter1/CentralHall/Meshes"
FOLDER = "Chapter1/CentralHall/OmenFront"
SHA_TAG = "TimeShuttler.OmenFrontSource"


def load_meshes(world, data):
    library = ue.EditorAssetLibrary
    meshes = {}
    materials = {slot:ue.load_asset(path) for slot,path in data["material_slots"].items()}
    assert all(materials.values()), materials
    if not library.does_directory_exist(DESTINATION):
        library.make_directory(DESTINATION)
    flag = "Interchange.FeatureFlags.Import.FBX"
    previous_flag = ue.SystemLibrary.get_console_variable_int_value(flag)
    try:
        ue.SystemLibrary.execute_console_command(world,f"{flag} 0")
        for name, model in data["models"].items():
            path = DESTINATION+"/"+name
            source = ROOT/model["fbx"]
            digest = hashlib.sha256(source.read_bytes()).hexdigest()
            mesh = ue.load_asset(path) if library.does_asset_exist(path) else None
            updated = not mesh or str(library.get_metadata_tag(mesh,SHA_TAG))!=digest
            if updated:
                options = ue.FbxImportUI()
                for key,value in {
                    "automated_import_should_detect_type":False,"mesh_type_to_import":ue.FBXImportType.FBXIT_STATIC_MESH,
                    "import_mesh":True,"import_animations":False,"import_as_skeletal":False,
                    "import_materials":False,"import_textures":False,
                }.items():
                    options.set_editor_property(key,value)
                for key,value in {
                    "combine_meshes":True,"auto_generate_collision":False,
                    "convert_scene":True, "convert_scene_unit":True, "force_front_x_axis":False,
                    "generate_lightmap_u_vs":False,
                    "normal_import_method":ue.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS,
                }.items():
                    options.static_mesh_import_data.set_editor_property(key,value)
                task = ue.AssetImportTask()
                for key,value in {"filename":str(source),"destination_path":DESTINATION,
                                  "destination_name":name,"automated":True,"save":False,
                                  "replace_existing":True,"replace_existing_settings":True,
                                  "options":options}.items():
                    task.set_editor_property(key,value)
                ue.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
                assert task.imported_object_paths,(name,"FBX import failed")
                mesh=ue.load_asset(path)
                assert mesh is not None,name
            slots = [str(s.get_editor_property("imported_material_slot_name")) for s in mesh.static_materials]
            assert set(slots)==set(model["slots"]),(name,slots,model["slots"])
            for index,slot in enumerate(slots):
                if mesh.get_material(index)!=materials[slot]:
                    mesh.set_material(index,materials[slot])
                    updated=True
            if not mesh.get_editor_property("allow_cpu_access"):
                mesh.set_editor_property("allow_cpu_access",True)
                updated=True
            bounds=mesh.get_bounds()
            bmin,bmax=model["bounds_cm"]
            for i,axis in enumerate(("x","y","z")):
                center=getattr(bounds.origin,axis)
                extent=getattr(bounds.box_extent,axis)
                assert abs(center-extent-bmin[i])<1.0 and abs(center+extent-bmax[i])<1.0, (name,axis,center,extent,bmin,bmax)
            if updated:
                library.set_metadata_tag(mesh,SHA_TAG,digest)
                assert library.save_loaded_asset(mesh,False),name
            meshes[name]=mesh
    finally:
        ue.SystemLibrary.execute_console_command(world,f"{flag} {previous_flag}")
    return meshes


def install():
    editor = ue.get_editor_subsystem(ue.UnrealEditorSubsystem)
    actors = ue.get_editor_subsystem(ue.EditorActorSubsystem)
    world = editor.get_editor_world()
    assert world.get_path_name().split(".")[0]=="/Game/Maps/Map_LabV39",world.get_path_name()
    data=json.loads((ROOT/"placement.json").read_text(encoding="utf8"))
    all_actors=actors.get_all_level_actors()
    original={}
    for name,label in data["original_visuals"].items():
        found=[a for a in all_actors if a.get_actor_label()==label]
        assert len(found)==1 and isinstance(found[0],ue.StaticMeshActor),(label,found)
        original[name]=found[0]
    meshes=load_meshes(world,data)
    placed={}
    with ue.ScopedEditorTransaction("Dress Omen entrance and reception"):
        for name,model in data["models"].items():
            label="Art_CH_"+name.removeprefix("SM_CH_")
            visual=[a for a in all_actors if a.get_actor_label()==label]
            assert len(visual)<=1,(label,visual)
            loc=ue.Vector(*model["location"])
            rot=ue.Rotator(roll=0,pitch=0,yaw=0)
            actor=visual[0] if visual else actors.spawn_actor_from_class(ue.StaticMeshActor,loc,rot)
            actor.modify()
            actor.set_actor_label(label)
            actor.set_folder_path(FOLDER)
            component=actor.static_mesh_component
            component.modify()
            component.set_static_mesh(meshes[name])
            component.set_editor_property("override_materials",[])
            component.set_collision_profile_name("NoCollision")
            component.set_editor_property("can_ever_affect_navigation",False)
            actor.set_actor_enable_collision(False)
            actor.set_actor_location_and_rotation(loc,rot,False,True)
            actor.set_actor_scale3d(ue.Vector(1,1,1))
            placed[name]=actor.get_path_name()
        # The gameplay blocks keep their original collisions and their GUIDs.
        for actor in original.values():
            actor.modify()
            component=actor.static_mesh_component
            component.modify()
            component.set_visibility(False,True)
            component.set_hidden_in_game(True,True)
    return {"actors":placed,"hidden_original_visuals":data["original_visuals"]}
