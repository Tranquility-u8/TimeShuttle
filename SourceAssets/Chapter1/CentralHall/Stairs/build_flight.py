"""Build one measured S1–S4 stair flight, in cm, rising from local X=0 to X=960."""
import math
from pathlib import Path

import bpy
from mathutils import Vector


HERE = Path(__file__).resolve().parent
NAME = 'SM_CH_OpenFlight'
RUN, RISE, COUNT = 32.0, 540.0 / 31.0, 30
WIDTH, RAIL_Y = 400.0, 197.25
TREAD = 'TC_Floor'
RISER = 'TC_Skirting'
STRINGER = 'TC_Graphite'
METAL = 'TC_Brushed'
POST = 'TC_Support'
SLOTS = [TREAD, RISER, STRINGER, METAL, POST]
colors = [(.16,.183,.197), (.058,.07,.075), (.033,.046,.052), (.32,.35,.36), (.104,.126,.133)]
vertices, faces, finishes, smooth = [], [], [], []


def component(points, polygons, materials, rounded=()):
    offset = len(vertices)
    vertices.extend(tuple(p) for p in points)
    for i, (face, finish) in enumerate(zip(polygons, materials, strict=True)):
        faces.append(tuple(v + offset for v in face))
        finishes.append(SLOTS.index(finish))
        smooth.append(i in rounded)


def side_extrusion(profile, left, right, finish, edge_finishes=None):
    """Extrude a counterclockwise X/Z section. Slot assignment follows the section edges."""
    n = len(profile)
    twice_area = sum(profile[i][0]*profile[(i+1)%n][1] - profile[(i+1)%n][0]*profile[i][1] for i in range(n))
    assert twice_area > 0, profile
    polygons = [tuple(range(n)), tuple(reversed(range(n, n*2)))]
    for i in range(n):
        j = (i + 1) % n
        polygons.append((i, n+i, n+j, j))
    component([(x,y,z) for y in (left, right) for x,z in profile],
              polygons, [finish,finish] + (edge_finishes or [finish] * n))


def box(x1,x2,y1,y2,z1,z2,material):
    side_extrusion([(x1,z1),(x2,z1),(x2,z2),(x1,z2)],y1,y2,material)


def round_rail(path, radius, finish, sides=12):
    """Round tubes swept through the X/Z stringer plane, including the end returns."""
    p = [Vector(v) for v in path]
    axis_y = Vector((0,1,0))
    verts, polys = [], []
    for k, v in enumerate(p):
        tangent = (p[min(len(p)-1,k+1)] - p[max(k-1,0)]).normalized()
        radial = tangent.cross(axis_y).normalized()
        for j in range(sides):
            t = 2 * math.pi * j / sides
            verts.append(v + radius*(axis_y*math.cos(t) + radial*math.sin(t)))
    for k in range(len(p)-1):
        for j in range(sides):
            a,b = k*sides+j, k*sides+(j+1)%sides
            polys.append((a,b,b+sides,a+sides))
    end = (len(p)-1)*sides
    polys += [tuple(reversed(range(sides))),tuple(range(end,end+sides))]
    component(verts,polys,[finish]*len(polys), range(len(polys)-2))


def round_corner(a,b,c,length):
    a,b,c = [Vector(v) for v in (a,b,c)]
    before = b + (a-b).normalized()*length
    after = b + (c-b).normalized()*length
    return [(1-t)**2*before + 2*(1-t)*t*b + t*t*after for t in (0,.25,.50,.75,1)]


def hand_height(x):
    return 127.4 + x / RUN * RISE


def tread_height(x):
    return (1 + min(COUNT-1,max(0,math.floor(x / RUN)))) * RISE


def shell():
    # A single folded deck with full risers, slim returns and an open volume beneath.
    # Adjacent pans meet at the rear of the tread. Landing is the 31st rise.
    for i in range(COUNT):
        x, h = i * RUN, (i + 1) * RISE
        toe = h - RISE
        profile = [(x,toe),(x+2.0,toe),(x+2.0,h-3.0),(x+RUN,h-3.0),
                   (x+RUN,h),(x+3.0,h),(x+.6,h),(x,h-.6)]
        edge = [STRINGER,STRINGER,STRINGER,STRINGER,TREAD,METAL,METAL,RISER]
        side_extrusion(profile,-WIDTH/2,WIDTH/2,STRINGER,edge)
    for y in [-184.0,184.0]:
        # Four points along the underside plus a clipped toe at the concrete floor.
        xend=RUN*COUNT
        top_at_foot=-4.4
        near_floor=(26.-top_at_foot)*RUN/RISE
        profile=[(-top_at_foot*RUN/RISE,0),(near_floor,0),
                 (xend,top_at_foot+COUNT*RISE-26),(xend,top_at_foot+COUNT*RISE)]
        side_extrusion(profile,y-7.2,y+7.2,STRINGER)
        box(1,37,y-10.5,y+10.5,.2,2.8,POST)
        # The connection plates are on each inner stringer face at the landing.
        side_extrusion([(930,489),(960,489),(960,520),(950,520),(930,505)],y-8.5,y+8.5,POST)


def guards():
    for sign in (-1,1):
        y = sign*RAIL_Y
        # Post locations follow the side-panel collision envelope, centered on the old rail axis.
        for x in [8,160+8,320+8,480+8,640+8,800+8,952]:
            floor=tread_height(x)
            box(x-5.4,x+5.4,y-4.8,y+4.8,floor+.05,floor+2.6,POST)
            if x != 8:
                round_rail([(x,y,floor+1.7),(x,y,hand_height(x)-1.3)],2.75,POST)
            # Base fasteners sit on the sides of the protruding mounting shoe.
            for dx in [-3.65,3.65]:
                for dy in [-3.2,3.2]:
                    round_rail([(x+dx,y+dy,floor+2.5),(x+dx,y+dy,floor+3.2)],.73,METAL,sides=6)
        start=(8,y,tread_height(8)+2.2)
        turn=(8,y,hand_height(8))
        last=(952,y,650)
        upper=(960,y,650)
        # Soft returns catch light with a unified normal, including the first post.
        round_rail([start,*round_corner(start,turn,last,8.5),
                    *round_corner(turn,last,upper,3.3),upper],3.15,METAL,16)
        for clearance in (38,72):
            round_rail([(8,y,hand_height(8)-clearance),(952,y,hand_height(952)-clearance)],1.75,POST)


def export():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene=bpy.context.scene
    scene.unit_settings.system='METRIC'
    scene.unit_settings.scale_length=.01
    shell()
    guards()
    mesh=bpy.data.meshes.new(NAME)
    mesh.from_pydata(vertices,[],faces)
    assert not mesh.validate(clean_customdata=False)
    mesh.update()
    for name, col in zip(SLOTS,colors):
        material=bpy.data.materials.new(name)
        material.diffuse_color=(*col,1)
        mesh.materials.append(material)
    uv=mesh.uv_layers.new(name='Surface')
    for f,finish,lateral in zip(mesh.polygons,finishes,smooth):
        f.material_index=finish
        f.use_smooth=lateral
        u,v=[a for a in range(3) if a != max(range(3),key=lambda b:abs(f.normal[b]))]
        for loop in f.loop_indices:
            pt=mesh.vertices[mesh.loops[loop].vertex_index].co
            uv.data[loop].uv = pt[u]/100,pt[v]/100
    obj=bpy.data.objects.new(NAME,mesh)
    scene.collection.objects.link(obj)
    obj.select_set(True)
    bpy.context.view_layer.objects.active=obj
    bpy.ops.export_scene.fbx(filepath=str(HERE/(NAME+'.fbx')),use_selection=True,
        object_types={'MESH'},axis_forward='-Y',axis_up='Z',apply_unit_scale=True,
        apply_scale_options='FBX_SCALE_UNITS',mesh_smooth_type='FACE',bake_anim=False,
        add_leaf_bones=False)
    mesh.calc_loop_triangles()
    print(f'{NAME}: {len(mesh.vertices)} vertices, {len(mesh.loop_triangles)} triangles, {len(mesh.materials)} slots')


if __name__=='__main__':
    export()
