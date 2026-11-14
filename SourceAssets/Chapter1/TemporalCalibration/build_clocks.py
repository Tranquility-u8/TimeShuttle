"""Build both timing instruments. Blender 4+, authored in metres; finish FBX in cm."""
import json
import math
from pathlib import Path
import bpy
from mathutils import Vector

ROOT=Path(__file__).resolve().parent
MESHES=ROOT/'Meshes'
def material(color, metal, rough, **kwargs):
    return dict(color_linear=color, metallic=metal, roughness=rough, **kwargs)

MATERIALS={
    'TC_Ceramic':material([.57,.59,.58],.20,.38),
    'TC_Slate':material([.113,.165,.202],.54,.35),
    'TC_Graphite':material([.033,.046,.052],.55,.38),
    'TC_Seal':material([.011,.016,.017],.06,.65),
    'TC_Alloy':material([.38,.43,.43],.78,.29),
    'TC_Optic':material([.019,.044,.046],.37,.16),
    'TC_Amber':material([.49,.245,.065],.36,.46),
    'TC_Index':material([.65,.72,.68],.17,.38),
    'TC_Pilot':material([.48,.84,.81],.06,.27,emissive=.65),
    'TC_ReferenceFace':material([1,1,1],.16,.47,texture='Textures/T_TC_ReferenceFace.png'),
    'TC_TestFace':material([1,1,1],.16,.47,texture='Textures/T_TC_TestFace.png'),
    'TC_LiveReadout':material([.03,.07,.07],.18,.28),
}

class Geometry:
    def __init__(self):
        self.parts={}
        self.group('01  Enclosure')
    def group(self,name):
        self.part=self.parts.setdefault(name,[[],[],[],[]])
    def piece(self,vertices,faces,materials,uv=None,orient=True):
        # Design axes use UE directions. Convert to the Blender basis on insertion.
        pts=[Vector(p) for p in vertices]
        center=sum(pts,Vector())/len(pts)
        verts,polys,ids,uvs=self.part
        offset=len(verts)
        verts.extend((p.x,-p.y,p.z) for p in pts)
        for i,f in enumerate(faces):
            ix=list(f)
            tex=list(uv[i]) if uv else None
            if orient and len(ix)>=3:
                a,b,c=[pts[j] for j in ix[:3]]
                fc=sum((pts[j] for j in ix),Vector())/len(ix)
                if (b-a).cross(c-a).dot(fc-center)<0:
                    ix.reverse()
            ix.reverse()
            if tex: tex.reverse()
            polys.append([offset+j for j in ix])
            ids.append(materials if isinstance(materials,str) else materials[i])
            uvs.append(tex)
    def stack(self,profile,n=6,rot=30):
        # A single turned/layered solid eliminates coincident surfaces at joints.
        vs=[(r*math.cos(math.radians(rot+i*360/n)),r*math.sin(math.radians(rot+i*360/n)),z) for z,r,_ in profile for i in range(n)]
        fs=[];keys=[]
        for j in range(len(profile)-1):
            for i in range(n):
                fs.append((j*n+i,j*n+(i+1)%n,(j+1)*n+(i+1)%n,(j+1)*n+i))
                keys.append(profile[j][2])
        fs.append(tuple(reversed(range(n))));keys.append(profile[0][2])
        fs.append(tuple((len(profile)-1)*n+i for i in range(n)));keys.append(profile[-1][2])
        self.piece(vs,fs,keys,orient=False)
    def at(self,yaw,u,z,d):
        a=math.radians(yaw)
        return (d*math.cos(a)+u*math.sin(a),d*math.sin(a)-u*math.cos(a),z)
    def bezel(self,ang,u,z,w,h,back,front,mat,c=.018):
        w,h=w/2,h/2;c=max(.0001,min(c,h*.44,w*.44))
        xy=[(-w+c,-h),(w-c,-h),(w,-h+c),(w,h-c),(w-c,h),(-w+c,h),(-w,h-c),(-w,-h+c)]
        pts=[self.at(ang,u+x,z+y,d) for d in (back,front) for x,y in xy]
        faces=[tuple(range(8)),tuple(range(8,16))]+[(j,(j+1)%8,(j+1)%8+8,j+8) for j in range(8)]
        self.piece(pts,faces,mat)
    def lens(self,ang,u,z,r,back,front,mat,n=16):
        pts=[self.at(ang,u+r*math.cos(i*math.tau/n),z+r*math.sin(i*math.tau/n),d) for d in (back,front) for i in range(n)]
        self.piece(pts,[tuple(range(n)),tuple(range(n,2*n))]+[(j,(j+1)%n,(j+1)%n+n,j+n) for j in range(n)],mat)
    def plaque(self,ang,u,z,w,h,d,mat):
        # Screen-space order TL, TR, BR, BL. Blender V increases upward.
        pts=[self.at(ang,u+x*w/2,z+y*h/2,d) for x,y in [(-1,1),(1,1),(1,-1),(-1,-1)]]
        self.piece(pts,[(0,1,2,3)],mat,[[(0,1),(1,1),(1,0),(0,0)]],orient=False)
    def line(self,ang,points,d,thickness,mat):
        for (u,z),(v,h) in zip(points,points[1:]):
            du,dz=v-u,h-z;length=math.hypot(du,dz)
            if length<.00001: continue
            x=-dz/length*thickness/2;y=du/length*thickness/2
            coordinates=[(u+x,z+y),(v+x,h+y),(v-x,h-y),(u-x,z-y)]
            self.piece([self.at(ang,p,q,d) for p,q in coordinates],[(0,1,2,3)],mat,orient=False)
    def bolt(self,a,u,z,r,d):
        self.lens(a,u,z,r,d-.003,d+.006,'TC_Alloy',8)
        self.bezel(a,u,z,r*1.05,r*.20,d+.006,d+.007,'TC_Seal',.0004)

def build_shell(g,main):
    g.group('01  Footing and service access')
    g.stack([(0,2.25,'TC_Graphite'),(.060,2.38,'TC_Graphite'),(.13,2.45,'TC_Slate'),
        (.205,2.45,'TC_Seal'),(.216,2.443,'TC_Graphite'),(.584,2.443,'TC_Slate'),
        (.595,2.45,'TC_Slate'),(.79,2.45,'TC_Graphite'),(.855,2.42,'TC_Alloy'),
        (.875,2.39,'TC_Slate'),(.94,2.34,'TC_Graphite'),(.995,2.29,'TC_Graphite')])
    for n in range(6):
        a=main+n*60
        # Lower relief grilles and recessed tie-downs sit within the foot rim.
        for u in (-.82,.82):
            g.bezel(a,u,.39,.51,.18,2.112,2.121,'TC_Seal')
            for k in range(3):
                g.bezel(a,u,.343+.048*k,.41,.012,2.121,2.125,'TC_Slate',.004)
        g.bezel(a,0,.72,.39,.045,2.119,2.125,'TC_Alloy',.006)
        g.bezel(a,0,.72,.25,.023,2.125,2.127,'TC_Graphite',.002)
    g.group('02  Isolated core')
    g.stack([(.985,1.33,'TC_Graphite'),(1.04,1.345,'TC_Alloy'),(1.11,1.345,'TC_Seal'),
             (1.135,1.31,'TC_Graphite'),(1.19,1.325,'TC_Graphite'),
             (5.10,1.325,'TC_Seal'),(5.15,1.31,'TC_Alloy'),(5.18,1.34,'TC_Graphite'),(5.32,1.34,'TC_Graphite')])
    for n in range(6):
        a=main+n*60
        for z,h in [(1.34,.27),(2.63,2.27),(4.44,1.31)]:
            g.bezel(a,0,z,1.307,h,1.140,1.167,'TC_Ceramic',.028)
        for u in (-.588,.588):
            g.bezel(a,u,4.89,.028,.32,1.166,1.171,'TC_Alloy',.006)
        if n not in (0,1,5):
            g.bezel(a,0,2.23,.73,.86,1.165,1.177,'TC_Alloy',.033)
            g.bezel(a,0,2.23,.709,.84,1.176,1.181,'TC_Ceramic',.03)
            g.bezel(a,0,2.45,.35,.057,1.18,1.185,'TC_Graphite',.007)
            for u in [-.30,.30]:
                for h in [1.88,2.58]: g.bolt(a,u,h,.014,1.182)
    g.group('03  Floating datum ring and upper shell')
    g.stack([(5.295,1.44,'TC_Graphite'),(5.34,2.17,'TC_Graphite'),(5.405,2.32,'TC_Slate'),
        (5.46,2.398,'TC_Slate'),(5.69,2.398,'TC_Slate'),(5.705,2.39,'TC_Seal'),
        (5.734,2.39,'TC_Alloy'),(5.748,2.398,'TC_Ceramic'),(5.82,2.37,'TC_Ceramic'),
        (5.89,2.22,'TC_Ceramic'),(5.90,2.10,'TC_Ceramic')])
    # Recessed segmented band: scribed scales appear on the two instrument-facing facets.
    for n in range(6):
        a=main+n*60
        for u in (-.95,.95):
            g.bezel(a,u,5.563,.018,.174,2.073,2.079,'TC_Seal',.003)
        if n in (0,1,5):
            g.bezel(a,0,5.548,.91,.11,2.073,2.081,'TC_Graphite',.009)
            for j in range(19):
                h=.054 if j%3==0 else .027
                g.bezel(a,(j-9)*.042,5.526+h/2,.005,h,2.08,2.084,'TC_Alloy',.001)

def side_instruments(g,main,ref):
    # Place the observation window on the lamp side of each instrument.
    for i,a in enumerate((main+60,main-60)):
        g.group('04  Oscillator inspection' if i==0 else '05  Field service and heat sink')
        if i==0:
            g.bezel(a,0,2.95,.79,2.35,1.164,1.193,'TC_Alloy',.11)
            g.bezel(a,0,2.95,.738,2.285,1.191,1.201,'TC_Seal',.095)
            g.bezel(a,0,2.95,.625,2.16,1.198,1.204,'TC_Optic',.068)
            # Three instrument carriers with isolated mounts, serial socket and crystal.
            for row,(z,r) in enumerate(((2.24,.19),(2.95,.145),(3.55,.175))):
                g.bezel(a,0,z,.53,.46,1.203,1.212,'TC_Graphite',.032)
                g.lens(a,0,z,r,1.21,1.221,'TC_Alloy',24)
                g.lens(a,0,z,r*.8,1.22,1.224,'TC_Seal',24)
                g.lens(a,0,z,r*.58,1.223,1.230,'TC_Optic',20)
                g.lens(a,0,z,r*.22,1.229,1.235,'TC_Amber' if row==1 else 'TC_Slate',12)
                for x in (-.23,.23): g.lens(a,x,z-.16,.012,1.212,1.216,'TC_Alloy',6)
            for n in range(2):
                g.bezel(a,(-1 if n else 1)*.283,2.94,.013,1.96,1.204,1.213,'TC_Slate',.004)
            for x in (-.336,.336):
                for z in (1.90,3.98):g.bolt(a,x,z,.021,1.197)
        else:
            g.bezel(a,0,3.52,.77,.72,1.166,1.181,'TC_Seal',.047)
            for j in range(8):
                g.bezel(a,0,3.216+j*.083,.69,.042,1.181,1.195,'TC_Slate',.016)
            for z in (2.09,2.43):
                g.bezel(a,0,z,.66,.21,1.166,1.184,'TC_Alloy',.032)
                for x in (-.21,0,.21):
                    g.lens(a,x,z,.056,1.183,1.197,'TC_Graphite',12)
                    g.lens(a,x,z,.031,1.196,1.200,'TC_Optic',10)
            g.bezel(a,0,1.75,.38,.034,1.166,1.174,'TC_Amber',.007)

def digit(g,a,u,z,number,d):
    # Reflective, unpowered segment inserts in the six mechanical counting drums.
    active={'0':'abcdef','1':'bc','2':'abdeg','3':'abcdg','4':'bcfg','5':'acdfg','6':'acdefg','7':'abc','8':'abcdefg','9':'abcdfg'}[number]
    shape={'a':(0,.039,.038,.006),'g':(0,0,.038,.006),'d':(0,-.039,.038,.006),
            'b':(.021,.020,.006,.033),'c':(.021,-.020,.006,.033),'f':(-.021,.020,.006,.033),'e':(-.021,-.020,.006,.033)}
    for k in active:
        x,y,w,h=shape[k]
        g.bezel(a,u+x,z+y,w,h,d,d+.0018,'TC_Index',.001)

def front_instrument(g,a,ref):
    g.group('06  Readout and faceplate')
    g.bezel(a,0,2.69,1.185,2.13,1.165,1.193,'TC_Graphite',.078)
    g.bezel(a,0,2.69,1.135,2.078,1.192,1.207,'TC_Alloy',.057)
    g.bezel(a,0,2.69,1.105,2.029,1.206,1.212,'TC_Ceramic',.042)
    g.plaque(a,0,2.69,1.05,1.87,1.213,'TC_ReferenceFace' if ref else 'TC_TestFace')
    for u in (-.551,.551):
        for z in (1.71,3.67):
            g.bolt(a,u,z,.022,1.209)
    # The dedicated screen is one quad with a conventional top-left UV origin in UE.
    z=2.925
    g.bezel(a,0,z,.78,.21,1.214,1.223,'TC_Graphite',.014)
    if ref:
        g.plaque(a,0,z,.62,.18,1.224,'TC_LiveReadout')
        for i in range(4):
            g.bezel(a,.165+i*.043,2.119,.031,.014,1.214,1.217,'TC_Pilot',.002)
    else:
        for i,n in enumerate('172408'):
            x=(i-2.5)*.111
            g.bezel(a,x,z,.096,.157,1.221,1.229,'TC_Optic',.006)
            digit(g,a,x,z,n,1.230)
        # Sparse hairline cracks propagate from a single broken corner of the window.
        for pts in [[(.371,3.018),(.316,2.995),(.247,2.955),(.226,2.913)],[(.316,2.995),(.282,3.006),(.242,3.013)],[(.316,2.995),(.323,2.963),(.310,2.937)]]:
            g.line(a,pts,1.234,.0028,'TC_Alloy')
        g.bezel(a,.24,2.119,.15,.018,1.214,1.218,'TC_Amber',.003)
    # Knurled trim wheel and a connector outside the removable display fascia.
    g.group('07  Trim and output ports')
    g.bezel(a,0,1.465,1.01,.205,1.165,1.184,'TC_Slate',.021)
    for x in (-.38,-.21,-.04):
        g.lens(a,x,1.47,.041,1.184,1.205,'TC_Alloy',12)
        g.lens(a,x,1.47,.026,1.204,1.21,'TC_Seal',12)
        g.lens(a,x,1.47,.008,1.21,1.215,'TC_Amber',8)
    g.lens(a,.304,1.47,.082,1.182,1.204,'TC_Seal',24)
    g.lens(a,.304,1.47,.064,1.202,1.232,'TC_Alloy',18)
    g.lens(a,.304,1.47,.048,1.229,1.235,'TC_Graphite',18)
    g.line(a,[(.304,1.47),(.281,1.504)],1.237,.007,'TC_Index')

def make_materials():
    result={}
    for key,params in MATERIALS.items():
        m=bpy.data.materials.new(key);m.diffuse_color=(*params['color_linear'],1);m.use_nodes=True
        shader=m.node_tree.nodes.get('Principled BSDF')
        for attr,prop in [('Base Color',m.diffuse_color),('Metallic',params['metallic']),('Roughness',params['roughness'])]:
            shader.inputs[attr].default_value=prop
        if 'texture' in params:
            bitmap=bpy.data.images.load(str(ROOT/params['texture']))
            image=m.node_tree.nodes.new('ShaderNodeTexImage');image.image=bitmap
            m.node_tree.links.new(image.outputs['Color'],shader.inputs['Base Color'])
            bitmap.pack()
        result[key]=m
    return result

def make_mesh(name,part,mats,collection):
    vs,fs,ids,uvs=part
    me=bpy.data.meshes.new(name)
    me.from_pydata(vs,[],fs)
    assert not me.validate(verbose=True),name
    me.update()
    slots=list(dict.fromkeys(ids))
    for key in slots:me.materials.append(mats[key])
    layer=me.uv_layers.new(name='UVMap')
    for ix,poly in enumerate(me.polygons):
        poly.material_index=slots.index(ids[ix])
        if uvs[ix]:
            for li,uv in zip(poly.loop_indices,uvs[ix]): layer.data[li].uv=uv
        else:
            n=poly.normal
            axis=(1,2) if abs(n.x)>=max(abs(n.y),abs(n.z)) else ((0,2) if abs(n.y)>abs(n.z) else (0,1))
            for li in poly.loop_indices:
                p=me.vertices[me.loops[li].vertex_index].co;layer.data[li].uv=(p[axis[0]],p[axis[1]])
    ob=bpy.data.objects.new(name,me);collection.objects.link(ob)
    return ob

def run():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    mats=make_materials()
    report={'material_manifest':'material_manifest.json','meshes':[]}
    for ref in (True,False):
        a=-60 if ref else 0
        name='SM_TC_ReferenceClock' if ref else 'SM_TC_TestClock'
        col=bpy.data.collections.new(name);bpy.context.scene.collection.children.link(col)
        g=Geometry();build_shell(g,a);side_instruments(g,a,ref);front_instrument(g,a,ref)
        objs=[make_mesh(part,data,mats,col) for part,data in g.parts.items() if data[1]]
        # Leave the editable component groups in the source. Export a merged duplicate.
        copies=[]
        for ob in objs:
            dup=ob.copy();dup.data=ob.data.copy();col.objects.link(dup);copies.append(dup)
        bpy.ops.object.select_all(action='DESELECT')
        for o in copies:o.select_set(True)
        bpy.context.view_layer.objects.active=copies[0];bpy.ops.object.join()
        ob=copies[0];ob.name=name;ob.data.name=name
        bpy.ops.export_scene.fbx(filepath=str(MESHES/(name+'.fbx')),use_selection=True,object_types={'MESH'},
            axis_forward='-Y',axis_up='Z',add_leaf_bones=False,mesh_smooth_type='FACE',bake_anim=False,
            path_mode='STRIP',use_triangles=True)
        ob.data.calc_loop_triangles()
        report['meshes'].append(dict(name=name,face_yaw_ue=a,pivot='base center',triangles=len(ob.data.loop_triangles),
            dims_m=[round(x,5) for x in ob.dimensions],slots=[s.name for s in ob.material_slots]))
        bpy.data.objects.remove(ob,do_unlink=True)
        for child in col.objects:child.location.x=0 if ref else 5.6
    bpy.context.preferences.filepaths.save_version=0
    bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'TC_ClockInstruments.blend'))
    (ROOT/'material_manifest.json').write_text(json.dumps(MATERIALS,indent=2))
    (ROOT/'clock_build.json').write_text(json.dumps(report,indent=2))
    print('CLOCKS:',json.dumps(report))

run()
