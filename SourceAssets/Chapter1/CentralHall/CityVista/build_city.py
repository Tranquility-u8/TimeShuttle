"""Build a two-tier exterior skyline plus a curved matte outside the hall.

The mesh has a single origin in UE centimetres at (0,-2500,0). The near and
middle towers stand in real space, while the far city/clouds share one texture.
"""
from math import cos, radians, sin
from pathlib import Path
import random

import bpy

ROOT=Path(__file__).resolve().parent
NAME="SM_CH_CityVista"
SLOTS=("Sky","NearWall","NearEnd","NearRim","MidWall","MidEnd","MidRim","Window","Glazing")
vertices=[]
faces=[]
slot_ids=[]
maps=[]


def face(corners,material,uv=None):
    start=len(vertices)
    vertices.extend((x*.01,-y*.01,z*.01) for x,y,z in corners)
    faces.append(tuple(range(start,start+len(corners))))
    slot_ids.append(SLOTS.index(material))
    maps.append(uv if uv else [(0,0),(1,0),(1,1),(0,1)][:len(corners)])


def distance_matte():
    # Add zenith and nadir skirts. Even when looking up from the near glass,
    # the angular horizon never exposes the original bright daytime background.
    radius=14300
    limit=100
    levels=[(-38500,.001),(-6250,.002),(9000,.998),(38500,.999)]
    def point(angle,z):
        a=radians(angle)
        return (radius*sin(a),-radius*cos(a),z)
    for i in range(60):
        a0=-limit+2*limit*i/60
        a1=-limit+2*limit*(i+1)/60
        for (z0,v0),(z1,v1) in zip(levels,levels[1:]):
            # UE-facing front of the cylindrical surface points inward. Mapping
            # is continuous between every segment, while terminal pixels stretch.
            face([point(a0,z0),point(a1,z0),point(a1,z1),point(a0,z1)],"Sky",
                 [(i/60,v0),((i+1)/60,v0),((i+1)/60,v1),(i/60,v1)])


def building(angle,radius,span,depth,top,bottom,tier,rng,profile):
    a=radians(angle)
    def point(u,d,z):
        return ((radius+d)*sin(a)+u*cos(a),-(radius+d)*cos(a)+u*sin(a),z)
    def wall(points,mat):
        face([point(*p) for p in points],mat)
    def mass(u,d,w,l,z0,z1):
        left=u-w*.5
        right=u+w*.5
        fore=d-l*.5
        back=d+l*.5
        wall([(left,fore,z0),(right,fore,z0),(right,fore,z1),(left,fore,z1)],tier+"Wall")
        wall([(right,fore,z0),(right,back,z0),(right,back,z1),(right,fore,z1)],tier+"End")
        wall([(left,back,z0),(left,fore,z0),(left,fore,z1),(left,back,z1)],tier+"End")
        wall([(right,back,z0),(left,back,z0),(left,back,z1),(right,back,z1)],tier+"Wall")
        wall([(left,fore,z1),(right,fore,z1),(right,back,z1),(left,back,z1)],tier+"Rim")
        return left,right,fore
    left,right,fore=mass(0,0,span,depth,bottom,top)
    spacing=rng.randrange(56,82)
    fen_w=rng.uniform(8,20)
    # Scattered quiet apertures with a few occupied offices. Horizontal room
    # divisions and recessed shadow bands do not form a luminous checkerboard.
    for i,z in enumerate(range(round(top-38),round(max(bottom+60,top-2400)),-spacing)):
        if i%5==0:
            wall([(left+7,fore-1,z),(right-7,fore-1,z),(right-7,fore-1,z+6),(left+7,fore-1,z+6)],tier+"End")
        for u in range(round(left+21),round(right-22),46):
            draw=rng.random()
            if draw<.155:
                length=fen_w if draw>.009 else 26
                wall([(u,fore-1.5,z+10),(u+length,fore-1.5,z+10),
                      (u+length,fore-1.5,z+18),(u,fore-1.5,z+18)],"Window" if draw<.009 else "Glazing")
    if profile==0:
        mass(-.06*span,0,span*.78,depth*.80,top,top+100)
        mass(-.08*span,-.02*depth,span*.56,depth*.64,top+100,top+222)
    elif profile==1:
        mass(.15*span,0,span*.41,depth*.61,top,top+int(span*.38))
        mass(.15*span,0,span*.27,depth*.42,top+int(span*.38),top+int(span*.48))
    elif profile==2:
        mass(0,0,span*1.03,depth*1.03,top,top+14)
        mass(-.2*span,0,span*.26,depth*.35,top+14,top+82)
    else:
        mass(.13*span,0,span*.62,depth*.77,top,top+58)


def skyline():
    rng=random.Random(1237)
    for radius,count,tier in ((10600,29,"Mid"),(7800,16,"Near")):
        for i in range(count):
            angle=-84+168*i/(count-1)+rng.uniform(-1.5,1.5)
            span=rng.uniform(310,760) if tier=="Mid" else rng.uniform(250,650)
            depth=rng.uniform(250,720)
            # Looking down through the lower glazing shows occupied buildings.
            # The middle row reaches, but only occasionally exceeds, the horizon.
            top=rng.uniform(-530,1450) if tier=="Mid" else rng.uniform(-1470,140)
            building(angle,radius+rng.uniform(-410,360),span,depth,top,-5700,
                     tier,rng,rng.randrange(4))


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    distance_matte()
    skyline()
    mesh=bpy.data.meshes.new(NAME)
    mesh.from_pydata(vertices,[],faces)
    mesh.update()
    for name in SLOTS:
        mesh.materials.append(bpy.data.materials.new(name))
    uv=mesh.uv_layers.new(name="CityUV")
    for polygon,coords,slot in zip(mesh.polygons,maps,slot_ids):
        polygon.material_index=slot
        for li,coord in zip(polygon.loop_indices,coords):
            uv.data[li].uv=coord
    obj=bpy.data.objects.new(NAME,mesh)
    bpy.context.scene.collection.objects.link(obj)
    obj.select_set(True)
    bpy.context.view_layer.objects.active=obj
    bpy.ops.export_scene.fbx(filepath=str(ROOT/(NAME+".fbx")),use_selection=True,
        object_types={"MESH"},axis_forward="-Y",axis_up="Z",add_leaf_bones=False,
        mesh_smooth_type="FACE",use_triangles=True,bake_anim=False)
    print(f"City vista exported: {2*len(faces)} triangles, {len(SLOTS)} sections")


if __name__=="__main__":
    main()
