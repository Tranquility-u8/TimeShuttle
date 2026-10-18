"""Coordinator-only. Place managed R17 doors; preserve all architecture/old actors.

Uses the reviewed door_placement_plan.json. Does not add frames and does not save
the map automatically. Rerun updates only this task's tagged door actors.
"""
import hashlib,json,os
from pathlib import Path
import unreal
PROJECT=Path(unreal.Paths.project_dir()).resolve()
SOURCE=Path(os.environ.get('TS_LAB_R17_AUTHORING_ROOT',str(PROJECT/'SourceAssets/LabV39/R17/runtime_authoring'))).resolve()
OUT=Path(unreal.Paths.project_saved_dir()).resolve()/'Agent'/'LabR17'/'doors'
OUT.mkdir(parents=True,exist_ok=True)
PLAN=json.loads((SOURCE/'doors'/'door_placement_plan.json').read_text(encoding='utf-8'))
assert hashlib.sha256((PROJECT/PLAN['source_geometry']).read_bytes()).hexdigest()==PLAN['source_sha256'],'Plan changed since placement review'
build=json.loads((OUT/'door_build_result.json').read_text(encoding='utf-8'))
assert build.get('source_specs')=={name:hashlib.sha256((SOURCE/'doors'/name).read_bytes()).hexdigest() for name in ('room_door_spec.json','omen_door_spec.json')},'Run the tracked apply_doors.py against these exact specs before placement; stale Saved reports are not accepted'
assert len(build['created'])==2 and all(x['errors']==0 for x in build['compile'])
world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
assert world.get_path_name()==PLAN['target_map'],'Wrong active map'
assert not unreal.EditorLevelLibrary.get_game_world(),'Stop PIE before actor placement'
sub=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
TAG='LabR17.InteractiveDoor'
ids={d['label'] for d in PLAN['doors']}
allactors=sub.get_all_level_actors()
managed=[a for a in allactors if TAG in [str(t) for t in a.tags]]
assert all(a.get_actor_label().startswith('LabR17_Door_') and a.get_actor_label() in ids for a in managed),'Unexpected managed actor; inspect rather than delete'
assert not [a for a in allactors if a.get_actor_label() in ids and a not in managed],'Label collision with unowned actor'
classes={}
for path in {d['blueprint'] for d in PLAN['doors']}:
    cls=unreal.load_class(None,path+'.'+path.rsplit('/',1)[-1]+'_C')
    assert cls,path
    classes[path]=cls
material=unreal.load_asset('/Game/Environment/TrainingRoom/Materials/M_TR_M_Door_satin_graphite')
assert material,'Existing training-room graphite door material missing'
created=[]
with unreal.ScopedEditorTransaction('Place R17 interactive laboratory doors'):
    for actor in managed:assert sub.destroy_actor(actor)
    for d in PLAN['doors']:
        actor=sub.spawn_actor_from_class(classes[d['blueprint']],unreal.Vector(*d['location_cm']),unreal.Rotator(**d['rotation_degrees']))
        assert actor,d['id']
        actor.set_actor_label(d['label'])
        actor.tags=[unreal.Name(TAG),unreal.Name('LabR17.DoorID:'+d['id']),unreal.Name('LabR17.Phase:'+d['phase'])]
        actor.set_folder_path('LabV39/R17/InteractiveDoors/'+d['level'])
        actor.set_actor_scale3d(unreal.Vector(1,1,1))
        for key,value in {'DoorWidth':d['width_cm'],'DoorHeight':d['height_cm'],'DoorThickness':d['leaf_thickness_cm'],
                          'bLocked':d['locked'],'bAutomatic':d['automatic'],
                          'AutoDistance':360.0 if d['automatic'] else 260.0}.items():
            actor.set_editor_property(key,value)
        # Reapply the new values even if Python property edits did not rerun the construction script.
        actor.call_method('ConfigureDoor');actor.call_method('ApplyDoorPose')
        leaves=[]
        for name in ('LeafLeft','LeafRight'):
            comp=actor.get_editor_property(name)
            assert isinstance(comp,unreal.StaticMeshComponent),(d['id'],name)
            comp.set_material(0,material);leaves.append(comp)
        # Editor-side exact geometry check before any map save.
        expected=unreal.Vector(d['leaf_thickness_cm']/100,d['width_cm']/200,d['height_cm']/100)
        assert all((c.get_editor_property('relative_scale3d')-expected).length()<.001 for c in leaves),d['id']
        created.append({'id':d['id'],'actor':actor.get_path_name(),'label':actor.get_actor_label(),
                        'locked':bool(actor.get_editor_property('bLocked')),
                        'location':str(actor.get_actor_location()),'width_cm':actor.get_editor_property('DoorWidth'),
                        'height_cm':actor.get_editor_property('DoorHeight')})
sub.set_selected_level_actors([])
result={'placed':len(created),'replaced_managed':len(managed),'source_sha256':PLAN['source_sha256'],
        'new_frames':0,'unrelated_actors_deleted':0,'saved_map':False,'doors':created}
(OUT/'door_placement_result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
result={k:v for k,v in result.items() if k!='doors'}
