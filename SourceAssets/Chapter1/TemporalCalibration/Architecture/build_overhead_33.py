"""Small underside fittings for the existing driven slab. UE local coordinates, cm."""
from pathlib import Path
import json
import math
import bpy
from mathutils import Vector

ROOT=Path(__file__).resolve().parent
# Reduced XY boundary of the live roof fragment. Retain the five straight sides
# but build all fittings inward of the original fracture and outside its collider.
PIVOT=(-5956.82,-1266.88,1415.0)
SURVEY=[(-6243.75,-1529.21),(-6116.35,-1558.35),(-6113.24,-1558.76),(-5989.65,-1511.92),(-5669.90,-975.00),(-6243.75,-975.00)]
HULL=[Vector((x-PIVOT[0],y-PIVOT[1])) for x,y in SURVEY]
VERTS=[];FACES=[];IDS=[]
def part(p,f,m):
    start=len(VERTS)
    pts=[Vector(a) for a in p]
    center=sum(pts,Vector())/len(pts)
    VERTS.extend((a.x/100,-a.y/100,a.z/100) for a in pts)
    for face in f:
        ids=list(face)
        a,b,c=[pts[i] for i in ids[:3]]
        mid=sum((pts[i] for i in ids),Vector())/len(ids)
        if (b-a).cross(c-a).dot(mid-center)<0:ids.reverse()
        FACES.append([i+start for i in reversed(ids)]);IDS.append(m)
def extrude(shape,hi,lo,m):
    n=len(shape)
    p=[(x,y,high) for high in (lo,hi) for x,y in shape]
    part(p,[list(range(n)),list(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)],m)
def rotated(shape,at,deg=0):
    a=math.radians(deg);c=math.cos(a);s=math.sin(a)
    return [(at[0]+c*x-s*y,at[1]+s*x+c*y) for x,y in shape]
def cover(x,y,w,h,c,hi,lo,m,ang=0):
    a,b=w/2,h/2
    shape=[(-a+c,-b),(a-c,-b),(a,-b+c),(a,b-c),(a-c,b),(-a+c,b),(-a,b-c),(-a,-b+c)]
    extrude(rotated(shape,(x,y),ang),hi,lo,m)
def line(p,q,w,high,low,m):
    d=Vector(q)-Vector(p)
    cover((p[0]+q[0])/2,(p[1]+q[1])/2,d.length,w,min(.25*w,1.0),high,low,m,math.degrees(math.atan2(d.y,d.x)))
def bolt(x,y,r,hi,lo):
    shape=[(x+r*math.cos(i*math.tau/8),y+r*math.sin(i*math.tau/8)) for i in range(8)]
    extrude(shape,hi,lo,'TC_Alloy')
    line((x-r*.65,y),(x+r*.65,y),r*.21,lo-.015,lo-.18,'TC_Seal')
def edge(i,f):
    p,q=HULL[i],HULL[(i+1)%len(HULL)]
    d=(q-p).normalized()
    return p+(q-p)*f,Vector((-d.y,d.x))

# Shallow adhesive seal and retaining rails. Their discontinuities follow the
# broken edge of this single fragment, leaving original fracture geometry visible.
for index,s0,s1 in [(0,.11,.89),(2,.12,.85),(3,.13,.40),(3,.425,.69),(3,.72,.95),(4,.045,.51),(4,.53,.96),(5,.055,.45),(5,.48,.95)]:
    p,n=edge(index,s0);q,_=edge(index,s1)
    line(p+n*8,q+n*8,4.5,-24.7,-25.9,'TC_Graphite')
    line(p+n*8,q+n*8,2.5,-25.91,-26.18,'TC_Alloy')

# Access panel is visible at an oblique angle over the west door. Individual
# latch and hinge parts face the observer below the slab.
px,py=-75,20
cover(px,py,131,151,9,-24.6,-26.35,'TC_Graphite')
cover(px,py,126,146,8,-26.36,-27.35,'TC_Alloy')
cover(px,py,123.5,143.5,7.3,-27.36,-27.95,'TC_Ceramic')
for x in (-54,54):
    for y in (-63,63):
        bolt(px+x,py+y,1.80,-27.91,-28.33)
for x in [-33,33]:
    cover(px+x,py-71.8,18,4,1,-26.8,-28.55,'TC_Graphite')
    cover(px+x,py-71.8,10,3.4,.7,-28.56,-29.1,'TC_Alloy')
cover(px,py+51,42,12.5,2,-27.96,-28.35,'TC_Graphite')
cover(px,py+51,32,3.5,1,-28.36,-28.95,'TC_Alloy')
cover(px-35,py-45,20,4.4,.4,-27.96,-28.16,'TC_Slate')
for j in range(3):
    cover(px-41+j*4.5,py-45,2.4,1.4,.3,-28.17,-28.26,'TC_Index')

# A bent keeper in two short collars by the torn diagonal and the original
# mounting seat. No part bridges the sky gap or extends to the slab above it.
for frac in (.31,.67):
    p,inward=edge(3,frac)
    tang=Vector((inward.y,-inward.x))
    anchor=p+inward*18
    ang=math.degrees(math.atan2(tang.y,tang.x))
    cover(*anchor,34,15,1.8,-24.7,-26.15,'TC_Graphite',ang)
    for along in (-12,12):
        at=anchor+tang*along+inward*2
        bolt(at.x,at.y,1.6,-26.16,-26.65)
    # Strip folds locally toward the underside with burnt edge at its torn tip.
    a=anchor-inward*2.5
    b=anchor-inward*11+tang*3
    c=anchor-inward*15+tang*4
    for s,t,hs,ht,mat in [(a,b,-26.15,-29.8,'TC_Alloy'),(b,c,-29.8,-30.3,'TC_Graphite')]:
        xy=[s-tang*3,s+tang*3,t+tang*3,t-tang*3]
        top=[(v.x,v.y,z) for v,z in zip(xy,[hs,hs,ht,ht])]
        bot=[(v.x,v.y,z-.75) for v,z in zip(xy,[hs,hs,ht,ht])]
        part(top+bot,[(0,1,2,3),(4,5,6,7),(0,4,5,1),(1,5,6,2),(2,6,7,3),(3,7,4,0)],mat)

bpy.ops.wm.read_factory_settings(use_empty=True)
mesh=bpy.data.meshes.new('SM_TC_OverheadServiceSkin33');mesh.from_pydata(VERTS,[],FACES)
assert not mesh.validate(verbose=True)
mesh.update()
materials=json.loads((ROOT.parent/'material_manifest.json').read_text())
names=list(dict.fromkeys(IDS))
for name in names:
    m=bpy.data.materials.new(name);m.diffuse_color=(*materials[name]['color_linear'],1);mesh.materials.append(m)
uv=mesh.uv_layers.new(name='UVMap')
for poly,name in zip(mesh.polygons,IDS):
    poly.material_index=names.index(name)
    # Give each flat fitting face a stable tangent frame, including thin vertical
    # bevels and side walls. Orient the U axis along its longest edge, then normalize
    # both UV spans independently so even the thin metal strips survive half UVs.
    points=[mesh.vertices[mesh.loops[li].vertex_index].co for li in poly.loop_indices]
    u=max((b-a for a,b in zip(points,points[1:]+points[:1])),key=lambda v:v.length_squared).normalized()
    v=poly.normal.cross(u).normalized()
    local=[((p-points[0]).dot(u),(p-points[0]).dot(v)) for p in points]
    xmin,xmax=min(p[0] for p in local),max(p[0] for p in local)
    ymin,ymax=min(p[1] for p in local),max(p[1] for p in local)
    assert xmax>xmin and ymax>ymin
    for li,(x,y) in zip(poly.loop_indices,local):
        uv.data[li].uv=((x-xmin)/(xmax-xmin),(y-ymin)/(ymax-ymin))
mesh.calc_loop_triangles()
def determinant(tri):
    a,b,c=(uv.data[li].uv for li in tri.loops)
    return abs((b.x-a.x)*(c.y-a.y)-(b.y-a.y)*(c.x-a.x))
assert min(determinant(t) for t in mesh.loop_triangles)>1e-6
ob=bpy.data.objects.new(mesh.name,mesh);bpy.context.collection.objects.link(ob)
bpy.context.view_layer.objects.active=ob;ob.select_set(True)
bpy.ops.export_scene.fbx(filepath=str(ROOT/'SM_TC_OverheadServiceSkin33.fbx'),use_selection=True,
    object_types={'MESH'},axis_forward='-Y',axis_up='Z',mesh_smooth_type='FACE',use_triangles=True,bake_anim=False)

mesh.calc_loop_triangles()
# Audit every vertex against all half-planes of the live convex hull.
margin=min((-(b.y-a.y)*(x*100-a.x)+(b.x-a.x)*(-y*100-a.y))/(b-a).length
           for x,y,z in VERTS for i,a in enumerate(HULL) for b in [HULL[(i+1)%len(HULL)]])
assert margin>1.0,margin
print('SLAB 33',len(mesh.loop_triangles),'triangles; minimum original boundary clearance cm',margin,
    'Z in cm',min(p[2] for p in VERTS)*100,max(p[2] for p in VERTS)*100,'slots',names)
