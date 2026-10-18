"""PIE visual setup only. Set OMEN_VIEW='left'/'right'/'restore' in execution globals.

Run after automated sampling has finished. Wait about two seconds after placing
each view, then root captures the live PIE viewport. No asset/map save.
"""
import unreal

mode = globals().get('OMEN_VIEW', 'left')
assert mode in ('left','right','restore')
assert unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).is_in_play_in_editor()
world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
pawn = unreal.GameplayStatics.get_player_character(world,0)
controller = unreal.GameplayStatics.get_player_controller(world,0)
camera = unreal.GameplayStatics.get_player_camera_manager(world,0)
observers = unreal.GameplayStatics.get_all_actors_with_tag(world,'OmenObserver')
assert pawn and controller and camera and len(observers)==1
assert getattr(unreal,'_lab_r17_jump_handle',None) is None
assert getattr(unreal,'_lab_v39_pie_handle',None) is None
observer = observers[0]
omen = observer.get_editor_property('OmenRoot')
saved = getattr(unreal,'_lab_r17_omen_view_saved',None)
if mode=='restore':
    assert saved and saved['pawn']==pawn, 'No matching visual setup to restore'
    pawn.stop_jumping()
    pawn.get_component_by_class(unreal.CharacterMovementComponent).stop_movement_immediately()
    pawn.set_actor_location(saved['location'],False,True)
    pawn.set_actor_rotation(saved['rotation'],True)
    controller.set_control_rotation(saved['control'])
    observer.set_editor_property('TrackingEnabled',saved['enabled'])
    unreal._lab_r17_omen_view_saved=None
else:
    if not saved:
        unreal._lab_r17_omen_view_saved={'pawn':pawn,'location':pawn.get_actor_location(),'rotation':pawn.get_actor_rotation(),
            'control':controller.get_control_rotation(),'enabled':observer.get_editor_property('TrackingEnabled')}
    else:
        assert saved['pawn']==pawn, 'A different PIE session owns the saved view'
    x=-1100 if mode=='left' else 1100
    previous=pawn.get_actor_location()
    camera_height=camera.get_camera_location().z-previous.z
    target_location=unreal.Vector(x,1800,150)
    pawn.stop_jumping()
    pawn.un_crouch()
    pawn.get_component_by_class(unreal.CharacterMovementComponent).stop_movement_immediately()
    pawn.set_actor_location(target_location,False,True)
    controller.set_control_rotation(unreal.MathLibrary.find_look_at_rotation(
        unreal.Vector(x,1800,150+camera_height),omen.get_actor_location()))
    observer.set_editor_property('TrackingEnabled',True)
print({'view':mode,'instruction':'After ~2 seconds, capture the live PIE viewport. Verify Eye/Pupil face the player; restore before other movement tests.'})
