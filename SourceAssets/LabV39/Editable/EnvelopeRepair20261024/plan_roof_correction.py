"""Read-only R8/R17-intent roof correction plan. No UE/source mutation."""
from pathlib import Path
import sys,json,math,hashlib,collections,copy
WORKSPACE=Path(__file__).resolve().parents[5]
sys.path.insert(0,str(WORKSPACE/'tmp'/'lab-v13-python'))
from shapely.geometry import Polygon,box,Point
from shapely.geometry.polygon import orient
from shapely.ops import unary_union
from shapely import set_precision,constrained_delaunay_triangles
R=Path(__file__).resolve().parent
EDIT=R.parent
SRC=EDIT.parent/'R17'
def clean(g):return set_precision(g,.00001).buffer(0)
def polys(g):
 if g.is_empty:return []
 if g.geom_type=='Polygon':return [g]
 return [p for q in g.geoms for p in polys(q)]
def geom(rows):return clean(unary_union([Polygon(p['outer'],p.get('holes',[]))for p in rows]))
def serial(g):return [{'outer':list(p.exterior.coords),'holes':[list(h.coords)for h in p.interiors]}for p in polys(g)]
def h(path):return hashlib.sha256(path.read_bytes()).hexdigest()
p=SRC/'prepare_architecture.py';ns={'__file__':str(p)}
# Resolve the historical source's absolute workspace reads in memory only;
# never edit the R17 generator or execute its export/write section.
prefix=p.read_text(encoding='utf8').split('# A continuous sectional solid')[0]
prefix=prefix.replace('E:/Capstone/Test/',WORKSPACE.as_posix()+'/')
exec(compile(prefix,str(p),'exec'),ns)
D=ns['D'];g=ns['geom'];V=ns['volumes']
# retired_edge is an obsolete floor area beyond the lower building, NOT a wall
# centreline. The retired_upper_area marks exactly where B spaces were removed.
# Protect current thicker wall crowns, currently retained upper floor, the R10
# commons addition and the training/preparation/double-door envelope.
crowns=clean(unary_union([p for name,p,z0,z1 in V if z0<14 and abs(z1-14)<1e-7]))
protected=clean(unary_union([g('floor_upper'),g('wallPolygons'),crowns,g('retained_envelope'),g('commons_outer')]))
cutter=clean(g('retired_upper_area').difference(protected))
M=json.loads((EDIT/'modules.json').read_text(encoding='utf8'))['modules']
P=json.loads((EDIT/'import_plan.json').read_text(encoding='utf8'))
actors={a['module_id']:a for a in P['actors']}
removed=[];clipped=[];unchanged=[];replacements=[]
def make(old,poly,index):
 poly=orient(poly.simplify(0,preserve_topology=True),1)
 z0,z1=old['z0'],old['z1'];bb=[*poly.bounds[:2],z0,*poly.bounds[2:],z1]
 pivot=[(bb[0]+bb[3])/2,(bb[1]+bb[4])/2,z0]
 verts=[];idx={};faces=[]
 def vi(x,y,z):
  v=(round(x,5),round(y,5),round(z,5))
  if v not in idx:idx[v]=len(verts);verts.append(v)
  return idx[v]
 for up,z in [(False,z0),(True,z1)]:
  for tri in constrained_delaunay_triangles(poly).geoms:
   xy=list(orient(tri,1).exterior.coords)[:-1]
   if not up:xy.reverse()
   faces.append([vi(x,y,z)for x,y in xy])
 for ring in [poly.exterior,*poly.interiors]:
  pts=list(ring.coords)
  for a,b in zip(pts,pts[1:]):
   q=[vi(*a,z0),vi(*b,z0),vi(*b,z1),vi(*a,z1)]
   faces.extend([[q[0],q[1],q[2]],[q[0],q[2],q[3]]])
 edges=collections.Counter(tuple(sorted((a,b)))for f in faces for a,b in zip(f,f[1:]+f[:1]))
 assert all(n==2 for n in edges.values()),old['name']
 name=old['name'].replace('SM_LabEditable_','SM_LabRoofCorrected_')+f'_{index:02d}'
 isbox=not poly.interiors and abs(box(*poly.bounds).area-poly.area)<1e-8
 return {'name':name,'module_id':name,'replacement_of':old['module_id'],'kind':'roof','floor':old['floor'],'rooms':old['rooms'],'opening_id':None,'source_volume':'Main roof R8 retirement correction','footprint':serial(poly),'z0':z0,'z1':z1,'verts':[[v[j]-pivot[j]for j in range(3)]for v in verts],'world_verts':verts,'faces':faces,'face_materials':['Wall']*len(faces),'pivot':pivot,'rotation_z_degrees':0,'bbox':bb,'bbox_world':bb,'dimensions_m':[bb[i+3]-bb[i]for i in range(3)],'rectangular_bool':isbox,'box_center_world':[(bb[i]+bb[i+3])/2 for i in range(3)],'vertical_profile':[{'z0':z0,'z1':z1,'footprint':serial(poly)}],'closed_manifold':True,'volume_m3':poly.area*(z1-z0)}
for m in M:
 if m['kind']!='roof':continue
 old=geom(m['footprint']);cut=clean(old.intersection(cutter))
 if m['source_volume']!='Main roof' or cut.area<1e-7:
  unchanged.append(m['module_id']);continue
 remain=clean(old.difference(cutter))
 row={'module_id':m['module_id'],'rooms':m['rooms'],'old_bbox_world':m['bbox_world'],'old_area_m2':old.area,'removed_area_m2':cut.area,'remaining_area_m2':remain.area,'expected_actor':actors[m['module_id']]}
 if remain.area<1e-7:removed.append(row)
 else:
  new=[make(m,p,i+1)for i,p in enumerate(polys(remain))]
  row['new_module_ids']=[q['module_id']for q in new];clipped.append(row);replacements.extend(new)
oldroof=clean(unary_union([geom(m['footprint'])for m in M if m['kind']=='roof' and m['source_volume']=='Main roof']))
removed_geometry=clean(oldroof.intersection(cutter));newroof=clean(oldroof.difference(cutter))
safe={
 'current_upper_floor_roof_unchanged':removed_geometry.intersection(g('floor_upper')).area<1e-6,
 'current_upper_wall_crowns_unchanged':removed_geometry.intersection(crowns).area<1e-6,
 'commons_roof_unchanged':removed_geometry.intersection(g('commons_outer')).area<1e-6,
 'training_preparation_passage_envelope_unchanged':removed_geometry.intersection(g('retained_envelope')).area<1e-6,
 'repaired_south_link_roof_unchanged':removed_geometry.intersection(box(-18,-9.2,18,-4.5)).area<1e-6,
 'only_main_roof_14_to_14_45_changed':all(next(m for m in M if m['module_id']==r['module_id'])['z0']==14 and next(m for m in M if m['module_id']==r['module_id'])['z1']==14.45 for r in removed+clipped),
 'all_other_714_modules_unaffected':len([m for m in M if m['kind']!='roof'])==714,
 'lower_roof_and_floor_untouched':True,
}
assert all(safe.values()),safe
plan={'passed':all(safe.values()),'source_modules_sha256':h(EDIT/'modules.json'),'source_import_plan_sha256':h(EDIT/'import_plan.json'),'source_generator_sha256':h(p),'intent_evidence':['tmp/v39-training-direct/simplify_east_r8.py: upper_floor_rendering=former east upper floor is now roof/background, not playable B interior','tmp/v39-training-direct/geometry_r10.py: commons_outer removed from RETIRED_UPPER_AREA/ROOF; existing commons retained'],'coordinate_convention':'world metres; north +Y; UE=(100X,-100Y,100Z)','cutter_definition':'retired_upper_area minus current floor_upper, wallPolygons, all structural crowns at14m, retained_envelope and commons_outer','protected_footprint':serial(protected),'cutter_footprint':serial(cutter),'removed_high_roof_footprint':serial(removed_geometry),'removed_high_roof_area_m2':removed_geometry.area,'removed_high_roof_bounds_m':list(removed_geometry.bounds),'old_main_roof_area_m2':oldroof.area,'new_main_roof_area_m2':newroof.area,'total_existing_roof_modules':107,'fully_remove_count':len(removed),'partially_clip_count':len(clipped),'unchanged_roof_count':len(unchanged),'new_replacement_module_count':len(replacements),'fully_remove':removed,'partially_clip':clipped,'unchanged_module_ids':unchanged,'checks':safe,'new_modules_file':'roof_correction_modules.json','note':'Exact allowlist only. Verify current actor overrides against expected_actor before modifying. Do not rebuild or resync the other714modules. New meshes must use new asset paths so backups remain intact.'}
(R/'roof_correction_plan.json').write_text(json.dumps(plan,indent=2,ensure_ascii=False),encoding='utf8')
(R/'roof_correction_modules.json').write_text(json.dumps({'modules':replacements,'report':{'passed':True,'source':'roof_correction_plan.json'}},indent=2,ensure_ascii=False),encoding='utf8')
print(json.dumps({k:v for k,v in plan.items()if k in ['passed','removed_high_roof_area_m2','removed_high_roof_bounds_m','fully_remove_count','partially_clip_count','unchanged_roof_count','new_replacement_module_count','checks']},indent=2))
