"""Create the initial editable asset set. Does not sync or overwrite UE actors.

Run with Blender --factory-startup --background --python-exit-code 1 --python.
After migration, the UE level is authoritative for teammate layout edits.
"""
from pathlib import Path
import bpy,json,sys,hashlib,math,re
R=Path(__file__).resolve().parent
PROJECT=R.parents[2]
sys.path.insert(0,str(PROJECT.parent/'SceneBridge/blender'))
from scene_bridge import _write_fbx
D=json.loads((R/'modules.json').read_text(encoding='utf8'))
assert D['report']['passed']
for o in list(bpy.data.objects):bpy.data.objects.remove(o,do_unlink=True)
scene=bpy.context.scene
scene.name='LabV39_EditableArchitecture'
scene.unit_settings.system='METRIC';scene.unit_settings.scale_length=1.0
wall=bpy.data.materials.new('R17_Wall');wall.diffuse_color=(.84,.86,.87,1)
floor=bpy.data.materials.new('R17_Floor');floor.diffuse_color=(.57,.62,.65,1)
assets={};instances=[];groups={}
def mesh(name,verts,faces,floor_top=False):
 me=bpy.data.meshes.new(name);me.from_pydata(verts,[],faces);me.update()
 me.materials.append(wall)
 if floor_top:me.materials.append(floor)
 uv=me.uv_layers.new(name='UVMap')
 for p in me.polygons:
  p.material_index=int(floor_top and p.normal.z>.9)
  axis=max(range(3),key=lambda j:abs(p.normal[j]));axes=[j for j in range(3) if j!=axis]
  for li in p.loop_indices:
   co=me.vertices[me.loops[li].vertex_index].co;uv.data[li].uv=(co[axes[0]],co[axes[1]])
 return me
boxv=[(-.5,-.5,-.5),(.5,-.5,-.5),(.5,.5,-.5),(-.5,.5,-.5),(-.5,-.5,.5),(.5,-.5,.5),(.5,.5,.5),(-.5,.5,.5)]
boxf=[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]
for name,isfloor in [('SM_LabEditable_WallUnit',False),('SM_LabEditable_SlabUnit',True)]:
 me=mesh(name,boxv,boxf,isfloor)
 assets[name]={'mesh':me,'floor_top':isfloor,'collision':'box'}
for m in D['modules']:
 isfloor=m['kind'] in ['floor','duct_platform','jump_block']
 rectangular=m.get('rectangular_bool',m.get('scale_editable_prism',False))
 if rectangular:
  asset='SM_LabEditable_SlabUnit' if isfloor else 'SM_LabEditable_WallUnit'
  b=m['bbox_world'];pivot=[(b[i]+b[i+3])/2 for i in range(3)]
  scale=[b[i+3]-b[i] for i in range(3)];angle=0
  if m['kind'] in ['wall','door_header','window_sill','duct_jamb','duct_header','duct_sill'] and scale[1]>scale[0]:
   scale=[scale[1],scale[0],scale[2]];angle=90
 else:
  asset=m['name'];pivot=m['pivot'];scale=[1,1,1];angle=m['rotation_z_degrees']
  assets[asset]={'mesh':mesh(asset,m['verts'],m['faces'],isfloor),'floor_top':isfloor,'collision':'complex'}
 room='_'.join(m['rooms']) if m['rooms'] else 'Public'
 if len(m['rooms'])>1:room='Shared_'+room
 folder=f"LabEditable/{m['floor']}/{room}/{m['kind']}"
 if folder not in groups:
  groups[folder]=bpy.data.collections.new(folder);scene.collection.children.link(groups[folder])
 o=bpy.data.objects.new(m['name'],assets[asset]['mesh']);groups[folder].objects.link(o)
 o.location=pivot;o.rotation_euler.z=math.radians(angle);o.scale=scale
 o['module_id']=m['module_id'];o['opening_id']=m['opening_id'] or '';o['ue_authoritative']=True
 label=re.sub('[^A-Za-z0-9_]', '_', f"{m['floor']}_{room}_{m['kind']}_{m['opening_id'] or len(instances):}")
 instances.append({'module_id':m['module_id'],'label':label,'asset_name':asset,'location':[pivot[0]*100,-pivot[1]*100,pivot[2]*100],'yaw':-angle,'scale':scale,'folder':folder,'opening_id':m['opening_id'],'rooms':m['rooms'],'kind':m['kind'],'bbox_world':m['bbox_world']})
asset_rows=[]
for name,a in assets.items():
 path=R/'meshes'/(name+'.fbx');_write_fbx(path,name,a['mesh'],[])
 asset_rows.append({'name':name,'fbx':path.relative_to(R).as_posix(),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'floor_top':a['floor_top'],'collision':a['collision']})
payload={'schema_version':1,'source_modules_sha256':hashlib.sha256((R/'modules.json').read_bytes()).hexdigest(),'assets':asset_rows,'actors':instances,'policy':'Initial migration only. Preserve UE edits; no automatic synchronization.'}
(R/'import_plan.json').write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding='utf8')
bpy.ops.wm.save_as_mainfile(filepath=str(R/'LabV39_EditableArchitecture.blend'))
print('EDITABLE_EXPORT_COMPLETE',len(instances),'actors',len(asset_rows),'assets')
