"""Build exact placement schedule from the R17 geometry + imported manifest (no UE)."""
import hashlib,json
from pathlib import Path
OUT=Path(__file__).resolve().parent
R=OUT.parents[1]  # SourceAssets/LabV39/R17
PROJECT=OUT.parents[4]
SOURCE=R/'revised-layout-geometry.json'
def prepare():
    raw=SOURCE.read_bytes();geometry=json.loads(raw)
    architecture=json.loads((R/'architecture_report.json').read_text(encoding='utf-8'))
    manifest=json.loads((R/'patch_bundle'/'manifest.json').read_text(encoding='utf-8'))
    digest=hashlib.sha256(raw).hexdigest()
    assert digest==architecture['source_sha256'],'Architecture and plan have diverged'
    assert geometry['checks']['version']=='single_west_entry_R17'
    assert manifest['complete'] and manifest['scene_name']=='TimeShuttler_LabV39_R17_Patch'
    names={o['name'] for o in manifest['objects']}
    doors=[]
    for op in geometry['openings']:
        if op['kind']!='door':continue
        id=op['id']
        assert 'R17_Frame_'+id+'_0_-1' in names,('Missing imported frame',id)
        assert op['axis'] in ('h','v') and type(op['locked']) is bool
        floor=5.4 if op['z'] else 0.0
        doors.append({'id':id,'label':'LabR17_Door_'+id,
                      'blueprint':'/Game/Environment/LabR17/Blueprints/'+('BP_LabOmenDoor' if id=='C0' else 'BP_LabRoomDoor'),
                      'location_cm':[op['x']*100,-op['y']*100,(floor+op.get('sill',0))*100],
                      'rotation_degrees':{'pitch':0,'yaw':90 if op['axis']=='h' else 0,'roll':0},
                      'scale':[1,1,1], 'width_cm':op['width']*100,'height_cm':op['height']*100,
                      'leaf_thickness_cm':16.0,'locked':op['locked'],'automatic':id=='C0',
                      'phase':op.get('phase',''),'connects':op.get('connects',[]),
                      'destination':op.get('destination',''),'level':'B' if op['z'] else 'A'})
    assert len(doors)==78 and sum(d['automatic'] for d in doors)==1
    result={'source_geometry':SOURCE.relative_to(PROJECT).as_posix(),'source_sha256':digest,
            'scene_id':manifest['scene_id'],'manifest_revision':manifest['revision'],
            'manifest_snapshot_hash':manifest['snapshot_hash'],'target_map':'/Game/Maps/Map_LabV39.Map_LabV39',
            'coordinate_rule':'plan m (x,y,z) -> UE cm (100x,-100y, floor + sill); B floor is 5.4m, not the legacy z=4.5 level marker',
            'door_count':len(doors),'locked_count':sum(d['locked'] for d in doors),
            'fit_note':'Width/height match each clear aperture. 16cm leaf thickness is the new whitebox-door setting; no new frame is added.',
            'doors':doors}
    (OUT/'door_placement_plan.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    return result
if __name__=='__main__':
    r=prepare();print(json.dumps({k:r[k] for k in ['door_count','locked_count','source_sha256']}))
