"""Editor-only, coordinated execution by root; leaves the map dirty for targeted root save.

Uses the editor-only LabAuthoring plugin to author a pure native-runtime Blueprint.
Never edits mesh/material assets, reparents art, or saves unrelated packages.
"""
import json,os
from pathlib import Path
import unreal

PROJECT=Path(unreal.Paths.project_dir()).resolve()
SOURCE=Path(os.environ.get('TS_LAB_R17_AUTHORING_ROOT',str(PROJECT/'SourceAssets/LabV39/R17/runtime_authoring'))).resolve()
HERE=Path(unreal.Paths.project_saved_dir()).resolve()/'Agent'/'LabR17'/'omen'
HERE.mkdir(parents=True,exist_ok=True)
ASSET = '/Game/Characters/Omen/Blueprints/BP_OmenObserver'
OWNER = 'LabR17.OmenObserver'
MAP = '/Game/Maps/Map_LabV39.Map_LabV39'

def path(obj):
    return obj.get_path_name() if obj else None

def v(value):
    return [float(value.x), float(value.y), float(value.z)]

def r(value):
    return [float(value.pitch), float(value.yaw), float(value.roll)]

def snapshot(actor):
    comp = actor.get_component_by_class(unreal.StaticMeshComponent)
    return dict(name=actor.get_name(), path=path(actor), location=v(actor.get_actor_location()),
                rotation=r(actor.get_actor_rotation()), scale=v(actor.get_actor_scale3d()),
                parent=path(actor.get_attach_parent_actor()), mesh=path(comp.static_mesh),
                materials=[path(comp.get_material(i)) for i in range(comp.get_num_materials())],
                mobility=str(comp.mobility), collision_profile=str(comp.get_collision_profile_name()),
                collision_enabled=str(comp.get_collision_enabled()), physics=comp.is_simulating_physics())

world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
assert world.get_path_name() == MAP, f'Wrong map: {world.get_path_name()}'
assert not unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).is_in_play_in_editor(), 'Stop PIE first'
assert hasattr(unreal, 'LabAuthoringLibrary'), 'LabAuthoring editor module must be compiled and loaded first'
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
actors = actors_api.get_all_level_actors()
art = [a for a in actors if 'OmenV4' in [str(t) for t in a.tags]]
expected = {'ShellUpper','ShellLower','Eye','InnerRing','OuterRing','Pupil'}
assert len(art) == 6, f'Expected six existing Omen actors, found {len(art)}'
by_part = {}
for actor in art:
    matches = [str(t).split('.',1)[1] for t in actor.tags if str(t).startswith('OmenPart.')]
    assert len(matches) == 1 and matches[0] not in by_part
    by_part[matches[0]] = actor
assert set(by_part) == expected
omen = by_part['ShellUpper']
assert all(a.get_attach_parent_actor() == omen for a in art if a != omen), 'Attachment contract changed; inspect before applying'
assert all(not a.root_component.get_editor_property('absolute_rotation') for a in art)
assert all(not a.get_component_by_class(unreal.StaticMeshComponent).is_simulating_physics() for a in art)
before = [snapshot(a) for a in art]

existing = unreal.EditorAssetLibrary.load_asset(ASSET) if unreal.EditorAssetLibrary.does_asset_exist(ASSET) else None
if existing:
    assert unreal.EditorAssetLibrary.get_metadata_tag(existing, 'AuthoringOwner') == OWNER, 'Refuse to overwrite an unowned existing asset'
spec = json.loads((SOURCE/'omen'/'BP_OmenObserver.spec.json').read_text(encoding='utf-8'))
assert spec['asset_path'] == ASSET and spec.get('save') is False
spec['allow_existing'] = bool(existing)  # ownership was checked above; no unknown asset overwrite
report = json.loads(unreal.LabAuthoringLibrary.apply_spec(json.dumps(spec)))
(HERE/'omen_blueprint_apply.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
blueprint = unreal.EditorAssetLibrary.load_asset(ASSET)
# Mark a newly created but incomplete asset as ours, so root can repair pins and retry safely.
if blueprint and not existing:
    unreal.EditorAssetLibrary.set_metadata_tag(blueprint, 'AuthoringOwner', OWNER)
assert report.get('ok') and report.get('compile_errors', 0) == 0, f'Blueprint authoring failed; see omen_blueprint_apply.json: {report.get("errors")}'
assert blueprint
blueprint_class = unreal.EditorAssetLibrary.load_blueprint_class(ASSET)
assert blueprint_class

found = [a for a in actors if 'OmenObserver' in [str(t) for t in a.tags]]
assert len(found) <= 1, 'Multiple observers; inspect before applying'
observer = found[0] if found else actors_api.spawn_actor_from_class(blueprint_class, unreal.Vector(0,3100,1150))
assert observer and observer.get_class() == blueprint_class
observer.set_actor_label('LabV39_OmenObserver')
observer.set_folder_path('Characters/Omen/OmenV4')
observer.set_editor_property('tags', [unreal.Name('LabR17.Runtime'), unreal.Name('OmenObserver')])
observer.set_actor_location(unreal.Vector(0,3100,1150), False, False)
observer.set_actor_rotation(unreal.Rotator(pitch=0, yaw=0, roll=0), False)
observer.set_actor_scale3d(unreal.Vector(1,1,1))
observer.set_editor_property('OmenRoot', omen)
observer.set_editor_property('TrackingEnabled', True)
observer.set_editor_property('FollowSpeed', 1.8)
observer.set_editor_property('ReturnSpeed', 2.0)
observer.set_editor_property('ModelForwardOffset', unreal.Rotator(pitch=0, yaw=-90, roll=0))
actual_offset = observer.get_editor_property('ModelForwardOffset')
assert abs(actual_offset.pitch) < 0.001 and abs(actual_offset.yaw+90) < 0.001 and abs(actual_offset.roll) < 0.001, 'Model forward-axis offset was not applied correctly'
bounds = observer.get_component_by_class(unreal.BoxComponent)
assert bounds
bounds.set_box_extent(unreal.Vector(2000,2100,1150), False)
bounds.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
bounds.set_editor_property('generate_overlap_events', False)
bounds.set_hidden_in_game(True)
for actor in [omen] + [a for a in art if a != omen]:
    actor.get_component_by_class(unreal.StaticMeshComponent).set_mobility(unreal.ComponentMobility.MOVABLE)

after = [snapshot(a) for a in art]
keys = ['name','path','location','rotation','scale','parent','mesh','materials','collision_profile','collision_enabled','physics']
checks = {key: all(a[key] == b[key] for a,b in zip(before,after)) for key in keys}
assert all(checks.values()), f'Unexpected art change: {checks}'
assert unreal.EditorAssetLibrary.save_loaded_asset(blueprint, only_if_is_dirty=True), 'Blueprint package save failed'
result = dict(map=MAP, asset=ASSET, observer=path(observer), before=before, after=after,
              art_preservation_checks=checks, room_center=[0,3100,1150], room_extent=[2000,2100,1150],
              model_forward_offset_pitch_yaw_roll=r(actual_offset),
              map_saved=False, runtime_tested=False,
              note='Blueprint saved; map intentionally left dirty for root targeted save after PIE validation.')
(HERE/'omen_observer_apply_result.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
print(json.dumps({'ok':True,'asset':ASSET,'observer':path(observer),'art_preserved':all(checks.values()),'map_saved':False}))
