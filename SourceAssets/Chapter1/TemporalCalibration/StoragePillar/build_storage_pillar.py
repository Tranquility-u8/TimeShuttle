"""Build the shared, metre-authored storage pillar FBX in Blender.

The retained parts come from the project's editable clock instruments. The new
shaft is built around an empty, coaxial glass tank. The display and accent are
material slots so either clock can use the same mesh and pivot.
"""
from collections import Counter
from pathlib import Path
import math

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parent
NAME = "SM_TC_ParticleStoragePillar"
SHAFT_RADIUS = 1.325
WALL_DEPTH = SHAFT_RADIUS * math.cos(math.pi / 6)
VESSEL_RADIUS = 0.835
SIDES = 48


def front(yaw, u, z, depth):
    angle = math.radians(yaw)
    return (depth * math.cos(angle) - u * math.sin(angle),
            depth * math.sin(angle) + u * math.cos(angle), z)


def clipped_rect(width, height, clip):
    u, v = width / 2, height / 2
    return [(-u + clip, -v), (u - clip, -v), (u, -v + clip), (u, v - clip),
            (u - clip, v), (-u + clip, v), (-u, v - clip), (-u, -v + clip)]


HALF_FACET = SHAFT_RADIUS / 2


def folded_front(u, z, depth):
    """Follow the original hex at the front and down its two shoulders."""
    if abs(u) <= HALF_FACET:
        return (depth, u * depth / WALL_DEPTH, z)
    along_shoulder = abs(u) - HALF_FACET
    y = depth * math.tan(math.pi/6) + .5 * along_shoulder
    return (depth - math.sin(math.pi/3) * along_shoulder, math.copysign(y, u), z)


def frame_outline(width, height, clip):
    r = clipped_rect(width, height, clip)
    return [r[0], (-HALF_FACET, -height/2), (HALF_FACET, -height/2), *r[1:5],
            (HALF_FACET, height/2), (-HALF_FACET, height/2), *r[5:]]


class Surface:
    def __init__(self):
        self.points = []
        self.polygons = []
        self.materials = []
        self.uvs = []
        self.smoothed = []

    def patch(self, points, polys, materials, uvs=None, smooth=False):
        offset = len(self.points)
        self.points.extend(points)
        for i, poly in enumerate(polys):
            self.polygons.append(tuple(offset + j for j in poly))
            self.materials.append(materials if isinstance(materials, str) else materials[i])
            self.uvs.append(uvs[i] if uvs else None)
            self.smoothed.append(smooth)

    def panel(self, yaw, u, z, w, h, back, face, material, clip=.018):
        shape = clipped_rect(w, h, clip)
        points = [front(yaw, u + x, z + y, d) for d in (back, face) for x, y in shape]
        polys = [tuple(reversed(range(8))), tuple(range(8, 16))]
        polys.extend((i, (i+1) % 8, (i+1) % 8 + 8, i+8) for i in range(8))
        self.patch(points, polys, material)

    def pane(self, yaw, z, w, h, depth, material, clip):
        shape = clipped_rect(w, h, clip)
        vertices = [front(yaw, x, z+y, depth) for x,y in shape]
        texcoords = [(x/w+.5,y/h+.5) for x,y in shape]
        self.patch(vertices,[tuple(range(8))],material,[texcoords])

    def frame(self, yaw, z, profiles):
        """Follow the outside, front bevel and inner reveal; leave the bay open."""
        rings = [frame_outline(w,h,clip) for w,h,clip,d,mat in profiles]
        verts = [folded_front(x,z+y,profiles[n][3]) for n,ring in enumerate(rings) for x,y in ring]
        size = len(rings[0])
        faces, slots = [], []
        for n in range(len(rings)-1):
            for i in range(size):
                j = (i+1) % size
                faces.append((size*n+i,size*n+j,size*(n+1)+j,size*(n+1)+i))
                slots.append(profiles[n][4])
        self.patch(verts,faces,slots)

    def turned(self, profile, sides=SIDES, angle=0):
        """Trace a closed wall section anticlockwise in radius/height space.

        The explicit inner radius creates a real bore. No centre triangles are
        introduced by this function, including on the two polished sealing lips.
        """
        verts = [(r*math.cos(angle+i*math.tau/sides),r*math.sin(angle+i*math.tau/sides),z)
                 for r,z,mat in profile for i in range(sides)]
        faces, mats = [], []
        for row, (_, _, mat) in enumerate(profile):
            nxt = (row+1) % len(profile)
            for i in range(sides):
                j = (i+1) % sides
                faces.append((row*sides+i,row*sides+j,nxt*sides+j,nxt*sides+i))
                mats.append(mat)
        self.patch(verts, faces, mats)

    def glass_cylinder(self, radius, z0, z1):
        # One optical side surface per wall crossing avoids a doubled tint. The
        # cast wall thickness is modelled at both ends in the surrounding rims.
        verts = [(radius*math.cos(i*math.tau/SIDES),radius*math.sin(i*math.tau/SIDES),z)
                 for z in (z0,z1) for i in range(SIDES)]
        faces = [(i,(i+1)%SIDES,(i+1)%SIDES+SIDES,i+SIDES) for i in range(SIDES)]
        coords = [[(i/SIDES,0),((i+1)/SIDES,0),((i+1)/SIDES,1),(i/SIDES,1)] for i in range(SIDES)]
        self.patch(verts,faces,"TC_StorageVesselGlass",coords,smooth=True)

    def disk(self, radius, height, material, upward):
        points = [(radius*math.cos(i*math.tau/SIDES), radius*math.sin(i*math.tau/SIDES), height)
                  for i in range(SIDES)]
        indices = tuple(range(SIDES)) if upward else tuple(reversed(range(SIDES)))
        self.patch(points,[indices],material)

    def pressure_lens(self):
        # Two shallow parallel domes join around the buried glass edge.
        # Each surface runs all the way to the axis, sealing the inspection port.
        radius, crown, rise, thickness = .425, 4.374, .044, .031
        points, faces = [], []
        for side in (0,1):
            summit=len(points)
            points.append((0,0,crown-side*thickness))
            for r in (.11,.23,.34,radius):
                h=crown-rise*(r/radius)**2-side*thickness
                points.extend((r*math.cos(i*math.tau/SIDES),r*math.sin(i*math.tau/SIDES),h)
                              for i in range(SIDES))
            for i in range(SIDES):
                j=(i+1)%SIDES
                top=(summit,summit+1+i,summit+1+j)
                faces.append(top if side==0 else tuple(reversed(top)))
                for n in range(3):
                    start=summit+1+n*SIDES
                    quad=(start+i,start+SIDES+i,start+SIDES+j,start+j)
                    faces.append(quad if side==0 else tuple(reversed(quad)))
        upper=1+3*SIDES
        lower=upper+1+4*SIDES
        for i in range(SIDES):
            j=(i+1)%SIDES
            faces.append((upper+i,lower+i,lower+j,upper+j))
        self.patch(points,faces,"TC_StorageVesselGlass",smooth=True)

    def screw(self,yaw,u,z,depth):
        radius=.018
        outline=[(u+radius*math.cos(i*math.tau/8),z+radius*math.sin(i*math.tau/8)) for i in range(8)]
        self.patch([front(yaw,x,y,depth) for x,y in outline],[tuple(range(8))],"TC_Alloy")
        self.panel(yaw,u,z,.016,.004,depth+.0004,depth+.0018,"TC_Seal",.001)

    def mesh_object(self):
        mesh = bpy.data.meshes.new("Empty tank and window housing")
        mesh.from_pydata(self.points, [], self.polygons)
        assert not mesh.validate(), "Invalid source polygon"
        mesh.update()
        names = list(dict.fromkeys(self.materials))
        for name in names:
            mesh.materials.append(bpy.data.materials[name])
        uvs = mesh.uv_layers.new(name="UVMap")
        for i,p in enumerate(mesh.polygons):
            p.material_index = names.index(self.materials[i])
            p.use_smooth = self.smoothed[i]
            if self.uvs[i]:
                for loop,uv in zip(p.loop_indices,self.uvs[i]):
                    uvs.data[loop].uv = uv
            else:
                normal = p.normal
                axis = max(range(3), key=lambda k:abs(normal[k]))
                axes = ((1,2),(0,2),(0,1))[axis]
                for loop in p.loop_indices:
                    co = mesh.vertices[mesh.loops[loop].vertex_index].co
                    uvs.data[loop].uv = (co[axes[0]],co[axes[1]])
        obj=bpy.data.objects.new(mesh.name,mesh)
        bpy.context.scene.collection.objects.link(obj)
        return obj


def make_shaft(s):
    for angle in (120,180,240):
        a=math.radians(angle)
        verts=[(SHAFT_RADIUS*math.cos(a+math.radians(v)),SHAFT_RADIUS*math.sin(a+math.radians(v)),z)
               for v,z in [(-30,1.10),(30,1.10),(30,5.18),(-30,5.18)]]
        s.patch(verts,[(0,1,2,3)],"TC_Graphite")
        for bottom,top in ((1.16,1.53),(1.54,4.51),(4.52,5.11)):
            s.panel(angle,0,(bottom+top)/2,1.305,top-bottom,WALL_DEPTH-.008,1.167,"TC_Ceramic",.023)
        # Inner liner is front-facing into the bay and picks up its local light.
        verts=[front(angle,u,z,WALL_DEPTH-.029)
               for u,z in [(-.648,1.12),(.648,1.12),(.648,5.16),(-.648,5.16)]]
        s.patch(verts,[(3,2,1,0)],"TC_Ceramic")
    for bottom,top in ((1.115,1.595),(4.625,5.15)):
        s.panel(0,0,(bottom+top)/2,1.318,top-bottom,1.105,1.167,"TC_Ceramic",.021)
    # The front half of each shoulder is glazing. Keep the service instruments
    # and their opaque backing on the rear half of those same facets.
    for angle, sign in ((60,1),(-60,-1)):
        for bottom, top, center, width in (
                (1.11,1.591,0,1.319), (4.629,5.15,0,1.319),
                (1.582,4.637,.321,.68)):
            s.panel(angle,sign*center,(top+bottom)/2,width,top-bottom,
                    WALL_DEPTH-.030,1.167,"TC_Ceramic",.007)
    for z0,z1 in ((.983,1.15),(5.12,5.32)):
        s.turned([(1.33,z0,"TC_Graphite"),(1.345,z0+.035,"TC_Alloy"),
                  (1.345,z0+.058,"TC_Seal"),(1.325,z1,"TC_Graphite"),
                  (1.18,z1,"TC_Graphite"),(1.18,z0,"TC_Graphite")],6,math.pi/6)
    # Recessed rear lining and secondary inspection runners. These sit behind
    # the tank, giving its curved transparent walls a contrasting background.
    for u in (-.42,.42):
        s.panel(180,u,2.98,.045,2.65,WALL_DEPTH-.082,WALL_DEPTH-.058,"TC_Alloy",.008)


def make_vessel(s):
    for z in (1.72,4.25):
        for side in (120,180,240):
            s.panel(side,0,z,.154,.074,.846,1.126,"TC_Slate",.012)
            s.panel(side,0,z+.039,.10,.033,1.031,1.105,"TC_Alloy",.007)
    # Short tapered steel feet and insulated coupling. A sealed cup bottom and
    # optical top are at the ends only; the space between them is entirely empty.
    s.turned([(.862,1.643,"TC_Graphite"),(.885,1.663,"TC_Alloy"),(.885,1.695,"TC_Seal"),
              (.877,1.702,"TC_Alloy"),(.883,1.717,"TC_Alloy"),(.883,1.756,"TC_Alloy"),
              (.871,1.771,"TC_Alloy"),(.831,1.776,"TC_Seal"),(.809,1.768,"TC_Graphite"),
              (.809,1.652,"TC_Graphite")])
    s.disk(.812,1.658,"TC_Slate",True)
    s.glass_cylinder(VESSEL_RADIUS,1.770,4.223)
    # A solid annular lid carries an inset optical port. The stepped underside
    # exposes its dark seal and a narrow metal bevel to a player gazing upward.
    s.turned([(.819,4.218,"TC_Seal"),(.854,4.209,"TC_Seal"),(.873,4.214,"TC_Alloy"),
              (.883,4.223,"TC_Alloy"),(.883,4.242,"TC_Seal"),(.877,4.248,"TC_Seal"),
              (.877,4.263,"TC_Alloy"),(.883,4.270,"TC_Alloy"),(.882,4.291,"TC_Alloy"),
              (.871,4.306,"TC_Slate"),(.836,4.317,"TC_Slate"),(.721,4.329,"TC_Slate"),
              (.478,4.337,"TC_Alloy"),(.451,4.340,"TC_Alloy"),(.437,4.345,"TC_Seal"),
              (.419,4.343,"TC_Seal"),(.412,4.332,"TC_Graphite"),(.412,4.295,"TC_Seal"),
              (.427,4.286,"TC_Alloy"),(.469,4.282,"TC_Slate"),(.703,4.257,"TC_Slate"),
              (.754,4.251,"TC_Alloy"),(.777,4.243,"TC_Graphite"),(.804,4.238,"TC_Graphite"),
              (.808,4.217,"TC_Graphite")])
    s.pressure_lens()
    # Lower pressure bulkhead has a thin plinth beneath the tank, not a sleeve
    # around it. Its surface helps distinguish the vessel from the case floor.
    s.disk(1.105,1.616,"TC_Graphite",True)


def make_glazing(s):
    z=3.11
    s.frame(0,z,[(2.66,3.062,.062,1.132,"TC_Seal"),(2.66,3.062,.062,1.179,"TC_Graphite"),
                 (2.642,3.044,.059,1.196,"TC_Alloy"),(2.590,2.991,.046,1.196,"TC_Seal"),
                 (2.565,2.968,.043,1.182,"TC_Graphite"),(2.565,2.968,.043,1.121,"TC_Graphite")])
    # One folded sheet. Splitting it on the original facet edges gives each
    # shoulder a planar normal, with no intermediate mullions across the tank.
    # Only the central pane uses the full UV island of the cracked B finish.
    w, h, d = 2.583, 2.978, 1.163
    outline = frame_outline(w,h,.044)
    for section, ids in (("left",[0,1,8,9,10,11]), ("middle",[1,2,7,8]),
                         ("right",[2,3,4,5,6,7])):
        poly = [outline[i] for i in ids]
        pts = [folded_front(x,z+y,d) for x,y in poly]
        if section=="middle":
            uv = [(x/(2*HALF_FACET)+.5, y/h+.5) for x,y in poly]
        else:
            uv = [(.025+.025*(abs(x)-HALF_FACET)/(w/2-HALF_FACET), .023+.085*(y/h+.5))
                  for x,y in poly]
        s.patch(pts,[tuple(range(len(ids)))],"TC_StorageFrontGlass",[uv])
    for angle,sign in ((60,1),(-60,-1)):
        for v in (1.635,4.585):
            s.screw(angle,sign*-.030,v,1.198)
    s.panel(0,0,4.615,.847,.024,1.197,1.207,"TC_StorageAccent",.008)
    # Screen is behind the face glazing and above the tank. UVs are local to
    # this one display, matching the existing HH:MM:SS shader and B's counter.
    s.panel(0,0,4.283,1.156,.347,.949,1.088,"TC_Graphite",.035)
    s.panel(0,0,4.283,1.112,.301,1.088,1.097,"TC_Seal",.022)
    s.pane(0,4.283,1.052,.277,1.099,"TC_StorageReadout",.009)
    for u in (-.545,.545):
        s.screw(0,u,4.282,1.099)
    # Hook the rear of the bezel into the solid lintel above the glass. The
    # horizontal return spans their different recess depths on each side.
    for u in (-.455,.455):
        s.panel(0,u,4.547,.064,.240,.974,1.018,"TC_Graphite",.007)
        s.panel(0,u,4.650,.081,.046,.970,1.141,"TC_Alloy",.006)
        s.panel(0,u,4.470,.079,.046,.969,1.025,"TC_Alloy",.006)


def create_new_finishes():
    finishes={
        "TC_StorageVesselGlass":((.77,.86,.83),.16,.12),
        "TC_StorageFrontGlass":((.88,.94,.93),.055,.08),
        "TC_StorageAccent":((.065,.40,.38),1.0,.31),
        "TC_StorageReadout":((.025,.035,.038),1.0,.32),
    }
    for name,(color,alpha,roughness) in finishes.items():
        mat=bpy.data.materials.new(name)
        mat.diffuse_color=(*color,alpha)
        mat.use_nodes=True
        shader=mat.node_tree.nodes.get("Principled BSDF")
        shader.inputs["Base Color"].default_value=(*color,1)
        shader.inputs["Alpha"].default_value=alpha
        shader.inputs["Roughness"].default_value=roughness


def check_mesh(obj):
    mesh=obj.data
    mesh.calc_loop_triangles()
    names=[slot.name for slot in obj.material_slots]
    assert len(set(names))==len(names) and all("Face" not in n for n in names)
    assert all(abs(v-w)<.001 for v,w in zip(obj.dimensions,(4.254,4.9,5.9)))
    assert obj.location.length<1e-6
    # Test the complete optical path. A ray through the window must cross the
    # flat glass, the front and back of the same central tank, then the rear liner.
    coords=[v.co for v in mesh.vertices]
    tree=BVHTree.FromPolygons(coords,[list(p.vertices) for p in mesh.polygons])
    for y in (-.825,-.70,-.47,0.,.47,.70,.825):
        origin=Vector((2.,y,2.92)); direction=Vector((-1,0,0))
        hits=[]
        for _ in range(5):
            location,_,index,_=tree.ray_cast(origin,direction,4)
            if index is None:
                break
            hits.append((names[mesh.polygons[index].material_index],round(location.x,3)))
            origin=location+.0001*direction
        assert [name for name,_ in hits[:3]]==["TC_StorageFrontGlass","TC_StorageVesselGlass","TC_StorageVesselGlass"],hits
        assert hits[1][1]>0 and hits[2][1]<0 and hits[3][1]<0,hits
    # The complete upper and lower rims must be visible, including the ends of
    # the ellipse, and daylight must separate each rim from the window frame.
    for y in (-.92,-.876,.876,.92):
        for z in (1.735,4.233):
            start=Vector((2.,y,z)); direction=Vector((-1,0,0))
            point,_,index,_=tree.ray_cast(start,direction,4)
            assert names[mesh.polygons[index].material_index]=="TC_StorageFrontGlass"
            point,_,index,_=tree.ray_cast(point+.0001*direction,direction,4)
            if abs(y)<.88:
                assert point.x>0 and names[mesh.polygons[index].material_index] in ("TC_Alloy","TC_Slate")
            else:
                assert point.x<.10, (y,z,point)
    # All axial samples must encounter the underside, then the outside of the
    # closed lid. Its optical centre is 31 mm thick; the silver shoulder is solid.
    for x,kind in ((0,"glass"),(.24,"glass"),(.405,"glass"),(.422,"seal"),
                   (.58,"metal"),(.76,"metal"),(.84,"metal")):
        axis=Vector((0,0,1))
        bottom,_,i,_=tree.ray_cast(Vector((x,.001,4.0)),axis,.5)
        top,_,j,_=tree.ray_cast(Vector((x,.001,4.48)),-axis,.5)
        assert bottom is not None and top is not None and bottom.z<top.z,(x,bottom,top)
        names_hit=[names[mesh.polygons[k].material_index] for k in (i,j)]
        if kind=="glass":
            assert all(n=="TC_StorageVesselGlass" for n in names_hit) and abs(top.z-bottom.z-.031)<.001,(x,names_hit)
        else:
            assert any(n in ("TC_Alloy","TC_Slate","TC_Seal","TC_Graphite") for n in names_hit),(x,names_hit)
    counts=Counter(names[mesh.polygons[t.polygon_index].material_index] for t in mesh.loop_triangles)
    print("Storage pillar dimensions and triangles",tuple(obj.dimensions),sum(counts.values()))
    print("Storage pillar slots",names)


def build():
    bpy.ops.wm.open_mainfile(filepath=str(ROOT.parent/"TC_ClockInstruments.blend"))
    original=bpy.data.collections["SM_TC_TestClock"]
    selected=[]
    for obj in original.objects:
        if obj.name[:2] in {"01","03","04","05","07"}:
            copy=obj.copy()
            copy.data=obj.data.copy()
            copy.location=(0,0,0)
            if obj.name[:2] in {"04","05"}:
                # Keep both service panels on their current facet, inset into
                # the shoulder that remains opaque beside the new glazing.
                sign = -1 if obj.name[:2]=="04" else 1
                tangent=Vector((-math.sin(sign*math.pi/3),math.cos(math.pi/3),0))
                for vertex in copy.data.vertices:
                    u=vertex.co.dot(tangent)
                    vertex.co+=tangent*(sign*.325-u*.26)
            bpy.context.scene.collection.objects.link(copy)
            selected.append(copy)
    assert len(selected)==5
    create_new_finishes()
    shell=Surface()
    make_shaft(shell)
    make_vessel(shell)
    make_glazing(shell)
    combined=shell.mesh_object()
    bpy.ops.object.select_all(action='DESELECT')
    for obj in [combined,*selected]:
        obj.select_set(True)
    bpy.context.view_layer.objects.active=combined
    bpy.ops.object.join()
    combined.name=NAME
    combined.data.name=NAME
    check_mesh(combined)
    bpy.ops.export_scene.fbx(filepath=str(ROOT/(NAME+".fbx")),use_selection=True,object_types={"MESH"},
                              axis_forward="-Y",axis_up="Z",add_leaf_bones=False,mesh_smooth_type="FACE",
                              bake_anim=False,path_mode="STRIP",use_triangles=True)


if __name__=="__main__":
    build()
