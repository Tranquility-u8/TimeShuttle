"""Install only central-atrium visual finishes and room-local lighting into the active editor world."""
import json
from pathlib import Path
import unreal as u

HERE = Path(__file__).resolve().parent
DEST = '/Game/Environment/Chapter1/CentralHall/Environment'
PARTICLE = '/Game/Environment/Chapter1/ParticleLab/Materials'
TAG = 'Chapter1CentralHallEnvironment'


def asset(path):
    obj=u.EditorAssetLibrary.load_asset(path)
    if not obj:
        raise ValueError('Missing project asset '+path)
    return obj


def hall_material(name, tint, metal, rough, emission=(0,0,0), opacity=None):
    folder=DEST+'/Materials'
    path=folder+'/MI_Hall'+name
    lib=u.EditorAssetLibrary
    m=lib.load_asset(path) if lib.does_asset_exist(path) else u.AssetToolsHelpers.get_asset_tools().create_asset('MI_Hall'+name,folder,u.MaterialInstanceConstant,u.MaterialInstanceConstantFactoryNew())
    if not m: raise RuntimeError(path)
    edit=u.MaterialEditingLibrary
    edit.set_material_instance_parent(m,asset(PARTICLE+('/M_LabGlass' if opacity is not None else '/M_LabSurface')))
    for key,c in [('Tint',tint),('Emission',emission)]:
        edit.set_material_instance_vector_parameter_value(m,key,u.LinearColor(*c,1))
    for key,v in [('Metallic',metal),('Roughness',rough)]:
        edit.set_material_instance_scalar_parameter_value(m,key,float(v))
    if opacity is not None:
        edit.set_material_instance_scalar_parameter_value(m,'Opacity',float(opacity))
    edit.update_material_instance(m)
    if not lib.save_loaded_asset(m,False): raise RuntimeError(path)
    return m


def optical_material(name, color, filter_glass=False):
    # Dedicated unlit emitters have luminance in scene units and remain visible at the
    # physical exposure used by Map_LabV39. A modulating pane attenuates the exterior
    # in HDR before tone mapping instead of mixing pale lit glass over a bright sky.
    folder=DEST+'/Materials'
    path=folder+'/M_Hall'+name
    lib=u.EditorAssetLibrary
    me=u.MaterialEditingLibrary
    material=lib.load_asset(path) if lib.does_asset_exist(path) else u.AssetToolsHelpers.get_asset_tools().create_asset(
        'M_Hall'+name,folder,u.Material,u.MaterialFactoryNew())
    if not material: raise RuntimeError(path)
    me.delete_all_material_expressions(material)
    material.set_editor_property('shading_model',u.MaterialShadingModel.MSM_UNLIT)
    material.set_editor_property('two_sided',True)
    if filter_glass:
        material.set_editor_property('blend_mode',u.BlendMode.BLEND_MODULATE)
        if hasattr(u,'MaterialTranslucencyPass'):
            material.set_editor_property('translucency_pass',u.MaterialTranslucencyPass.MTP_BEFORE_DOF)
    parameter='Transmission' if filter_glass else 'LensRadiance'
    value=me.create_material_expression(material,u.MaterialExpressionVectorParameter,-260,0)
    value.set_editor_property('parameter_name',parameter)
    value.set_editor_property('default_value',u.LinearColor(*color,1))
    assert me.connect_material_property(value,'',u.MaterialProperty.MP_EMISSIVE_COLOR)
    me.recompile_material(material)
    assert lib.save_loaded_asset(material,False),path
    # Preserve the named finish assets as editable instances. Interior artists can
    # tune an individual lens or pane without recompiling the reference shader.
    instance_names={'CeilingLenses':'CeilingDiffuser','WayfindingLenses':'WayfindingDiffuser',
                    'FaultLens':'AlarmLens','StatusCells':'StatusLens','SolarGlass':'CityGlazing'}
    instance_name='MI_Hall'+instance_names[name]
    instance_path=folder+'/'+instance_name
    instance=lib.load_asset(instance_path) if lib.does_asset_exist(instance_path) else u.AssetToolsHelpers.get_asset_tools().create_asset(
        instance_name,folder,u.MaterialInstanceConstant,u.MaterialInstanceConstantFactoryNew())
    me.set_material_instance_parent(instance,material)
    me.set_material_instance_vector_parameter_value(instance,parameter,u.LinearColor(*color,1))
    me.update_material_instance(instance)
    assert lib.save_loaded_asset(instance,False),instance_path
    return instance


def import_mesh(name,mats,world,slots,*,source_dir=HERE,destination=DEST):
    folder=destination+'/Meshes'
    path=folder+'/'+name
    opts=u.FbxImportUI()
    for k,v in dict(automated_import_should_detect_type=False,mesh_type_to_import=u.FBXImportType.FBXIT_STATIC_MESH,
                    import_mesh=True,import_materials=False,import_textures=False,import_animations=False,import_as_skeletal=False).items():
        opts.set_editor_property(k,v)
    for k,v in dict(combine_meshes=True,auto_generate_collision=False,convert_scene=True,convert_scene_unit=True,
                    force_front_x_axis=False,generate_lightmap_u_vs=False,normal_import_method=u.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS).items():
        opts.static_mesh_import_data.set_editor_property(k,v)
    task=u.AssetImportTask()
    for k,v in dict(filename=str(source_dir/(name+'.fbx')),destination_path=folder,destination_name=name,
                    automated=True,save=False,replace_existing=True,replace_existing_settings=True,options=opts).items():
        task.set_editor_property(k,v)
    u.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    if not task.imported_object_paths:
        raise RuntimeError('FBX import failed: '+name)
    mesh=asset(path)
    imported=[str(s.get_editor_property('imported_material_slot_name')) for s in mesh.static_materials]
    if sorted(imported)!=sorted(slots): raise RuntimeError((name,imported,slots))
    for j,slot in enumerate(imported):
        mesh.set_material(j,mats[slot])
    mesh.set_editor_property('allow_cpu_access',True)
    if not u.EditorAssetLibrary.save_loaded_asset(mesh,False): raise RuntimeError(path)
    return mesh


def get_actor(sub,lookup,cls,label,pos,rotation):
    a=lookup.get(label)
    if a is None:
        a=sub.spawn_actor_from_class(cls,u.Vector(*pos),rotation)
        a.set_actor_label(label)
        lookup[label]=a
    if not isinstance(a,cls): raise ValueError(label)
    a.modify()
    a.set_actor_location_and_rotation(u.Vector(*pos),rotation,False,True)
    a.tags=[u.Name(TAG)]
    return a


def has_dedicated_glazing(lookup):
    # The original environment installer also runs on older versions of this room.
    # An upgraded room owns its curtain wall through both measured frame assemblies.
    dest='/Game/Environment/Chapter1/CentralHall/Glazing'
    for side in ('West','East'):
        actor=lookup.get('Art_CH_Glazing_Frame'+side)
        if not isinstance(actor,u.StaticMeshActor) or u.Name('Chapter1CentralHallGlazing') not in actor.tags:
            return False
        mesh=actor.static_mesh_component.static_mesh
        name='SM_HallGlazingFrame'+side
        if not mesh or mesh.get_path_name()!=f'{dest}/Meshes/{name}.{name}':
            return False
    glass_path=dest+'/Materials/MI_HallCurtainGlass.MI_HallCurtainGlass'
    panes=[a for label,a in lookup.items() if label.startswith('FacadeGlass::')]
    mullions=[a for label,a in lookup.items() if label.startswith('FacadeMullion::')]
    if len(panes)!=70 or len(mullions)!=33:
        return False
    for pane in panes:
        component=pane.get_component_by_class(u.StaticMeshComponent)
        material=component.get_material(0) if component else None
        if not material or material.get_path_name()!=glass_path:
            return False
    return True


def install():
    editor=u.get_editor_subsystem(u.UnrealEditorSubsystem)
    world=editor.get_editor_world()
    assert world.get_name()=='Map_LabV39'
    assert not u.get_editor_subsystem(u.LevelEditorSubsystem).is_in_play_in_editor()
    actors=u.get_editor_subsystem(u.EditorActorSubsystem)
    lookup={a.get_actor_label():a for a in actors.get_all_level_actors()}
    for n in ('HallRoofBeam::15','HallRoofBeam::34','LabR17_Door_C0','B_TIME_wall_666','B_TR01_wall_669'):
        assert n in lookup,n
    manifest=json.loads((HERE/'environment_meshes.json').read_text(encoding='utf8'))
    for n in manifest:
        assert (HERE/(n+'.fbx')).is_file()
    mats={k:asset(PARTICLE+'/MI_LabShell'+n) for k,n in {
        'Panel':'Panel','WallCool':'Shadow','Seal':'Seal','Alloy':'Steel','Graphite':'Graphite'}.items()}
    mats.update({
        'Floor':hall_material('Paving',(.118,.135,.148),.26,.31),
        'FloorAlt':hall_material('PavingInset',(.124,.138,.15),.23,.34),
        'Joint':hall_material('Seam',(.026,.030,.034),.16,.52),
        'Ceiling':hall_material('Soffit',(.185,.195,.212),.19,.49),
        'CoolDiffuser':optical_material('CeilingLenses',(510,555,580)),
        'WarmDiffuser':optical_material('WayfindingLenses',(455,310,184)),
        'Warning':optical_material('FaultLens',(490,65,6)),
        'Status':optical_material('StatusCells',(8,34,40)),
        'Glass':optical_material('SolarGlass',(.70,.72,.74),filter_glass=True),
    })
    # Disable FBX Interchange only for this import, then restore its previous setting.
    flag='Interchange.FeatureFlags.Import.FBX'
    prev=u.SystemLibrary.get_console_variable_int_value(flag)
    try:
        u.SystemLibrary.execute_console_command(world,flag+' 0')
        meshes={n:import_mesh(n,mats,world,v['slots']) for n,v in manifest.items()}
    finally:
        u.SystemLibrary.execute_console_command(world,flag+' '+str(prev))
    report={'architecture':{},'light_fixtures':{},'hall_base_lights':{},'facade_glass':[],'facade_mullions':[]}
    with u.ScopedEditorTransaction('Install central hall finishes and emergency lighting'):
        for name,mesh in meshes.items():
            pos=manifest[name]['pivot_cm']
            label='Art_CH1_'+name[3:]
            a=get_actor(actors,lookup,u.StaticMeshActor,label,pos,u.Rotator())
            a.set_actor_scale3d(u.Vector(1,1,1))
            c=a.static_mesh_component;c.modify()
            c.set_static_mesh(mesh)
            c.set_collision_profile_name('NoCollision')
            c.set_editor_property('can_ever_affect_navigation',False)
            c.set_editor_property('cast_shadow',False)
            a.set_actor_enable_collision(False)
            # The entry glazing filters daylight. Restrict the finish at the city
            # window to indoor bounce and room lights to avoid clipped sun patches.
            if name=='SM_HallAtriumFloor':
                c.set_lighting_channels(False,True,False)
            a.set_folder_path('Chapter1/CentralHall/Environment')
            report['architecture'][label]=mesh.get_path_name()

        # The curved facade already has the measured flat glass segments. Apply overrides per actor only.
        dedicated_glazing=has_dedicated_glazing(lookup)
        for label,a in lookup.items():
            if not (label.startswith('FacadeGlass::') or label.startswith('FacadeMullion::')): continue
            if dedicated_glazing:continue
            y=a.get_actor_location().y
            if not -5350 < y < -5100:continue
            c=a.get_component_by_class(u.StaticMeshComponent)
            if not c or not c.static_mesh:continue
            is_glass=label.startswith('FacadeGlass::')
            c.modify();a.modify()
            for j in range(c.get_num_materials()):
                c.set_material(j,mats['Glass' if is_glass else 'Graphite'])
            report['facade_glass' if is_glass else 'facade_mullions'].append(label)

        # Keep physical glazing transparent. If this level was dressed with the
        # early shadow-screen prototype, remove only our three named test actors.
        for segment in ('Centre','West','East'):
            label='Art_CH1_HallSolarControl_'+segment
            shade=lookup.get(label)
            if shade and u.Name(TAG) in list(shade.tags):
                if not actors.destroy_actor(shade): raise RuntimeError(label)
                del lookup[label]

        # Eight hall lights were 75,000 and six lower-gallery lights were 15,000 in Map_LabV39.
        # Keep more ceiling fill towards the glazed facade; use absolute values for idempotence.
        for lab,a in lookup.items():
            if lab.startswith('LabV39_Light_Hall_'):
                strength=42000 if a.get_actor_location().y< -3000 else 39500
                color=(.84,.89,1.0)
            elif lab.startswith('LabV39_Light_LowerGallery_'):
                strength=8300; color=(.98,.89,.77)
            else:
                continue
            c=a.get_component_by_class(u.RectLightComponent)
            if not c:continue
            a.modify();c.modify()
            c.set_lighting_channels(True,True,False)
            c.set_intensity(float(strength)); c.set_light_color(u.LinearColor(*color,1),False)
            report['hall_base_lights'][lab]=c.get_editor_property('intensity')

        # Mount points coincide with the lenses in SM_HallAtriumLightFittings.
        def area(label,pos,target,size,intensity,color,radius,*,casts_shadows=False,hall_only=False):
            name='Art_CH1_HallLight_'+label
            rot=u.MathLibrary.find_look_at_rotation(u.Vector(*pos),u.Vector(*target))
            a=get_actor(actors,lookup,u.RectLight,name,pos,rot)
            a.set_folder_path('Chapter1/CentralHall/Lighting')
            c=a.rect_light_component;c.modify();c.set_mobility(u.ComponentMobility.MOVABLE)
            c.set_lighting_channels(not hall_only,True,False)
            c.set_intensity_units(u.LightUnits.LUMENS);c.set_intensity(float(intensity))
            c.set_light_color(u.LinearColor(*color,1),False)
            c.set_attenuation_radius(float(radius));c.set_source_width(float(size[0]));c.set_source_height(float(size[1]))
            # Bounce cards have no physical diffuser to mirror on the polished floor.
            c.set_editor_property('specular_scale',0.0 if label in ('DeskFaceWash','AtriumCeilingReturn') else 1.0)
            c.set_cast_shadows(casts_shadows)
            report['light_fixtures'][name]={'position':list(pos),'lumens':intensity}

        # Large low-contrast bounce sources face into the hall from its glazed end.
        # The original ceiling-only rig left the underside of railings and the vertical
        # face of the desk almost black. These sources remain local to the atrium.
        # Only the atrium dress receives these sources. The original room lights
        # still illuminate moving characters and cast the main architectural shadows.
        for label,receiver in lookup.items():
            if label.startswith(('Art_CH1_Hall','Art_CH_C0','Art_CH_Omen','Art_CH_Reception','Art_CH_TrainingLanding','CH_Art_OpenFlight_')) and isinstance(receiver,u.StaticMeshActor):
                component=receiver.static_mesh_component
                component.modify()
                component.set_lighting_channels(label!='Art_CH1_HallAtriumFloor',True,False)
        area('FacadeBounceWest',(-1340,-2890,1130),(-900,-620,390),(820,380),120000,(.83,.89,.96),3090,hall_only=True)
        area('FacadeBounceEast',(1340,-2890,1130),(900,-560,430),(820,380),120000,(.83,.89,.96),3090,hall_only=True)
        area('ReceptionFrontWash',(420,-1630,1050),(0,690,640),(1100,510),144000,(1,.89,.75),2690,casts_shadows=True,hall_only=True)
        area('StairReturn',(-80,-630,700),(1280,22,525),(630,310),59500,(.96,.87,.75),1930,hall_only=True)
        # Light reflected from the occupied floor softens the unlit ceiling beam.
        # The dial and stair keys stay local, so the two destinations read from floor level.
        area('AtriumCeilingReturn',(0,-825,808),(0,-720,1400),(1750,460),64000,(.92,.89,.84),2840,hall_only=True)
        area('DialFaceWash',(230,45,1210),(0,915,843),(540,100),62500,(1,.85,.70),1410,hall_only=True)
        area('DeskFaceWash',(-505,-1240,317),(0,-620,87),(320,170),31000,(1,.88,.72),1100,hall_only=True)
        for side in (-1,1):
            area(('East' if side>0 else 'West')+'TreadWash',(310*side,-150,238),(770*side,79,186),
                 (130,50),17500,(1,.80,.61),970,hall_only=True)
        warm=(1,.655,.395)
        area('C0_Lintel',(0,902,478),(0,790,105),(485,9),16800,warm,810)
        area('S1_Turn',(-1867,-3237,740),(-1540,-3110,540),(89,17),10500,warm,800)
        # Light from the signal faces the open gallery and the vertical surround.
        area('S4_Signal',(1868,-245,753),(1700,-150,650),(84,18),6700,(1,.115,.018),635)
        area('S4_FirstTread',(462,296,18),(543,154,43),(43,10),2200,warm,320)
        for i,x in enumerate((-990,990)):
            area('FrontGallery'+str(i+1),(x,383,489),(x,110,175),(57,7),2150,warm,635)
        for side in (-1,1):
            for i,y in enumerate((-2040,-1280)):
                x=1887*side
                area(('East' if side>0 else 'West')+'Skirt'+str(i+1),(x-side*15,y,30),(x-side*120,y,4),(43,8),500,warm,270)
        for i,y in enumerate((-560,-1520,-2480)):
            area('EastRailFootlight'+str(i+1),(1425,y,554),(1525,y+24,542),
                 (44,9),1800,warm,345)
        for i,x in enumerate((-1040,1040)):
            area('CityGallery'+str(i+1),(x,-3382,500),(x,-3030,165),(45,8),2010,warm,590)
    return report
