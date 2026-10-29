"""Export only the 15 roof-repair modules. Never rebuild or sync the full lab.
Run: blender --factory-startup --background --python build_roofs.py
Requires the repository SceneBridge Blender add-on, or SCENE_BRIDGE_BLENDER.
"""
import bpy,json,sys,hashlib,math,os
from pathlib import Path
R=Path(__file__).resolve().parent
WORKSPACE=R.parents[4]
if not bpy.app.background:
    raise RuntimeError('Run this repair-only export in background Blender with --factory-startup.')
BRIDGE=Path(os.environ.get('SCENE_BRIDGE_BLENDER', str(WORKSPACE/'SceneBridge'/'blender')))
sys.path.insert(0,str(BRIDGE))
from scene_bridge import _write_fbx
D=json.loads((R/'roof_correction_modules.json').read_text(encoding='utf-8'))
for o in list(bpy.data.objects):bpy.data.objects.remove(o,do_unlink=True)
bpy.context.scene.unit_settings.system='METRIC';bpy.context.scene.unit_settings.scale_length=1
material=bpy.data.materials.new('R17_Wall');material.diffuse_color=(.84,.86,.87,1)
rows=[]
for m in D['modules']:
    me=bpy.data.meshes.new(m['name']);me.from_pydata(m['verts'],[],m['faces']);me.update();me.materials.append(material)
    uv=me.uv_layers.new(name='UVMap')
    for poly in me.polygons:
        axis=max(range(3),key=lambda j:abs(poly.normal[j]));axes=[j for j in range(3) if j!=axis]
        for li in poly.loop_indices:
            co=me.vertices[me.loops[li].vertex_index].co;uv.data[li].uv=(co[axes[0]],co[axes[1]])
    fp=R/'roof_meshes'/(m['name']+'.fbx');_write_fbx(fp,m['name'],me,[])
    o=bpy.data.objects.new(m['name'],me);bpy.context.collection.objects.link(o)
    o.location=m['pivot'];o.rotation_euler.z=math.radians(m['rotation_z_degrees'])
    rows.append({'name':m['name'],'fbx':fp.relative_to(R).as_posix(),'sha256':hashlib.sha256(fp.read_bytes()).hexdigest()})
(R/'roof_assets.json').write_text(json.dumps(rows,indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(R/'LabRoofEnvelopeCorrection.blend'))
print('EXPORTED',len(rows))
