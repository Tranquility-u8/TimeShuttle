import bpy, math
from mathutils import Vector
from pathlib import Path
root=Path(__file__).parent/'FBX'
root.mkdir(exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
materials={}
for name,color in {'Housing':(.055,.07,.08),'Glass':(.95,.96,.9),'Amber':(1,.40,.035),'Grip':(.12,.09,.045)}.items():
    mat=bpy.data.materials.new(name);mat.diffuse_color=(*color,1);materials[name]=mat
pieces=[]
def piece(obj,mat,bevel=0):
    obj.data.materials.append(materials[mat])
    if bevel:
        m=obj.modifiers.new('Rolled edges','BEVEL');m.width=bevel*.01;m.segments=2
        bpy.ops.object.modifier_apply(modifier=m.name)
    pieces.append(obj)
def box(pos,size,mat,bevel):
    bpy.ops.mesh.primitive_cube_add(size=1,location=Vector(pos)*.01)
    o=bpy.context.object;o.dimensions=Vector(size)*.01;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    piece(o,mat,bevel)
def tube(z,r,h,mat):
    bpy.ops.mesh.primitive_cylinder_add(vertices=24,radius=r*.01,depth=h*.01,location=(0,0,z*.01));piece(bpy.context.object,mat,.6)
def export(name):
    bpy.ops.object.select_all(action='DESELECT')
    for o in pieces:o.select_set(True)
    bpy.context.view_layer.objects.active=pieces[0];bpy.ops.object.join()
    o=bpy.context.object;o.name=name
    bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
    bpy.ops.export_scene.fbx(filepath=str(root/(name+'.fbx')),use_selection=True,axis_forward='-Y',axis_up='Z',add_leaf_bones=False,bake_anim=False,use_triangles=True)
    pieces.clear()
box((0,0,0),(310,115,25),'Housing',3.6)
box((0,0,-12.5),(296,101,4),'Glass',1.7)
for x in (-83,0,83):box((x,54,0),(58,1.8,3),'Glass',.5)
tube(14,17,5,'Housing')
export('SM_TR_DropLight')
tube(0,13.2,147,'Amber')
for z in (-76,76):tube(z,16,9,'Housing')
# Raised diagonal strands keep the shootable length orange at a distance.
for phase in range(6):
    vs=[];fs=[]
    for i in range(65):
        angle=phase*math.tau/6+i*math.tau/41
        for k in range(5):
            b=k*math.tau/5
            radius=13.05+1.10*math.cos(b)
            vs.append((.01*radius*math.cos(angle),.01*radius*math.sin(angle),.01*(-72+i*144/64+1.3*math.sin(b))))
        if i:
            for k in range(5):fs.append(((i-1)*5+k,(i-1)*5+(k+1)%5,i*5+(k+1)%5,i*5+k))
    mesh=bpy.data.meshes.new('Woven strand');mesh.from_pydata(vs,[],fs);mesh.update()
    o=bpy.data.objects.new('Strand',mesh);bpy.context.collection.objects.link(o);piece(o,'Amber')
export('SM_TR_DropLightRope')
for y in (-56,56):box((0,y,0),(310,3,.9),'Amber',.35)
for x in (-153.5,153.5):box((x,0,0),(3,110,.9),'Amber',.35)
export('SM_TR_DropLightFootprint')
box((0,0,0),(204,10,67),'Housing',3)
box((0,5.7,0),(194,3,56),'Grip',1.5)
export('SM_TR_DropLightClockCase')
box((0,0,3),(32,27,6),'Housing',2)
tube(7,10,3,'Grip')
tube(9,8.8,3.8,'Amber')
export('SM_TR_DropLightStartButton')
