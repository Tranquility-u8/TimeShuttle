"""Build atrium finish meshes in surveyed UE centimetres. Run with background Blender."""
from pathlib import Path
import json
import math
import bpy
from mathutils import Vector

HERE = Path(__file__).resolve().parent
SOURCE = HERE.parents[2]
LAYOUT = json.loads((SOURCE / 'LabV39/R17/revised-layout-geometry.json').read_text(encoding='utf8'))
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.unit_settings.system = 'METRIC'
scene.unit_settings.scale_length = .01
manifest = {}


class Part:
    def __init__(self, name, pivot):
        self.name = 'SM_Hall' + name
        self.pivot = tuple(pivot)
        self.verts = []
        self.faces = []
        self.slots = []
        self.face_slots = []

    def face(self, points, normal, slot):
        ox, oy, oz = self.pivot
        vv = [Vector((x-ox, oy-y, z-oz)) for x,y,z in points]
        n = Vector((normal[0], -normal[1], normal[2]))
        if (vv[1]-vv[0]).cross(vv[2]-vv[0]).dot(n) < 0:
            vv.reverse()
        start = len(self.verts)
        self.verts.extend(vv)
        self.faces.append(tuple(range(start,start+len(vv))))
        if slot not in self.slots:
            self.slots.append(slot)
        self.face_slots.append(self.slots.index(slot))

    def box(self, center, dims, material):
        cx,cy,cz=center
        dx,dy,dz=(n*.5 for n in dims)
        for i,n in enumerate(((1,0,0),(-1,0,0),(0,1,0),(0,-1,0),(0,0,1),(0,0,-1))):
            a = i//2
            uv = [k for k in range(3) if k!=a]
            pts=[]
            for u,v in ((-1,-1),(-1,1),(1,1),(1,-1)):
                s=list(n)
                s[uv[0]]=u;s[uv[1]]=v
                pts.append((cx+s[0]*dx,cy+s[1]*dy,cz+s[2]*dz))
            self.face(pts,n,material)

    def export(self):
        me=bpy.data.meshes.new(self.name)
        me.from_pydata(self.verts,[],self.faces)
        me.update()
        for m in self.slots:
            me.materials.append(bpy.data.materials.get(m) or bpy.data.materials.new(m))
        uv=me.uv_layers.new(name='Surface')
        for poly,idx in zip(me.polygons,self.face_slots):
            poly.material_index=idx
            ax=max(range(3),key=lambda j:abs(poly.normal[j]))
            p,q = [i for i in range(3) if i!=ax]
            for l in poly.loop_indices:
                co=me.vertices[me.loops[l].vertex_index].co
                uv.data[l].uv = co[p]/160, co[q]/160
        ob=bpy.data.objects.new(self.name,me)
        scene.collection.objects.link(ob)
        bpy.ops.object.select_all(action='DESELECT')
        ob.select_set(True);bpy.context.view_layer.objects.active=ob
        bpy.ops.export_scene.fbx(filepath=str(HERE/(self.name+'.fbx')),use_selection=True,object_types={'MESH'},
            axis_forward='-Y',axis_up='Z',apply_unit_scale=True,apply_scale_options='FBX_SCALE_UNITS',
            mesh_smooth_type='FACE',bake_anim=False,add_leaf_bones=False)
        manifest[self.name]={'pivot_cm':self.pivot,'slots':self.slots,'triangles':sum(len(v)-2 for v in self.faces)}


def bands(lo,hi,step):
    count=max(1,round((hi-lo)/step))
    return [(lo+(hi-lo)*i/count,lo+(hi-lo)*(i+1)/count) for i in range(count)]


def facade_limit(layer,x):
    # Balcony edge and facade have different radii in the whitebox.
    samples=[]
    for poly in LAYOUT[layer]:
        for ring in [poly['outer'],*poly['holes']]:
            for (a,b),(c,d) in zip(ring,ring[1:]+ring[:1]):
                if min(a,c)<=x/100<max(a,c):
                    y=-(b+(d-b)*(x/100-a)/(c-a))*100
                    if -7000 < y < -4200:
                        samples.append(y)
    return max(samples)+3


def finish_plane(part, box, z, layer, ceiling=False):
    left,start,right,end=box
    n=(0,0,-1 if ceiling else 1)
    sign=n[2]
    pitch=370 if ceiling else 192
    for ix,(a,b) in enumerate(bands(left,right,pitch)):
        for iy,(c,d) in enumerate(bands(start,end,pitch)):
            ends=[facade_limit(layer,x) if start < -4700 else -8000 for x in (a,b)]
            for reveal,offset,slot in [(0,.34,'Joint'),(.44 if ceiling else .25,1.05 if ceiling else .72,'Ceiling' if ceiling else ('FloorAlt' if (ix*7+iy*5)%17==3 else 'Floor'))]:
                l,r=a+reveal,b-reveal
                bottom_l=max(c,ends[0])+reveal
                bottom_r=max(c,ends[1])+reveal
                top=d-reveal
                if top <= max(bottom_l,bottom_r):continue
                zz=z+sign*offset
                part.face([(l,bottom_l,zz),(r,bottom_r,zz),(r,top,zz),(l,top,zz)],n,slot)


floor=Part('AtriumFloor',(0,-1500,0))
# The front threshold, wall faces and gallery void are explicit clip edges.
for lower in [(-1884,-5300,1884,-3400),(-1884,-3400,1884,400),(-1884,400,1884,922)]:
    finish_plane(floor,lower,0,'floor_lower')
for upper in [(-1884,-4900,1884,-3400),(-1884,-3400,-1400,400),(1400,-3400,1884,400),(-1884,400,1884,922)]:
    finish_plane(floor,upper,540,'floor_upper')
floor.export()

ceiling=Part('AtriumSoffit',(0,-1500,1400))
for rect in [(-1884,-5300,1884,-3400),(-1884,-3400,1884,400),(-1884,400,1884,922)]:
    finish_plane(ceiling,rect,1400,'floor_lower',True)
ceiling.export()


def quad_on_wall(part,side,base,u,v,U,V,depth,slot):
    x=base-side*depth
    part.face([(x,u,v),(x,U,v),(x,U,V),(x,u,V)],(-side,0,0),slot)


def wall_skin(part,side,base,lo,hi,bottom,top):
    # Build within one surveyed solid piece: door and window apertures stay open.
    quad_on_wall(part,side,base,lo,bottom,hi,top,1.3,'Joint')
    zs = sorted({bottom,top,*[z for z in (18,208,356,490,562,809,1140,1377) if bottom < z < top]})
    for i,(a,b) in enumerate(bands(lo,hi,312)):
        for c,d in zip(zs,zs[1:]):
            if b-a<2 or d-c<2: continue
            trim=(c in (0,540) and d-c<40) or c==1377
            finish='Graphite' if trim else ('WallCool' if c>=1140 else 'Panel')
            quad_on_wall(part,side,base,a+.55,c+.55,b-.55,d-.55,2.0,finish)
            if trim and b-a>48:
                quad_on_wall(part,side,base,a+2,d-3,b-2,d-2.05,2.17,'Alloy')


def loop(w,h,bevel,z):
    return [(-w+bevel,z-h),(w-bevel,z-h),(w,z-h+bevel),(w,z+h-bevel),(w-bevel,z+h),(-w+bevel,z+h),(-w,z+h-bevel),(-w,z-h+bevel)]


def window_frame(part,side,base,center,width,low,high):
    h=(high-low)/2; z=(high+low)/2
    # Ring is narrower at the opening, forming one dark lip and a brushed bevel.
    rings = [(width/2+16,h+16,30,2.35),(width/2+14,h+14,29,6),
             (width/2+7,h+7,24,8.5),(width/2-2,h-2,18,8.5),(width/2-3,h-3,17,5.0)]
    for k,(a,b) in enumerate(zip(rings,rings[1:])):
        pp=loop(*a[:3],z);qq=loop(*b[:3],z)
        for j in range(8):
            raw=[(pp[j],a[3]),(pp[(j+1)%8],a[3]),(qq[(j+1)%8],b[3]),(qq[j],b[3])]
            part.face([(base-side*d,center+u,v) for (u,v),d in raw],(-side,0,0),['Joint','Alloy','Graphite','Seal'][k])
    for k in range(3):
        v = low+7+k*2.9
        quad_on_wall(part,side,base,center+width*.43,v,center+width*.43+8,v+1.55,8.9,'Status')


walls=Part('GalleryWallLinings',(0,-1400,600))
# UE world coordinates for uninterrupted wall runs, door heads and window sill/header.
west=[(-3318,-3157,540,1400),(-3157,-2837,930,1400),(-3157,-2837,540,630),
      (-2837,-1320,540,1400),(-1320,-1000,880,1400),(-1000,-975,540,1400),
      (-911.6,-130,540,1400),(-58,192,920,1400),(192,550,540,1400),
      (550,850,920,1400),(850,925,540,1400)]
east=[(-3295,-2700,540,1400),(-2700,-2100,930,1400),(-2700,-2100,540,630),
      (-2100,-1760,540,1400),(-1760,-1440,880,1400),(-1440,-730,540,1400),
      (-670,-370,540,1400),(-310,-93,540,1400),(-93,227,920,1400),(227,447,540,1400),
      (507,925,540,1400)]
for side,upper in [(-1,west),(1,east)]:
    for span in upper:
        wall_skin(walls,side,side*1885,*span)
    for span in [(-2184,-1960,0,496),(-1340,-1116,0,496),(-1960,-1340,0,90),(-1960,-1340,330,494)]:
        wall_skin(walls,side,side*1890,*span)
    window_frame(walls,side,side*1890,-1650,620,90,330)
window_frame(walls,-1,-1885,-2997,320,630,930)
window_frame(walls,1,1885,-2400,600,630,930)
walls.export()

fascia=Part('GalleryEdge',(0,-1500,540))
# Cover the 44 cm cut edge of the original slab just below the walking elevation,
# including a bevel, reveal and narrow recessed cyan status cassette.
def apron(center,direction,length):
    dx,dy=direction; nx,ny=-dy,dx
    cx,cy=center
    def xyz(u,d,z): return (cx+dx*u+nx*d,cy+dy*u+ny*d,z)
    segments=bands(-length/2,length/2,360)
    for a,b in segments:
        a+=.32;b-=.32
        for d,e,lo,hi,slot in [(1.8,3.0,498,507,'Graphite'),(3.0,3.0,507,530,'Graphite'),(3.0,4.2,530,534,'Alloy'),(4.2,2.0,534,539.5,'Graphite')]:
            fascia.face([xyz(a,d,lo),xyz(b,d,lo),xyz(b,e,hi),xyz(a,e,hi)],(nx,ny,0),slot)
    if length>=450:
        for u in [-(length*.26),length*.26]:
            for width,d,lo,hi,mat in [(58,3.35,512,525,'Joint'),(27,3.6,515.5,520.5,'Status')]:
                fascia.face([xyz(u-width/2,d,lo),xyz(u+width/2,d,lo),xyz(u+width/2,d,hi),xyz(u-width/2,d,hi)],(nx,ny,0),mat)
for y,dirx in [(-3400,1),(400,-1)]:
    apron((0,y),(dirx,0),2800)
for x,diry in [(-1400,-1),(1400,1)]:
    for lo,hi in [(-3400,-3267),(-2867,-133),(267,400)]:
        apron((x,(lo+hi)/2),(0,diry),hi-lo)
fascia.export()

fixtures=Part('AtriumLightFittings',(0,-1450,600))
# Two existing 3,800 cm transverse ceiling beams on the approach to the facade.
for y in (-1500,-3400):
    fixtures.box((0,y,1368),(3780,53,42),'Graphite')
    fixtures.box((0,y,1341.4),(3781,60,11.2),'Graphite')
    fixtures.box((0,y-25,1335.55),(3766,1.65,.65),'Alloy')
    fixtures.box((0,y+25,1335.55),(3766,1.65,.65),'Alloy')
    for i,x in enumerate((-1450,-500,500,1450)):
        fixtures.box((x,y,1335.2),(211,39,1.8),'Joint')
        for k in (-1,0,1):
            fixtures.box((x+k*64,y,1334.0),(59,29,1.25),'CoolDiffuser')
        for off in (-117,117):
            fixtures.box((x+off,y,1335.25),(10,13,1.4),'Seal')

# Face normal nx,ny points out from the mounting wall. All lenses have a dark reveal.
def lamp(pos,normal,width,height,lens):
    x,y,z=pos;nx,ny=normal;axisx=abs(ny)>0
    def shell(offset,along,depth,high,mat,z_offset=0):
        dims=(along,depth,high) if axisx else (depth,along,high)
        fixtures.box((x+offset*nx,y+offset*ny,z+z_offset),dims,mat)
    shell(1,width+5,3,height+4,'Seal')
    shell(3.5,width,5,height,'Graphite')
    shell(6.2,width-6,1.4,height-4,'Alloy')
    shell(7.1,width-10,1.2,height-6,lens)
    shell(7.3,width+1,2,2.8,'Graphite',height/2-1)

lamp((0,909,487),(0,-1),510,15,'WarmDiffuser')
lamp((-1883,-3237,744),(1,0),99,23,'WarmDiffuser')
lamp((1883,-245,755),(-1,0),104,29,'Warning')
# Curb lamp sits outside tread S4 rather than in its sweep.
fixtures.box((462,274,15),(57,18,30),'Graphite')
lamp((462,283,16),(0,1),52,15,'WarmDiffuser')
for cx in (-990,990):
    lamp((cx,396,500),(0,-1),64,12,'WarmDiffuser')
for side in (-1,1):
    for pos_y in (-2040,-1280):
        lamp((side*1887,pos_y,30),(-side,0),52,16,'WarmDiffuser')
# Flush warm locators on the lower edge of gallery fascia. Their small size respects circulation.
for cx in (-1040,1040):
    lamp((cx,-3395,510),(0,1),47,13,'WarmDiffuser')
# Three low angled fittings sit on the walking side of the glass base shoe.
# The top of each diffuser tilts both toward the player and upward from the floor.
for y in (-560,-1520,-2480):
    section=[(1402,541),(1420,541),(1420,547),(1406,560),(1402,560)]
    for idx,((x,z),(xx,zz)) in enumerate(zip(section,section[1:]+section[:1])):
        fixtures.face([(x,y-30,z),(xx,y-30,zz),(xx,y+30,zz),(x,y+30,z)],
                      (zz-z,0,x-xx),'Alloy' if idx==2 else 'Graphite')
    for sign in (-1,1):
        fixtures.face([(x,y+30*sign,z) for x,z in section],(0,sign,0),'Graphite')
    for inset,a,b,dy,lens in [(.27,1407,1419,26,'Joint'),(.55,1408,1417.8,22,'WarmDiffuser')]:
        top=lambda x:560-(x-1406)*13/14+inset
        fixtures.face([(a,y-dy,top(a)),(a,y+dy,top(a)),(b,y+dy,top(b)),(b,y-dy,top(b))],
                      (1,0,1),lens)
fixtures.export()

(HERE/'environment_meshes.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf8')
print('Hall environment mesh totals:',len(manifest),sum(a['triangles'] for a in manifest.values()))
