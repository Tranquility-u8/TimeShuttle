"""Build the intact entrance to Omen's room in Chapter 1. Run in Blender.

Drawing coordinates are centimetres, as seen by a visitor facing the gate:
u goes to screen right, v goes up, and depth increases toward the viewer.
The FBXs use UE world axes and base-centred pivots documented in placement.json.
"""
import importlib.util
import json
from math import cos, radians, sin
from pathlib import Path

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parent
BUILDER = ROOT.parents[1] / "TemporalCalibration/NorthExit/build_north_exit.py"
spec = importlib.util.spec_from_file_location("chapter1_fabrication", BUILDER)
fabrication = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fabrication)
fabrication.ROOT = ROOT
Asset, rect, ellipse = fabrication.Asset, fabrication.rect, fabrication.ellipse


def ring(model, name, outer, inner, rear, lip, material):
    """Extrude one open bezel, including its folded inner and outer returns."""
    n = len(outer)
    assert n == len(inner)
    vertices = [(u, depth, v) for shape, depth in
                ((outer, rear), (outer, lip), (inner, lip), (inner, rear))
                for u, v in shape]
    faces = []
    for band in range(4):
        start, end = band*n, (band+1)%4*n
        for j in range(n):
            k = (j+1) % n
            faces.append([start+j,start+k,end+k,end+j])
    return model.geometry(name, vertices, faces, material)


def inset_polygon(outline, distance):
    center = Vector((sum(u for u,v in outline)/len(outline),
                     sum(v for u,v in outline)/len(outline)))
    return [tuple(Vector(pt) + (center-Vector(pt)).normalized()*distance) for pt in outline]


def panel(model, name, outline, depths, material):
    """Facade sheet with a folded front plane. Narrow gasket between sheets."""
    face = inset_polygon(outline, 1.65)
    size = len(face)
    points = [(u,1.8,v) for u,v in face]
    points.extend((u,d,v) for (u,v),d in zip(face,depths))
    faces = [list(range(size)), list(range(size,2*size))]
    faces.extend((i,(i+1)%size,(i+1)%size+size,i+size) for i in range(size))
    return model.geometry(name, points, faces, material)


def arc(model, name, center, radii, width, first, last, depth, material, steps):
    def point(angle, inset):
        a = radians(angle)
        return (center[0]+(radii[0]-inset)*cos(a), center[1]+(radii[1]-inset)*sin(a))
    angles = [first+(last-first)*i/steps for i in range(steps+1)]
    # Separate quads avoid concave-ngon tessellation across the inner radius.
    layers = [[point(a,s) for a in angles] for s in (0,width)]
    pts = [(u,d,v) for d in (depth-1.1,depth) for layer in layers for u,v in layer]
    n = len(angles)
    faces = []
    for j in range(n-1):
        for start,end in ((0,n),(n,3*n),(3*n,2*n),(2*n,0)):
            faces.append([start+j,start+j+1,end+j+1,end+j])
    faces.extend(([0,n,3*n,2*n],[n-1,2*n-1,4*n-1,3*n-1]))
    return model.geometry(name, pts, faces, material)


def graduations(model, name, center, radii, start, stop, increment, outer):
    """Discrete raised strokes on the two concentric engraved scales."""
    pts, faces = [], []
    for j, angle in enumerate(range(start,stop+1,increment)):
        a = radians(angle)
        major = j%5 == 0
        length = (32 if major else 16) if outer else (24 if major else 12)
        thick = (2.8 if major else 1.05) if outer else (2.1 if major else .95)
        u = center[0]+radii[0]*cos(a)
        v = center[1]+radii[1]*sin(a)
        # Tick normal follows the real elliptical track rather than a radial axis.
        norm = Vector((cos(a)/radii[0],sin(a)/radii[1])).normalized()
        across = Vector((-norm.y,norm.x))*thick/2
        t = Vector((u,v))
        tail = t - norm*length
        outline = [t+across,t-across,tail-across,tail+across]
        base = len(pts)
        for depth in ((24.5,26.3) if outer else (26.1,27.9)):
            pts.extend((q.x,depth,q.y) for q in outline)
        faces.extend([[base+i for i in face] for face in
                      ([0,1,2,3],[4,5,6,7],[0,4,5,1],[1,5,6,2],
                       [2,6,7,3],[3,7,4,0])])
    return model.geometry(name,pts,faces,"TC_Seal" if outer else "TC_Index")


def clock_facade():
    m = Asset("SM_CH_OmenClockFacade")
    m.box("Wall underlay", -1798,1798,0,1.6,1,858,"TC_Graphite")
    outer = rect(-953,953,182,743,132)
    # Wall folds meet the bezel and return to the wall in three planes.
    lx,rx=-1798,1798
    wing_left = [(lx,1),(-1100,1),(-820,182),(-953,314),(lx,543)]
    wing_mid = [(lx,543),(-953,314),(-953,611),(-1550,858),(lx,858)]
    wing_top = [(-1550,858),(-953,611),(-821,743),(-1045,858)]
    wing_bottom = [(-1100,1),(-695,1),(-652,182),(-821,182)]
    for side,scale in (("west",1),("east",-1)):
        for i,(profile,depths,mat) in enumerate([
            (wing_left,[8,12,39,30,16],"TC_Brushed"),
            (wing_mid,[16,30,28,9,8],"TC_Ceramic"),
            (wing_top,[9,28,38,11],"TC_Pearl"),
            (wing_bottom,[12,9,34,39],"TC_Ceramic"),
        ]):
            panel(m,f"Folded cladding {side} {i+1}",[(u*scale,v) for u,v in profile],depths,mat)
    panel(m,"Infill below bezel left",[(-695,1),(0,1),(0,182),(-652,182)],
          [9,8,35,34],"TC_Ceramic")
    panel(m,"Infill below bezel right",[(0,1),(695,1),(652,182),(0,182)],
          [8,9,34,35],"TC_Ceramic")
    for s in (-1,1):
        panel(m,"Upper crown segment",[(0,743),(821*s,743),(1045*s,858),(0,858)],
              [35,38,11,10],"TC_Ceramic")
    m.prism("Instrument cavity",outer,2.4,16.8,"TC_Seal")
    ring(m,"Shadow line behind aperture",rect(-960,960,176,749,134),
         rect(-927,927,200,722,112),16.9,39.2,"TC_Graphite")
    ring(m,"Brushed folded outer bezel",outer,rect(-872,872,224,696,107),27.2,50,"TC_Brushed")
    ring(m,"Silver aperture reveal",rect(-873,873,222,698,108),
         rect(-851,851,238,683,96),29,48.3,"TC_Alloy")
    ring(m,"Black return around dial",rect(-851,851,238,683,96),
         rect(-842,842,244,676,94),18.3,42,"TC_Graphite")
    # The scale is observed through the cut-corner aperture. The pivot sits on
    # its lower edge; the dial's inner radius and bearing belong to one needle.
    pole=(0,247)
    arc(m,"Dark back of elapsed arc",pole,(658,427),93,1.5,178.5,20,"TC_Support",72)
    arc(m,"Recessed silver sector of scale",pole,(651,423),73,2,111,24,"TC_Alloy",62)
    arc(m,"Smoked arc remaining sector",pole,(651,423),73,111.2,178,24,"TC_Graphite",42)
    graduations(m,"Etched primary graduations",pole,(647,419),2,178,2,True)
    arc(m,"Inner minute race",pole,(350,221),5,9,171,25.4,"TC_Brushed",64)
    graduations(m,"Machined inner divisions",pole,(358,235),9,171,2,False)
    m.prism("Pointer clearance shadow",[(-16,246),(-7,262),(297,501),(12,245)],29,31,"TC_Seal")
    m.prism("Single tapered indicator", [(-13,249),(-7,263),(295,502),(14,253)],
            32,39.7,"TC_Index",.35)
    for r,depth,mat in [(62,31,"TC_Seal"),(53,37,"TC_Alloy"),(43,41,"TC_Brushed"),
                        (13,42.7,"TC_Graphite")]:
        # The lowest half of the bearing is hidden behind the bottom sill.
        semi=[(-r,244),(r,244)]+[(r*cos(radians(a)),244+r*sin(radians(a)))
                                   for a in range(6,180,6)]
        m.prism("Central bearing",semi,17.5,depth,mat)
    screen=[(470,245),(796,245),(838,288),(838,420),(659,420)]
    m.prism("Readout flange",screen,17.5,31.6,"TC_Alloy",1.1)
    m.prism("Readout gasket",inset_polygon(screen,8),31.2,35.7,"TC_Graphite",.65)
    m.prism("Status glass",inset_polygon(screen,14),35.2,37.6,"TC_Optic",.55)
    for i,(x,length) in enumerate([(614,30),(646,16),(678,46),(710,23),(742,36),(774,17)]):
        m.box(f"Readout segment {i+1}",x,x+4.7,37.7,38.5,268,268+length,"TC_Pilot",.45)
    for u,v in [(u,v) for u in (-904,904) for v in (331,579)]+[
                    (u,v) for u in (-763,0,763) for v in (202,723)]:
        m.prism("Countersunk rim fastener",ellipse(u,v,4.3,4.3,8),49.8,51,"TC_Support")
        m.prism("Bolt drive",ellipse(u,v,1.65,1.65,6),51.1,51.4,"TC_Seal")
    return m


def desk():
    m = Asset("SM_CH_ReceptionDesk")
    # The upper and lower profiles share eight vertices. The front face splits
    # on its architectural diagonal, creating an actual change of normal.
    m.prism("Inset graphite plinth",rect(-277,277,-49,52,14),0,15,"TC_Graphite",1.2,axis="Z")
    bottom=[(-281,-52),(281,-52),(289,-44),(289,33),(260,54),(-238,52),(-286,35),(-286,-45)]
    top=[(-282,-59),(282,-59),(300,-43),(300,40),(278,59),(-269,59),(-300,36),(-300,-42)]
    pts=[(u,d,12) for u,d in bottom]+[(u,d,89) for u,d in top]
    fs=[list(range(8)),list(range(8,16))]
    for j in range(8):
        k=(j+1)%8
        if j==4:
            fs.extend(([j,k,k+8],[j,k+8,j+8]))
        else:
            fs.append([j,k,k+8,j+8])
    shell=m.geometry("Folded desk shell",pts,fs,"TC_Ceramic",.8)
    m.prism("Machined top edge",top,89.4,91.6,"TC_Alloy",.55,axis="Z")
    m.prism("Inset dark terminal case",rect(-267,267,-28,26,8),91.7,103.0,
            "TC_Graphite",1.1,axis="Z")
    m.prism("Display glass",rect(-259,259,-21,19,5),103.0,104.3,
            "TC_Optic",.45,axis="Z")
    for i in range(4):
        m.box("Small console status diode",211+i*9,213+i*9,25.8,26.8,97.4,100.5,"TC_Pilot")
    # Human side of the desk can be inspected when the player walks behind it.
    for s in (-1,1):
        m.prism("Rear service door",rect(-120+s*125,120+s*125,25,76,4),-58,-58.9,
                "TC_Support",.4)
        m.box("Recessed service grip",s*125-13,s*125+13,-60,-58.8,63,67,"TC_Seal",.4)
    return m


def beam():
    m=Asset("SM_CH_OmenBeam")
    # Include the rear and end faces so the source block can be hidden while
    # its collision stays in the original position.
    m.box("Squared structural body",-1899,1899,-16,16.3,-30.6,29.7,"TC_Graphite",.42)
    m.box("Black upper shadow line",-1899,1899,16.5,19.8,-30.8,29.6,"TC_Seal")
    m.box("Upper dark folded fascia",-1899,1899,19.9,22.4,-30.4,24.5,"TC_Graphite",.65)
    # Built underside with actual dark slots between face sheets.
    m.box("Beam underside backing",-1899,1899,-16.5,22.4,-31.6,-30.7,"TC_Seal")
    for u0,u1 in [(-1899,-1165),(-760,760),(1165,1899)]:
        m.box("Pressed lower flange",u0,u1,-16.5,22.4,-33.8,-31.7,"TC_Graphite",.45)
    for x in (-962.5,962.5):
        for d0,d1 in [(-16.5,-11),(15.5,22.4)]:
            m.box("Slot return",x-202.5,x+202.5,d0,d1,-33.8,-31.7,"TC_Graphite",.42)
    return m


def portal():
    m=Asset("SM_CH_C0PortalTrim")
    # The original clear opening is x ±400 and z 0–480. All static trim lies
    # outside this rectangle. C0's moving doors and trigger remain independent.
    for s in (-1,1):
        def jamb(name,p,back,front,mat,b):
            m.prism(name,[(s*u,z) for u,z in p],back,front,mat,b)
        jamb("Fixed jamb gasket",[(400.6,.5),(476,.5),(476,471),(412,535),(0,535),(0,481),(397,481),(400.6,477.4)],
             1,6,"TC_Seal",.3)
        jamb("Chamfered pivot-side frame",[(402.2,1),(450,1),(450,461),(392,520),(0,520),(0,487),(392,487),(402.2,477)],
             6.3,12.8,"TC_Brushed",.6)
        jamb("Inner door reveal",[(401,1),(412,1),(412,473),(398,487),(0,487),(0,481.2),(395,481.2),(401,475.2)],
             13.1,16,"TC_Graphite",.38)
    return m


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    for name,info in fabrication.PALETTE.items():
        material=bpy.data.materials.new(name)
        material.diffuse_color=(*info["color_linear"],1)
        material.metallic=info["metallic"]
        material.roughness=info["roughness"]
        fabrication.MATERIALS[name]=material
    installations=[(clock_facade(),[0,925,540]),(beam(),[0,400,1370]),
                   (desk(),[0,-613.3,0]),(portal(),[0,925,0])]
    exports={}
    for model,origin in installations:
        # A 180-degree turn points these viewer-space drawings toward the hall.
        for obj in model.objects:
            for vertex in obj.data.vertices:
                vertex.co.x *= -1
                vertex.co.y *= -1
            obj.data.update()
        report=model.export()
        report.update(fbx=model.name+".fbx",location=origin,rotation=[0,0,0],scale=[1,1,1],
                      visible_only=True)
        exports[model.name]=report
    # Save a clean editable scene with all meshes positioned in the same UE world.
    for m,(x,y,z) in installations:
        pivot=bpy.data.objects.new(m.name+"_pivot",None)
        m.collection.objects.link(pivot)
        for obj in m.objects:
            obj.parent=pivot
        pivot.location=(.01*x,-.01*y,.01*z)
    eye=Vector((0,27,1.7))
    target=Vector((0,-6,5.8))
    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type=="VIEW_3D":
                view=area.spaces.active
                view.region_3d.view_rotation=(target-eye).to_track_quat("-Z","Y")
                view.region_3d.view_distance=34
                view.region_3d.view_location=target
                view.overlay.show_overlays=False
                view.shading.color_type="MATERIAL"
    bpy.ops.object.select_all(action="DESELECT")
    bpy.context.preferences.filepaths.save_version=0
    bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/"OmenEntrance.blend"),compress=True)
    slots={name:"/Game/Environment/Chapter1/TemporalCalibration/Materials/MI_"+name
           for model in exports.values() for name in model["slots"]}
    manifest={"units":"UE world centimetres","combine_meshes":True,
              "material_slots":slots,"models":exports,
              "original_visuals":{"SM_CH_ReceptionDesk":"R17_Furniture_025_reception",
                                  "SM_CH_OmenBeam":"HallRoofBeam::-4"}}
    (ROOT/"placement.json").write_text(json.dumps(manifest,indent=2)+"\n",encoding="utf8")
    print("Completed Omen entrance:",{m:r["triangles"] for m,r in exports.items()})


if __name__=="__main__":
    main()
