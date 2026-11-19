"""Build the two curtain wall frame halves in surveyed Map_LabV39 centimetres."""
from bisect import bisect_right
from math import dist, hypot
from pathlib import Path
import json

import bpy


HERE = Path(__file__).resolve().parent
LAYOUT = HERE.parents[2] / 'LabV39/R17/revised-layout-geometry.json'
SLOTS = ['Graphite', 'Alloy', 'Seal', 'WallCool']
BAY_COUNT = 36


def unit(x, y):
    length = hypot(x,y)
    return x/length, y/length


class Curtain:
    def __init__(self, points):
        self.points = sorted({(x*100,-y*100) for x,y in points})
        self.s = [0.]
        normals = []
        for a,b in zip(self.points,self.points[1:]):
            self.s.append(self.s[-1]+dist(a,b))
            normals.append(unit(a[1]-b[1],b[0]-a[0]))
        self.miters = []
        for i in range(len(self.points)):
            a,b = normals[max(i-1,0)], normals[min(i,len(normals)-1)]
            # Dot with either face normal is exactly one, including the return bends.
            dot = 1 + a[0]*b[0] + a[1]*b[1]
            self.miters.append(((a[0]+b[0])/dot,(a[1]+b[1])/dot))

    def at(self, station, depth, z):
        i = min(max(bisect_right(self.s,station)-1,0),len(self.s)-2)
        t = (station-self.s[i])/(self.s[i+1]-self.s[i])
        a,b = self.points[i:i+2]
        left,right = self.miters[i:i+2]
        return tuple((1-t)*(a[j]+left[j]*depth)+t*(b[j]+right[j]*depth) for j in (0,1)) + (z,)

    def vertex(self, x):
        i = min(range(len(self.points)),key=lambda j:abs(x-self.points[j][0]))
        assert abs(self.points[i][0]-x)<.02
        return self.s[i]


class Frame:
    def __init__(self, name, pivot, slots=SLOTS):
        self.name, self.pivot, self.slots = name, pivot, slots
        self.verts, self.faces, self.materials = [],[],[]

    def face(self, points, slot):
        start = len(self.verts)
        x,y,z = self.pivot
        self.verts.extend((px-x,y-py,pz-z) for px,py,pz in reversed(points))
        self.faces.append(tuple(range(start,len(self.verts))))
        self.materials.append(self.slots.index(slot))

    def loft(self, rings, slots, close_start=True, close_end=True):
        if close_start:
            self.face(rings[0][::-1],self.slots[0])
        if close_end:
            self.face(rings[-1],self.slots[0])
        for a,b in zip(rings,rings[1:]):
            for j,slot in enumerate(slots):
                nxt=(j+1)%len(a)
                self.face([a[j],a[nxt],b[nxt],b[j]],slot)

    def rail(self, arc, start, end, profile, slots, ends=(True,True)):
        stops=[start,*[s for s in arc.s if start+.001<s<end-.001],end]
        rings=[[arc.at(s,d,z) for d,z in profile] for s in stops]
        self.loft(rings,slots,*ends)

    def export(self):
        mesh=bpy.data.meshes.new(self.name)
        mesh.from_pydata(self.verts,[],self.faces)
        mesh.update()
        assert not mesh.validate()
        for slot in self.slots:
            mesh.materials.append(bpy.data.materials.get(slot) or bpy.data.materials.new(slot))
        uv=mesh.uv_layers.new(name='Surface')
        for p,idx in zip(mesh.polygons,self.materials):
            p.material_index=idx
            axis=max(range(3),key=lambda i:abs(p.normal[i]))
            u,v=[i for i in range(3) if i!=axis]
            for loop in p.loop_indices:
                co=mesh.vertices[mesh.loops[loop].vertex_index].co
                uv.data[loop].uv=(co[u]/128.,co[v]/128.)
        obj=bpy.data.objects.new(self.name,mesh)
        bpy.context.scene.collection.objects.link(obj)
        bpy.ops.object.select_all(action='DESELECT')
        obj.select_set(True)
        bpy.context.view_layer.objects.active=obj
        bpy.ops.export_scene.fbx(filepath=str(HERE/(self.name+'.fbx')),use_selection=True,
            object_types={'MESH'},axis_forward='-Y',axis_up='Z',apply_unit_scale=True,
            apply_scale_options='FBX_SCALE_UNITS',mesh_smooth_type='FACE',bake_anim=False,
            add_leaf_bones=False)
        return dict(pivot_cm=self.pivot,slots=self.slots,triangles=sum(len(f)-2 for f in self.faces))


# Each section runs counterclockwise in depth/height. The deep outward faces
# screen both slab cuts, including the underside of the existing lower slab.
SILL = [(-17,-46),(13,-46),(13,-42),(6,-41),(6,1.5),(31,1.5),(31,13),
        (27.5,17),(27.5,21.5),(21,28),(7,28),(4,24),(-8,24),(-14,20),
        (-16,17),(-16,8),(-19,6),(-19,-5),(-16.5,-7),(-16.5,-39),(-19,-41)]
SILL_SLOTS=['Graphite','Graphite','Alloy','Seal','Seal','Graphite','Alloy','Seal',
            'WallCool','Graphite','Seal','Graphite','Alloy','WallCool','Graphite',
            'Alloy','WallCool','Seal','Graphite','Alloy','Graphite']
HEAD = [(-19,1372),(8,1372),(14,1375),(25,1375),(36,1386),(36,1397),
        (14,1397),(14,1439),(30,1441),(30,1446.5),(-17,1446.5),(-22,1442),
        (-22,1433),(-19,1430),(-19,1393),(-22,1391),(-22,1378)]
HEAD_SLOTS=['Graphite','Seal','Graphite','WallCool','Graphite','Alloy','Seal','Seal',
            'Graphite','Graphite','Alloy','WallCool','Seal','Graphite','Alloy','WallCool','Graphite']
TRANSOM = [(-11,513),(7.5,513),(12.5,517),(12.5,521.5),(9,525.5),
           (2.2,525.5),(.7,524),(-8,524),(-12,521.5),(-12,515.5)]
TRANSOM_SLOTS=['Graphite','Graphite','WallCool','Alloy','Graphite','Seal','Graphite',
               'Alloy','WallCool','Graphite']
# Local (along-arc, depth) mullion section. Raised caps, gaskets, and brushed
# chamfers exist on both sides of the glass. No other glazing sheet is added.
STILE = [(-10.4,-12.6),(-7.1,-16.7),(7.1,-16.7),(10.4,-12.6),
         (10.4,-7.8),(8.5,-6),(8.5,5),(10.8,6.8),(10.8,12.8),(8.4,15),
         (8.4,18.5),(5.4,22),(-5.4,22),(-8.4,18.5),(-8.4,15),
         (-10.8,12.8),(-10.8,6.8),(-8.5,5),(-8.5,-6),(-10.4,-7.8)]
STILE_SLOTS=['Alloy','WallCool','Alloy','Graphite','Seal','Graphite','Seal',
             'Graphite','Alloy','Seal','Graphite','WallCool','Alloy','Seal','Graphite',
             'Graphite','Seal','Graphite','Seal','Graphite']


def stile(mesh, arc, s):
    # Wider shoes fit into the sill/head extrusion; the section thins in the field of view.
    sections=[(27.7,1.45,1.33),(41,1.45,1.33),(44.5,1.36,1.25),
              (97,1.36,1.25),(126,1,1),(488,1,1),(501,1.21,1.17),
              (533,1.21,1.17),(548,1,1),(1254,1,1),(1306,1.52,1.42),
              (1360,1.52,1.42),(1372.4,1.36,1.30)]
    start = s < .01
    end = s > arc.s[-1]-.01
    def corner(u,d,z,sx,sy):
        # Terminate at the two actual wall returns instead of extending the glass arc.
        along = (u+10.8 if start else u-10.8 if end else u)*sx
        return arc.at(s+along,d*sy,z)
    rings=[[corner(u,d,z,width,depth) for u,d in STILE] for z,width,depth in sections]
    mesh.loft(rings,STILE_SLOTS)


def load_curtain():
    layout=json.loads(LAYOUT.read_text(encoding='utf8'))
    ring=layout['floor_lower'][0]['outer']
    segments=[(a,b) for a,b in zip(ring,ring[1:]+ring[:1])
              if min(a[1],b[1])>=37.4 and max(a[1],b[1])>=37.6]
    arc=Curtain([p for segment in segments for p in segment])
    assert len(arc.points)==71
    return arc


def bay_stations(arc):
    length=arc.s[-1]
    # One setting-out line for the weather screen, inner guard, and slab edge.
    # Centre the layout on the existing building axis, in surveyed world cm.
    return [length*i/BAY_COUNT for i in range(BAY_COUNT+1)]


def glass_bay(mesh, arc, left, right):
    # The pane follows each existing facet with no end face at the old survey
    # vertices. The only end faces are inside the uniform mullions and transom.
    for low, high in [(26,517),(520,1374)]:
        profile=[(-4.5,low),(4.5,low),(4.5,high),(-4.5,high)]
        mesh.rail(arc,left+2,right-2,profile,['Pane']*4)


def build():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.context.scene.unit_settings.system='METRIC'
    bpy.context.scene.unit_settings.scale_length=.01
    arc=load_curtain()
    stations=bay_stations(arc)
    middle=BAY_COUNT//2
    assert abs(stations[middle]-arc.vertex(0))<0.1
    frames,panes={},{}
    for side,start,end in [('West',0,middle),('East',middle,BAY_COUNT)]:
        pivot=((-1 if side=='West' else 1)*2450,-4630,700)
        mesh=Frame('SM_HallGlazingFrame'+side,pivot)
        glass=Frame('SM_HallGlazingPanes'+side,pivot,['Pane'])
        half=stations[start:end+1]
        ends=(start==0,end==BAY_COUNT)
        mesh.rail(arc,half[0],half[-1],SILL,SILL_SLOTS,ends)
        mesh.rail(arc,half[0],half[-1],HEAD,HEAD_SLOTS,ends)
        for i,s in enumerate(half,start=start):
            if i!=middle or side=='East':
                stile(mesh,arc,s)
        for a,b in zip(half,half[1:]):
            mesh.rail(arc,a+10,b-10,TRANSOM,TRANSOM_SLOTS)
            glass_bay(glass,arc,a,b)
        frames[mesh.name]=mesh.export()
        panes[glass.name]=glass.export()
    for name,manifest in [('glass_frames.json',frames),('glass_panes.json',panes)]:
        (HERE/name).write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf8')


if __name__=='__main__':
    build()
