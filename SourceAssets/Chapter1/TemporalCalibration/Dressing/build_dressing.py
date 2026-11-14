"""Build UE-ready portable dressing for the Temporal Calibration Lab. Blender units are metres."""
from pathlib import Path
from math import radians
import sys
import bpy
from mathutils import Vector, Matrix

ROOT = Path(__file__).resolve().parent
MESHES = ROOT / "Meshes"
MESHES.mkdir(exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)

# The existing ParticleLab equipment instances supply materials after UE import.
COLORS = {
    "Ceramic": (.66,.66,.64), "Panel": (.39,.43,.47), "Graphite": (.15,.17,.18),
    "Seal": (.035,.043,.045), "Metal": (.48,.51,.53), "Screen": (.045,.089,.095),
    "Status": (.39,.65,.63), "Red": (.61,.17,.09),
}
def coat(obj, name, slot):
    obj.name = name
    mat = bpy.data.materials.get(slot)
    if mat is None:
        mat = bpy.data.materials.new(slot)
        mat.diffuse_color = (*COLORS[slot],1.0)
    obj.data.materials.append(mat)
    return obj

def box(name,p,size,slot,bevel=0):
    bpy.ops.mesh.primitive_cube_add(size=1,location=p)
    obj=bpy.context.object
    obj.dimensions=size
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    if bevel:
        mod=obj.modifiers.new("Pressed edge","BEVEL")
        mod.width=bevel
        mod.segments=2
        bpy.ops.object.modifier_apply(modifier=mod.name)
    return coat(obj,name,slot)

def barrel(name,p,r,d,slot,axis=(1,0,0),sides=12):
    bpy.ops.mesh.primitive_cylinder_add(vertices=sides,radius=r,depth=d,location=p)
    obj=bpy.context.object
    obj.rotation_euler=Vector(axis).to_track_quat('Z','Y').to_euler()
    return coat(obj,name,slot)

def trace(name,p,q,r,slot):
    a,b=Vector(p),Vector(q)
    return barrel(name,(a+b)*.5,r,(b-a).length,slot,b-a,8)

def words(name,phrase,p,size,slot):
    curve=bpy.data.curves.new(name,'FONT')
    curve.body=phrase
    curve.size=size
    curve.align_y='CENTER'
    curve.resolution_u=2
    obj=bpy.data.objects.new(name,curve)
    bpy.context.collection.objects.link(obj)
    obj.location=p
    obj.rotation_euler=Matrix(((0,0,1),(1,0,0),(0,1,0))).to_euler()
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active=obj
    bpy.ops.object.convert(target='MESH')
    return coat(obj,name,slot)

def recorder():
    # Physical feet register on the bench; recessed features stay inside the desk footprint.
    for x in (-.19,.18):
        for y in (-.53,.53):
            barrel("Elastomer foot",(x,y,.022),.044,.044,"Seal",(0,0,1))
    box("Rolled lower tray",(0,0,.075),(.51,1.27,.076),"Graphite",.015)
    box("Two-channel bridge",(-.003,0,.232),(.49,1.254,.291),"Ceramic",.028)
    box("Replaceable lid",(-.012,0,.381),(.46,1.245,.030),"Panel",.010)
    for y in (-.35,-.275,-.20,-.125,-.05):
        box("Recessed upper exhaust",(-.04,y,.397),(.245,.016,.006),"Seal",.002)
    box("Face gasket",(.242,0,.225),(.015,1.164,.226),"Graphite",.009)
    box("Input panel",(.249,.405,.225),(.022,.347,.210),"Panel",.005)
    box("Signal window",(.252,-.177,.229),(.016,.741,.184),"Screen",.007)
    # Vertical graticules are lower contrast than the two traces and their labels.
    for i in range(9):
        box("Grid / time",(.261,-.493+i*.078,.221),(.002,.0018,.112),"Graphite")
    words("Reference label","REF",(.264,-.52,.258),.023,"Ceramic")
    words("Test label","DUT",(.264,-.52,.193),.023,"Ceramic")
    for y0 in (-.394,-.245,-.096,.053):
        pts=[(y0,.250),(y0+.037,.250),(y0+.037,.276),(y0+.087,.276),(y0+.087,.250),(y0+.149,.250)]
        for (y,z),(yy,zz) in zip(pts,pts[1:]):
            trace("Latched reference waveform",(.265,y,z),(.265,yy,zz),.0019,"Status")
    box("Latched test trace",(.265,-.105,.187),(.003,.596,.003),"Ceramic")
    for y in (.297,.423):
        barrel("Coax mount",(.270,y,.241),.042,.028,"Metal",sides=6)
        barrel("Coax sleeve",(.294,y,.241),.027,.021,"Graphite")
        barrel("Coax dielectric",(.307,y,.241),.015,.006,"Seal")
        barrel("Contact",(.312,y,.241),.004,.006,"Metal")
    barrel("Trim collar",(.272,.512,.176),.035,.020,"Seal")
    barrel("Channel trim",(.292,.512,.176),.029,.024,"Metal",sides=16)
    box("Trim index",(.306,.512,.189),(.003,.003,.013),"Graphite")
    words("Range label","A    /    B",(.264,.276,.156),.028,"Ceramic")
    words("Chassis designation","PHASE COMPARATOR",(.246,-.522,.358),.020,"Graphite")
    for y in (-.586,.585):
        for z in (.144,.316):
            barrel("Fascia screw",(.251,y,z),.010,.009,"Graphite",sides=8)

def tray():
    box("Tool case",(0,0,.031),(.38,.61,.062),"Graphite",.016)
    box("Dark insert",(0,0,.063),(.339,.566,.012),"Seal",.008)
    for side in (-1,1):
        y=.099*side
        barrel("Probe handle",(0,y,.086),.024,.169,"Panel",(1,0,0))
        barrel("Channel identification",(.071,y,.086),.0245,.014,"Status" if side<0 else "Metal")
        barrel("Probe ferrule",(.100,y,.086),.017,.03,"Metal")
        barrel("Probe tip",(.132,y,.086),.004,.035,"Metal")
        barrel("Probe socket",(-.107,y,.086),.014,.042,"Graphite")
        for x in (-.042,-.024,-.006):
            barrel("Molded grip",(x,y,.086),.0245,.006,"Graphite")
    for y in (-.274,.274):
        box("Instrument tray lip",(0,y,.071),(.35,.013,.032),"Panel",.004)

def plate():
    box("Wall plate mounting cleat",(.005,0,0),(.010,1.78,.326),"Seal",.002)
    box("Back-anodized enamel plate",(.015,0,0),(.020,1.82,.342),"Graphite",.004)
    box("Identification strip",(.026,-.832,0),(.003,.036,.248),"Status")
    words("Lab name","TEMPORAL CALIBRATION",(.029,-.754,.045),.114,"Ceramic")
    words("Directory line","LAB 02     /     METROLOGY",(.029,-.749,-.083),.045,"Ceramic")
    for y in (-.88,.88):
        for z in (-.135,.135):
            barrel("Captive rivet",(.029,y,z),.007,.006,"Metal")

requested=set(sys.argv[sys.argv.index('--')+1:]) if '--' in sys.argv else set()
for name,builder in [('SM_TS_PhaseComparator',recorder),('SM_TS_MatchedProbeTray',tray),
                     ('SM_TS_CalibrationPlaque',plate)]:
    if requested and name not in requested:
        continue
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    builder()
    meshes=[o for o in bpy.context.scene.objects if o.type=='MESH']
    bpy.ops.object.select_all(action='DESELECT')
    for obj in meshes:
        obj.select_set(True)
    bpy.context.view_layer.objects.active=meshes[0]
    bpy.ops.object.join()
    obj=bpy.context.object
    bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
    bpy.context.scene.cursor.location=(0,0,0)
    bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
    obj.name=name
    obj.data.name=name
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project(angle_limit=radians(60),island_margin=.007)
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.export_scene.fbx(filepath=str(MESHES/(name+'.fbx')),use_selection=True,
        object_types={'MESH'},apply_unit_scale=True,apply_scale_options='FBX_SCALE_UNITS',
        axis_forward='-Y',axis_up='Z',add_leaf_bones=False,mesh_smooth_type='FACE')
