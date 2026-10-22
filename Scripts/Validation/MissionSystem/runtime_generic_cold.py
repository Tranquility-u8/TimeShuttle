import unreal,json,time,traceback
MF=ROOT/'MissionFlow';B='/Game/MissionSystem/'
w=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
p=unreal.GameplayStatics.get_player_pawn(w,0);pc=unreal.GameplayStatics.get_player_controller(w,0)
gs=unreal.get_default_object(unreal.GameplayStatics.static_class())
def cls(path):return unreal.load_class(None,path+'.'+path.rsplit('/',1)[-1]+'_C')
def get(o,k):return o.get_editor_property(k)
def call(o,n,*args):return o.call_method(n,args)
def state(o,k='FlowState'):return str(get(o,k)).split('.')[-1].strip('> ').upper()
def isstate(o,n,k='FlowState'):return n.upper() in str(get(o,k)).upper()
def spawn(name):
 a=gs.call_method('BeginDeferredActorSpawnFromClass',(w,cls(B+'Tests/BP_Test'+name),unreal.Transform(),unreal.SpawnActorCollisionHandlingMethod.ALWAYS_SPAWN,p))
 return gs.call_method('FinishSpawningActor',(a,unreal.Transform()))
def task(a,id):return call(a,'FindTask',unreal.Name(id))
report={'status':'running','checks':[],'started':time.time()};actors=[]
def save():(MF/'runtime-generic-cold.json').write_text(json.dumps(report,indent=2),encoding='utf8')
def check(n,v,detail=''):
 report['checks'].append(dict(name=n,passed=bool(v),detail=str(detail)));save()
 if not v:raise AssertionError(n+': '+str(detail))
def until(f,timeout=10,detail=lambda:''):
 end=time.monotonic()+timeout
 while not f():
  if time.monotonic()>end:raise AssertionError('Timed out: '+str(detail()))
  yield .03
def start(n):
 a=spawn(n);actors.append(a);return a
def destroy(a):a.destroy_actor();actors.remove(a)
def ready(a):return until(lambda:bool(get(a,'bInitialized')) or isstate(a,'FAILED'),detail=lambda:(get(a,'FlowState'),get(a,'LastError')))
def complete(a):return until(lambda:isstate(a,'COMPLETED'),detail=lambda:(get(a,'FlowState'),get(a,'LastError'),get(a,'PendingStep'),get(a,'CurrentTask')))
manager=p.get_component_by_class(cls('/Game/DialogSystem/Blueprints/AC_DialogueManager'))
endtype=type(get(manager,'LastEndReason'))
lib=unreal.get_default_object(cls('/Game/DialogSystem/Blueprints/BFL_Dialogue'))
meta=json.loads((MF/'dialogue-library-reflection.json').read_text())
order={f['name']:[v['name'] for v in f['params'] if not v['out']] for f in meta['functions']}
def allowed(name):
 values={'Player':p,'ActionName':unreal.Name(name),'__WorldContext':w}
 return call(lib,'AllowGameplayInput',*[values[n] for n in order['AllowGameplayInput']])
def cancel_dialog():call(manager,'CancelDialogue',endtype.CANCELLED_BY_STORY)
def tests():
 cancel_dialog();call(manager,'SetAutomatic',True)
 a=start('Basic');yield from complete(a)
 check('Derived Blueprint override executes through base task API',get(task(a,'Step0'),'ExtensionCalls')==1 and get(task(a,'Step2'),'ExtensionCalls')==1)
 check('Sequential steps complete exactly once',len(get(a,'CompletedSteps'))==3)
 destroy(a)
 for n in ['Invalid','Duplicate']:
  a=start(n);yield from until(lambda:isstate(a,'FAILED'))
  check(n+' configuration is rejected before executing any task',get(a,'CurrentTask') is None and bool(get(a,'LastError')),get(a,'LastError'));destroy(a)
 a=start('Background');begin=time.monotonic();yield from complete(a)
 check('Background task join waits for actual completion',time.monotonic()-begin>=.48)
 check('Join continuation executes once',get(task(a,'Step2'),'ExtensionCalls')==1);destroy(a)
 a=start('Timeout');yield from complete(a)
 check('Timeout follows configured failure route',isstate(task(a,'Step0'),'FAILED','TaskState') and get(task(a,'Recovery'),'ExtensionCalls')==1);destroy(a)
 a=start('Locks');yield from until(lambda:get(a,'CurrentTask') and str(get(get(a,'CurrentTask'),'StepId'))=='Step3')
 check('Releasing one lock preserves another movement lock',pc.is_move_input_ignored())
 check('Released look/gameplay lock restores only those inputs',not pc.is_look_input_ignored() and allowed('IA_Fire'))
 yield from complete(a);check('Normal completion releases all owned locks',not pc.is_move_input_ignored() and not pc.is_look_input_ignored());destroy(a)
 a=start('Locks');yield from until(lambda:pc.is_move_input_ignored())
 pc.set_ignore_move_input(True);call(a,'StopFlow',False,'QA cancel')
 check('Cancelling preserves an unrelated movement lock',pc.is_move_input_ignored())
 pc.set_ignore_move_input(False);check('Cancel does not leak its own lock',not pc.is_move_input_ignored() and allowed('IA_Fire'));destroy(a)
 a=start('Locks');yield from until(lambda:pc.is_move_input_ignored());destroy(a);yield .1
 check('Destroying flow owner releases locks',not pc.is_move_input_ignored())
 a=start('Pause');yield from until(lambda:get(a,'CurrentTask') is not None);t=task(a,'Step0');yield .2
 unreal.GameplayStatics.set_game_paused(w,True);before=get(t,'Elapsed');yield .5
 check('Pause suspends task elapsed time',abs(get(t,'Elapsed')-before)<.03)
 unreal.GameplayStatics.set_game_paused(w,False);yield from complete(a);destroy(a)
 unreal.GameplayStatics.set_global_time_dilation(w,.05)
 a=start('Pause');begin=time.monotonic();yield from complete(a)
 check('Task timers are independent of bullet time',.9<=time.monotonic()-begin<3,time.monotonic()-begin)
 unreal.GameplayStatics.set_global_time_dilation(w,1);destroy(a)
 a=start('Dialogue');yield from until(lambda:call(manager,'IsDialogueActive'))
 check('Dialogue step owns its exact request',get(manager,'ActiveSource')==task(a,'Step0'))
 yield from complete(a);check('Dialogue completion advances once',get(task(a,'Step1'),'ExtensionCalls')==1);destroy(a)
 a=start('Dialogue');yield from until(lambda:call(manager,'IsDialogueActive'));cancel_dialog()
 yield from until(lambda:isstate(a,'FAILED'))
 check('Cancelled dialogue never advances to success',get(task(a,'Step1'),'ExtensionCalls')==0 and bool(get(a,'LastError')))
 call(a,'RestartFlow',True);yield from complete(a)
 check('Restart rebinds callbacks without duplicate completion',get(task(a,'Step1'),'ExtensionCalls')==1);destroy(a)
 a=start('MissingDialogue');yield from until(lambda:isstate(a,'FAILED'));check('Invalid dialogue data fails visibly',bool(get(a,'LastError')));destroy(a)
 view=pc.get_view_target();a=start('Cutscene');yield from until(lambda:task(a,'Step0') is not None and get(task(a,'Step0'),'SequencePlayer') is not None)
 check('Cutscene applies configured look and movement locks',pc.is_move_input_ignored() and pc.is_look_input_ignored())
 check('Cutscene suppresses combat through player input gate',not allowed('IA_Fire'))
 yield .15
 check('Camera-cut track changes the view target',pc.get_view_target()!=view,str(pc.get_view_target()))
 pass
 yield from complete(a);check('Cutscene completion restores camera and input',pc.get_view_target()==view and not pc.is_move_input_ignored() and not pc.is_look_input_ignored())
 check('Cutscene completion destroys its temporary sequence actor',get(task(a,'Step0'),'SequenceActor') is None);destroy(a)
 a=start('Cutscene');yield from until(lambda:task(a,'Step0') is not None and get(task(a,'Step0'),'SequencePlayer') is not None)
 call(get(task(a,'Step0'),'SequencePlayer'),'Stop');yield from until(lambda:isstate(a,'FAILED'))
 check('Early sequence stop does not advance',get(task(a,'Step1'),'ExtensionCalls')==0)
 check('Interrupted sequence restores camera and locks',pc.get_view_target()==view and not pc.is_move_input_ignored());destroy(a)
 a=start('MissingCutscene');yield from until(lambda:isstate(a,'FAILED'));check('Missing sequence fails without locking player',not pc.is_move_input_ignored());destroy(a)
 gi=unreal.GameplayStatics.get_game_instance(w)
 check('Dialogue persistent memory remains disabled',not call(gi,'IsMemoryEnabled'))
 report['status']='passed';report['ended']=time.time();save()

gen=tests();next_time=time.monotonic()
def tick(dt):
 global next_time,handle
 if time.monotonic()<next_time:return
 try:next_time=time.monotonic()+next(gen)
 except StopIteration:unreal.unregister_slate_post_tick_callback(handle)
 except Exception:
  report['status']='failed';report['error']=traceback.format_exc();save();unreal.unregister_slate_post_tick_callback(handle)
  unreal.GameplayStatics.set_game_paused(w,False);unreal.GameplayStatics.set_global_time_dilation(w,1);cancel_dialog()
  for a in actors:
   if unreal.SystemLibrary.is_valid(a):call(a,'StopFlow',False,'QA failure cleanup');a.destroy_actor()
handle=unreal.register_slate_post_tick_callback(tick)
RESULT={'started':True}


