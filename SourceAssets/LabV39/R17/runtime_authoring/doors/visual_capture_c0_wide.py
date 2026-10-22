"""PIE-only wide-angle C0 views, restoring live camera FOV and player pose.

SetFOV/UnlockFOV on PlayerCameraManager are not reflected in UE 5.6. Use the
reflected CameraComponent.SetFieldOfView instead, without adding an FOV lock.
No Blueprint/default asset, map, door state, or game save is modified.
"""
import json,time,traceback
from pathlib import Path
import unreal

OUT=Path(unreal.Paths.project_saved_dir()).resolve()/'Agent'/'LabR17'/'doors'
PREVIEWS=OUT/'Previews';PREVIEWS.mkdir(exist_ok=True)
REPORT=OUT/'door_c0_wide_capture.json'
assert getattr(unreal,'_lab_r17_door_qa_handle',None) is None,'Wait for QA to finish'
assert getattr(unreal,'_lab_r17_door_capture_handle',None) is None,'Wait for existing capture to finish'
assert getattr(unreal,'_lab_r17_c0_wide_handle',None) is None,'C0 wide capture already running'
world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
assert world and 'UEDPIE_' in world.get_path_name(),'Start PIE first'
pawn=unreal.GameplayStatics.get_player_character(world,0)
pc=unreal.GameplayStatics.get_player_controller(world,0)
manager=unreal.GameplayStatics.get_player_camera_manager(world,0)
assert pawn and pc and manager
cameras=[c for c in pawn.get_components_by_class(unreal.CameraComponent) if c.is_active()]
assert len(cameras)==1,'Expected one active player CameraComponent'
camera=cameras[0]
original_fov=float(camera.get_editor_property('field_of_view'))
original_effective_fov=manager.get_fov_angle()
original_position=pawn.get_actor_location();original_rotation=pc.get_control_rotation()
movement=pawn.get_component_by_class(unreal.CharacterMovementComponent)
half=pawn.get_component_by_class(unreal.CapsuleComponent).get_scaled_capsule_half_height()
door=next(a for a in unreal.GameplayStatics.get_all_actors_of_class(world,unreal.Actor) if a.get_actor_label()=='LabR17_Door_C0')
assert door.get_editor_property('bAutomatic') and not door.get_editor_property('bLocked')

def pose(offset):
    point=door.get_actor_location()+door.get_actor_forward_vector()*offset;point.z+=half+2
    movement.stop_movement_immediately();pawn.set_actor_location(point,False,True)
def aim():
    target=door.get_actor_location();target.z+=float(door.get_editor_property('DoorHeight'))*.5
    pc.set_control_rotation(unreal.MathLibrary.find_look_at_rotation(manager.get_camera_location(),target))
def snapshot():
    offset=pawn.get_actor_location()-door.get_actor_location();normal=door.get_actor_forward_vector()
    return {'open':bool(door.get_editor_property('bDoorOpen')),'alpha':float(door.get_editor_property('OpenAlpha')),
            'effective_fov':manager.get_fov_angle(),'component_fov':float(camera.get_editor_property('field_of_view')),
            'player_offset_cm':offset.x*normal.x+offset.y*normal.y+offset.z*normal.z,
            'left_relative_location':str(door.get_editor_property('LeafLeft').get_editor_property('relative_location')),
            'right_relative_location':str(door.get_editor_property('LeafRight').get_editor_property('relative_location'))}
state={'phase':'far','started':time.monotonic(),'deadline':time.monotonic(),'done':False,'busy':False,'captures':[]}
def write(error=None):
    REPORT.write_text(json.dumps({'done':state['done'],'error':error,'passed':state['done'] and error is None and len(state['captures'])==2,
        'captures':state['captures'],'original_component_fov':original_fov,'original_effective_fov':original_effective_fov,
        'restored_component_fov':float(camera.get_editor_property('field_of_view')) if state['done'] else None,
        'phase':state['phase'],'elapsed_seconds':time.monotonic()-state['started'],
        'method':'Live PIE player camera with temporary CameraComponent FOV 120, actual C0 player proximity. No door interface/state calls; no saved assets changed.'},ensure_ascii=False,indent=2),encoding='utf-8')
def finish(error=None):
    handle=getattr(unreal,'_lab_r17_c0_wide_handle',None);unreal._lab_r17_c0_wide_handle=None
    if handle is not None:
        try:unreal.unregister_slate_post_tick_callback(handle)
        except Exception:pass
    state['done']=True;state['phase']='finished'
    try:
        camera.set_field_of_view(original_fov)
        movement.stop_movement_immediately();pawn.set_actor_location(original_position,False,True);pc.set_control_rotation(original_rotation)
    except Exception:error=(error+'\n' if error else '')+'Cleanup: '+traceback.format_exc()
    finally:write(error)
def capture(name,next_phase):
    path=PREVIEWS/(name+'.png')
    if path.exists():path.unlink()
    state['pending_path']=path;state['pending_row']={'path':str(path),'name':name,'state':snapshot()}
    state['next_phase']=next_phase;state['phase']='capture_wait';state['capture_started']=time.monotonic()
    write()  # Update before capture, which may pump Slate recursively.
    unreal.AutomationLibrary.take_high_res_screenshot(1600,900,str(path),delay=0)
def tick(delta):
    if state['done'] or state['busy']:return
    state['busy']=True
    try:
        now=time.monotonic()
        if state['phase']=='capture_wait':
            path=state['pending_path']
            if path.is_file() and path.stat().st_size>100:
                with path.open('rb') as stream:assert stream.read(8)==b'\x89PNG\r\n\x1a\n'
                state['pending_row'].update(file_verified=True,bytes=path.stat().st_size);state['captures'].append(state['pending_row'])
                state['phase']=state['next_phase'];state['deadline']=now+1.1;write()
            elif now-state['capture_started']>10:raise TimeoutError('PNG not saved: '+str(path))
            return
        if state['phase']=='far':
            state['phase']='far_wait';state['deadline']=now+1.3
            camera.set_field_of_view(120);pose(650);aim();write();return
        aim()
        if now<state['deadline']:return
        if state['phase']=='far_wait':
            assert float(door.get_editor_property('OpenAlpha'))<.02,'C0 did not close at far pose'
            assert manager.get_fov_angle()>110,'Current camera is not using the temporary wide FOV'
            state['phase']='opening';state['deadline']=now+.13
            pose(390);aim();write();return
        if state['phase']=='opening':
            data=snapshot();assert data['open'] and 0<data['alpha']<.9,str(data)
            capture('04_Omen_double_leaves_opening_wide','full_wait');return
        if state['phase']=='full_wait':
            data=snapshot();assert data['open'] and data['alpha']>.98,str(data)
            capture('05_Omen_full_open_frame_wide','finish');return
        if state['phase']=='finish':finish();return
    except Exception:finish(traceback.format_exc())
    finally:state['busy']=False
unreal._lab_r17_c0_wide_handle=unreal.register_slate_post_tick_callback(tick)
write()
result={'started':True,'report':str(REPORT),'note':'Serial PIE-only camera capture; wait until done before other tests.'}
