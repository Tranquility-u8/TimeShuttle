"""Model the non-colliding shared training hall finishes. All design dimensions are UE cm."""
import json
from pathlib import Path
import bpy
from mathutils import Vector

HERE=Path(__file__).resolve().parent
bpy.ops.wm.read_factory_settings(use_empty=True)
scene=bpy.context.scene
scene.unit_settings.system="METRIC"
scene.unit_settings.scale_length=.01

# sRGB chips, metalness, roughness, emission.
palette={
 "Porcelain":([.754,.748,.730],.15,.54),"Fog":([.741,.739,.725],.15,.56),
 "Seal":([.572,.575,.570],.06,.75),"CeilingSeal":([.163,.172,.179],.06,.77),
 "Plinth":([.244,.259,.270],.38,.48),
 "Ballistic":([.376,.411,.452],.17,.68),"BallisticAlt":([.364,.403,.440],.16,.66),
 "Rail":([.347,.377,.395],.52,.39),"Lid":([.198,.209,.217],.17,.65),
 "LidAlt":([.210,.220,.228],.16,.65),"Lens":([.965,.955,.922],.0,.27,3.6)}
mats={}
for key,props in palette.items():
    mat=bpy.data.materials.new(key)
    mat.diffuse_color=(*props[0],1)
    mats[key]=mat

def linear_positions(start,end,num):
    return [start+(end-start)*i/num for i in range(num+1)]

class Mesh:
    def __init__(self):
        self.points=[];self.faces=[];self.slots=[]
    def face(self,points,normal,slot):
        pts=[Vector((v.x,-v.y,v.z)) for v in points]
        n=Vector((normal.x,-normal.y,normal.z))
        if (pts[1]-pts[0]).cross(pts[2]-pts[0]).dot(n)<0: pts.reverse()
        idx=len(self.points)
        self.faces.append(tuple(range(idx,idx+len(pts))))
        self.points.extend(pts);self.slots.append(slot)

    def export(self,name):
        data=bpy.data.meshes.new(name)
        data.from_pydata(self.points,[],self.faces);data.update()
        slots=list(dict.fromkeys(self.slots))
        for slot in slots: data.materials.append(mats[slot])
        uv=data.uv_layers.new(name="SurfaceUV")
        for poly,slot in zip(data.polygons,self.slots):
            poly.material_index=slots.index(slot)
            dominant=max(range(3),key=lambda k:abs(poly.normal[k]))
            ax,ay=[(1,2),(0,2),(0,1)][dominant]
            for li in poly.loop_indices:
                co=data.vertices[data.loops[li].vertex_index].co
                uv.data[li].uv=(co[ax]/128,co[ay]/128)
        ob=bpy.data.objects.new(name,data);scene.collection.objects.link(ob)
        bpy.ops.object.select_all(action="DESELECT");ob.select_set(True);bpy.context.view_layer.objects.active=ob
        bpy.ops.export_scene.fbx(filepath=str(HERE/(name+".fbx")),use_selection=True,object_types={"MESH"},
                 axis_forward="-Y",axis_up="Z",global_scale=1,apply_unit_scale=True,apply_scale_options="FBX_SCALE_UNITS",
                 mesh_smooth_type="FACE",add_leaf_bones=False,bake_anim=False)
        data.calc_loop_triangles()
        per_slot={s:0 for s in slots}
        height={s:[] for s in slots}
        for tri in data.loop_triangles:
            role=slots[data.polygons[tri.polygon_index].material_index]
            per_slot[role]+=1
            height[role].extend(data.vertices[v].co.z for v in tri.vertices)
        z_bounds={s:[round(min(v),4),round(max(v),4)] for s,v in height.items()}
        return dict(name=name,slots=slots,triangles=len(data.loop_triangles),triangles_by_slot=per_slot,
                    z_by_slot=z_bounds,position=[0,0,0])

class Plane:
    def __init__(self,origin,hor,vert,normal):
        self.o,self.h,self.v,self.n=map(Vector,(origin,hor,vert,normal))
    def project(self,p,d):
        return self.o+p[0]*self.h+p[1]*self.v+d*self.n
    def polygon(self,points,d,slot):
        geom.face([self.project(p,d) for p in points],self.n,slot)
    def plate(self,l,b,r,t,d,slot,bevel=.28,skew=0):
        if r<=l or t<=b: return
        bevel=min(bevel,(r-l)/5,(t-b)/5)
        outer=[(l+skew,b),(r+skew,b),(r,t),(l,t)]
        if bevel<=0: self.polygon(outer,d,slot);return
        inner=[(l+skew+bevel,b+bevel),(r+skew-bevel,b+bevel),(r-bevel,t-bevel),(l+bevel,t-bevel)]
        self.polygon(inner,d,slot)
        for i in range(4):
            j=(i+1)%4
            geom.face([self.project(outer[i],d-bevel),self.project(outer[j],d-bevel),
                       self.project(inner[j],d),self.project(inner[i],d)],self.n,slot)

walls=[(Plane((-1000,0,0),(0,1,0),(0,0,1),(1,0,0)),-2270,1200,10,False),
       (Plane((1000,0,0),(0,1,0),(0,0,1),(-1,0,0)),-2270,1200,10,False),
       (Plane((0,-2270,0),(1,0,0),(0,0,1),(0,1,0)),-1000,1000,6,False),
       (Plane((0,1200,0),(1,0,0),(0,0,1),(0,-1,0)),-1000,1000,6,True)]
geom=Mesh()
for wall,lo,hi,count,entry in walls:
    # Keep the original jambs, the moving door and the whole header exposed.
    # A 5 cm shadow gap around the existing frame prevents it clipping a panel.
    fields=[(lo+3.4,-77,0,797),(77,hi-3.4,0,797),(-77,77,237,797)] if entry else [(lo+3.4,hi-3.4,0,797)]
    edges=linear_positions(lo,hi,count)
    for left,right,bottom,top in fields:
        wall.plate(left,bottom+.1,right,top,1.0,"Seal",0)
        for col,(a,b) in enumerate(zip(edges,edges[1:])):
            l=max(left+.15,a+1.4);r=min(right-.15,b-1.4)
            if r-l<1: continue
            for row,(z0,z1) in enumerate([(1,17.4),(20.2,80.5),(83.5,294.5),(297.5,540.8),(543.6,796)]):
                z0=max(z0,bottom+.32);z1=min(z1,top)
                if z1-z0<1: continue
                if row==0:
                    wall.plate(l,z0,r,z1,3.15,"Plinth",.56)
                elif row==2:
                    wall.plate(l,z0,r,z1,3.25,"BallisticAlt" if col%7==5 else "Ballistic",.63)
                    # Small recesses near the bottom of occasional removable liners.
                    if r-l>170 and col%3!=0:
                        for x in (l+5.3,r-5.3):
                            wall.plate(x-1.1,z0+5.2,x+1.1,z0+5.7,3.32,"Rail",0)
                else:
                    wall.plate(l,z0,r,z1,2.08,"Fog" if (col+4*row)%8==3 else "Porcelain",.26)
        # Independent liner bedding prevents a light grout stripe across the
        # dark ballistic band. The first-seen material slot order is preserved.
        z0,z1=max(82.6,bottom+.15),min(295.4,top)
        if z1>z0:
            wall.plate(left,z0,right,z1,1.22,"Rail",0)
        if bottom<17.4:
            wall.plate(left,bottom+.2,right,17.4,1.22,"Plinth",0)
        for z in (81.7,295.5):
            if bottom<z<top:
                wall.plate(left+.2,z,right-.2,z+.9,2.8,"Rail",.22)
assets=[geom.export("SM_TR_A3_WallPanels")]

# Retain perimeter light emitters and do not overdraw their existing white strips.
# Two alternated banks of low-profile lights leave center ceiling anchors readable.
ceil=Plane((0,0,800),(1,0,0),(0,1,0),(0,0,-1))
geom=Mesh()
ceil.plate(-979,-2238,979,1177,.8,"Seal",0)
xx=linear_positions(-979,979,7);yy=linear_positions(-2238,1177,10)
for i,(a,b) in enumerate(zip(xx,xx[1:])):
    for j,(c,d) in enumerate(zip(yy,yy[1:])):
        ceil.plate(a+1.3,c+1.3,b-1.3,d-1.3,1.65,"LidAlt" if (2*i+j)%9==3 else "Lid",.29)
for row,y in enumerate((-2080,-1440,-790,-140,505,1015)):
    for x,w in ([(-613,235),(0,375),(613,235)] if row%2 else [(-485,340),(485,340)]):
        ceil.plate(x-w/2-4,y-9,x+w/2+4,y+9,3.5,"Plinth",1.0)
        ceil.plate(x-w/2,y-4.4,x+w/2,y+4.4,3.9,"Lens",.48)
assets.append(geom.export("SM_TR_A3_CeilingPanels"))
out={"palette":palette,"assets":assets,"room_cm":{"x":[-1000,1000],"y":[-2270,1200],"z":[0,800]},"entry_clearance_cm":[-77,77,237]}
(HERE/"shell_manifest.json").write_text(json.dumps(out,indent=2),encoding="utf8")
print("TRAINING_SHELL_READY",[(row["name"],row["triangles"]) for row in assets])
