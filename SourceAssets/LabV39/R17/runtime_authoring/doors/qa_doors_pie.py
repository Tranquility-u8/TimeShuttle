"""Serial live-player door tests; coordinator starts PIE, then runs this script.

Uses real IA_Interact / IA_TimeAbility injection into EnhancedInput. Never calls
Interface_Interact, SetDoorOpen or changes door state to manufacture a pass.
Teleports are setup between independent cases; every aim/input/assert has frames.
Reports asynchronously to door_pie_qa.json, restoring the pawn at completion.
"""
import json,time,traceback
from pathlib import Path
import unreal

OUT=Path(unreal.Paths.project_saved_dir()).resolve()/'Agent'/'LabR17'/'doors'
REPORT=OUT/'door_pie_qa.json'
world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
assert world and 'UEDPIE_' in world.get_path_name(),'Start PIE first'
pawn=unreal.GameplayStatics.get_player_character(world,0)
pc=unreal.GameplayStatics.get_player_controller(world,0)
assert pawn and pc and 'BP_FPCharacter' in pawn.get_class().get_path_name()
capsule=pawn.get_component_by_class(unreal.CapsuleComponent)
movement=pawn.get_component_by_class(unreal.CharacterMovementComponent)
half=capsule.get_scaled_capsule_half_height();radius=capsule.get_scaled_capsule_radius()
assert 70<half<110,'Begin tests standing'
lib=unreal.get_default_object(unreal.load_class(None,'/Script/Engine.SubsystemBlueprintLibrary'))
sub=lib.call_method('GetLocalPlayerSubSystemFromPlayerController',args=(pc,unreal.EnhancedInputLocalPlayerSubsystem.static_class()))
assert sub
interact=unreal.load_asset('/Game/Input/Actions/IA_Interact')
time_action=unreal.load_asset('/Game/Input/Actions/IA_TimeAbility')
interaction_class=unreal.load_class(None,'/Game/Blueprints/Components/Player/AC_Interaction.AC_Interaction_C')
interaction=pawn.get_component_by_class(interaction_class)
assert interaction,'Real AC_Interaction required'
allactors=unreal.GameplayStatics.get_all_actors_of_class(world,unreal.Actor)
doors={a.get_actor_label().removeprefix('LabR17_Door_'):a for a in allactors if a.get_actor_label().startswith('LabR17_Door_')}
for id in ['R10-UP-NORTH','R9-TIME-EXIT','TR-CONNECT-PREP','C0']:assert id in doors,id
initial_position=pawn.get_actor_location();initial_rotation=pc.get_control_rotation()
initial_dilation=unreal.GameplayStatics.get_global_time_dilation(world)
assert abs(initial_dilation-1)<.01,'Start this suite outside time stop'

def vec(v):return [v.x,v.y,v.z]
def prop(obj,name):
    try:return obj.get_editor_property(name)
    except Exception:return None
def snapshot(id):
    d=doors[id];front=prop(d,'PromptFront');back=prop(d,'PromptBack')
    return {'door':id,'open':bool(prop(d,'bDoorOpen')),'alpha':float(prop(d,'OpenAlpha')),
            'locked':bool(prop(d,'bLocked')),'prompt_until':float(prop(d,'PromptUntil')),
            'real_time':unreal.GameplayStatics.get_real_time_seconds(world),
            'front_text':str(prop(front,'text')),'back_text':str(prop(back,'text')),
            'front_visible':bool(prop(front,'visible')),'back_visible':bool(prop(back,'visible')),
            'occupied':prop(d,'SafetyBounds').is_overlapping_actor(pawn),
            'global_time_dilation':unreal.GameplayStatics.get_global_time_dilation(world)}
def focused(id):
    observations={};ok=False
    for name in ['FocusedActor','FocusedInteractionArea','CurrentInteractionWidgetRef']:
        obj=prop(interaction,name);observations[name]=obj.get_path_name() if obj else None
        if obj==doors[id]:ok=True
        if isinstance(obj,unreal.Actor) and obj.get_parent_actor()==doors[id]:ok=True
    return ok,observations
def aim(id):
    camera=unreal.GameplayStatics.get_player_camera_manager(world,0)
    location=doors[id].get_actor_location();location.z+=float(prop(doors[id],'DoorHeight'))*.5
    pc.set_control_rotation(unreal.MathLibrary.find_look_at_rotation(camera.get_camera_location(),location))
def pose(id,offset):
    door=doors[id];point=door.get_actor_location()+door.get_actor_forward_vector()*offset
    point.z+=half+2
    movement.stop_movement_immediately();pawn.set_actor_location(point,False,True)
def inject(action,pressed):sub.inject_input_vector_for_action(action,unreal.Vector(1 if pressed else 0,0,0),[],[])
def clear_path(id):
    door=doors[id];centre=door.get_actor_location();centre.z+=half+3
    forward=door.get_actor_forward_vector()
    hit=unreal.SystemLibrary.capsule_trace_single_by_profile(world,centre-forward*110,centre+forward*110,
         radius,half,'Pawn',False,[pawn],unreal.DrawDebugTrace.NONE)
    if isinstance(hit,tuple):hit=next((x for x in hit if not isinstance(x,bool) and x is not None),None)
    if hit is None:return {'clear':True}
    values=hit.to_tuple();actor=values[9]
    return {'clear':not bool(values[0]),'blocking_actor':actor.get_actor_label() if actor else None,'initial_overlap':bool(values[1])}

steps=[]
def add(name,wait=0.0,start=None,tick=None,check=None):steps.append(dict(name=name,wait=wait,start=start,tick=tick,check=check))
def setup(id,offset=165):
    add('pose_'+id+'_'+str(offset),.15,lambda:pose(id,offset))
    add('focus_'+id,.65,tick=lambda elapsed:aim(id),check=lambda:(focused(id)[0],focused(id)[1]))
def press(action=interact,label='F'):
    add('press_'+label,.15,tick=lambda elapsed:inject(action,True))
    add('release_'+label,.10,start=lambda:inject(action,False))
def expect_state(id,expected,extra=None):
    s=snapshot(id);ok=s['open']==expected and (s['alpha']>.98 if expected else s['alpha']<.02)
    if extra:
        extra_ok,detail=extra(s);ok=ok and extra_ok;s.update(detail)
    return ok,s
def state_check(id,expected,name):add(name,1.1,check=lambda:expect_state(id,expected))

# Ordinary width 3.2m: close leaf blocks; F opens; a second F closes.
normal='R10-UP-NORTH'
setup(normal);add('normal_closed_collision',check=lambda:(not clear_path(normal)['clear'],clear_path(normal)))
press();state_check(normal,True,'normal_F_open');add('normal_open_collision',check=lambda:(clear_path(normal)['clear'],clear_path(normal)))
press();state_check(normal,False,'normal_F_close')
# Locked door uses the same F chain and both runtime text components.
locked='R9-TIME-EXIT'
setup(locked);press()
def locked_check():
    s=snapshot(locked);return (not s['open'] and s['alpha']<.02 and s['front_text']=='LOCKED' and s['back_text']=='LOCKED' and s['prompt_until']>s['real_time']),s
add('locked_F_feedback',.6,check=locked_check)
# Minimum-width 1.2m training link; validate capsule clearance once open.
small='TR-CONNECT-PREP'
setup(small);press();state_check(small,True,'small_F_open');add('small_capsule_clearance',check=lambda:(clear_path(small)['clear'],clear_path(small)))
press();state_check(small,False,'small_F_close')
# Sill occupied before F: no closing target and explicit feedback.
setup(normal);press();state_check(normal,True,'safety_setup_open')
setup(normal,110);press()
def blocked_check():
    s=snapshot(normal);return s['open'] and s['occupied'] and s['front_text']=='DOORWAY BLOCKED',s
add('occupied_F_rejected',.45,check=blocked_check)
# Start closing from clear ground, then step into the moving opening.
setup(normal,165);press()
add('closing_started',check=lambda:(not snapshot(normal)['open'],snapshot(normal)))
add('enter_closing_sill',.15,start=lambda:pose(normal,0))
state_check(normal,True,'closing_reverses_for_player')
setup(normal,165);press();state_check(normal,False,'safety_cleanup_close')
# Omen C0 opens from either side without F; leaving closes it.
for side in [1,-1]:
    add('C0_far_'+str(side),1.2,start=lambda side=side:pose('C0',side*650),check=lambda:expect_state('C0',False))
    add('C0_near_'+str(side),1.2,start=lambda side=side:pose('C0',side*250),check=lambda:expect_state('C0',True))
    add('C0_open_clear_'+str(side),check=lambda:(clear_path('C0')['clear'],clear_path('C0')))
    add('C0_leave_'+str(side),1.2,start=lambda side=side:pose('C0',side*650),check=lambda:expect_state('C0',False))
# Time stop is entered through the actual action. Focus is acquired beforehand.
setup(normal);press(time_action,'Q_time_ability')
add('time_ability_active',.25,check=lambda:(unreal.GameplayStatics.get_global_time_dilation(world)<.5,{'global_time_dilation':unreal.GameplayStatics.get_global_time_dilation(world)}))
press();state_check(normal,True,'F_open_during_time_ability')
press(time_action,'Q_restore')
add('time_ability_restored',.3,check=lambda:(abs(unreal.GameplayStatics.get_global_time_dilation(world)-1)<.01,{'global_time_dilation':unreal.GameplayStatics.get_global_time_dilation(world)}))

old=getattr(unreal,'_lab_r17_door_qa_handle',None)
if old is not None:
    try:unreal.unregister_slate_post_tick_callback(old)
    except Exception:pass
state={'index':-1,'started':time.monotonic(),'rows':[],'done':False,'phase':'next'}
def write(error=None):
    report={'done':state['done'],'error':error,'rows':state['rows'],
            'passed':state['done'] and error is None and all(x['passed'] for x in state['rows']),
            'frame_based':True,'input_evidence':'EnhancedInput IA_Interact and IA_TimeAbility. No direct door Interface/SetDoorOpen calls.',
            'initial_dilation':initial_dilation,'capsule_radius_cm':radius,'capsule_half_height_cm':half,
            'elapsed_seconds':time.monotonic()-state['started'],'current_step':steps[state['index']]['name'] if 0<=state['index']<len(steps) else None}
    REPORT.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
def finish(error=None):
    # Unregister before cleanup/reporting: even a cleanup exception cannot leave
    # a live callback repeatedly throwing on every editor frame.
    handle=getattr(unreal,'_lab_r17_door_qa_handle',None)
    unreal._lab_r17_door_qa_handle=None
    if handle is not None:
        try:unreal.unregister_slate_post_tick_callback(handle)
        except Exception:pass
    state['done']=True;state['phase']='finished'
    try:
        inject(interact,False);inject(time_action,False)
        movement.stop_movement_immediately();pawn.set_actor_location(initial_position,False,True);pc.set_control_rotation(initial_rotation)
    except Exception:
        error=(error+'\n' if error else '')+'Cleanup: '+traceback.format_exc()
    finally:write(error)
def tick(delta):
    if state['done']:return
    try:
        if state['phase']=='next':
            state['index']+=1
            if state['index']>=len(steps):finish();return
            step=steps[state['index']];state['step_started']=time.monotonic();state['phase']='wait'
            if step['start']:step['start']()
            write();return  # Always yield one real frame, even for zero-delay checks.
        step=steps[state['index']];elapsed=time.monotonic()-state['step_started']
        if step['tick']:step['tick'](elapsed)
        if elapsed>=step['wait']:
            if step['check']:
                ok,detail=step['check']();state['rows'].append({'name':step['name'],'passed':bool(ok),'detail':detail})
                if step['name'].startswith('focus_') and not ok:finish('Real interaction focus was not acquired; inspect the trace before retrying');return
            state['phase']='next';write()
    except Exception:finish(traceback.format_exc())
unreal._lab_r17_door_qa_handle=unreal.register_slate_post_tick_callback(tick)
write()
result={'started':True,'report':str(REPORT),'steps':len(steps),'note':'Asynchronous; allow real frames. Do not run another player-input test concurrently.'}
