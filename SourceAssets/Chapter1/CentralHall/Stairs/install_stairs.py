"""Install the open stair flights and smoke glass in the current Map_LabV39 editor world.

Call install_stairs() inside the editor after the map has been backed up. The caller saves the map.
"""
from pathlib import Path

import unreal as u


SOURCE = Path(__file__).resolve().parent / 'SM_CH_OpenFlight.fbx'
DEST = '/Game/Environment/Chapter1/CentralHall'
PALETTE = '/Game/Environment/Chapter1/TemporalCalibration/Materials/MI_'
SLOTS = ('TC_Floor', 'TC_Skirting', 'TC_Graphite', 'TC_Brushed', 'TC_Support')
ED = u.EditorAssetLibrary


def load(path):
    asset = ED.load_asset(path)
    if not asset:
        raise RuntimeError('Missing stair asset: ' + path)
    return asset


def save(asset):
    if not ED.save_loaded_asset(asset, only_if_is_dirty=False):
        raise RuntimeError('Unable to save ' + asset.get_path_name())


def flight_mesh(world, palette):
    directory = DEST + '/Meshes'
    path = directory + '/' + SOURCE.stem
    if not ED.does_asset_exist(path):
        task = u.AssetImportTask()
        options = u.FbxImportUI()
        for k,v in dict(automated_import_should_detect_type=False,mesh_type_to_import=u.FBXImportType.FBXIT_STATIC_MESH,
                        import_mesh=True,import_materials=False,import_textures=False,import_animations=False,
                        import_as_skeletal=False).items():
            options.set_editor_property(k,v)
        for k,v in dict(combine_meshes=True,auto_generate_collision=False,convert_scene=True,convert_scene_unit=True,
                        force_front_x_axis=False,generate_lightmap_u_vs=True,
                        normal_import_method=u.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS).items():
            options.static_mesh_import_data.set_editor_property(k,v)
        for k,v in dict(filename=str(SOURCE),destination_path=directory,destination_name=SOURCE.stem,
                        automated=True,replace_existing=False,save=False,options=options).items():
            task.set_editor_property(k,v)
        flag = 'Interchange.FeatureFlags.Import.FBX'
        previous = u.SystemLibrary.get_console_variable_int_value(flag)
        u.SystemLibrary.execute_console_command(world,flag+' 0')
        try:
            u.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
        finally:
            u.SystemLibrary.execute_console_command(world,flag+' '+str(previous))
    mesh = load(path)
    bb = mesh.get_bounding_box()
    if abs(bb.min.x)>.75 or abs(bb.max.x-960)>.75 or abs(bb.min.z)>.75 or abs(bb.max.z-653.15)>2:
        raise RuntimeError('Unexpected stair FBX import basis/scale: '+str((bb.min,bb.max)))
    slots = [str(s.get_editor_property('imported_material_slot_name')) for s in mesh.static_materials]
    if set(slots) != set(SLOTS):
        raise RuntimeError('Unexpected tread material slots: '+str(slots))
    mesh.modify()
    mesh.set_editor_property('allow_cpu_access',True)
    for i,key in enumerate(slots):
        mesh.set_material(i,palette[key])
    save(mesh)
    return mesh


def gallery_glass():
    directory = DEST+'/Materials'
    name = 'MI_CH_GallerySmokeGlass'
    path = directory+'/'+name
    if ED.does_asset_exist(path):
        return load(path)
    asset = u.AssetToolsHelpers.get_asset_tools().create_asset(
        name,directory,u.MaterialInstanceConstant,u.MaterialInstanceConstantFactoryNew())
    edit = u.MaterialEditingLibrary
    edit.set_material_instance_parent(asset,load('/Game/Environment/Chapter1/ParticleLab/Materials/M_LabGlass'))
    edit.set_material_instance_vector_parameter_value(asset,'Tint',u.LinearColor(.105,.145,.156,1))
    for parameter,value in [('Metallic',.08),('Roughness',.18),('Opacity',.31)]:
        edit.set_material_instance_scalar_parameter_value(asset,parameter,value)
    edit.update_material_instance(asset)
    save(asset)
    return asset


def install_stairs():
    world = u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
    if world.get_path_name().split('.')[0] != '/Game/Maps/Map_LabV39':
        raise RuntimeError('Stair survey is for Map_LabV39; current world is '+world.get_path_name())
    subsystem = u.get_editor_subsystem(u.EditorActorSubsystem)
    actors = {a.get_actor_label():a for a in subsystem.get_all_level_actors()}
    surveyed = []
    for stair, direction in [('S1',-1),('S2',1),('S3',-1),('S4',1)]:
        base = actors['Stair::'+stair]
        origins = [base]
        for suffix in ('Handrail 0','Handrail 1','SidePanel 0','SidePanel 1'):
            origins.append(actors[stair+' '+suffix])
        center, extent = base.get_actor_bounds(False)
        if max(abs(extent.x-480),abs(extent.y-200),abs(extent.z-261.29)) > 1:
            raise RuntimeError('Stair extent has changed: '+str((stair,extent)))
        position = u.Vector(center.x-direction*extent.x,center.y,center.z-extent.z)
        rotation = u.Rotator(pitch=0,yaw=0 if direction==1 else 180,roll=0)
        surveyed.append((stair,origins,position,rotation))
    gallery = [(label,actor) for label,actor in actors.items()
               if label.startswith(('Atrium::','AtriumCross::')) and label.split()[-1] in ('Posts','Rail','Panel')]
    if len(gallery) != 24:
        raise RuntimeError('Expected 8 surveyed glass assemblies, found '+str(len(gallery))+' rail elements')
    palette = {key:load(PALETTE+key) for key in SLOTS}
    mesh = flight_mesh(world,palette)
    frame = {'Panel':gallery_glass(),'Rail':palette['TC_Brushed'],'Posts':palette['TC_Graphite']}
    installed = []
    with u.ScopedEditorTransaction('Dress the central hall stairs and gallery guards'):
        for stair,originals,position,rotation in surveyed:
            label = 'CH_Art_OpenFlight_'+stair
            actor = actors.get(label)
            if actor is None:
                actor = subsystem.spawn_actor_from_class(u.StaticMeshActor,position,rotation)
                actor.set_actor_label(label)
            actor.modify()
            actor.set_actor_location_and_rotation(position,rotation,False,True)
            actor.set_actor_scale3d(u.Vector(1,1,1))
            actor.set_folder_path('Chapter1/CentralHall/Art/Stairs')
            actor.tags = [u.Name('CentralHallArt'),u.Name('HallStair'+stair)]
            comp = actor.static_mesh_component
            comp.modify()
            comp.set_static_mesh(mesh)
            comp.set_collision_profile_name('NoCollision')
            comp.set_editor_property('can_ever_affect_navigation',False)
            actor.set_actor_enable_collision(False)
            for blockout in originals:
                component = blockout.static_mesh_component
                component.modify()
                component.set_visibility(False,False)
                component.set_hidden_in_game(True,False)
                component.set_cast_shadow(False)
                # The original collision body and all original response channels remain active.
            installed.append(label)
        for label,actor in gallery:
            component = actor.static_mesh_component
            component.modify()
            for i in range(component.get_num_materials()):
                component.set_material(i,frame[label.split()[-1]])
    return dict(flights=installed, gallery_components=len(gallery), original_collision_sources=20,
                mesh=mesh.get_path_name())
