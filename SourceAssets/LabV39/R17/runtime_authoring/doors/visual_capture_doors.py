"""Serial PIE door screenshots, after qa_doors_pie.py has finished.

Moves only the live player for the views, injects actual IA_Interact, and uses the
current PIE camera. No door interface/state setter is called. Does not save map.
"""
import json
import time
import traceback
from pathlib import Path
import unreal

OUT=Path(unreal.Paths.project_saved_dir()).resolve()/'Agent'/'LabR17'/'doors'
PREVIEWS=OUT/'Previews';PREVIEWS.mkdir(exist_ok=True)
REPORT=OUT/'door_visual_capture.json'
assert getattr(unreal,'_lab_r17_door_qa_handle',None) is None,'Wait for door QA to finish first'
assert getattr(unreal,'_lab_r17_door_capture_handle',None) is None,'A door capture is already active'
world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
assert world and 'UEDPIE_' in world.get_path_name(),'Start PIE first'
pawn=unreal.GameplayStatics.get_player_character(world,0)
pc=unreal.GameplayStatics.get_player_controller(world,0)
assert pawn and pc
assert abs(unreal.GameplayStatics.get_global_time_dilation(world)-1)<.01,'Restore normal time first'
movement=pawn.get_component_by_class(unreal.CharacterMovementComponent)
capsule=pawn.get_component_by_class(unreal.CapsuleComponent)
half=capsule.get_scaled_capsule_half_height()
initial_position=pawn.get_actor_location();initial_rotation=pc.get_control_rotation()
lib=unreal.get_default_object(unreal.load_class(None,'/Script/Engine.SubsystemBlueprintLibrary'))
sub=lib.call_method('GetLocalPlayerSubSystemFromPlayerController',args=(pc,unreal.EnhancedInputLocalPlayerSubsystem.static_class()))
interact=unreal.load_asset('/Game/Input/Actions/IA_Interact')
interaction=pawn.get_component_by_class(unreal.load_class(None,'/Game/Blueprints/Components/Player/AC_Interaction.AC_Interaction_C'))
assert sub and interact and interaction
doors={a.get_actor_label().removeprefix('LabR17_Door_'):a for a in unreal.GameplayStatics.get_all_actors_of_class(world,unreal.Actor)
       if a.get_actor_label().startswith('LabR17_Door_')}
for door_id in ['R9-TIME-EXIT','R10-UP-NORTH','C0']:assert door_id in doors,door_id

def prop(obj,key):return obj.get_editor_property(key)
def pose(door_id,offset):
    door=doors[door_id];p=door.get_actor_location()+door.get_actor_forward_vector()*offset;p.z+=half+2
    movement.stop_movement_immediately();pawn.set_actor_location(p,False,True)
def aim(door_id,height=.5):
    target=doors[door_id].get_actor_location();target.z+=float(prop(doors[door_id],'DoorHeight'))*height
    camera=unreal.GameplayStatics.get_player_camera_manager(world,0)
    pc.set_control_rotation(unreal.MathLibrary.find_look_at_rotation(camera.get_camera_location(),target))
def inject(pressed):sub.inject_input_vector_for_action(interact,unreal.Vector(1 if pressed else 0,0,0),[],[])
def focused(door_id):
    for name in ['FocusedActor','FocusedInteractionArea']:
        obj=prop(interaction,name)
        if obj==doors[door_id] or (isinstance(obj,unreal.Actor) and obj.get_parent_actor()==doors[door_id]):return True
    return False
def snapshot(door_id):
    door=doors[door_id]
    return {'door':door_id,'open':bool(prop(door,'bDoorOpen')),'alpha':float(prop(door,'OpenAlpha')),
            'locked':bool(prop(door,'bLocked')),'front_text':str(prop(prop(door,'PromptFront'),'text')),
            'back_text':str(prop(prop(door,'PromptBack'),'text')),
            'front_visible':bool(prop(prop(door,'PromptFront'),'visible')),
            'back_visible':bool(prop(prop(door,'PromptBack'),'visible')),
            'prompt_until':float(prop(door,'PromptUntil')),
            'real_time':unreal.GameplayStatics.get_real_time_seconds(world)}
def assert_open(door_id):
    s=snapshot(door_id);assert s['open'] and s['alpha']>.98,str(s)
def assert_locked():
    s=snapshot('R9-TIME-EXIT')
    assert s['locked'] and not s['open'] and s['front_text']=='LOCKED' and s['back_text']=='LOCKED',str(s)
    assert s['front_visible'] and s['back_visible'] and s['prompt_until']>s['real_time'],str(s)

steps=[]
def add(name,wait=0,start=None,tick=None,check=None,shot=None):
    steps.append(dict(name=name,wait=wait,start=start,tick=tick,check=check,shot=shot))
def setup(door_id,offset=165):
    add('place_'+door_id,.15,lambda:pose(door_id,offset))
    add('focus_'+door_id,.65,tick=lambda:aim(door_id),check=lambda:ensure_focus(door_id))
def ensure_focus(door_id):assert focused(door_id),'Real interaction focus missing: '+door_id
def press():
    add('F_press',.15,tick=lambda:inject(True))
    add('F_release',.1,start=lambda:inject(False))
def shot(name,door_id,check):add(name,check=check,shot=(name,door_id))

# Keep close enough for the existing interaction trace. Capture immediately
# after the real F input, within the two-real-second LOCKED feedback lifetime.
setup('R9-TIME-EXIT');press()
shot('01_Locked_F_feedback','R9-TIME-EXIT',assert_locked)

# QA ends with this door open. Close it with F if necessary, then reopen with F
# so the final screenshot also follows the actual player input chain.
setup('R10-UP-NORTH')
if bool(prop(doors['R10-UP-NORTH'],'bDoorOpen')):
    press();add('normal_closed_settle',1.1)
press();add('normal_open_settle',1.1,check=lambda:assert_open('R10-UP-NORTH'))
add('normal_wide_view',.5,lambda:pose('R10-UP-NORTH',300),tick=lambda:aim('R10-UP-NORTH'))
shot('02_Normal_F_open','R10-UP-NORTH',lambda:assert_open('R10-UP-NORTH'))

# C0 is automatic. No F injection here; proximity opens both leaves.
add('C0_near',1.2,lambda:pose('C0',300),tick=lambda:aim('C0',.45),check=lambda:assert_open('C0'))
shot('03_Omen_automatic_double_open','C0',lambda:assert_open('C0'))

state={'index':-1,'phase':'next','busy':False,'done':False,'started':time.monotonic(),'captures':[]}
def write(error=None):
    REPORT.write_text(json.dumps({'done':state['done'],'error':error,'captures':state['captures'],
        'passed':state['done'] and error is None and len(state['captures'])==3 and all(x['file_verified'] for x in state['captures']),
        'current_step':steps[state['index']]['name'] if 0<=state['index']<len(steps) else None,
        'elapsed_seconds':time.monotonic()-state['started'],
        'method':'Live PIE camera. Normal/locked use actual EnhancedInput IA_Interact; C0 uses player proximity. No direct door state/interface calls.'},ensure_ascii=False,indent=2),encoding='utf-8')
def finish(error=None):
    handle=getattr(unreal,'_lab_r17_door_capture_handle',None)
    unreal._lab_r17_door_capture_handle=None
    if handle is not None:
        try:unreal.unregister_slate_post_tick_callback(handle)
        except Exception:pass
    state['done']=True;state['phase']='finished'
    try:
        inject(False);movement.stop_movement_immediately()
        pawn.set_actor_location(initial_position,False,True);pc.set_control_rotation(initial_rotation)
    except Exception:error=(error+'\n' if error else '')+'Cleanup: '+traceback.format_exc()
    finally:write(error)
def tick(delta):
    if state['done'] or state['busy']:return
    state['busy']=True
    try:
        if state['phase']=='next':
            state['index']+=1
            if state['index']>=len(steps):finish();return
            step=steps[state['index']];state['step_started']=time.monotonic();state['phase']='wait'
            if step['start']:step['start']()
            write();return
        step=steps[state['index']]
        if state['phase']=='capture_wait':
            path=state['pending_path']
            if path.is_file() and path.stat().st_size>100:
                with path.open('rb') as stream:signature=stream.read(8)
                assert signature==b'\x89PNG\r\n\x1a\n','Capture is not PNG: '+str(path)
                state['pending_row'].update(file_verified=True,bytes=path.stat().st_size)
                state['captures'].append(state['pending_row']);state['phase']='next';write();return
            if time.monotonic()-state['capture_started']>10:raise TimeoutError('Screenshot did not reach disk: '+str(path))
            return
        if step['tick']:step['tick']()
        if time.monotonic()-state['step_started']<step['wait']:return
        if step['check']:step['check']()
        if step['shot']:
            name,door_id=step['shot'];path=PREVIEWS/(name+'.png')
            if path.exists():path.unlink()  # Only this script's named output.
            state['pending_path']=path;state['pending_row']={'name':name,'path':str(path),'door_state':snapshot(door_id),'file_verified':False}
            # Both phase and pending state are committed BEFORE the UE capture
            # call, which can pump nested Slate ticks. busy blocks re-entry too.
            state['phase']='capture_wait';state['capture_started']=time.monotonic();write()
            unreal.AutomationLibrary.take_high_res_screenshot(1600,900,str(path),delay=0)
        else:state['phase']='next';write()
    except Exception:finish(traceback.format_exc())
    finally:state['busy']=False
unreal._lab_r17_door_capture_handle=unreal.register_slate_post_tick_callback(tick)
write()
result={'started':True,'report':str(REPORT),'output_directory':str(PREVIEWS),'note':'Serial asynchronous capture. Do not run alongside door QA or other player-input/camera tests.'}
