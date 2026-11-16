from pathlib import Path
import importlib.util
import json
import unreal as u

HERE=Path(__file__).resolve().parent
def install():
    editor=u.get_editor_subsystem(u.UnrealEditorSubsystem)
    sub=u.get_editor_subsystem(u.EditorActorSubsystem)
    world=editor.get_editor_world()
    assert world.get_name()=='Map_LabV39'
    loader=importlib.util.spec_from_file_location('hall_panel_fbx',HERE.parent/'OmenFront/install_hero.py')
    library=importlib.util.module_from_spec(loader)
    loader.loader.exec_module(library)
    library.ROOT=HERE
    meshes=library.load_meshes(world,json.loads((HERE/'panels.json').read_text()))
    actors={a.get_actor_label():a for a in sub.get_all_level_actors()}
    door=actors['LabR17_Door_C0']
    leaves={c.get_name():c for c in door.get_components_by_class(u.StaticMeshComponent)}
    snap=u.AttachmentRule.SNAP_TO_TARGET
    results={}
    for name,mesh in meshes.items():
        if name in ('SM_CH_C0LeafLeft','SM_CH_C0LeafRight','SM_CH_TrainingLandingFrame') and 'DoorDressLeft' in leaves:
            # The shared lab door now supplies the moving panels and training portal.
            continue
        label='Art_'+name.removeprefix('SM_')
        parent=leaves[name.removeprefix('SM_CH_C0')] if name.startswith('SM_CH_C0Leaf') else None
        point=parent.get_world_location() if parent else u.Vector(0,925,0)
        rot=u.Rotator(0,0,0)
        if name=='SM_CH_TrainingLandingFrame':
            point=u.Vector(1883,66.7,540)
            rot=u.Rotator(roll=0,pitch=0,yaw=-90)
        actor=actors.get(label) or sub.spawn_actor_from_class(u.StaticMeshActor,point,rot)
        actor.modify()
        c=actor.static_mesh_component
        c.modify()
        if parent:c.set_mobility(u.ComponentMobility.MOVABLE)
        actor.set_actor_label(label)
        actor.set_folder_path('Chapter1/CentralHall/OmenFront')
        if not parent:
            actor.set_actor_location_and_rotation(point,rot,False,True)
            actor.set_actor_scale3d(u.Vector(1,1,1))
        c.set_static_mesh(mesh); c.set_collision_profile_name('NoCollision')
        c.set_editor_property('can_ever_affect_navigation',False)
        actor.set_actor_enable_collision(False)
        if parent:
            if c.get_attach_parent()!=parent:
                assert actor.attach_to_component(parent,u.Name('None'),snap,snap,snap,False) is not False
            # Construction-script reruns rebuild the leaf component when the
            # map reopens. Identity remains valid before and after that rebuild.
            c.set_relative_location(u.Vector(0,0,0),False,True)
            c.set_relative_rotation(u.Rotator(roll=0,pitch=0,yaw=0),False,True)
            c.set_relative_scale3d(u.Vector(1,1,1))
            assert c.get_attach_parent()==parent
        results[label]=str(parent.get_name()) if parent else 'solid architectural wall'
    # The persistent whitebox paint is independent of the Chapter 1 guidance waypoint actors.
    for index in range(6):
        mark=actors['MainRouteTick::'+str(index)]
        assert isinstance(mark,u.StaticMeshActor) and -2401<=mark.get_actor_location().y<=601
        mark.modify()
        mark.static_mesh_component.modify()
        mark.static_mesh_component.set_visibility(False,False)
        mark.static_mesh_component.set_hidden_in_game(True,False)
        mark.static_mesh_component.set_cast_shadow(False)
    results['suppressed_static_floor_marks']=6
    return results
