"""PIE-only geometry fit audit; functional input is separately verified by qa_doors_pie."""
import unreal,json,time,traceback
from pathlib import Path
R=Path(unreal.Paths.project_saved_dir()).resolve()/'Agent'/'LabR17'/'doors'
R.mkdir(parents=True,exist_ok=True)
w=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world();assert w
p=unreal.GameplayStatics.get_player_character(w,0);c=p.get_component_by_class(unreal.CapsuleComponent)
ds=unreal.GameplayStatics.get_all_actors_with_tag(w,'LabR17.InteractiveDoor');assert len(ds)==78
old_position=p.get_actor_location()
auto=next(d for d in ds if d.get_actor_label()=='LabR17_Door_C0')
near=auto.get_actor_location()+auto.get_actor_forward_vector()*260;near.z+=c.get_scaled_capsule_half_height()+3
p.get_component_by_class(unreal.CharacterMovementComponent).stop_movement_immediately()
p.set_actor_location(near,False,True)
before=[(d,bool(d.get_editor_property('bDoorOpen')),bool(d.get_editor_property('bAutomatic'))) for d in ds]
for d,_,_ in before:
    d.set_editor_property('bAutomatic',False);d.call_method('SetDoorOpen',args=(True,))
state={'start':time.monotonic(),'done':False}
def tick(dt):
    if state['done'] or time.monotonic()-state['start']<1.4:return
    state['done']=True;unreal.unregister_slate_post_tick_callback(state['h'])
    rows=[];error=None
    try:
        for d in ds:
            centre=d.get_actor_location();centre.z+=c.get_scaled_capsule_half_height()+3
            normal=d.get_actor_forward_vector()
            hit=unreal.SystemLibrary.capsule_trace_single_by_profile(w,centre-normal*110,centre+normal*110,c.get_scaled_capsule_radius(),c.get_scaled_capsule_half_height(),'Pawn',False,[p],unreal.DrawDebugTrace.NONE)
            if isinstance(hit,tuple):hit=next((v for v in hit if not isinstance(v,bool) and v is not None),None)
            vals=hit.to_tuple() if hit else None
            blocked=bool(vals and vals[0]);a=vals[9] if vals else None
            rows.append({'door':d.get_actor_label(),'alpha':d.get_editor_property('OpenAlpha'),'clear':not blocked,'blocking_actor':a.get_actor_label() if a else None})
    except Exception:error=traceback.format_exc()
    finally:
        for d,opened,automatic in before:
            d.set_editor_property('bAutomatic',automatic);d.call_method('SetDoorOpen',args=(opened,))
        p.set_actor_location(old_position,False,True)
    report={'passed':not error and len(rows)==78 and all(r['clear'] and r['alpha']>.98 for r in rows),'error':error,'doors':rows,'scope':'Geometry fit in PIE, temporarily command doors open. Does not claim to test F input; see door_pie_qa.json for input evidence.'}
    (R/'all_door_fit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
state['h']=unreal.register_slate_post_tick_callback(tick)
result={'started':True,'doors':len(ds)}
