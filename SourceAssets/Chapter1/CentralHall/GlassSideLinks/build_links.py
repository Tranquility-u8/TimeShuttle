"""Rebuild both glass-side lift galleries with Blender, working in UE world centimetres."""
import json
import math
from pathlib import Path

import bpy
from mathutils import Vector


HERE = Path(__file__).resolve().parent
LAYOUT = json.loads((HERE.parents[2] / 'LabV39/R17/revised-layout-geometry.json').read_text(encoding='utf8'))
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.unit_settings.system = 'METRIC'
scene.unit_settings.scale_length = .01
manifest = {}


class Skin:
    def __init__(self, name, pivot):
        self.name = name
        self.pivot = pivot
        self.vertices = []
        self.faces = []
        self.materials = []
        self.indices = []

    def face(self, pts, normal, slot):
        ox, oy, oz = self.pivot
        points = []
        for x, y, z in pts:
            p = Vector((x-ox, oy-y, z-oz))
            if not points or (p-points[-1]).length > .002:
                points.append(p)
        if len(points) > 1 and (points[-1]-points[0]).length <= .002:
            points.pop()
        if len(points) < 3:
            return
        norm = sum(((a-points[0]).cross(b-points[0]) for a,b in zip(points[1:],points[2:])), Vector())
        if norm.length < .02:
            return
        if norm.dot(Vector((normal[0], -normal[1], normal[2]))) < 0:
            points.reverse()
        first = len(self.vertices)
        self.vertices.extend(points)
        self.faces.append(tuple(range(first, first+len(points))))
        if slot not in self.materials:
            self.materials.append(slot)
        self.indices.append(self.materials.index(slot))

    def export(self):
        mesh = bpy.data.meshes.new(self.name)
        mesh.from_pydata(self.vertices, [], self.faces)
        mesh.update()
        assert not mesh.validate()
        for slot in self.materials:
            mesh.materials.append(bpy.data.materials.get(slot) or bpy.data.materials.new(slot))
        uv = mesh.uv_layers.new(name='Surface')
        for poly, slot in zip(mesh.polygons, self.indices):
            poly.material_index = slot
            axis = max(range(3), key=lambda i:abs(poly.normal[i]))
            u,v = [i for i in range(3) if i!=axis]
            for loop in poly.loop_indices:
                pos = mesh.vertices[mesh.loops[loop].vertex_index].co
                uv.data[loop].uv = (pos[u]/160, pos[v]/160)
        obj = bpy.data.objects.new(self.name,mesh)
        scene.collection.objects.link(obj)
        bpy.ops.object.select_all(action='DESELECT')
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        bpy.ops.export_scene.fbx(filepath=str(HERE/(self.name+'.fbx')), use_selection=True,
            object_types={'MESH'}, axis_forward='-Y', axis_up='Z', apply_unit_scale=True,
            apply_scale_options='FBX_SCALE_UNITS', mesh_smooth_type='FACE', bake_anim=False,
            add_leaf_bones=False)
        manifest[self.name] = dict(pivot_cm=self.pivot, slots=self.materials,
            triangles=sum(len(face)-2 for face in self.faces))


def subranges(lo, hi, step):
    count = max(1, round((hi-lo)/step))
    return [(lo + (hi-lo)*i/count, lo+(hi-lo)*(i+1)/count) for i in range(count)]


def subtract_ranges(ranges, cuts):
    for bottom, top in cuts:
        result = []
        for lo,hi in ranges:
            if lo < min(hi,bottom):
                result.append((lo,min(hi,bottom)))
            if max(lo,top) < hi:
                result.append((max(lo,top),hi))
        ranges = result
    return ranges


def ring_edges(ring):
    pts = [(x*100,-y*100) for x,y in ring]
    return [(a,b) for a,b in zip(pts,pts[1:]+pts[:1]) if abs(a[0]-b[0])>.000001]


def spans_at(edges, x):
    cross = sorted(y+(v-y)*(x-u)/(w-u) for (u,y),(w,v) in edges if min(u,w)<x<max(u,w))
    assert len(cross)%2 == 0
    return list(zip(cross[::2],cross[1::2]))


def clip_y(poly, bound, up):
    result = []
    for a,b in zip(poly[-1:]+poly[:-1],poly):
        ina, inb = (a[1]-bound)*up>=0, (b[1]-bound)*up>=0
        if ina != inb:
            result.append((a[0]+(b[0]-a[0])*(bound-a[1])/(b[1]-a[1]),bound))
        if inb:
            result.append(b)
    return result


def floor_finish(part, side, layer):
    name = 'floor_upper' if layer else 'floor_lower'
    slab, = LAYOUT[name]
    outer = ring_edges(slab['outer'])
    holes = [ring_edges(r) for r in slab['holes']]
    # The R17 upper slab already has hoistway voids. The lower slab is solid beneath
    # the hoistways. Neither finish should intersect the five enclosed shaft interiors.
    shafts = [(side*x-120,side*x+120) for x in (1610,1870,2130,2390,2650)]
    if not layer:
        north = [(1884,2857.9 if side<0 else 2902.636,-2230),
                 (2857.9 if side<0 else 2902.636,4902.6,-3735.87)]
    elif side<0:
        north = [(1884,3978.7,-3378.33),(3978.7,4902.6,-3055)]
    else:
        north = [(1884,2902.636,-3355),(2902.636,2925,-3735.87),(2925,4902.6,-3750)]
    def section(x):
        r = spans_at(outer,x)
        for h in holes:
            r = subtract_ranges(r,spans_at(h,x))
        if any(a<x<b for a,b in shafts):
            r = subtract_ranges(r,[(-4190,-3910)])
        # Offsets match the adjoining slab finish at the glazing; retain the measured curve.
        return [(lo+(3 if lo < -3743 else 0),hi) for lo,hi in r]
    # Split at all corners in the real slab. Its outline within each such strip is linear.
    cuts = {p[0] for edges in [outer,*holes] for edge in edges for p in edge}
    cuts.update(x for shaft in shafts for x in shaft)
    south = -4900 if layer else -5300
    tile_rows = subranges(south,-3400,192) + [(a,min(a+190,-2230)) for a in range(-3400,-2230,190)]
    for ix in range(17):
        cell_l = 1884+ix*188.4
        cell_r = cell_l+188.4
        for iy,(row_a,row_b) in enumerate(tile_rows):
            tile = 'FloorAlt' if ((ix+20)*7+iy*5)%17==3 else 'Floor'
            for inset,rise,slot in [(0,.34,'Joint'),(.25,.72,tile)]:
                for inner,outer_x,limit in north:
                    al,ar = max(cell_l+inset,inner),min(cell_r-inset,outer_x)
                    if ar-al < .02 or row_a >= limit:
                        continue
                    left,right = sorted((side*al,side*ar))
                    xs = sorted({left,right,*[x for x in cuts if left<x<right]})
                    for a,b in zip(xs,xs[1:]):
                        if b-a<.01:
                            continue
                        r1 = section(a+(b-a)*.25)
                        r2 = section(a+(b-a)*.75)
                        assert len(r1)==len(r2), (a,b,r1,r2)
                        for (f,h),(g,i) in zip(r1,r2):
                            shape = [(a,1.5*f-.5*g),(b,1.5*g-.5*f),(b,1.5*i-.5*h),(a,1.5*h-.5*i)]
                            shape = clip_y(shape,row_a+inset,1)
                            shape = clip_y(shape,min(row_b-inset,limit),-1)
                            if shape:
                                part.face([(x,y,layer+rise) for x,y in shape],(0,0,1),slot)


class Face:
    """Rectangular-wall coordinates (horizontal distance, height, depth into the room)."""
    def __init__(self, part, start, end, normal):
        self.part, self.start, self.normal = part, start, normal
        self.width = math.dist(start,end)
        self.along = tuple((b-a)/self.width for a,b in zip(start,end))

    def plate(self, poly, depth, slot):
        ns = self.normal
        self.part.face([(self.start[0]+self.along[0]*u+ns[0]*depth,
                         self.start[1]+self.along[1]*u+ns[1]*depth,z) for u,z in poly],
                       (ns[0],ns[1],0),slot)

    def rect(self, a,b,c,d,depth,slot):
        if b>a and d>c:
            self.plate([(a,c),(b,c),(b,d),(a,d)],depth,slot)

    def service_cover(self, z):
        # Lift end inspection access. A flush folded cover with a short finger recess.
        mid = self.width/2
        def outline(w,h,cut):
            return [(mid-w,z-h),(mid+w-cut,z-h),(mid+w,z-h+cut),(mid+w,z+h),
                    (mid-w+cut,z+h),(mid-w,z+h-cut)]
        self.plate(outline(47,21,6),2.28,'Joint')
        self.plate(outline(45.8,19.8,5.6),2.57,'WallCool')
        self.rect(mid+22,mid+34,z-12,z-10,2.85,'Seal')

    def panels(self, low, high, openings=(), pitch=218, endcap=False, trims=(0,0)):
        # Independent front rectangles terminate at the actual jamb and the bottom of the lintel.
        heights = {low,high,*[h for h in (18,166,311,472,495,539,558,706,850,1048,1220,1377)
                              if low<h<high]}
        for _,_,bottom,top in openings:
            heights.update(h for h in (bottom,top) if low<h<high)
        levels = sorted(heights)
        for z,Z in zip(levels,levels[1:]):
            ranges = subtract_ranges([(trims[0],self.width-trims[1])],
                                     [(u,v) for u,v,b,t in openings if b<Z and z<t])
            for lo,hi in ranges:
                self.rect(lo,hi,z,Z,.78,'Joint')
                for a,b in subranges(lo,hi,pitch):
                    if b-a<2 or Z-z<2:
                        continue
                    plinth = z in (0,540,1377) or (z==539 and Z==558)
                    band = z in (472,495)
                    finish = 'Graphite' if plinth else ('WallCool' if band or z>=1220 else 'Panel')
                    lip = .45
                    self.rect(a+lip,b-lip,z+lip,Z-lip,1.64 if not plinth else 2.05,finish)
                    if plinth and hi-lo>48:
                        self.rect(a+2,b-2,Z-3.8,Z-2.9,2.26,'Alloy')
        if endcap:
            for z in (101,641):
                self.service_cover(z)


EDGE = 2.55


def fold_corner(part,x,y,nx,ny,low,high):
    # Closed returns sit directly against the source wall at both ends of the fold.
    # Retract each adjacent panel to the edge so the assembly has no coplanar flanges.
    profile = [(0,-EDGE),(2.5,-EDGE),(2.5,.85),(.85,2.5),(-EDGE,2.5),(-EDGE,0)]
    for (a,b),(c,d) in zip(profile,profile[1:]):
        start,end = (x+nx*a,y+ny*b),(x+nx*c,y+ny*d)
        part.face([(*start,low),(*end,low),(*end,high),(*start,high)],
                  (nx*(d-b),ny*(a-c),0),'Graphite')


def hoistways(part,side):
    for i,x in enumerate((1610,1870,2130,2390,2650)):
        center = side*x
        l,r = center-120,center+120
        rear,front = -4190,-3901
        openings = [(29,211,z,z+290) for z in (0,540)]
        Face(part,(l,front),(r,front),(0,1)).panels(0,1400,openings,trims=(EDGE,EDGE))
        Face(part,(l,rear),(r,rear),(0,-1)).panels(0,1400,pitch=245,trims=(EDGE,EDGE))
        for a,normal in [(l,-1),(r,1)]:
            exposed = (i==0 and normal==-side) or (i==4 and normal==side)
            Face(part,(a,rear),(a,front),(normal,0)).panels(0,1400,pitch=160,endcap=exposed,trims=(EDGE,EDGE))
            for y,ny in [(rear,-1),(front,1)]:
                fold_corner(part,a,y,normal,ny,0,1400)


def corridor_walls(part,side):
    if side<0:
        corners = [(-2857.9,-3735.87,1,-1,0,495),(-1885,-3378.33,1,-1,540,1400),
                   (-3978.7,-3378.33,-1,-1,540,1400),(-4640.1,-3055,1,-1,540,1400),
                   (-4231.5,-3055,-1,-1,540,1400)]
    else:
        corners = [(2902.636,-3735.87,-1,-1,0,495),(1885,-3355,-1,-1,540,1400),
                   (2902.636,-3735.87,-1,-1,540,1400),(2925,-3750,-1,-1,540,1400)]
    def u_wall(start,end,normal,low,high,openings=()):
        trims = tuple(EDGE if any(abs(x-p[0])+abs(y-p[1])<.01 and z<=low and Z>=high
                                  for x,y,nx,ny,z,Z in corners) else 0 for p in (start,end))
        Face(part,start,end,normal).panels(low,high,openings,trims=trims)
    south=(0,-1)
    # Panel the wall faces actually exposed to the corridor, including solid header/sill zones.
    # Distinct upper/lower plans are intentional: the two wings aren't symmetric.
    def along_x(a,b,y,z,Z,holes=()):
        u_wall((a,y),(b,y),south,z,Z,[(x-a,X-a,lo,hi) for x,X,lo,hi in holes])
    def along_y(x,a,b,normal,z,Z,holes=()):
        u_wall((x,a),(x,b),(normal,0),z,Z,[(y-a,Y-a,lo,hi) for y,Y,lo,hi in holes])
    if side<0:
        along_x(-4902.0,-2857.9,-3735.87,0,495)
        along_y(-2857.9,-3735.87,-2230,1,0,495,[(-3366.8,-3166.6,0,340)])
        along_x(-2550,-1890,-2230,0,495,[(-2340.1,-2099.9,0,340)])
        along_x(-3978.7,-1885,-3378.33,540,1400)
        along_y(-1885,-3378.33,-3318,1,540,1400)
        along_y(-3978.7,-3378.33,-3055,-1,540,1400)
        along_x(-4902,-4640.1,-3055,540,1400)
        along_y(-4640.1,-3055,-3045,1,540,1400)
        along_x(-4640.1,-4319.9,-3045,880,1400)
        along_x(-4319.9,-4231.5,-3045,540,1400)
        along_y(-4231.5,-3055,-3045,-1,540,1400)
        along_x(-4231.5,-3978.7,-3055,540,1400)
    else:
        along_x(2902.636,4902.5,-3735.87,0,495,[(3964.9,4902.5,90,350)])
        along_x(3964.9,4902.5,-3735.87,495,540)
        along_y(2902.636,-3735.87,-2230,-1,0,495,[(-3053.4,-2813.2,0,380)])
        along_x(1890,2550,-2230,0,495,[(2099.9,2340.1,0,340)])
        along_x(1885,2902.636,-3355,540,1400,[(2289.9,2610.1,540,880)])
        along_y(1885,-3355,-3295,-1,540,1400)
        along_y(2902.636,-3735.87,-3355,-1,540,1400)
        along_x(2902.636,2925,-3735.87,540,1400)
        along_y(2925,-3750,-3735.87,-1,540,1400)
        along_x(2925,4902,-3750,540,1400)
    for corner in corners:
        fold_corner(part,*corner)


for direction,side in [('West',-1),('East',1)]:
    floor = Skin('SM_HallGlassLinkFloor'+direction,(side*3000,-3930,0))
    for elevation in (0,540):
        floor_finish(floor,side,elevation)
    floor.export()
    walls = Skin('SM_HallGlassLinkWall'+direction,(side*3000,-3930,700))
    hoistways(walls,side)
    corridor_walls(walls,side)
    walls.export()

(HERE/'glass_links.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf8')
