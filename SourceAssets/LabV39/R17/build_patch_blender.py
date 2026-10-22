"""Rebuild the audited R17 patch, including the final UV/clearance fixes.

This is the full build path; refresh_blender_patch.py is no longer required
afterward. Existing manifest identities are retained for repeatable sync.
"""
import bpy,json,sys,math,hashlib,uuid
from pathlib import Path
R=Path(__file__).resolve().parent
PLAN=R/'revised-layout-geometry.json'
plan_raw=PLAN.read_bytes();architecture_raw=(R/'architecture_meshes.json').read_bytes()
D=json.loads(plan_raw);P=json.loads(architecture_raw)
# Fail before touching Blender objects if the geometry or its audit is stale.
assert D['checks']['version']=='single_west_entry_R17', 'This builder targets the R17 plan'
assert P['report']['source_sha256']==hashlib.sha256(plan_raw).hexdigest(), 'Re-run prepare_architecture.py for the current plan'
qa=json.loads((R/'independent_3d_qa.json').read_text(encoding='utf8'))
# Manifest placement is checked after export; excluding those two checks here
# avoids a circular dependency when legitimately rebuilding changed geometry.
geometry_checks={k:v for k,v in qa['checks'].items() if k not in {'refreshed_manifest_architecture_bounds_match','POD1_shifted_prop_042_approach_clear'}}
assert geometry_checks and all(geometry_checks.values()) and qa['architecture_meshes_sha256']==hashlib.sha256(architecture_raw).hexdigest(), 'Run independent_3d_qa.py on the current repaired architecture before building'
manifest_path=R/'patch_bundle'/'manifest.json'
previous=json.loads(manifest_path.read_text(encoding='utf8')) if manifest_path.exists() else {}
if previous:
 assert previous['scene_name']=='TimeShuttler_LabV39_R17_Patch' and previous['scope_collection']=='LAB_R17_PATCH', 'Output manifest belongs to another patch'
scene_id=uuid.UUID(previous['scene_id']).hex if previous else uuid.uuid5(uuid.NAMESPACE_URL,'TimeShuttler/LabV39/R17/architecture').hex
scope_id=uuid.UUID(previous['scope_id']).hex if previous else uuid.uuid5(uuid.UUID(scene_id),'LAB_R17_PATCH').hex
previous_ids={o['name']:uuid.UUID(o['id']).hex for o in previous.get('objects',[])}
assert len(previous_ids)==len(previous.get('objects',[])), 'Previous manifest contains duplicate object names'

def implementation_prop_bounds(index,prop):
 """Keep the approved plan unchanged; apply the recorded POD1 clearance fix."""
 bounds=list(prop['bounds'])
 if index==42:
  expected=[85.1,-11.5,85.8,-8.6]
  assert prop['level']==0 and all(math.isclose(a,b,abs_tol=1e-6) for a,b in zip(bounds,expected)), 'POD1 prop 042 changed: review the implementation override before rebuilding'
  bounds[1]-=1.5;bounds[3]-=1.5
 return bounds

# Check the positional override before any scene mutation.
implementation_prop_bounds(42,D['props'][42])
sys.path.insert(0,'E:/Capstone/Test/SceneBridge/blender')
import scene_bridge
scene_bridge.register()
scene=bpy.context.scene
scene.name='TimeShuttler_LabV39_R17_Patch'
scene.scene_bridge.auto_sync=False
for o in list(scene.objects):bpy.data.objects.remove(o,do_unlink=True)
scene.unit_settings.system='METRIC';scene.unit_settings.scale_length=1
scene['sb_scene_id']=scene_id
root=bpy.data.collections.get('LAB_R17_PATCH') or bpy.data.collections.new('LAB_R17_PATCH')
if root.name not in scene.collection.children:scene.collection.children.link(root)
root['sb_scope_id']=scope_id
colors={'Wall':(.84,.86,.87,1),'Floor':(.57,.62,.65,1),'Trim':(.13,.20,.24,1),'Glass':(.46,.72,.79,.15),'Prop':(.65,.69,.70,1)}
mats={}
for k,c in colors.items():
 m=bpy.data.materials.get('R17_'+k) or bpy.data.materials.new('R17_'+k);m.diffuse_color=c;m.use_nodes=True
 bs=m.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=c;bs.inputs['Roughness'].default_value=.78;bs.inputs['Alpha'].default_value=c[3]
 if c[3]<1:m.surface_render_method='DITHERED'
 mats[k]=m
groups={}
def group(n):
 if n not in groups:
  groups[n]=root.children.get(n) or bpy.data.collections.get(n) or bpy.data.collections.new(n)
  if groups[n].name not in root.children:root.children.link(groups[n])
 return groups[n]
def project_uvs(me):
 """Same dominant-face-axis projection used by the validated final refresh."""
 uv=me.uv_layers.get('UVMap') or me.uv_layers.new(name='UVMap')
 for p in me.polygons:
  axis=max(range(3),key=lambda j:abs(p.normal[j]));axes=[j for j in range(3) if j!=axis]
  for li in p.loop_indices:
   co=me.vertices[me.loops[li].vertex_index].co
   uv.data[li].uv=(co[axes[0]],co[axes[1]])
def mesh(name,vs,fs,cat='Structure',material='Wall',collision='complex',face_mats=None):
 # Recenter without altering world placement. The bridge writes UE centimetres.
 center=tuple((min(p[i] for p in vs)+max(p[i] for p in vs))/2 for i in range(3))
 me=bpy.data.meshes.new(name);me.from_pydata([tuple(p[i]-center[i] for i in range(3)) for p in vs],[],fs);me.update()
 project_uvs(me)
 o=bpy.data.objects.new(name,me);group(cat).objects.link(o);o.location=center
 o['sb_id']=previous_ids.get(name) or uuid.uuid5(uuid.UUID(scene_id),name).hex
 for mat in (['Wall','Floor'] if face_mats else [material]):me.materials.append(mats[mat])
 if face_mats:
  for p,k in zip(me.polygons,face_mats):p.material_index=int(k=='Floor')
 o['sb_export']=True;o['sb_collision']=collision;o['sb_collision_profile']='BlockAll';o['revision']='R17';return o
F=[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]
def cube(name,loc,dim,cat,mat,collision='box'):
 cx,cy,cz=loc;x,y,z=[d/2 for d in dim]
 vs=[(cx+a,cy+b,cz+c) for a,b,c in [(-x,-y,-z),(x,-y,-z),(x,y,-z),(-x,y,-z),(-x,-y,z),(x,-y,z),(x,y,z),(-x,y,z)]]
 return mesh(name,vs,F,cat,mat,collision)
for p in P['parts']:mesh(p['name'],p['verts'],p['faces'],'Structure',face_mats=p['face_materials'])
profile={r['id']:r['range'] for r in P['report']['opening_profiles']}
for op in D['openings']:
 x,y=op['x'],op['y'];base=5.4 if op['z'] else 0;win=op['kind']=='window';sill=op.get('sill',.9 if win else 0);w,h=op['width'],op['height'];z=base+sill;vertical=op['axis']=='v';oid=op['id']
 if win:cube('R17_Window_'+oid,(x,y,z+h/2),(.06,w,h) if vertical else (w,.06,h),'Windows','Glass','complex')
 # Two shallow projecting frame strips on both wall faces. Avoid buried/fighting trim.
 sides=profile.get(oid,[ (x if vertical else y)-.375,(x if vertical else y)+.375])
 for face,normal in enumerate([sides[0]-.035,sides[1]+.035]):
  for side in [-1,1]:
   px=normal if vertical else x+side*(w/2+.03);py=y+side*(w/2+.03) if vertical else normal
   cube(f'R17_Frame_{oid}_{face}_{side}',(px,py,z+h/2),(.07,.06,h) if vertical else (.06,.07,h),'Frames','Trim')
  cube(f'R17_HeaderTrim_{oid}_{face}',(normal,y,z+h+.03) if vertical else (x,normal,z+h+.03),(.07,w+.12,.06) if vertical else (w+.12,.07,.06),'Frames','Trim')
heights={'table':.76,'desk':.76,'labbench':.95,'teaching':.95,'reception':1.05,'counter':.95,'bench':.48,'sofa':.75,'bed':.5,'machine':1.75,'terminal':1.4,'kit':1.6,'wardrobe':2,'shelf':1.8,'storage':1.8,'sink':.84,'stall':2,'target':1.6,'cover':1.1}
for i,p in enumerate(D['props']):
 if p.get('omit_for_clearance'):continue
 x1,y1,x2,y2=implementation_prop_bounds(i,p);h=p.get('height',heights.get(p['kind'],.9));base=5.4 if p['level'] else 0
 cube(f'R17_Furniture_{i:03d}_{p["kind"]}',((x1+x2)/2,(y1+y2)/2,base+h/2),(x2-x1,y2-y1,h),'Furniture_B' if base else 'Furniture_A','Prop')
for j,w in enumerate(D['control_windows']):
 for base in [5.4,11.4]:
  cube(f'R17_OmenGlass_{j}_{base}',(w['x'],(w['y1']+w['y2'])/2,base+2.4),(.075,w['y2']-w['y1'],3),'OmenGallery','Glass','complex')
scene.scene_bridge.output_dir=str(R/'patch_bundle');scene.scene_bridge.collection_name=root.name;scene.scene_bridge.auto_sync=False
bpy.ops.wm.save_as_mainfile(filepath=str(R/'TimeShuttler_LabV39_R17_Patch.blend'))
report=scene_bridge.export_scene(str(R/'patch_bundle'),root.name,scene=scene)
(R/'blender_export.json').write_text(json.dumps(report,indent=2,default=str),encoding='utf8')
bpy.ops.wm.save_as_mainfile(filepath=str(R/'TimeShuttler_LabV39_R17_Patch.blend'))
print('R17_EXPORT_COMPLETE',len(scene.objects))
