"""Coordinator-run asset creation. No map changes; no existing project BP changes.

Requires LabAuthoring compiled/loaded. Creates two new Blueprints, compiles, verifies,
then saves only those two packages. Existing target assets cause a guarded stop.
For deliberate iteration set ALLOW_EXISTING=True after reading its prior report.
"""
import hashlib,json,os
from pathlib import Path
import unreal

ALLOW_EXISTING=False
PROJECT=Path(unreal.Paths.project_dir()).resolve()
SOURCE=Path(os.environ.get('TS_LAB_R17_AUTHORING_ROOT',str(PROJECT/'SourceAssets/LabV39/R17/runtime_authoring'))).resolve()
OUT=Path(unreal.Paths.project_saved_dir()).resolve()/'Agent'/'LabR17'/'doors'
OUT.mkdir(parents=True,exist_ok=True)
assert hasattr(unreal,'LabAuthoringLibrary'),'Load LabAuthoring editor-only plugin before applying'
base='/Game/Blueprints/Interactables/Interaction/BP_Interaction_Base'
base_report=json.loads(unreal.LabAuthoringLibrary.inspect_blueprint(base))
base_class=json.loads(unreal.LabAuthoringLibrary.inspect_class(base+'.BP_Interaction_Base_C'))
assert base_report['ok'] and base_class['ok'],'Existing interaction base could not be inspected'
functions={x['name']:x for x in base_class['functions']}
assert 'Interface_Interact' in functions,'F interface missing; do not add a competing input binding'
iface=functions['Interface_Interact']
assert not iface['params'],'Interaction signature changed; inspect before connecting an override'
roots=[x['name'] for x in base_report['components'] if x['class']=='/Script/Engine.SceneComponent']
root=next((n for n in ('DefaultRoot','DefaultSceneRoot') if n in roots),None)
assert root, f'Cannot identify inherited root safely: {base_report["components"]}'
reports=[]
for filename in ('room_door_spec.json','omen_door_spec.json'):
    spec=json.loads((SOURCE/'doors'/filename).read_text(encoding='utf-8'))
    spec['allow_existing']=ALLOW_EXISTING
    for component in spec.get('components',[]):
        if component.get('parent')=='__BASE_ROOT__':component['parent']=root
    report=json.loads(unreal.LabAuthoringLibrary.apply_spec(json.dumps(spec)))
    reports.append(report)
    (OUT/(filename.replace('_spec.json','_apply_report.json'))).write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    assert report.get('ok') and report.get('compile_errors',0)==0, report.get('errors')
    # Ensure emitted graphs have no editor-helper runtime function calls.
    assert '/Script/LabAuthoring.' not in json.dumps(report['blueprint'])
for report in reports:
    path=report['blueprint']['asset'].split('.')[0]
    assert unreal.EditorAssetLibrary.save_asset(path,only_if_is_dirty=True),path
result={'created':[r['blueprint']['asset'] for r in reports],
        'compile':[{'errors':r.get('compile_errors'),'warnings':r.get('compile_warnings')} for r in reports],
        'source_specs':{name:hashlib.sha256((SOURCE/'doors'/name).read_bytes()).hexdigest() for name in ('room_door_spec.json','omen_door_spec.json')},
        'map_modified':False,'runtime_playtest':'not yet performed'}
(OUT/'door_build_result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
