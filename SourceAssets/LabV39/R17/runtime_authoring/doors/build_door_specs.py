"""Generate pure-Blueprint door specifications. Normal Python; does NOT contact UE.

Apply with apply_doors.py only when the coordinator has loaded LabAuthoring.
Local coordinates: X is wall normal, Y spans aperture, Z is up. Origin at sill.
"""
import json
from pathlib import Path

OUT = Path(__file__).resolve().parent
ACTOR = '/Script/Engine.Actor'
SCENE = '/Script/Engine.SceneComponent'
PRIMITIVE = '/Script/Engine.PrimitiveComponent'
MATH = '/Script/Engine.KismetMathLibrary'
SYSTEM = '/Script/Engine.KismetSystemLibrary'
GAME = '/Script/Engine.GameplayStatics'
TEXT = '/Script/Engine.TextRenderComponent'
BASE = '/Game/Blueprints/Interactables/Interaction/BP_Interaction_Base.BP_Interaction_Base_C'
BPI = '/Game/Blueprints/Interfaces/BPI_Interaction.BPI_Interaction_C'
ROOM_ASSET = '/Game/Environment/LabR17/Blueprints/BP_LabRoomDoor'
AUTO_ASSET = '/Game/Environment/LabR17/Blueprints/BP_LabOmenDoor'


class Graph:
    def __init__(self, name, kind='function', inputs=None, outputs=None, pure=False):
        self.data = dict(name=name, kind=kind, clear=True, nodes=[], links=[])
        if inputs: self.data['inputs'] = inputs
        if outputs: self.data['outputs'] = outputs
        if pure: self.data['pure'] = True
        self.count = 0

    def node(self, id, kind, **kwargs):
        kwargs.setdefault('x', (self.count % 6) * 320)
        kwargs.setdefault('y', (self.count // 6) * 260)
        self.data['nodes'].append(dict(id=id, kind=kind, **kwargs))
        self.count += 1
        return id

    def call(self, id, fn, cls='', defaults=None):
        return self.node(id, 'call', function=fn, **({'class': cls} if cls else {}), **({'defaults': defaults} if defaults else {}))

    def get(self, name, id=None):
        return self.node(id or 'get_' + name, 'get', variable=name)

    def set(self, name, id=None, value=None):
        return self.node(id or 'set_' + name, 'set', variable=name, **({'defaults': {name: value}} if value is not None else {}))

    def link(self, a, ap, b, bp):
        self.data['links'].append([a, ap, b, bp])

    def val(self, a, b, bp, ap='ReturnValue'):
        self.link(a, ap, b, bp)

    def flow(self, *ids):
        for a,b in zip(ids, ids[1:]): self.link(a, 'then', b, 'execute')

    def member(self, name, node, pin='self'):
        id = 'v_' + node + '_' + name
        self.get(name, id); self.link(id, name, node, pin)

    def comment(self, text):
        self.node('comment', 'comment', text=text, x=-100, y=-100,
                  width=2100, height=max(400, ((self.count+5)//6)*260+200))
        return self.data


def ctor_component(name, cls, props):
    return dict(name=name, **{'class':cls}, parent='__BASE_ROOT__', properties=props)


def make_spec():
    variables = []
    def var(name, type, default, public=False, tooltip=''):
        variables.append(dict(name=name, type=type, default=default, instance_editable=public,
                              category='Lab Door', tooltip=tooltip))
    for n,d in [('DoorWidth',240),('DoorHeight',300),('DoorThickness',16),('OpenSeconds',0.8),('AutoDistance',260),('LeafClearance',4)]:
        var(n,'float',str(d),True,'Centimetres, except OpenSeconds. Keep actor scale at 1.')
    var('bLocked','bool','false',True,'Locked doors reject F. Set per instance; no new campaign unlock mechanism.')
    var('bAutomatic','bool','false',True,'Omen variant opens when the player is near; ordinary doors use existing F interaction.')
    var('bDoorOpen','bool','false')
    for n in ['OpenAlpha','LastRealTime','PromptUntil']: var(n,'float','0')
    components = []
    for name in ['LeafLeft','LeafRight']:
        components.append(ctor_component(name, '/Script/Engine.StaticMeshComponent', {
            'StaticMesh': {'object':'/Engine/BasicShapes/Cube.Cube'}, 'Mobility':'Movable',
            'BodyInstance':'(CollisionProfileName="BlockAllDynamic")',
            'bGenerateOverlapEvents':'false',
        }))
    for name in ['AutoBounds','SafetyBounds']:
        components.append(ctor_component(name, '/Script/Engine.BoxComponent', {
            'Mobility':'Movable', 'BoxExtent':'(X=260,Y=180,Z=200)',
            'BodyInstance':'(CollisionProfileName="Trigger")',
            'bGenerateOverlapEvents':'true', 'bHiddenInGame':'true',
        }))
    for name,yaw in [('PromptFront',0),('PromptBack',180)]:
        components.append(ctor_component(name, TEXT, {
            'Mobility':'Movable', 'Text':'LOCKED', 'WorldSize':'18',
            'HorizontalAlignment':'EHTA_Center','VerticalAlignment':'EVRTA_TextCenter',
            'RelativeRotation':f'(Pitch=0,Yaw={yaw},Roll=0)', 'bVisible':'false',
            'TextRenderColor':'(B=45,G=160,R=255,A=255)',
        }))

    graphs=[]
    # Dimensions are controlled by variables, not actor scaling. Keep both leaves collidable.
    g=Graph('ConfigureDoor'); g.node('entry','entry')
    for n in ['DoorWidth','DoorHeight','DoorThickness','AutoDistance']: g.get(n)
    for id,n,factor in [('halfWidth','DoorWidth',.5),('halfHeight','DoorHeight',.5),('scaleX','DoorThickness',.01),('scaleY','DoorWidth',.005),('scaleZ','DoorHeight',.01)]:
        g.call(id,'Multiply_DoubleDouble',MATH,{'B':str(factor)}); g.link('get_'+n,n,id,'A')
    g.call('scale','MakeVector',MATH)
    for id,pin in [('scaleX','X'),('scaleY','Y'),('scaleZ','Z')]: g.val(id,'scale',pin)
    chain=['entry']
    for leaf in ['LeafLeft','LeafRight']:
        n='scale_'+leaf; g.call(n,'SetRelativeScale3D',SCENE);g.member(leaf,n);g.val('scale',n,'NewScale3D');chain.append(n)
    g.call('halfWidthSafety','Add_DoubleDouble',MATH,{'B':'50'});g.val('halfWidth','halfWidthSafety','A')
    # The actual inherited interaction child is a 12 cm half-extent box.
    # Scale that existing contract to cover both door faces; do not add another F input.
    for id,source,factor,extra in [('areaX','DoorThickness',1/24,2/3),('areaY','DoorWidth',1/24,1/3),('areaZ','DoorHeight',1/24,1/6)]:
        g.call(id+'base','Multiply_DoubleDouble',MATH,{'B':str(factor)});g.link('get_'+source,source,id+'base','A')
        g.call(id,'Add_DoubleDouble',MATH,{'B':str(extra)});g.val(id+'base',id,'A')
    g.call('areaScale','MakeVector',MATH)
    for id,pin in [('areaX','X'),('areaY','Y'),('areaZ','Z')]:g.val(id,'areaScale',pin)
    g.call('scaleInteraction','SetRelativeScale3D',SCENE);g.member('InteractionArea','scaleInteraction');g.val('areaScale','scaleInteraction','NewScale3D');chain.append('scaleInteraction')
    g.call('areaCenter','MakeVector',MATH);g.val('halfHeight','areaCenter','Z')
    g.call('centreInteraction','K2_SetRelativeLocation',SCENE,{'bSweep':'false','bTeleport':'true'});g.member('InteractionArea','centreInteraction');g.val('areaCenter','centreInteraction','NewLocation');chain.append('centreInteraction')
    g.call('centreWidget','K2_SetRelativeLocation',SCENE,{'bSweep':'false','bTeleport':'true'});g.member('Widget','centreWidget');g.val('areaCenter','centreWidget','NewLocation');chain.append('centreWidget')
    for box,x in [('AutoBounds',None),('SafetyBounds','95')]:
        n='ignore_'+box;g.call(n,'SetCollisionResponseToAllChannels',PRIMITIVE,{'NewResponse':'ECR_Ignore'});g.member(box,n);chain.append(n)
        n='pawn_'+box;g.call(n,'SetCollisionResponseToChannel',PRIMITIVE,{'Channel':'ECC_Pawn','NewResponse':'ECR_Overlap'});g.member(box,n);chain.append(n)
        vec='extent_'+box;g.call(vec,'MakeVector',MATH,{'X':x} if x else None)
        if not x:g.link('get_AutoDistance','AutoDistance',vec,'X')
        g.val('halfWidthSafety',vec,'Y');g.val('halfHeight',vec,'Z')
        n='setextent_'+box;g.call(n,'SetBoxExtent','/Script/Engine.BoxComponent',{'bUpdateOverlaps':'true'});g.member(box,n);g.val(vec,n,'InBoxExtent');chain.append(n)
        loc='loc_'+box;g.call(loc,'MakeVector',MATH);g.val('halfHeight',loc,'Z')
        n='setloc_'+box;g.call(n,'K2_SetRelativeLocation',SCENE,{'bSweep':'false','bTeleport':'true'});g.member(box,n);g.val(loc,n,'NewLocation');chain.append(n)
    # Prompts use TextRender (cooked runtime component), not DevelopmentOnly PrintString.
    g.call('textZ','Multiply_DoubleDouble',MATH,{'B':'.65'});g.link('get_DoorHeight','DoorHeight','textZ','A')
    g.call('textX','Multiply_DoubleDouble',MATH,{'B':'.5'});g.link('get_DoorThickness','DoorThickness','textX','A')
    g.call('textOffset','Add_DoubleDouble',MATH,{'B':'5'});g.val('textX','textOffset','A')
    for component,sgn in [('PromptFront',1),('PromptBack',-1)]:
        g.call(component+'X','Multiply_DoubleDouble',MATH,{'B':str(sgn)});g.val('textOffset',component+'X','A')
        g.call(component+'Loc','MakeVector',MATH);g.val(component+'X',component+'Loc','X');g.val('textZ',component+'Loc','Z')
        n='loc_'+component;g.call(n,'K2_SetRelativeLocation',SCENE,{'bSweep':'false','bTeleport':'true'});g.member(component,n);g.val(component+'Loc',n,'NewLocation');chain.append(n)
    g.flow(*chain)
    graphs.append(g.comment('DIMENSIONS | Width/height in cm; two sliding leaves span the aperture. X wall normal, Y aperture width. Safety box is wider than the collision plane.'))

    g=Graph('ApplyDoorPose');g.node('entry','entry')
    for n in ['DoorWidth','DoorHeight','LeafClearance','OpenAlpha','PromptUntil']:g.get(n)
    for id,n,factor in [('halfHeight','DoorHeight',.5),('halfWidth','DoorWidth',.5),('quarterWidth','DoorWidth',.25)]:
        g.call(id,'Multiply_DoubleDouble',MATH,{'B':str(factor)});g.link('get_'+n,n,id,'A')
    g.call('travel','Add_DoubleDouble',MATH);g.val('halfWidth','travel','A');g.link('get_LeafClearance','LeafClearance','travel','B')
    g.call('travelAlpha','Multiply_DoubleDouble',MATH);g.val('travel','travelAlpha','A');g.link('get_OpenAlpha','OpenAlpha','travelAlpha','B')
    g.call('leafOffset','Add_DoubleDouble',MATH);g.val('quarterWidth','leafOffset','A');g.val('travelAlpha','leafOffset','B')
    chain=['entry']
    for leaf,sign in [('LeafLeft',-1),('LeafRight',1)]:
        g.call(leaf+'Y','Multiply_DoubleDouble',MATH,{'B':str(sign)});g.val('leafOffset',leaf+'Y','A')
        g.call(leaf+'Loc','MakeVector',MATH);g.val(leaf+'Y',leaf+'Loc','Y');g.val('halfHeight',leaf+'Loc','Z')
        n='pose_'+leaf;g.call(n,'K2_SetRelativeLocation',SCENE,{'bSweep':'false','bTeleport':'true'});g.member(leaf,n);g.val(leaf+'Loc',n,'NewLocation');chain.append(n)
    g.call('now','GetRealTimeSeconds',GAME)
    g.call('show','Less_DoubleDouble',MATH);g.val('now','show','A');g.link('get_PromptUntil','PromptUntil','show','B')
    for component in ['PromptFront','PromptBack']:
        n='show_'+component;g.call(n,'SetVisibility',SCENE,{'bPropagateToChildren':'false'});g.member(component,n);g.val('show',n,'bNewVisibility');chain.append(n)
    g.flow(*chain)
    graphs.append(g.comment('POSE | Smooth horizontal double opening. Collision stays enabled. Doorway occupancy is checked before every closing step. Prompts are visible from both sides.'))

    g=Graph('WakeDoor');g.node('entry','entry');g.call('now','GetRealTimeSeconds',GAME);g.set('LastRealTime');g.val('now','set_LastRealTime','LastRealTime')
    g.call('tickOn','SetActorTickEnabled',ACTOR,{'bEnabled':'true'});g.flow('entry','set_LastRealTime','tickOn')
    graphs.append(g.comment('WAKE | Reset real-time delta before movement. Tick runs only during animation or transient feedback.'))

    g=Graph('SetDoorOpen',inputs=[{'name':'WantsOpen','type':'bool'}]);g.node('entry','entry');g.set('bDoorOpen');g.link('entry','WantsOpen','set_bDoorOpen','bDoorOpen');g.call('wake','WakeDoor');g.flow('entry','set_bDoorOpen','wake')
    graphs.append(g.comment('TARGET | Set desired open state. Runtime scripts may call this after changing bLocked; story permissions remain outside the door.'))

    g=Graph('ShowDoorPrompt',inputs=[{'name':'Message','type':'string'}]);g.node('entry','entry');g.call('asText','Conv_StringToText','/Script/Engine.KismetTextLibrary');g.link('entry','Message','asText','InString')
    chain=['entry']
    for component in ['PromptFront','PromptBack']:
        n='text_'+component;g.call(n,'K2_SetText',TEXT);g.member(component,n);g.val('asText',n,'Value');chain.append(n)
    g.call('now','GetRealTimeSeconds',GAME);g.call('expiry','Add_DoubleDouble',MATH,{'B':'2'});g.val('now','expiry','A');g.set('PromptUntil');g.val('expiry','set_PromptUntil','PromptUntil');g.call('wake','WakeDoor');g.flow(*chain,'set_PromptUntil','wake')
    graphs.append(g.comment('FEEDBACK | Runtime text, shown for two real seconds. LOCKED or DOORWAY BLOCKED. No debug-only PrintString.'))

    g=Graph('DoorwayOccupied',outputs=[{'name':'Occupied','type':'bool'}],pure=True);g.node('entry','entry');g.node('result','result')
    g.call('player','GetPlayerPawn',GAME,{'PlayerIndex':'0'});g.call('overlap','IsOverlappingActor',PRIMITIVE);g.member('SafetyBounds','overlap');g.val('player','overlap','Other');g.val('overlap','result','Occupied');g.flow('entry','result')
    graphs.append(g.comment('SAFETY | Uses the pawn overlap of the sill box; null/unpossessed pawn safely returns false in native IsOverlappingActor.'))

    g=Graph('CheckAutomaticDoor');g.node('entry','entry');g.call('player','GetPlayerPawn',GAME,{'PlayerIndex':'0'});g.call('near','IsOverlappingActor',PRIMITIVE);g.member('AutoBounds','near');g.val('player','near','Other')
    g.get('bLocked');g.get('bDoorOpen');g.call('unlocked','Not_PreBool',MATH);g.link('get_bLocked','bLocked','unlocked','A')
    g.call('want','BooleanAND',MATH);g.val('near','want','A');g.val('unlocked','want','B')
    g.call('changed','NotEqual_BoolBool',MATH);g.val('want','changed','A');g.link('get_bDoorOpen','bDoorOpen','changed','B')
    g.node('branch','branch');g.val('changed','branch','Condition');g.call('change','SetDoorOpen');g.val('want','change','WantsOpen');g.flow('entry','branch');g.link('branch','then','change','execute')
    graphs.append(g.comment('OMEN AUTO | Near-player check at 10 Hz. Opens both leaves; waits until the player leaves before closing. Lock state remains instance-editable.'))

    g=Graph('UserConstructionScript');g.node('entry','entry');g.call('config','ConfigureDoor');g.call('pose','ApplyDoorPose');g.flow('entry','config','pose')
    graphs.append(g.comment('CONSTRUCTION | Size the door from instance parameters. Actor transform sets placement/orientation; keep scale at one.'))

    g=Graph('EventGraph',kind='event')
    g.node('begin','event',**{'class':ACTOR},function='ReceiveBeginPlay',x=0,y=0)
    g.node('parentBegin','call_parent',**{'class':BASE},function='ReceiveBeginPlay',x=320,y=0)
    g.call('config','ConfigureDoor');g.call('poseBegin','ApplyDoorPose');g.call('tickOffStart','SetActorTickEnabled',ACTOR,{'bEnabled':'false'})
    g.get('bAutomatic');g.node('isAuto','branch');g.link('get_bAutomatic','bAutomatic','isAuto','Condition');g.flow('begin','parentBegin','config','poseBegin','tickOffStart','isAuto')
    g.node('self','self');g.call('autoTimer','K2_SetTimer',SYSTEM,{'FunctionName':'CheckAutomaticDoor','Time':'.1','bLooping':'true'});g.link('self','self','autoTimer','Object');g.link('isAuto','then','autoTimer','execute')
    for suffix,event in [('Enter','ReceiveActorBeginOverlap'),('Leave','ReceiveActorEndOverlap')]:
        g.node('auto'+suffix,'event',**{'class':ACTOR},function=event)
        g.node('autoGate'+suffix,'branch');g.link('get_bAutomatic','bAutomatic','autoGate'+suffix,'Condition');g.flow('auto'+suffix,'autoGate'+suffix)
        g.call('autoCheck'+suffix,'CheckAutomaticDoor');g.link('autoGate'+suffix,'then','autoCheck'+suffix,'execute')
    # F follows the existing player interaction component and dialogue input gate.
    g.node('interact','event',**{'class':BPI},function='Interface_Interact',x=0,y=1800)
    g.node('manualOnly','branch');g.link('get_bAutomatic','bAutomatic','manualOnly','Condition');g.flow('interact','manualOnly')
    g.get('bLocked');g.node('locked','branch');g.link('get_bLocked','bLocked','locked','Condition');g.link('manualOnly','else','locked','execute')
    g.call('lockPrompt','ShowDoorPrompt',defaults={'Message':'LOCKED'});g.link('locked','then','lockPrompt','execute')
    g.get('bDoorOpen');g.node('currentlyOpen','branch');g.link('get_bDoorOpen','bDoorOpen','currentlyOpen','Condition');g.link('locked','else','currentlyOpen','execute')
    g.call('open','SetDoorOpen',defaults={'WantsOpen':'true'});g.link('currentlyOpen','else','open','execute')
    g.call('occupied','DoorwayOccupied');g.node('safeToClose','branch');g.val('occupied','safeToClose','Condition',ap='Occupied');g.link('currentlyOpen','then','safeToClose','execute')
    g.call('blockedPrompt','ShowDoorPrompt',defaults={'Message':'DOORWAY BLOCKED'});g.link('safeToClose','then','blockedPrompt','execute')
    g.call('close','SetDoorOpen',defaults={'WantsOpen':'false'});g.link('safeToClose','else','close','execute')
    # Tick is only awake while moving or showing a prompt. Reopen if a pawn enters during closing.
    g.node('tick','event',**{'class':ACTOR},function='ReceiveTick',x=0,y=3600)
    g.call('notOpen','Not_PreBool',MATH);g.link('get_bDoorOpen','bDoorOpen','notOpen','A');g.call('nearClosing','BooleanAND',MATH);g.val('notOpen','nearClosing','A');g.val('occupied','nearClosing','B',ap='Occupied')
    g.call('stillOpen','Greater_DoubleDouble',MATH,{'B':'.001'});g.link('get_OpenAlpha','OpenAlpha','stillOpen','A')
    g.call('isUnsafe','BooleanAND',MATH);g.val('nearClosing','isUnsafe','A');g.val('stillOpen','isUnsafe','B')
    g.node('safety','branch');g.val('isUnsafe','safety','Condition');g.flow('tick','safety');g.set('bDoorOpen','reopen','true');g.link('safety','then','reopen','execute')
    g.call('now','GetRealTimeSeconds',GAME);g.get('LastRealTime');g.get('OpenSeconds');g.get('OpenAlpha');g.get('PromptUntil')
    g.call('elapsed','Subtract_DoubleDouble',MATH);g.val('now','elapsed','A');g.link('get_LastRealTime','LastRealTime','elapsed','B');g.call('delta','FClamp',MATH,{'Min':'0','Max':'.05'});g.val('elapsed','delta','Value')
    g.call('duration','FMax',MATH,{'B':'.05'});g.link('get_OpenSeconds','OpenSeconds','duration','A');g.call('rate','Divide_DoubleDouble',MATH,{'A':'1'});g.val('duration','rate','B')
    g.call('target','Conv_BoolToDouble',MATH);g.link('get_bDoorOpen','bDoorOpen','target','InBool')
    g.call('interp','FInterpTo_Constant',MATH);g.link('get_OpenAlpha','OpenAlpha','interp','Current');g.val('target','interp','Target');g.val('delta','interp','DeltaTime');g.val('rate','interp','InterpSpeed')
    g.set('OpenAlpha');g.val('interp','set_OpenAlpha','OpenAlpha');g.link('safety','else','set_OpenAlpha','execute');g.flow('reopen','set_OpenAlpha')
    g.set('LastRealTime');g.val('now','set_LastRealTime','LastRealTime');g.call('poseTick','ApplyDoorPose');g.flow('set_OpenAlpha','set_LastRealTime','poseTick')
    g.call('atRest','NearlyEqual_FloatFloat',MATH,{'ErrorTolerance':'.001'});g.link('get_OpenAlpha','OpenAlpha','atRest','A');g.val('target','atRest','B')
    g.call('expired','GreaterEqual_DoubleDouble',MATH);g.val('now','expired','A');g.link('get_PromptUntil','PromptUntil','expired','B')
    g.call('canSleep','BooleanAND',MATH);g.val('atRest','canSleep','A');g.val('expired','canSleep','B');g.node('sleepBranch','branch');g.val('canSleep','sleepBranch','Condition');g.flow('poseTick','sleepBranch');g.call('sleep','SetActorTickEnabled',ACTOR,{'bEnabled':'false'});g.link('sleepBranch','then','sleep','execute')
    graphs.append(g.comment('RUNTIME | Existing F interface -> lock check -> toggle. Omen automatic variant uses proximity. Smooth motion uses bounded real delta and reverses safely if occupied.'))
    return dict(asset_path=ROOM_ASSET, parent_class=BASE, variables=variables, components=components,
                defaults={'PrimaryActorTick.bCanEverTick':'true','PrimaryActorTick.bStartWithTickEnabled':'true'},
                graphs=graphs, compile=True, save=False)


def validate(spec):
    functions={g['name'] for g in spec['graphs'] if g['kind']=='function'}
    for g in spec['graphs']:
        ids=[n['id'] for n in g['nodes']]
        assert len(ids)==len(set(ids)), (g['name'],'duplicate ids')
        for a,ap,b,bp in g['links']: assert a in ids and b in ids,(g['name'],a,b)
        for n in g['nodes']:
            if n['kind']=='call' and not n.get('class'): assert n['function'] in functions,n


def layout(spec):
    """Execution spine and nearby pure producers; source/links stay unchanged."""
    from door_graph_layout import layout_group
    event=next(g for g in spec['graphs'] if g['kind']=='event')
    def duplicate(old,new,targets):
        node=dict(next(n for n in event['nodes'] if n['id']==old));node['id']=new;event['nodes'].append(node)
        for link in event['links']:
            if link[0]==old and link[2] in targets:link[0]=new
    fids={'interact','manualOnly','get_bLocked','locked','lockPrompt','get_bDoorOpen','currentlyOpen','open','occupied','safeToClose','blockedPrompt','close'}
    autoids={n['id'] for n in event['nodes'] if n['id'].startswith(('autoEnter','autoLeave','autoGate','autoCheck'))}
    beginids={'begin','parentBegin','config','poseBegin','tickOffStart','get_bAutomatic','isAuto','self','autoTimer'}
    tickids={n['id'] for n in event['nodes'] if n['kind']!='comment'}-fids-autoids-beginids
    duplicate('get_bAutomatic','manualMode',fids);fids.add('manualMode')
    duplicate('get_bAutomatic','automaticMode',autoids);autoids.add('automaticMode')
    duplicate('get_bDoorOpen','tickTargetOpen',tickids);tickids.add('tickTargetOpen')
    duplicate('occupied','tickDoorwayOccupied',tickids);tickids.add('tickDoorwayOccupied')
    groups=[(beginids,'BEGIN PLAY | Preserve existing parent setup, configure dimensions, initialise motion and automatic polling.'),
            (autoids,'AUTOMATIC DOOR | Overlap enter/leave immediately reevaluate proximity. Timer also notices lock changes.'),
            (fids,'F INTERACTION | Existing interface only. Locked -> feedback. Open -> check sill. Clear -> toggle.'),
            (tickids,'MOTION AND SAFETY | Bounded real delta, reverse a closing leaf if occupied, sleep when settled and message expired.')]
    for graph in spec['graphs']:
        old_comments=[n.get('text','') for n in graph['nodes'] if n['kind']=='comment']
        graph['nodes']=[n for n in graph['nodes'] if n['kind']!='comment']
        localgroups=groups if graph is event else [({n['id'] for n in graph['nodes']},' '.join(old_comments))]
        top=0
        for gi,(ids,description) in enumerate(localgroups):
            bounds,top=layout_group(graph,ids,top)
            graph['nodes'].append(dict(id='section_'+str(gi),kind='comment',text=description,
                                       **bounds,
                                       color='(R=0.04,G=0.12,B=0.20,A=1)'))


if __name__=='__main__':
    spec=make_spec();layout(spec);validate(spec)
    (OUT/'room_door_spec.json').write_text(json.dumps(spec,ensure_ascii=False,indent=2),encoding='utf-8')
    auto=dict(asset_path=AUTO_ASSET,parent_class=ROOM_ASSET+'.BP_LabRoomDoor_C',
              defaults={'bAutomatic':'true','DoorWidth':'420','DoorHeight':'420','AutoDistance':'360'},
              graphs=[],compile=True,save=False)
    (OUT/'omen_door_spec.json').write_text(json.dumps(auto,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'graphs':len(spec['graphs']),'nodes':sum(len(g['nodes']) for g in spec['graphs']),
                      'links':sum(len(g['links']) for g in spec['graphs']), 'status':'specs only; no UE contact'}))
