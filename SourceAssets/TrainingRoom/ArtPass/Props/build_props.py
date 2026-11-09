"""Build original range fixtures. Run with Blender in background. Sizes below are UE centimetres."""
import hashlib
import json
import math
from pathlib import Path

import bpy
import bmesh


ROOT = Path(__file__).resolve().parent
FBX = ROOT / "FBX"
FBX.mkdir(exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.context.preferences.filepaths.save_version = 0

COLORS = {"White": (.66,.69,.68), "DarkMetal": (.055,.075,.084),
          "Rubber": (.02,.026,.029), "Amber": (.95,.29,.025)}
RECEIPTS = {}
TARGETS = {}


class Part:
    def __init__(self, name, scale, roles, y_long=False):
        self.name = "SM_TR_" + name
        self.scale = scale
        self.roles = list(roles)
        self.y_long = y_long
        self.vertices, self.faces, self.face_slots = [], [], []

    def rings(self, layers, material):
        n = len(layers[0])
        base = len(self.vertices)
        for layer in layers:
            for x, y, z in layer:
                if self.y_long:
                    x, y = -y, x
                sx, sy, sz = self.scale
                self.vertices.append((x * .01/sx, -y * .01/sy, z * .01/sz))
        faces = [tuple(range(base+n-1,base-1,-1))]
        for j in range(len(layers) - 1):
            a = base + j*n
            faces.extend((a+i, a+(i+1)%n, a+(i+1)%n+n, a+i+n) for i in range(n))
        end = base + (len(layers)-1)*n
        faces.append(tuple(range(end,end+n)))
        self.faces.extend(faces)
        self.face_slots.extend([self.roles.index(material)]*len(faces))

    def box(self, pos, size, material, chamfer=.7, bevel=.3):
        x,y,z = pos
        a,b,h = [v/2 for v in size]
        cut = min(chamfer,a*.35,b*.35)
        radius = min(bevel,h*.4,b*.15,a*.15,cut*.5)
        layers=[]
        for dz, inset in [(-h,radius),(-h+radius,0),(h-radius,0),(h,radius)]:
            w,d = a-inset, b-inset
            k=max(.001,cut-inset*.5)
            layer=[(-w+k,-d),(w-k,-d),(w,-d+k),(w,d-k),(w-k,d),(-w+k,d),(-w,d-k),(-w,-d+k)]
            layers.append([(x+vx,y+vy,z+dz) for vx,vy in layer])
        self.rings(layers, material)

    def lathe(self, x, y, zr, material, sides=12):
        self.rings([[(x+r*math.cos(i*math.tau/sides), y+r*math.sin(i*math.tau/sides), z)
                     for i in range(sides)] for z,r in zr],material)

    def export(self, old):
        mesh=bpy.data.meshes.new(self.name)
        ordered=sorted(zip(self.face_slots,self.faces),key=lambda item:item[0])
        mesh.from_pydata(self.vertices,[],[face for slot,face in ordered])
        for i,role in enumerate(self.roles):
            key=f"RA{i:02d}_{role}"
            mat=bpy.data.materials.get(key) or bpy.data.materials.new(key)
            mat.diffuse_color=(*COLORS[role],1)
            mesh.materials.append(mat)
        for p,(slot,_) in zip(mesh.polygons,ordered):
            p.material_index=slot
        mesh.update()
        bm=bmesh.new()
        bm.from_mesh(mesh)
        bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
        bm.to_mesh(mesh)
        bm.free()
        # A planar projection per face gives bevels and shells nondegenerate UVs.
        uv=mesh.uv_layers.new(name="PanelUV")
        for poly in mesh.polygons:
            axis=max(range(3),key=lambda i:abs(poly.normal[i]))
            s,t=[i for i in range(3) if i!=axis]
            for loop in poly.loop_indices:
                v=mesh.vertices[mesh.loops[loop].vertex_index].co
                uv.data[loop].uv=(v[s],v[t])
        mesh.calc_loop_triangles()
        obj=bpy.data.objects.new(self.name,mesh)
        bpy.context.collection.objects.link(obj)
        bpy.ops.object.select_all(action="DESELECT")
        obj.select_set(True)
        bpy.context.view_layer.objects.active=obj
        file=FBX/(self.name+".fbx")
        bpy.ops.export_scene.fbx(filepath=str(file),use_selection=True,object_types={"MESH"},
            axis_forward="-Y",axis_up="Z",add_leaf_bones=False,mesh_smooth_type="FACE",use_triangles=True,bake_anim=False)
        bounds=[[round(f(v.co[i]*[100,-100,100][i] for v in mesh.vertices),4) for i in range(3)] for f in (min,max)]
        RECEIPTS[self.name]={"source":old,"slots":self.roles,"bounds":bounds,"triangles":len(mesh.loop_triangles),
                             "sha256":hashlib.sha256(file.read_bytes()).hexdigest()}
        return self.name


CUBE="/Engine/BasicShapes/Cube.Cube"
CYL="/Engine/BasicShapes/Cylinder.Cylinder"
CARGO="/Game/Environment/TrainingRoom/Stages/Meshes/SM_TS_SuspendedContainer.SM_TS_SuspendedContainer"


def cover(actor, name, width, depth, height, high=False, trim=False):
    along_y=depth>width
    L,D=sorted((width,depth),reverse=True)
    face="DarkMetal" if high else "White"
    roles=(face,"Rubber") if high else ("White","DarkMetal","Rubber")
    p=Part(name,(width/100,depth/100,height/100),roles,along_y)
    x0,x1=-L/2,L/2
    if trim:
        # The 20 cm return intersects this rail. Dock its exterior shell against
        # the return, with a buried tongue retaining the original local bounds.
        x1-=20.15
        p.box(((x1+L/2)/2,0,-height/2+4),(L/2-x1,D-4,3),"Rubber",.35,.2)
    cx,length=(x0+x1)/2,x1-x0
    top=height/2
    bottom=-top
    p.box((cx,0,bottom+3.0),(length,D,6),"Rubber",1.1,.45)
    p.box((cx,0,1.7),(length-.8,D-.8,height-8.6),face,1.1,.7)
    cap_top=top-.16 if D>45 else top
    p.box((cx,0,cap_top-1.8),(length-1.1,D-.4,3.6),"Rubber" if high else "DarkMetal",1.0,.45)
    # Wide removable covers carry a single shallow panel break with two flush
    # corner fasteners at each side. Thin rails keep their clean silhouette.
    if D>45:
        n=2 if length>285 else 1
        pitch=(length-4)/n
        for i in range(n):
            xx=x0+2+(i+.5)*pitch
            for side in (-1,1):
                p.box((xx,side*(D/2-.25),1.75),(pitch-.7,.5,height-12),face,1.0,.2)
        for x in (x0+5.5,x1-5.5):
            for y in (-D/2+5.5,D/2-5.5):
                p.lathe(x,y,[(top-.24,.85),(top-.04,.85),(top,.82)],"Rubber" if not high else face,8)
    return p.export(CUBE)


def rope():
    p=Part("PairedCutCable",(.18,.18,1.18),("Amber","DarkMetal","Rubber"))
    p.lathe(0,0,[(-59,6),(-56,7.1),(-48,7.1),(-46,6.2),(45,6.2),(48,7.1),(56,7.1),(59,6)],"Amber",16)
    for z in (-52,49):
        p.lathe(0,0,[(z-4,7),(z-2.8,8.8),(z+3.5,9),(z+4.6,7.2)],"DarkMetal",12)
    for z in (-43,42):
        p.lathe(0,0,[(z-.9,6.24),(z-.7,6.55),(z+.8,6.55),(z+1,6.24)],"Rubber",16)
    # Six low-profile strands twist across the orange jacket. The hit silhouette
    # stays legible at firing distance and does not protrude past the end ferrules.
    for phase in range(6):
        rings=[]
        for j in range(49):
            z=-40+80*j/48
            theta=math.tau*(phase/6+j/24)
            ring=[]
            for k in range(5):
                r=6.08+.31*math.cos(k*math.tau/5)
                angle=theta+.058*math.sin(k*math.tau/5)
                ring.append((r*math.cos(angle),r*math.sin(angle),z))
            rings.append(ring)
        p.rings(rings,"Amber")
    return p.export(CYL)


def plank():
    p=Part("PairedImpactPlate",(4,1.5,.24),("DarkMetal","Rubber"))
    p.box((0,0,.8),(400,150,22.4),"DarkMetal",2.8,1.15)
    p.box((0,0,-10.4),(396,146,2),"Rubber",1.65,.64)
    p.box((0,0,-11.38),(389,139,.96),"DarkMetal",2,.35)
    for x in (-170,170):
        for y in (-51,51):
            p.lathe(x,y,[(-12,1.75),(-11.94,2),(-11.1,2)],"Rubber",8)
    return p.export(CUBE)


def beam():
    p=Part("PairedLoadRail",(4.7,.38,.30),("DarkMetal","Rubber"))
    p.box((0,0,7),(470,38,16),"DarkMetal",1.6,.7)
    p.box((0,0,-7),(463,29,16),"Rubber",1,.6)
    p.box((0,0,-9.5),(458,30.5,8),"DarkMetal",1,.5)
    return p.export(CUBE)


def bracket(name,size):
    x,y,z=size
    p=Part(name,(x/100,y/100,z/100),("DarkMetal","Rubber"))
    p.box((0,0,z*.25),(x,y,z*.5),"DarkMetal",1.4,.5)
    p.lathe(0,0,[(-z*.5,x*.28),(-z*.4,x*.34),(0,x*.34),(z*.06,x*.36)],"Rubber",12)
    return p.export(CUBE)


def cargo():
    p=Part("SuspendedLoadCassette",(1,1,.5),("Amber","DarkMetal","White"))
    # The thin module has a bottom-centred pivot. Model in as-installed cm;
    # the authoring scale on Z is divided out during export.
    p.box((0,0,3),(450,300,6),"DarkMetal",2,.9)
    p.box((0,0,37.5),(437,286,63),"Amber",1.6,1)
    p.box((0,0,70),(450,300,5),"DarkMetal",1.8,.6)
    for x in (-220.7,220.7):
        for y in (-145.7,145.7):
            p.box((x,y,37),(8.6,8.6,63),"DarkMetal",1.1,.6)
    for side in (-1,1):
        for i in range(15):
            p.box((-201+i*28.7,side*144.35,37),(5.9,5.2,58),"Amber",1.1,.6)
        for i in range(9):
            p.box((side*218.7,-119+i*29.7,37),(6.2,5.9,58),"Amber",1.1,.6)
        for x in (-205,205):
            p.box((x,side*148.2,10.5),(6.5,.85,1.8),"White",.3,.14)
    for x in (-160,0,160):
        p.box((x,0,72.55),(5,273,1.4),"DarkMetal",.5,.25)
    p.box((0,137,73.75),(25,24,2.5),"DarkMetal",1.3,.35)
    p.box((225,135,35),(.8,12,16),"DarkMetal",.2,.08)
    return p.export(CARGO)


cover_specs=[
    ("L1 Low cover","Lo300",300,120,95),("H1 High cover","Hi450",450,120,220),
    ("H2 High cover","Hi370Y",100,370,200),("L2 Low cover","Lo220",220,100,95),
    ("L3 Low cover","Lo270",270,120,95),("H3 High cover","Hi560Y",100,560,160),
    ("H4 High cover","Hi390Y",100,390,150),("L4 Low cover","Wing560",560,20,95),
    ("L4 Low cover3","Wing320Y",20,320,95),("L3 Low cover2","Wing120Y",20,120,95),
    ("L4 Low cover2","Wing480",480,20,95)]
for label,name,w,d,h in cover_specs:
    TARGETS["S7B | "+label]=cover(label,name,w,d,h,high=label.startswith("H"),trim=name=="Wing560")
TARGETS["S7B | L3 Low cover3"]=TARGETS["S7B | L3 Low cover2"]
TARGETS["S7B | Suspended cargo container"]=cargo()
TARGETS["S5 | FallingPlank"]=plank()
TARGETS["S5 | GantryBeam"]=beam()
for label,n in [("ShootableLink",rope()),("Hanger",bracket("PairedCeilingSocket",(28,28,12))),
                ("LinkArm",bracket("PairedCableFerrule",(22,22,12)))]:
    for suffix in ("A","B"):
        TARGETS[f"S5 | {label}_{suffix}"]=n

(ROOT/"manifest.json").write_text(json.dumps({"assets":RECEIPTS,"targets":TARGETS},indent=2),encoding="utf8")
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/"RangeFixtures.blend"))
