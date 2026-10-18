"""Run only in an active PIE session, with no other automated player test running.

Nonblocking Slate sampling (~20 s). Temporarily teleports the PIE pawn between
test points, restores it on completion, and writes evidence without saving assets.
This verifies controller math/state; human PIE still checks visual/collision feel.
"""
import json
import math
import time
from pathlib import Path
import unreal

HERE = Path(unreal.Paths.project_saved_dir()).resolve()/'Agent'/'LabR17'/'omen'
world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
assert world and unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).is_in_play_in_editor(), 'Start PIE first'
pawn = unreal.GameplayStatics.get_player_pawn(world, 0)
camera = unreal.GameplayStatics.get_player_camera_manager(world, 0)
assert pawn and camera, 'Local player and camera must be ready'
observers = unreal.GameplayStatics.get_all_actors_with_tag(world, 'OmenObserver')
assert len(observers) == 1, 'Expected exactly one PIE observer'
observer = observers[0]
assert observer.get_class().get_path_name() == '/Game/Characters/Omen/Blueprints/BP_OmenObserver.BP_OmenObserver_C'
omen = observer.get_editor_property('OmenRoot')
assert omen and observer.get_editor_property('Initialized'), 'Observer not initialized'
parts = unreal.GameplayStatics.get_all_actors_with_tag(world, 'OmenV4')
assert len(parts) == 6
original_location = pawn.get_actor_location()
original_rotation = pawn.get_actor_rotation()
rest = observer.get_editor_property('RestRotation')
original_enabled = observer.get_editor_property('TrackingEnabled')
observer.set_editor_property('TrackingEnabled', True)

def vec(value):
    return [float(value.x), float(value.y), float(value.z)]

def rot(value):
    return [float(value.pitch), float(value.yaw), float(value.roll)]

def angle_delta(a, b):
    return abs((a-b+180) % 360-180)

def aim_error():
    eye = omen.get_actor_location()
    target = camera.get_camera_location()
    d = [target.x-eye.x, target.y-eye.y, target.z-eye.z]
    n = math.sqrt(sum(x*x for x in d))
    forward = vec(omen.get_actor_right_vector()) # mesh front is local +Y
    dot = sum(d[i]*forward[i] for i in range(3))/max(n, 0.0001)
    return math.degrees(math.acos(max(-1.0, min(1.0, dot))))

baseline = {a.get_name(): {'location':vec(a.get_actor_location()), 'scale':vec(a.get_actor_scale3d())} for a in parts}
phases = [
    ('outside_initial', (0,700,200), 2.5, False),
    ('inside_left', (-1100,1800,200), 3.5, True),
    ('inside_right', (1100,1800,200), 3.5, True),
    ('short_exit', (0,700,200), 0.35, False),
    ('reenter_during_return', (-1100,1800,200), 3.0, True),
    ('outside_final', (0,700,200), 4.5, False),
]
state = {'phase':0, 'start':time.monotonic(), 'phase_start':time.monotonic(),
         'last_sample':0.0, 'samples':[], 'handle':None, 'finished':False}

def place(index):
    _, loc, _, _ = phases[index]
    if hasattr(pawn, 'character_movement') and pawn.character_movement:
        pawn.character_movement.stop_movement_immediately()
    pawn.set_actor_location(unreal.Vector(*loc), False, True)

def finish(error=None):
    if state['finished']:
        return
    state['finished'] = True
    if state['handle'] is not None:
        unreal.unregister_slate_post_tick_callback(state['handle'])
    restore_error = None
    try:
        observer.set_editor_property('TrackingEnabled', original_enabled)
        pawn.set_actor_location(original_location, False, True)
        pawn.set_actor_rotation(original_rotation, True)
    except Exception as exc:
        restore_error = str(exc)
    checks = {}
    grouped = {name: [s for s in state['samples'] if s['phase']==name] for name,_,_,_ in phases}
    for name, _, _, expected in phases:
        samples = grouped[name]
        checks[name+'_recorded'] = len(samples) >= 2
        checks[name+'_state'] = bool(samples) and samples[-1]['tracking'] == expected
        if expected:
            checks[name+'_aligned_under_3_degrees'] = bool(samples) and samples[-1]['aim_error'] < 3.0
    end = grouped['outside_final']
    checks['returns_home_under_1_degree'] = bool(end) and end[-1]['rest_error'] < 1.0
    for name in ['inside_left','inside_right','outside_final']:
        samples = grouped[name]
        if samples:
            values = [s['aim_error' if name!='outside_final' else 'rest_error'] for s in samples]
            checks[name+'_smooth_intermediate_samples'] = sum(x>2.0 for x in values) >= 2 and values[-1] < values[0]
        else:
            checks[name+'_smooth_intermediate_samples'] = False
    checks['all_parts_keep_location_scale'] = all(s['art_transform_preserved'] for s in state['samples']) and bool(state['samples'])
    checks['child_parts_follow_parent'] = all(s['child_rotation_error'] < 0.01 for s in state['samples']) and bool(state['samples'])
    report = {'ok': not error and not restore_error and all(checks.values()), 'error':error,
              'restore_error':restore_error, 'checks':checks, 'samples':state['samples'],
              'scope':'PIE only, no editor assets/map saved; teleport setup tests activation/rotation, not navigation',
              'still_required':['Visual review of Omen and graph layout','Real walking collision check','Output Log review','Saved map reload check']}
    (HERE/'omen_pie_check.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    unreal.log('Omen PIE sampling complete: '+json.dumps({'ok':report['ok'],'checks':checks,'error':error}))

def tick(delta_seconds):
    try:
        now = time.monotonic()
        if now-state['start'] > 35:
            finish('35 second wall clock timeout')
            return
        if not unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).is_in_play_in_editor():
            finish('PIE ended before sampling completed')
            return
        phase_name, _, duration, _ = phases[state['phase']]
        age = now-state['phase_start']
        if now-state['last_sample'] >= 0.05:
            rr = rot(omen.get_actor_rotation())
            preserved = all(max(abs(x-y) for x,y in zip(vec(a.get_actor_location()),baseline[a.get_name()]['location'])) < 0.01
                            and max(abs(x-y) for x,y in zip(vec(a.get_actor_scale3d()),baseline[a.get_name()]['scale'])) < 0.0001 for a in parts)
            child_err = max(max(angle_delta(x,y) for x,y in zip(rot(a.get_actor_rotation()),rr)) for a in parts)
            state['samples'].append({'phase':phase_name, 'seconds':round(age,3), 'rotation':rr,
                'tracking':bool(observer.get_editor_property('IsTrackingPlayer')), 'pawn':vec(pawn.get_actor_location()),
                'aim_error':aim_error(), 'rest_error':max(angle_delta(x,y) for x,y in zip(rr,rot(rest))),
                'art_transform_preserved':preserved, 'child_rotation_error':child_err})
            state['last_sample'] = now
        if age >= duration:
            state['phase'] += 1
            if state['phase'] == len(phases):
                finish()
                return
            place(state['phase'])
            state['phase_start'] = now
    except Exception as exc:
        finish(repr(exc))

place(0)
state['handle'] = unreal.register_slate_post_tick_callback(tick)
print('Started Omen PIE sampling; do not run another player automation until omen_pie_check.json is written.')
