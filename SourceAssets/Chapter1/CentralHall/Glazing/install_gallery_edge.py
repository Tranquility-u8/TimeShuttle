"""Install the walkable observation deck and continuous, equal-bay glass guard."""
from pathlib import Path
import json
import re
import runpy
import unreal as ue

HERE = Path(__file__).resolve().parent
DEST = '/Game/Environment/Chapter1/CentralHall/Glazing'
HALL = '/Game/Environment/Chapter1/CentralHall/Environment/Materials/MI_Hall'
LAB = '/Game/Environment/Chapter1/ParticleLab/Materials/MI_LabShell'
TAG = 'Chapter1ObservationGalleryEdge'
MATERIALS = {'Graphite': LAB+'Graphite','Alloy': LAB+'Steel','Seal': LAB+'Seal',
             'Soffit':HALL+'Soffit','Floor':HALL+'Paving','FloorAlt':HALL+'PavingInset',
             'Joint':HALL+'Seam','GuardGlass':DEST+'/Materials/MI_HallGuardLaminatedGlass'}

def enable_surface_collision(mesh):
    subsystem = ue.get_editor_subsystem(ue.StaticMeshEditorSubsystem)
    mesh.modify()
    body = mesh.get_editor_property('body_setup')
    if not body:
        raise RuntimeError('Missing static body for ' + mesh.get_name())
    body.modify()
    body.set_editor_property('double_sided_geometry', True)
    body.set_editor_property('collision_trace_flag', ue.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE)
    for index in range(mesh.get_num_sections(0)):
        if not subsystem.is_section_collision_enabled(mesh, 0, index):
            subsystem.enable_section_collision(mesh, True, 0, index)
    assert ue.EditorAssetLibrary.save_loaded_asset(mesh, False)


def install():
    editor=ue.get_editor_subsystem(ue.UnrealEditorSubsystem)
    level=ue.get_editor_subsystem(ue.LevelEditorSubsystem)
    world=editor.get_editor_world()
    assert world.get_path_name()=='/Game/Maps/Map_LabV39.Map_LabV39' and not level.is_in_play_in_editor()
    actors=ue.get_editor_subsystem(ue.EditorActorSubsystem)
    manifest=json.loads((HERE/'gallery_edge.json').read_text(encoding='utf8'))
    assert set(manifest)=={'SM_HallGlazing'+piece+side for piece in ('Deck','Guard') for side in ('East','West')}
    labels={name:'Art_CH_Glazing_'+name.removeprefix('SM_HallGlazing') for name in manifest}
    existing={}
    original=[]
    for actor in actors.get_all_level_actors():
        label=actor.get_actor_label()
        if label in labels.values():
            if label in existing or ue.Name(TAG) not in actor.tags or not isinstance(actor,ue.StaticMeshActor):
                raise ValueError('Conflicting deck actor '+label)
            existing[label]=actor
        if re.fullmatch(r'Observation::\d{3} (Panel|Posts|Rail)',label):
            assert isinstance(actor,ue.StaticMeshActor)
            original.append(actor)
    assert len(original)==204 and len({a.get_actor_label() for a in original})==204
    finishes={k:ue.load_asset(p) for k,p in MATERIALS.items()}
    assert all(finishes.values())
    importer=runpy.run_path(str(HERE.parent/'Environment/install_environment.py'))['import_mesh']
    flag='Interchange.FeatureFlags.Import.FBX'
    previous=ue.SystemLibrary.get_console_variable_int_value(flag)
    meshes={}
    try:
        ue.SystemLibrary.execute_console_command(world,flag+' 0')
        for name,info in manifest.items():
            mesh=importer(name,finishes,world,info['slots'],source_dir=HERE,destination=DEST)
            enable_surface_collision(mesh)
            meshes[name]=mesh
    finally:
        ue.SystemLibrary.execute_console_command(world,f'{flag} {previous}')
    placed={}
    with ue.ScopedEditorTransaction('Extend the gallery slab and align its guard with the curtain wall'):
        for name,mesh in meshes.items():
            label=labels[name]
            location=ue.Vector(*manifest[name]['pivot_cm'])
            actor=existing.get(label)
            if not actor:
                actor=actors.spawn_actor_from_class(ue.StaticMeshActor,location,ue.Rotator())
                actor.set_actor_label(label)
                actor.tags=[ue.Name(TAG)]
            actor.modify()
            actor.set_folder_path('Chapter1/CentralHall/Glazing')
            actor.set_actor_location_and_rotation(location,ue.Rotator(),False,True)
            actor.set_actor_scale3d(ue.Vector(1,1,1))
            component=actor.static_mesh_component
            component.modify()
            component.set_static_mesh(mesh)
            component.set_editor_property('override_materials',[])
            component.set_lighting_channels(False,True,False)
            component.set_editor_property('cast_shadow',False)
            component.set_collision_profile_name('BlockAll')
            component.set_editor_property('can_ever_affect_navigation',True)
            actor.set_actor_enable_collision(True)
            placed[label]=mesh.get_path_name()
        # Retain the original components as a reversible source of the old
        # survey. Removing all three old physical shapes opens the former line.
        for actor in original:
            actor.modify()
            c=actor.static_mesh_component
            c.modify()
            c.set_visibility(False)
            c.set_hidden_in_game(True)
            c.set_editor_property('cast_shadow',False)
            c.set_editor_property('can_ever_affect_navigation',False)
            c.set_collision_profile_name('NoCollision')
            actor.set_actor_enable_collision(False)
    return {'architecture':placed,'retired_guard_components':len(original),
            'guard_center_offset_cm':46,'slab_edge_offset_cm':39,'bay_count':36,
            'slab_top_cm':540,'slab_soffit_cm':496}
