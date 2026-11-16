"""Build Chapter 1's cosmetic kit from the training-room and Omen door pieces.

Run with Blender in background mode. Blueprint leaves keep their existing
centred 100 cm cube, collision, animation, interaction and per-instance scale.
"""
import importlib.util
import json
import sys
from pathlib import Path

import bpy
from mathutils import Matrix


ROOT = Path(__file__).resolve().parent
CHAPTER = ROOT.parents[1]
TRAINING = CHAPTER.parent / 'TrainingRoom'
builder = CHAPTER / 'TemporalCalibration/NorthExit/build_north_exit.py'
spec = importlib.util.spec_from_file_location('door_fabrication', builder)
fabrication = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fabrication)
fabrication.ROOT = ROOT
Asset, rect = fabrication.Asset, fabrication.rect


def source_meshes(path):
    bpy.ops.object.select_all(action='DESELECT')
    bpy.ops.import_scene.fbx(filepath=str(path), use_custom_normals=False)
    result = [o for o in bpy.context.selected_objects if o.type == 'MESH']
    assert result, path
    return result


def map_geometry(model, source, name, points_to_blender, material):
    vertices = [points_to_blender(source.matrix_world @ v.co) for v in source.data.vertices]
    faces = [tuple(f.vertices) for f in source.data.polygons]
    # Asset.geometry expects cm and reverses the UE Y axis for Blender.
    return model.geometry(name, [(100*x,-100*y,100*z) for x,y,z in vertices], faces, material)


def stock_panel(model, u0, u1, z0, z1, depth_back, depth_front, mat, mesh):
    # Preserve the original machined bevel geometry of the training-room face.
    # The source is in metres: X depth, Y width, Z height, pivot at its centre.
    def remap(point):
        x,y,z=point
        width_ratio=y/1.08+.5
        height_ratio=z/1.94+.5
        through=x/.01+.5
        return ((u0+(u1-u0)*width_ratio)/100,
                -(depth_back+(depth_front-depth_back)*through)/100,
                (z0+(z1-z0)*height_ratio)/100)
    map_geometry(model,mesh,'Training door | formed backing',remap,mat)


def transform_meshes(model, transform):
    mirrored=transform.to_3x3().determinant()<0
    for obj in model.objects:
        obj.data.transform(transform)
        if mirrored: obj.data.flip_normals()
        obj.data.update()

def fit_prompt_clearance(model):
    # A stock 16 cm door puts the two projected text planes at +/-13 cm.
    # Fold the relief closer to the stock door while retaining a physical
    # gap to the collision cube and the same front silhouette.
    for obj in model.objects:
        for vertex in obj.data.vertices:
            x=vertex.co.x
            vertex.co.x=(1 if x>0 else -1)*(.515+(abs(x)-.52)*.46)
        obj.data.update()


def slide_leaf(side, stock):
    model=Asset('SM_LabDoorLeaf'+('Left' if side<0 else 'Right'))
    # Drawing uses one physical 120 x 340 cm leaf. u grows from its closing
    # edge to its pocket; the profile meets its mate across the central gap.
    for face in (-1,1):
        def plate(name,outline,back,front,mat,bevel=.36):
            return model.prism(name,outline,face*back,face*front,mat,bevel)
        stock_panel(model,.8,119.2,1.0,339.0,face*8.32,face*9.25,'TC_Graphite',stock)
        plate('Perimeter gasket',[(2,12),(106,12),(116,22),(116,308),(102,328),(2,328)],
              9.42,10.51,'TC_Seal')
        plate('Cold rolled surround',[(2.2,17),(103,17),(112,26),(112,306),(99,323),(2.2,323)],
              10.64,11.82,'TC_Brushed')
        plate('Recessed liner',[(2.4,23),(100,23),(108,32),(108,302),(95,317),(2.4,317)],
              11.96,12.58,'TC_Support')
        # The main satin pressing has a diagonal shoulder and a separate
        # removable toe panel. These large forms survive low-light viewing.
        plate('Upper leaf pressing',[(3.4,102),(62,102),(78,120),(104.9,120),
              (104.9,300),(93,313),(3.4,313)],12.74,14.0,'TC_Slate',.65)
        plate('Lower graphite pressing',[(3.4,28),(98,28),(104.9,35),
              (104.9,115.3),(79,115.3),(63,97.5),(3.4,97.5)],12.74,13.55,'TC_Support',.5)
        plate('Brushed stile',[(90,125),(102.5,125),(102.5,290),(90,278)],
              14.17,14.9,'TC_Brushed',.24)
        plate('Inspection recess',rect(91.8,100.6,204,241,1.3),
              15.02,15.48,'TC_Seal',.16)
        plate('Index behind smoked insert',rect(94.0,98.3,211,234,.65),
              15.61,15.91,'TC_Pilot',.12)
        plate('Kick rail shoulder',[(7,40),(90,40),(96,46),(96,50),(7,50)],
              13.72,14.28,'TC_Brushed',.27)
    # UE leaf axes: +X normal, +Y across, +Z height. BP scales this local
    # mesh and the underlying cube by (thickness, half-width, height)/100.
    transform_meshes(model,Matrix(((0,-1/.16,0,0),
                                  (-side/1.20,0,0,.5*side),
                                  (0,0,1/3.40,-.5),(0,0,0,1))))
    return model


def portal(stock_jamb,stock_head):
    model=Asset('SM_LabDoorPortal320')
    # Drawing x is width, +depth points out towards player. Export faces -Y.
    w,h=160,380
    for side in (-1,1):
        def half(name,outline,d0,d1,mat,b=.35):
            model.prism(name,[(side*x,z) for x,z in outline],-d0,-d1,mat,b)
        def jamb_map(p):
            a,b,c=p
            return (side*(176+b/.12*20)/100,(2.8+a/.14*3.6)/100,(185+c/2.32*368)/100)
        map_geometry(model,stock_jamb,'Training jamb | rear extrusion',jamb_map,'TC_Graphite')
        # All widths are outside the surveyed rectangle. Shoulder turns occur
        # above the opening to maintain its complete rectangular clear profile.
        half('Backing seal',[(w+.4,.7),(w+32,.7),(w+32,h-11),
            (w+6,h+30),(.15,h+30),(.15,h+.6),(w+.4,h+.6)],1.2,6.1,'TC_Seal')
        half('Folded enamel casing',[(w+5.4,3),(w+28,3),(w+28,h-10),
            (w+4,h+25),(.35,h+25),(.35,h+7),(w+5.4,h+7)],6.3,12.5,'TC_Ceramic',.7)
        half('Cabinet inner moulding',[(w+.8,2),(w+6.6,2),(w+6.6,h+8.3),
            (.45,h+8.3),(.45,h+1.3),(w+.8,h+1.3)],6.25,13.7,'TC_Brushed',.3)
        half('Pocket foot guard',[(w+7.8,2.5),(w+26,2.5),(w+26,37),(w+20,44),
            (w+7.8,44)],12.7,14.2,'TC_Support')
        half('Corner split',[(w+7,h+7.8),(w+12.5,h+7.8),(w+21,h+18),
            (w+17.1,h+22)],12.74,13.0,'TC_Support',.12)
    def head_map(p):
        a,b,c=p
        return (b/1.44*3.21,(3+a/.14*3.2)/100,(h+16+c/.12*19)/100)
    map_geometry(model,stock_head,'Training portal | upper rail housing',head_map,'TC_Graphite')
    return model


def omen(side):
    suffix='Left' if side<0 else 'Right'
    model=Asset('SM_LabDoorOmenLeaf'+suffix)
    source=source_meshes(ROOT.parent/'EntrancePanels'/('SM_CH_C0Leaf'+suffix+'.fbx'))
    for obj in source:
        mat=obj.data.materials[0].name.split('.')[0]
        # The existing C0 piece has the inverse BP scale baked in. Its
        # drawing is faithfully retained on both sides of the original leaf.
        for orientation in (-1,1):
            map_geometry(model,obj,'Omen leaf | '+obj.name,
                         lambda p:(p.x*orientation,p.y,p.z),mat)
    return model


def lift_front(stock):
    model=Asset('SM_LabLiftFront160')
    # One opaque shallow assembly for the fixed lift recess. Drawing depth
    # points directly toward the landing (+UE Y) from the shaft's front face.
    model.prism('Landing closure backing',rect(-91,91,.5,290,4),.2,1.3,'TC_Seal',.2)
    for side in (-1,1):
        def plate(name,outline,back,front,mat,bevel=.32):
            return model.prism(name,[(side*x,z) for x,z in outline],back,front,mat,bevel)
        stock_panel(model,min(side*.75,side*79.25),max(side*.75,side*79.25),
                    1.8,269.5,1.55,2.8,'TC_Support',stock)
        plate('Lift leaf satin face',[(1.35,22),(77.8,22),(77.8,259),(71,266),
              (1.35,266)],3.03,4.1,'TC_Brushed')
        plate('Lift leaf edge pressing',[(63,23),(77.3,23),(77.3,257),
              (70.3,264),(63,264)],4.31,4.74,'TC_Alloy',.16)
        plate('Leaf edge gasket',rect(.8,2.25,3.5,267),4.32,4.8,'TC_Support',.16)
        plate('Lower wear plate',[(2,3.5),(77.5,3.5),(77.5,18),(73,20),
              (2,20)],3.03,4.0,'TC_Alloy')
        plate('Inlaid pocket seam',[(62.5,29),(63.3,29),(63.3,256),(62.5,256)],
              4.89,5.07,'TC_Support',.08)
        plate('Return gasket',[(80,.7),(91,.7),(91,275),(85,285),
              (.25,285),(.25,270.5),(80,270.5)],1.55,7.3,'TC_Graphite')
        plate('Folded lift trim',[(80.7,2),(89.8,2),(89.8,274),(83,284),
              (.35,284),(.35,272),(80.7,272)],7.55,10.2,'TC_Ceramic',.4)
        plate('Recessed dark runner',[(79.2,2),(81.5,2),(81.5,271.3),
              (.5,271.3),(.5,268.8),(79.2,268.8)],5.2,7.45,'TC_Seal',.18)
    model.prism('Arrival panel rim',rect(-26,26,273.6,289.3,3.0),10.45,11.2,'TC_Support',.26)
    model.prism('Arrival smoked glazing',rect(-23,23,275,287.8,1.6),11.42,11.96,'TC_Optic',.21)
    model.prism('Up travel indicator',[(-14,278.4),(-8,285.1),(-2,278.4)],
                12.12,12.4,'TC_Index',.12)
    model.prism('Down travel indicator',[(2,284.3),(14,284.3),(8,277.6)],
                12.12,12.4,'TC_Support',.12)
    return model


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    for mat,data in fabrication.PALETTE.items():
        material=bpy.data.materials.new(mat)
        material.diffuse_color=(*data['color_linear'],1)
        material.metallic=data['metallic']
        material.roughness=data['roughness']
        fabrication.MATERIALS[mat]=material
    stock=source_meshes(TRAINING/'SM_TR_Door_inset_front_panel.fbx')[0]
    manifest=ROOT/'door_kit.json'
    if '--lift-only' in sys.argv:
        models=[lift_front(stock)]
        exports=json.loads(manifest.read_text(encoding='utf8'))['models']
    else:
        jamb=source_meshes(TRAINING/'SM_TR_Frame_North_jamb.fbx')[0]
        head=source_meshes(TRAINING/'SM_TR_Frame_upper_rail_housing.fbx')[0]
        models=[slide_leaf(-1,stock),slide_leaf(1,stock),portal(jamb,head),
                omen(-1),omen(1),lift_front(stock)]
        exports={}
    for model in models:
        if 'Leaf' in model.name:
            fit_prompt_clearance(model)
        data=model.export()
        data['fbx']=model.name+'.fbx'
        exports[model.name]=data
    slots={slot:'/Game/Environment/Chapter1/TemporalCalibration/Materials/MI_'+slot
           for data in exports.values() for slot in data['slots']}
    slots['TC_Pilot']='/Game/Environment/Chapter1/CentralHall/Environment/Materials/MI_HallStatusLens'
    manifest.write_text(json.dumps({'material_slots':slots,'models':exports},
                                   ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print({name:(data['triangles'],data['bounds_cm']) for name,data in exports.items()})


if __name__=='__main__':
    main()
