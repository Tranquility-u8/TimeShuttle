"""Chapter 1 metrology room interior finishes. Inputs are surveyed inward faces in UE cm."""
from pathlib import Path
import math
import bpy
from mathutils import Vector

base=Path(__file__).resolve().parent
bpy.ops.wm.read_factory_settings(use_empty=True)
scene=bpy.context.scene
scene.unit_settings.system='METRIC'
scene.unit_settings.scale_length=.01
origin=(-5100,-2000,540)
west,east,north,south=-6243.75,-4057.5,-2985.,-975.
vertices,faces,face_slots=[],[],[]
materials={}

def sheet(point,normal,uv,depth,material):
    p=[point(h,v,depth) for h,v in uv]
    xyz=[Vector((x-origin[0],origin[1]-y,z-origin[2])) for x,y,z in p]
    n=Vector((normal[0],-normal[1],normal[2]))
    if (xyz[1]-xyz[0]).cross(xyz[2]-xyz[0]).dot(n)<0:
        xyz.reverse()
    start=len(vertices)
    vertices.extend(xyz)
    faces.append(tuple(range(start,start+len(xyz))))
    face_slots.append(material)

def clipped(rect,apertures):
    pieces=[rect]
    for l,b,r,t in apertures:
        remaining=[]
        for x,y,X,Y in pieces:
            a,c,A,C=max(x,l),max(y,b),min(X,r),min(Y,t)
            if a>=A or c>=C:
                remaining.append((x,y,X,Y))
            else:
                remaining.extend(q for q in ((x,y,X,c),(x,C,X,Y),(x,c,a,C),(A,c,X,C)) if min(q[2]-q[0],q[3]-q[1])>.01)
        pieces=remaining
    return pieces

def panel(point,n,box,d,slot,apertures=(),reveal=0):
    for x,y,X,Y in clipped(box,apertures):
        x+=reveal;y+=reveal;X-=reveal;Y-=reveal
        if X>x and Y>y:
            sheet(point,n,[(x,y),(X,y),(X,Y),(x,Y)],d,slot)

def axis(low,high,n):
    return [low+(high-low)*i/n for i in range(n+1)]

walls=[
    (lambda s,z,d:(west+d,s,z),(1,0,0),north,south,[(-1282,538,-1038,881)],8),
    (lambda s,z,d:(east-d,s,z),(-1,0,0),north,south,[(-2208,1018,-2052,1188)],8),
    (lambda s,z,d:(s,north+d,z),(0,1,0),west,east,[(-4642,538,-4318,882)],9),
    (lambda s,z,d:(s,south-d,z),(0,-1,0),west,east,[(-5344,1004,-5136,1215)],9),
]
for point,n,lo,hi,openings,count in walls:
    panel(point,n,(lo,540,hi,1390),.48,'TC_Seal',openings)
    xs=axis(lo,hi,count)
    for i,(a,b) in enumerate(zip(xs,xs[1:])):
        for j,(low,high) in enumerate([(540,559),(559,804),(804,1132),(1132,1355),(1355,1390)]):
            material=['TC_Skirting','TC_Porcelain','TC_Porcelain','TC_Pearl','TC_Seal'][j]
            panel(point,n,(a,low,b,high),1.65 if j in (0,4) else 1.85,material,openings,.39)
            if j==0:
                panel(point,n,(a+1,high-1.5,b-1,high-.5),1.93,'TC_Brushed',openings)
    # Thin panel reveals read through grazing reflections. All finishes stay inside the original thresholds.
floor=lambda x,y,d:(x,y,540+d)
panel(floor,(0,0,1),(west,north,east,south),.14,'TC_Seal')
xs,ys=axis(west,east,12),axis(north,south,11)
for i,(l,r) in enumerate(zip(xs,xs[1:])):
    for j,(b,t) in enumerate(zip(ys,ys[1:])):
        slot='TC_FloorB' if (i*7+j*5)%12==0 else 'TC_Floor'
        panel(floor,(0,0,1),(l,b,r,t),.62,slot,reveal=.29)
# Painted calibration/service clearance marks at the two clock bases, interrupted where people approach.
for cx,cy in [(-4590,-1630),(-5540,-2270)]:
    for ang in (0,60,120,180,240,300):
        a=math.radians(ang+30)
        radial=(math.cos(a),math.sin(a)); tangent=(-radial[1],radial[0])
        for offset,length in ((-48,23),(-19,9)):
            uv=[(cx+radial[0]*depth+tangent[0]*d,cy+radial[1]*depth+tangent[1]*d) for depth,d in [(223,offset),(223,offset+length),(225,offset+length),(225,offset)]]
            sheet(floor,(0,0,1),uv,.81,'TC_FloorInk')

name='SM_TC_RoomLining'
mesh=bpy.data.meshes.new(name)
mesh.from_pydata(vertices,[],faces);mesh.update()
slots=list(dict.fromkeys(face_slots))
for slot in slots:mesh.materials.append(bpy.data.materials.new(slot))
uv=mesh.uv_layers.new(name='Surface')
for poly,mat in zip(mesh.polygons,face_slots):
    poly.material_index=slots.index(mat)
    axis_ix=max(range(3),key=lambda i:abs(poly.normal[i]))
    p,q=[i for i in range(3) if i!=axis_ix]
    for idx in poly.loop_indices:
        coord=mesh.vertices[mesh.loops[idx].vertex_index].co
        uv.data[idx].uv=(coord[p]/120,coord[q]/120)
obj=bpy.data.objects.new(name,mesh);scene.collection.objects.link(obj);obj.select_set(True)
bpy.context.view_layer.objects.active=obj
bpy.ops.export_scene.fbx(filepath=str(base/(name+'.fbx')),use_selection=True,object_types={'MESH'},axis_forward='-Y',axis_up='Z',apply_unit_scale=True,apply_scale_options='FBX_SCALE_UNITS',mesh_smooth_type='FACE',bake_anim=False,add_leaf_bones=False)
