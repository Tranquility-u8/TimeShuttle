"""Generate the native-runtime BP_OmenObserver graph; ordinary Python, no UE import."""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ASSET = '/Game/Characters/Omen/Blueprints/BP_OmenObserver'
ACTOR = '/Script/Engine.Actor'
MATH = '/Script/Engine.KismetMathLibrary'
GAME = '/Script/Engine.GameplayStatics'
SYSTEM = '/Script/Engine.KismetSystemLibrary'
nodes, links = [], []

def node(id, kind, x, y, **kw):
    nodes.append(dict(id=id, kind=kind, x=x, y=y, **kw))
    return id

def call(id, cls, function, x, y, **defaults):
    return node(id, 'call', x, y, **{'class': cls, 'function': function, 'defaults': defaults})

def get(id, var, x, y):
    return node(id, 'get', x, y, variable=var)

def setvar(id, var, x, y, **defaults):
    return node(id, 'set', x, y, variable=var, defaults=defaults)

def wire(a, ap, b, bp):
    links.append([a, ap, b, bp])

def execute(a, b, pin='then'):
    wire(a, pin, b, 'execute')

def comment(id, title, description, x, y, w, h, color='(R=0.04,G=0.12,B=0.20,A=1)'):
    node(id, 'comment', x, y, text=title+'\n'+description, width=w, height=h, color=color)

# BeginPlay only: cache the placed art's orientation, never recache on re-entry.
node('begin', 'event', 0, 0, **{'class': ACTOR, 'function': 'ReceiveBeginPlay'})
get('initRoot', 'OmenRoot', 0, 160)
call('initValid', SYSTEM, 'IsValid', 220, 160)
node('initBranch', 'branch', 440, 0)
call('restRead', ACTOR, 'K2_GetActorRotation', 440, 180)
setvar('cacheRest', 'RestRotation', 710, 0)
setvar('initializedSet', 'Initialized', 960, 0, Initialized='true')
wire('initRoot', 'OmenRoot', 'initValid', 'Object')
wire('initRoot', 'OmenRoot', 'restRead', 'self')
wire('initValid', 'ReturnValue', 'initBranch', 'Condition')
execute('begin', 'initBranch')
execute('initBranch', 'cacheRest')
wire('restRead', 'ReturnValue', 'cacheRest', 'RestRotation')
execute('cacheRest', 'initializedSet')
comment('cInit', '01 | Remember the placed pose',
        'Input: OmenRoot references the existing ShellUpper. Invalid reference: do nothing.\nCache RestRotation once so entering/leaving never changes the home pose.', -80, -160, 1330, 530)

# Gate each access; no pure-node boolean AND that might evaluate an invalid target.
node('tick', 'event', 0, 700, **{'class': ACTOR, 'function': 'ReceiveTick'})
get('initializedRead', 'Initialized', 0, 870)
node('tickInit', 'branch', 240, 700)
get('tickRoot', 'OmenRoot', 250, 1010)
call('tickValid', SYSTEM, 'IsValid', 490, 1010)
node('tickRootBranch', 'branch', 710, 700)
get('enabledRead', 'TrackingEnabled', 740, 880)
node('enabledBranch', 'branch', 980, 700)
execute('tick', 'tickInit')
wire('initializedRead', 'Initialized', 'tickInit', 'Condition')
execute('tickInit', 'tickRootBranch')
wire('tickRoot', 'OmenRoot', 'tickValid', 'Object')
wire('tickValid', 'ReturnValue', 'tickRootBranch', 'Condition')
execute('tickRootBranch', 'enabledBranch')
wire('enabledRead', 'TrackingEnabled', 'enabledBranch', 'Condition')
comment('cGuards', '02 | Safe tick and enable switch',
        'Missing art reference: no rotation writes. Tracking disabled: smoothly return home.\nOnly local player 0 is considered; no per-frame actor searches or collision queries.', -80, 530, 1330, 690)

call('pawn', GAME, 'GetPlayerPawn', 1400, 1010, PlayerIndex='0')
call('pawnValid', SYSTEM, 'IsValid', 1680, 1010)
node('pawnBranch', 'branch', 1920, 700)
call('pawnLocation', ACTOR, 'K2_GetActorLocation', 1940, 1010)
get('bounds', 'RoomBounds', 1400, 1260)
call('boundsTransform', '/Script/Engine.SceneComponent', 'K2_GetComponentToWorld', 1680, 1230)
call('boundsExtent', '/Script/Engine.BoxComponent', 'GetUnscaledBoxExtent', 1680, 1410)
call('inside', MATH, 'IsPointInBoxWithTransform', 2240, 1150)
node('insideBranch', 'branch', 2610, 700)
execute('enabledBranch', 'pawnBranch')
wire('pawn', 'ReturnValue', 'pawnValid', 'Object')
wire('pawnValid', 'ReturnValue', 'pawnBranch', 'Condition')
execute('pawnBranch', 'insideBranch')
wire('pawn', 'ReturnValue', 'pawnLocation', 'self')
wire('bounds', 'RoomBounds', 'boundsTransform', 'self')
wire('bounds', 'RoomBounds', 'boundsExtent', 'self')
wire('pawnLocation', 'ReturnValue', 'inside', 'Point')
wire('boundsTransform', 'ReturnValue', 'inside', 'BoxWorldTransform')
wire('boundsExtent', 'ReturnValue', 'inside', 'BoxExtent')
wire('inside', 'ReturnValue', 'insideBranch', 'Condition')
comment('cRoom', '03 | Room membership',
        'Pawn center inside RoomBounds activates tracking. Camera location is used only for aiming.\nThe box uses world transform + unscaled extents, so rotating/scaling the volume stays correct.', 1320, 530, 1570, 1120)

call('camera', GAME, 'GetPlayerCameraManager', 3050, 1010, PlayerIndex='0')
call('cameraValid', SYSTEM, 'IsValid', 3340, 1010)
node('cameraBranch', 'branch', 3580, 700)
call('cameraLocation', '/Script/Engine.PlayerCameraManager', 'GetCameraLocation', 3350, 1250)
get('aimRoot', 'OmenRoot', 3050, 1450)
call('rootLocation', ACTOR, 'K2_GetActorLocation', 3350, 1450)
call('lookAt', MATH, 'FindLookAtRotation', 3700, 1230)
get('modelOffset', 'ModelForwardOffset', 3700, 1490)
call('compose', MATH, 'ComposeRotators', 4020, 1230)
setvar('followTarget', 'TargetRotation', 4320, 700)
get('followSpeed', 'FollowSpeed', 4320, 1020)
setvar('followSpeedSet', 'ActiveSpeed', 4600, 700)
setvar('trackingTrue', 'IsTrackingPlayer', 4880, 700, IsTrackingPlayer='true')
execute('insideBranch', 'cameraBranch')
wire('camera', 'ReturnValue', 'cameraValid', 'Object')
wire('cameraValid', 'ReturnValue', 'cameraBranch', 'Condition')
execute('cameraBranch', 'followTarget')
wire('camera', 'ReturnValue', 'cameraLocation', 'self')
wire('aimRoot', 'OmenRoot', 'rootLocation', 'self')
wire('rootLocation', 'ReturnValue', 'lookAt', 'Start')
wire('cameraLocation', 'ReturnValue', 'lookAt', 'Target')
wire('modelOffset', 'ModelForwardOffset', 'compose', 'A')
wire('lookAt', 'ReturnValue', 'compose', 'B')
wire('compose', 'ReturnValue', 'followTarget', 'TargetRotation')
execute('followTarget', 'followSpeedSet')
wire('followSpeed', 'FollowSpeed', 'followSpeedSet', 'ActiveSpeed')
execute('followSpeedSet', 'trackingTrue')
comment('cFollow', '04 | Aim the existing model at the player camera',
        'Omen artwork faces local +Y; apply yaw -90 before the +X look-at rotation.\nComposeRotators(A=offset, B=look-at) is B * A. Preserve location, scale, meshes and materials.', 2970, 530, 2230, 1120)

get('restReadBack', 'RestRotation', 1400, 2150)
setvar('returnTarget', 'TargetRotation', 1680, 1900)
get('returnSpeed', 'ReturnSpeed', 1950, 2150)
setvar('returnSpeedSet', 'ActiveSpeed', 2210, 1900)
setvar('trackingFalse', 'IsTrackingPlayer', 2490, 1900, IsTrackingPlayer='false')
for branch in ('enabledBranch', 'pawnBranch', 'insideBranch', 'cameraBranch'):
    execute(branch, 'returnTarget', 'else')
wire('restReadBack', 'RestRotation', 'returnTarget', 'TargetRotation')
execute('returnTarget', 'returnSpeedSet')
wire('returnSpeed', 'ReturnSpeed', 'returnSpeedSet', 'ActiveSpeed')
execute('returnSpeedSet', 'trackingFalse')
comment('cReturn', '05 | Leave the room / disable / no player',
        'Choose the original pose and ReturnSpeed. The shared interpolation continues from the current pose.\nRe-entry during the return is continuous; no snapping or timers.', 1320, 1730, 1570, 630)

get('applyRoot', 'OmenRoot', 5470, 1110)
call('currentRotation', ACTOR, 'K2_GetActorRotation', 5720, 1110)
get('targetRead', 'TargetRotation', 5730, 1320)
get('speedRead', 'ActiveSpeed', 5450, 1530)
call('positiveSpeed', MATH, 'FMax', 5720, 1530, B='0.01')
call('interpolate', MATH, 'RInterpTo', 6050, 1110)
call('applyRotation', ACTOR, 'K2_SetActorRotation', 6430, 700, bTeleportPhysics='false')
wire('applyRoot', 'OmenRoot', 'currentRotation', 'self')
wire('applyRoot', 'OmenRoot', 'applyRotation', 'self')
wire('currentRotation', 'ReturnValue', 'interpolate', 'Current')
wire('targetRead', 'TargetRotation', 'interpolate', 'Target')
wire('tick', 'DeltaSeconds', 'interpolate', 'DeltaTime')
wire('speedRead', 'ActiveSpeed', 'positiveSpeed', 'A')
wire('positiveSpeed', 'ReturnValue', 'interpolate', 'InterpSpeed')
wire('interpolate', 'ReturnValue', 'applyRotation', 'NewRotation')
execute('trackingTrue', 'applyRotation')
execute('trackingFalse', 'applyRotation')
comment('cApply', '06 | One smooth rotation write',
        'RInterpTo uses Tick DeltaSeconds, following world time dilation. Speed stays > 0 (zero would snap).\nThe ShellUpper parent rotates; its five existing attached parts follow. No position/scale changes.', 5370, 530, 1580, 1120)

variables = [
    dict(name='OmenRoot', type='object', **{'class':ACTOR}, instance_editable=True),
    dict(name='TrackingEnabled', type='bool', default='True', instance_editable=True),
    dict(name='FollowSpeed', type='float', default='1.8', instance_editable=True),
    dict(name='ReturnSpeed', type='float', default='2.0', instance_editable=True),
    dict(name='ModelForwardOffset', type='rotator', default='(Pitch=0,Yaw=-90,Roll=0)', instance_editable=True),
    dict(name='RestRotation', type='rotator', default='(Pitch=0,Yaw=0,Roll=0)'),
    dict(name='TargetRotation', type='rotator', default='(Pitch=0,Yaw=0,Roll=0)'),
    dict(name='ActiveSpeed', type='float', default='2.0'),
    dict(name='Initialized', type='bool', default='False'),
    dict(name='IsTrackingPlayer', type='bool', default='False'),
]
tooltips = {
    'OmenRoot':'Existing ShellUpper actor; five original Omen parts must remain attached to it.',
    'TrackingEnabled':'Follow the local player inside RoomBounds. False smoothly returns to the initial pose.',
    'FollowSpeed':'Positive RInterpTo speed for looking at the player. Default 1.8.',
    'ReturnSpeed':'Positive RInterpTo speed for returning to the original pose. Default 2.0.',
    'ModelForwardOffset':'Existing Omen artwork faces local +Y; yaw -90 converts it to look-at +X.',
    'RestRotation':'Placed Omen rotation cached once at BeginPlay.',
    'TargetRotation':'Current desired world rotation, selected by follow/return path.',
    'ActiveSpeed':'Current positive smoothing speed selected by follow/return path.',
    'Initialized':'True only after the original Omen pose has been cached successfully.',
    'IsTrackingPlayer':'Debug state: true when the local pawn is in the room and its camera is valid.',
}
for variable in variables:
    variable['category'] = 'Omen|Settings' if variable.get('instance_editable') else 'Omen|Runtime'
    variable['tooltip'] = tooltips[variable['name']]
spec = dict(
    asset_path=ASSET, parent_class=ACTOR, variables=variables,
    components=[
        dict(name='SceneRoot', **{'class':'/Script/Engine.SceneComponent'}, properties={'Mobility':'Movable'}),
        dict(name='RoomBounds', **{'class':'/Script/Engine.BoxComponent'}, parent='SceneRoot', properties={
            'BoxExtent':'(X=2000,Y=2100,Z=1150)', 'bGenerateOverlapEvents':'False',
            'bHiddenInGame':'True', 'BodyInstance':'(CollisionEnabled=NoCollision)', 'Mobility':'Movable',
        }),
    ],
    defaults={'PrimaryActorTick':'(bCanEverTick=True,bStartWithTickEnabled=True,TickInterval=0.0)'},
    graphs=[dict(name='EventGraph', kind='event', replace=True, nodes=nodes, links=links)], compile=True, save=False,
)

def validate_spec(data):
    """Structure check only; UE compilation/pin contracts remain editor validation."""
    for graph in data['graphs']:
        ids = [n['id'] for n in graph['nodes']]
        assert len(ids) == len(set(ids)), 'duplicate node ID'
        for a, ap, b, bp in graph['links']:
            assert a in ids and b in ids and ap and bp, (a, ap, b, bp)
    assert all(n.get('class', '').startswith('/Script/Engine.') for n in nodes if n['kind'] in ('event','call'))
    return {'nodes':len(nodes), 'links':len(links), 'native_runtime_only':True}

if __name__ == '__main__':
    print(validate_spec(spec))
    (HERE/'BP_OmenObserver.spec.json').write_text(json.dumps(spec, ensure_ascii=False, indent=2), encoding='utf-8')
