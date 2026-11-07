"""Build the north return plenum, removable service shroud, and its wall dock.

Run in Blender 4+. Dimensions are in UE cm, +Y is the room-facing side.
The two floor props use base-centred pivots. The rail pivot is on the wall.
"""
import json
import math
from pathlib import Path
import sys

import bmesh
import bpy
from mathutils import Vector
from mathutils.geometry import delaunay_2d_cdt

ROOT = Path(__file__).resolve().parent
PALETTE = json.loads((ROOT.parent / 'material_manifest.json').read_text())
PALETTE.update({
    'TC_Pearl': dict(color_linear=(.77,.779,.776), metallic=.11, roughness=.43),
    'TC_Brushed': dict(color_linear=(.32,.35,.36), metallic=.64, roughness=.34),
    'TC_Support': dict(color_linear=(.104,.126,.133), metallic=.39, roughness=.51),
})
MATERIALS = {}


def rect(x0, x1, z0, z1, clip=0):
    if clip == 0:
        return [(x0,z0),(x1,z0),(x1,z1),(x0,z1)]
    c = min(clip, (z1-z0)*.45, (x1-x0)*.45)
    return [(x0+c,z0),(x1-c,z0),(x1,z0+c),(x1,z1-c),
            (x1-c,z1),(x0+c,z1),(x0,z1-c),(x0,z0+c)]


def translated(points, x, z):
    return [(x+a,z+b) for a,b in points]


def ellipse(x,z,rx,rz,n=12):
    return [(x+rx*math.cos(math.tau*i/n), z+rz*math.sin(math.tau*i/n)) for i in range(n)]


def contains(poly, point):
    x,y = point
    inside = False
    for (ax,ay),(bx,by) in zip(poly, poly[1:]+poly[:1]):
        if (ay>y)!=(by>y) and x<(bx-ax)*(y-ay)/(by-ay)+ax:
            inside = not inside
    return inside


class Asset:
    def __init__(self, name):
        self.name = name
        self.collection = bpy.data.collections.new(name)
        bpy.context.scene.collection.children.link(self.collection)
        self.objects = []

    def geometry(self, name, pts, faces, material, bevel=0):
        mesh = bpy.data.meshes.new(name)
        mesh.from_pydata([(x*.01,-y*.01,z*.01) for x,y,z in pts],[],faces)
        mesh.validate()
        bm = bmesh.new()
        bm.from_mesh(mesh)
        bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
        bm.to_mesh(mesh)
        bm.free()
        obj = bpy.data.objects.new(name,mesh)
        self.collection.objects.link(obj)
        obj.data.materials.append(MATERIALS[material])
        if bevel:
            modifier = obj.modifiers.new('Folded edge radius','BEVEL')
            modifier.width = bevel*.01
            modifier.segments = 1
            modifier.limit_method = 'ANGLE'
            modifier.angle_limit = math.radians(37)
            bpy.context.view_layer.objects.active = obj
            bpy.ops.object.modifier_apply(modifier=modifier.name)
        self.objects.append(obj)
        return obj

    def prism(self,name,outline,back,front,material,bevel=0,axis='Y'):
        n=len(outline)
        if axis=='Y':
            points=[(a,d,b) for d in (back,front) for a,b in outline]
        else:
            points=[(a,b,d) for d in (back,front) for a,b in outline]
        faces=[list(range(n)),list(range(n,2*n))]
        faces.extend((i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n))
        return self.geometry(name,points,faces,material,bevel)

    def box(self,name,x0,x1,y0,y1,z0,z1,mat,bevel=0):
        return self.prism(name,rect(x0,x1,z0,z1),y0,y1,mat,bevel)

    def perforated(self,name,outer,holes,back,front,material,bevel=0):
        loops=[outer]+holes
        flat=[]; edges=[]
        for chain in loops:
            start=len(flat)
            flat.extend(chain)
            edges.extend((start+i,start+(i+1)%len(chain)) for i in range(len(chain)))
        verts,_,tris,_,_,_=delaunay_2d_cdt([Vector(v) for v in flat],edges,[],0,1e-7)
        xy=[tuple(p) for p in verts]; n=len(xy)
        mapping={tuple(round(float(k),4) for k in p):i for i,p in enumerate(xy)}
        points=[(x,d,z) for d in (back,front) for x,z in xy]
        faces=[]
        for ids in tris:
            center=[sum(xy[i][k] for i in ids)/len(ids) for k in (0,1)]
            if contains(outer,center) and not any(contains(h,center) for h in holes):
                faces.extend((list(ids),[n+i for i in ids]))
        for j,k in edges:
            a,b=[mapping[tuple(round(float(t),4) for t in flat[i])] for i in (j,k)]
            faces.append((a,b,b+n,a+n))
        return self.geometry(name,points,faces,material,bevel)

    def loft(self,name,sections,material,bevel=0):
        size=len(sections[0])
        faces=[list(range(size)),list(range((len(sections)-1)*size,len(sections)*size))]
        for k in range(len(sections)-1):
            for j in range(size):
                v=k*size+j; q=k*size+(j+1)%size
                faces.append((v,q,q+size,v+size))
        return self.geometry(name,[p for row in sections for p in row],faces,material,bevel)

    def fastener(self,x,y,z,rad,part):
        self.prism(part+' | head',ellipse(x,z,rad,rad,8),y-.25,y+.24,'TC_Alloy',.07)
        self.prism(part+' | drive',ellipse(x,z,rad*.38,rad*.38,6),y+.23,y+.35,'TC_Seal')

    def type(self,name,words,x,y,z,width,back=False):
        curve=bpy.data.curves.new(name,'FONT')
        curve.body=words;curve.align_x='CENTER';curve.align_y='CENTER'
        curve.resolution_u=3
        obj=bpy.data.objects.new(name,curve)
        self.collection.objects.link(obj)
        bpy.ops.object.select_all(action='DESELECT');obj.select_set(True)
        bpy.context.view_layer.objects.active=obj
        bpy.ops.object.convert(target='MESH')
        max_x=max(v.co.x for v in obj.data.vertices);min_x=min(v.co.x for v in obj.data.vertices)
        fac=width/(max_x-min_x)
        for vertex in obj.data.vertices:
            a,b,c=vertex.co
            vertex.co=((x+(-1 if back else 1)*(a-.5*(max_x+min_x))*fac)*.01,-y*.01,(z+b*fac)*.01)
        if back:
            obj.data.flip_normals()
        obj.data.materials.append(MATERIALS['TC_Graphite'])
        self.objects.append(obj)

    def export(self):
        # Independently parameterize each planar face, including all bevels and
        # folded side walls, for stable shading after UE half-precision UVs.
        import struct
        smallest=1.; total=0
        for obj in self.objects:
            mesh=obj.data
            bm=bmesh.new();bm.from_mesh(mesh)
            bmesh.ops.triangulate(bm,faces=list(bm.faces))
            # A clamped bevel on a narrow chamfer can end in a collinear triangle.
            # It has no visible surface and no valid tangent, so remove it here.
            empty=[f for f in bm.faces if f.calc_area()<1e-12]
            if empty:bmesh.ops.delete(bm,geom=empty,context='FACES')
            bm.to_mesh(mesh);bm.free();mesh.update()
            # Font conversion creates its own UV0. UE uses the first channel even
            # if Blender marks our replacement as active; publish only this map.
            while mesh.uv_layers:
                mesh.uv_layers.remove(mesh.uv_layers[0])
            uv=mesh.uv_layers.new(name='UVMap')
            for face in mesh.polygons:
                pts=[mesh.vertices[i].co for i in face.vertices]
                u=max((b-a for a,b in zip(pts,pts[1:]+pts[:1])),key=lambda x:x.length_squared).normalized()
                v=face.normal.cross(u).normalized()
                local=[((p-pts[0]).dot(u),(p-pts[0]).dot(v)) for p in pts]
                scales=[max(p[k] for p in local)-min(p[k] for p in local) for k in (0,1)]
                if min(scales)<1e-10:
                    raise ValueError((obj.name,face.index,scales))
                coords=[[(p[k]-min(q[k] for q in local))/scales[k] for k in (0,1)] for p in local]
                for idx,pt in zip(face.loop_indices,coords): uv.data[idx].uv=pt
                a,b,c=[[struct.unpack('e',struct.pack('e',s))[0] for s in pt] for pt in coords]
                smallest=min(smallest,abs((b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])))
            total+=len(mesh.polygons)
        assert smallest>1e-6,(self.name,smallest)
        bpy.ops.object.select_all(action='DESELECT')
        for o in self.objects:o.select_set(True)
        bpy.context.view_layer.objects.active=self.objects[0]
        bpy.ops.export_scene.fbx(filepath=str(ROOT/(self.name+'.fbx')),use_selection=True,
            object_types={'MESH'},axis_forward='-Y',axis_up='Z',add_leaf_bones=False,
            mesh_smooth_type='FACE',use_triangles=True,bake_anim=False)
        points=[(v.co.x*100,-v.co.y*100,v.co.z*100) for o in self.objects for v in o.data.vertices]
        return dict(triangles=total,min_uv_det=smallest,
                bounds_cm=[[round(op(p[k] for p in points),4) for k in range(3)] for op in (min,max)],
                slots=sorted({o.data.materials[0].name for o in self.objects}))


def plenum():
    a=Asset('SM_TC_ReturnPlenum')
    # The back is continuous across both air inlets and the foundation.
    a.prism('Elastomer floor plinth',rect(-225,225,0,15,1.5),-39,39,'TC_Graphite',.65)
    # The perimeter is already folded in section. Keep those rear border planes
    # flat: beveling the 2 cm clipping edge again collapses its corner triangles.
    a.prism('Closed rear pressure skin',rect(-226,226,12,549,2),-40,-28.4,'TC_Ceramic')
    a.prism('Matte acoustic baffle',rect(-224,224,12.5,546,2),-28,-21.8,'TC_Seal',.85)
    skin=[(-228,14),(-215.5,14),(-215.5,532),(-103.5,532),(-88,513),
          (-88,18),(-61,74),(222,74),(228,79),(228,546),(225,549),(-225,549),(-228,546)]
    a.prism('One piece formed front cheek',skin,-29,40,'TC_Ceramic',1.5)
    a.box('Lower intake silencer',-68,224,-17,-13.5,15,76,'TC_Graphite',1.2)
    a.box('Left return side below folded lip',-227,-216,-30,39,13.5,39,'TC_Ceramic',.65)
    a.prism('Bent lower intake sill',[(-216,14),(224,14),(224,20),(-84,20),(-96,24),(-216,21)],
            -26,37.6,'TC_Brushed',.7)
    for i in range(6):
        cx=-205+i*19.6
        cross=[(-2.4,31.3),(1.25,33),(3.9,29.8),(10,-8),(8,-14),(4,-7.7)]
        loops=[]
        for z,scale,offset in [(23.8,.82,-1),(34,1,0),(505,1,0),(525,.62,2)]:
            loops.append([(cx+x*scale+offset,y*scale,z) for x,y in cross])
        a.loft('Vertical airfoil %02d'%(i+1),loops,'TC_Brushed',.42)
    # The opaque rear carries a removable access panel, seen when walking around it.
    a.prism('Rear inspection seal',rect(-184,184,73,503,3),-40.65,-39.5,'TC_Graphite')
    a.prism('Rear inspection panel',rect(-182.3,182.3,74.7,501.3,2.5),-41.3,-40.6,'TC_Ceramic')
    a.type('Return bank index','RETURN 02',145,40.42,492,62)
    return a


def handle(a,x,z,n):
    # The well occupies a real aperture in the formed sheet. A chamfered metal
    # mouth, dark back wall and rolled lower grip give it depth at glancing views.
    outer=translated(rect(-21,21,-13,13,2),x,z)
    inner=translated(rect(-17.5,17.5,-9.7,9.7,1.45),x,z)
    a.perforated(n+' | rolled mouth',outer,[inner],25.8,27.7,'TC_Alloy',.36)
    outlines=[inner,translated(rect(-15.7,15.7,-7.5,7.5,1.3),x,z)]
    points=[(xx,depth,zz) for loop,depth in zip(outlines,(27.23,18.4)) for xx,zz in loop]
    nn=len(inner)
    faces=[(i,(i+1)%nn,(i+1)%nn+nn,i+nn) for i in range(nn)]
    obj=a.geometry(n+' | pressed well',points,faces,'TC_Brushed')
    # This surface is the inside of the grip bowl (front normal has positive UE Y).
    bm=bmesh.new();bm.from_mesh(obj.data)
    if sum(f.normal.y for f in bm.faces)>0:bmesh.ops.reverse_faces(bm,faces=list(bm.faces))
    bm.to_mesh(obj.data);bm.free()
    a.prism(n+' | socket shadow',outlines[1],17.4,18.45,'TC_Support')
    a.prism(n+' | finger return',translated(rect(-16.9,16.9,-9.8,-6.0,.7),x,z),23.7,27.1,'TC_Alloy',.23)


def shroud():
    a=Asset('SM_TC_ServiceShroud')
    outer=[(-195,12),(-187,0),(190,0),(195,5),(195,374),(190,379),(-191,379),(-195,375)]
    a.prism('Shallow steel back tray',outer,-27.5,16.8,'TC_Support',1.3)
    a.prism('Continuous charcoal gasket',rect(-194.1,194.1,1.7,378,3),12.5,19.1,'TC_Seal',.75)
    a.prism('Copper contact visible on exposed edge',[(-193,13),(-190.7,11),(-190.7,371.8),(-193,373.2)],
            16.8,20.2,'TC_Amber',.2)
    # Integral bottom-left ding with a shallow return lip.
    face=[(-192,15),(-184.8,1.9),(189.7,1.9),(193.6,5.5),(193.6,373.1),(190.3,376.2),
          (-188.9,376.2),(-192,372.7)]
    hpos=[(-135,324),(74,324)]
    holes=[translated(rect(-18.3,18.3,-10.1,10.1,1.5),x,z) for x,z in hpos]
    a.perforated('Pressed removable front skin',face,holes,19.5,26.3,'TC_Brushed',.72)
    for j,(x,z) in enumerate(hpos):handle(a,x,z,'Recessed lifting cup %d'%(j+1))
    for j,x in enumerate((-136,136)):
        left=j==0
        sh=(.85 if left else 0)
        tab=[(-12.5,374),(12.5,374),(12.5+sh,387),(8+sh,392),(-8+sh,392),(-12.5+sh,387)]
        a.perforated('Top hanger piercing %d'%j,translated(tab,x,0),
            [ellipse(x+sh,384.5,4.5,4.5,12)],-12,-7.6,'TC_Alloy',.4)
        a.prism('Top ear shoe %d'%j,rect(x-16,x+16,372.8,376.4,1.4),-17,-2,'TC_Graphite',.35)
    # Backside fittings are visible when the original driven cabinet rotates.
    a.prism('Rear seam',rect(-177,177,19,359,4),-27.85,-27.0,'TC_Seal')
    a.prism('Rear skin stiffener',rect(-175,175,21,357,3.2),-28.4,-27.7,'TC_Brushed',.45)
    for x in (-142,142):
        for z in (50,288):
            a.prism('Back wall glide pad',rect(x-10,x+10,z-13,z+13,2.5),-29.15,-28.3,'TC_Graphite',.42)
    return a


def dock():
    a=Asset('SM_TC_ShroudDock')
    a.prism('Wall mounting rail',rect(-178,178,-7,11,3.2),-.6,4.8,'TC_Support',.65)
    a.prism('Folded satin track',rect(-175,175,-3.8,9.1,1.5),4.7,12,'TC_Brushed',.62)
    a.prism('Rail upper folded edge',rect(-175.2,175.2,7.3,10,.9),10.5,14,'TC_Alloy',.38)
    a.prism('Recessed rail channel',rect(-171,171,-3,1.7,.7),12,12.36,'TC_Seal',.12)
    for j,x in enumerate((-136,136)):
        side='L' if j==0 else 'R'
        a.prism(side+' | wall plate',rect(x-26,x+26,-20,23,4.2),-.75,4.3,'TC_Ceramic',.75)
        for dx in (-17.5,17.5):
            a.fastener(x+dx,4.75,16.5,2.1,side+' anchor')
        a.prism(side+' | seat back',rect(x-21.5,x+21.5,-19.3,17.5,2.9),
                3.9,14.2,'TC_Graphite',.7)
        a.prism(side+' | empty socket',rect(x-15.9,x+15.9,-18.8,11.2,1.7),
                14,14.65,'TC_Seal',.42)
        a.prism(side+' | keeper crown',rect(x-22.5,x+22.5,8.2,18.9,2.7),
                12.6,23.9,'TC_Brushed',.8)
        for sx in (-1,1):
            # One torn retainer is splayed toward the viewer. The open dark saddle
            # beneath the upper lip is sized to accept the matching shroud tang.
            x0=x+sx*18.8
            skew=-4 if side=='L' and sx==-1 else 0
            outline=[(x0-4,13),(x0+4,13),(x0+4+skew,-16.9),(x0+skew,-21.5),(x0-4.8+skew,-18)]
            a.prism(side+' | socket keeper '+str(sx),outline,13.35,24.5+(2 if skew else 0),'TC_Alloy',.56)
        a.prism(side+' | worn keeper stop',rect(x-11.5,x+11.5,5.6,7.5,.55),14.5,16.7,'TC_Amber',.24)
    return a


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    for key,defs in PALETTE.items():
        mat=bpy.data.materials.new(key)
        mat.diffuse_color=(*defs['color_linear'],1)
        mat.metallic=defs['metallic'];mat.roughness=defs['roughness']
        MATERIALS[key]=mat
    models=[plenum(),shroud(),dock()]
    reports={m.name:m.export() for m in models}
    # Keep groups and individual named parts editable in the assembly. Assembly
    # translations are only applied after exporting each mesh around its pivot.
    for m,offset in zip(models,[(0,0,0),(-.4,2.65,0),(-.4,3.8315,4.843)]):
        pivot=bpy.data.objects.new(m.name.replace('SM_TC_','')+' | pivot',None)
        m.collection.objects.link(pivot)
        for part in m.objects:part.parent=pivot
        pivot.location=offset
    bpy.ops.object.select_all(action='DESELECT')
    look=Vector((-.05,.35,2.6))
    eye=Vector((-8,-11,4.1))
    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type=='VIEW_3D':
                space=area.spaces.active
                space.region_3d.view_rotation=(look-eye).to_track_quat('-Z','Y')
                space.region_3d.view_distance=12.5
                space.region_3d.view_location=look
                space.shading.color_type='MATERIAL'
                space.overlay.show_overlays=False
    bpy.context.preferences.filepaths.save_version=0
    bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'NorthExitAssembly.blend'),compress=True)
    if '--' in sys.argv:
        dst=Path(sys.argv[sys.argv.index('--')+1])
        dst.write_text(json.dumps(reports,indent=2),encoding='utf8')
    print(json.dumps(reports,indent=2))

if __name__=='__main__':
    main()
