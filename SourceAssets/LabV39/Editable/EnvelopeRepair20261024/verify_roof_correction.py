from pathlib import Path
import sys,json,importlib.util,hashlib
R=Path(__file__).resolve().parent
S=R.parent
spec=importlib.util.spec_from_file_location('independent_mesh',R/'module_mesh_audit_helpers.py')
audit=importlib.util.module_from_spec(spec);spec.loader.exec_module(audit)
from shapely.ops import unary_union
from shapely import set_precision
P=json.loads((R/'roof_correction_plan.json').read_text(encoding='utf8'))
new=json.loads((R/'roof_correction_modules.json').read_text(encoding='utf8'))['modules']
old=json.loads((S/'modules.json').read_text(encoding='utf8'))['modules']
changed={r['module_id'] for r in P['fully_remove']+P['partially_clip']}
original=unary_union([audit.section(m,14.225)for m in old if m['source_volume']=='Main roof'])
actual=unary_union([audit.section(m,14.225)for m in old if m['source_volume']=='Main roof' and m['module_id'] not in changed]+[audit.section(m,14.225)for m in new])
cutter=audit.geomrows(P['cutter_footprint']);desired=original.difference(cutter)
checks=[audit.topology(m)for m in new]
bad=[q for q in checks if q['signed_volume_m3']<=0 or any(q[k]for k in ('unpaired_edges','incorrect_edge_orientation','duplicate_faces','degenerate_triangles'))]
diff=set_precision(actual,1e-5).symmetric_difference(set_precision(desired,1e-5)).area
actual_volume=sum(q['signed_volume_m3']for q in checks)
expected_volume=sum(audit.geomrows(m['footprint']).area*(m['z1']-m['z0'])for m in new)
lower=unary_union([audit.section(m,5.175)for m in old if m['z0']<5.175<m['z1']])
lower_gap=set_precision(audit.geomrows(P['removed_high_roof_footprint']),1e-5).difference(set_precision(lower,1e-5)).area
result={'passed':not bad and diff<.001 and abs(actual_volume-expected_volume)<.00001 and lower_gap<.001,'replacement_count':len(new),'bad_meshes':bad,'actual_section_difference_m2':diff,'newly_exposed_footprint_missing_lower_roof_m2':lower_gap,'actual_replacement_volume_m3':actual_volume,'expected_replacement_volume_m3':expected_volume,'plan_sha256':hashlib.sha256((R/'roof_correction_plan.json').read_bytes()).hexdigest(),'modules_sha256':hashlib.sha256((R/'roof_correction_modules.json').read_bytes()).hexdigest(),'rows':checks}
(R/'roof_correction_mesh_audit.json').write_text(json.dumps(result,indent=2),encoding='utf8')
print(json.dumps({k:v for k,v in result.items()if k!='rows'},indent=2))
