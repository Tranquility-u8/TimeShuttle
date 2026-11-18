"""Faceted leaf skins and flush under-gallery panels, dimensioned from C0 in UE cm."""
from pathlib import Path
import json
import runpy
import sys
import bpy

HERE=Path(__file__).resolve().parent
tools=runpy.run_path(str(HERE.parent/'OmenFront/build_omen_front.py'))
fabrication=tools['fabrication']
fabrication.ROOT=HERE
Asset=fabrication.Asset
rect=fabrication.rect
bpy.ops.wm.read_factory_settings(use_empty=True)
for name,data in fabrication.PALETTE.items():
    m=bpy.data.materials.new(name)
    m.diffuse_color=(*data['color_linear'],1)
    fabrication.MATERIALS[name]=m

def leaf(suffix,side):
    model=Asset('SM_CH_C0Leaf'+suffix)
    def outline(points):return [(side*(u-200),z-240) for u,z in points]
    # Each half moves with its own leaf. The paired inlays make a single gate motif when closed.
    shapes=[
        ('Outer leaf skin',[(1,4),(394,4),(394,477),(1,477)],0,1,'TC_Slate'),
        ('Inset dark reveal',[(2,47),(311,47),(364,95),(364,381),(310,437),(2,437)],1.15,2.65,'TC_Seal'),
        ('Milled edge',[(2,51),(310,51),(359,98),(359,378),(307,432),(2,432)],2.75,4.15,'TC_Brushed'),
        ('Recessed door face',[(2,59),(306,59),(351,101),(351,374),(304,424),(2,424)],4.25,6.8,'TC_Slate'),
        ('Lock cover',[(11,59),(39,59),(39,155),(13,180),(11,180)],7.,7.7,'TC_Graphite')]
    for name,shape,b,f,mat in shapes:
        model.prism(name,outline(shape),b,f,mat,.55)
    return model

def wings():
    model=Asset('SM_CH_C0LowerWallPanels')
    for side in (-1,1):
        def plate(name,points,back,front,mat):
            model.prism(name,[(side*u,z) for u,z in points],back,front,mat,.38)
        for a,b in [(477,765),(765,1080),(1080,1410),(1410,1720),(1720,1950)]:
            plate('Sealed panel backing',rect(a,b,2,497),.6,1.9,'TC_Graphite')
            plate('Lower formed panel',[(a+1.4,19),(b-1.4,19),(b-1.4,105),(a+1.4,105)],2.1,3.3,'TC_Support')
            plate('Main satin panel',[(a+1.4,106.8),(b-1.4,106.8),(b-1.4,444),(a+1.4,444)],2.1,4.2,'TC_Ceramic')
            plate('Head reveal',rect(a+1.4,b-1.4,445.5,496),2.1,3.7,'TC_Slate')
            for x in (a+9,b-9):
                for z in (114,435):
                    model.prism('Recessed fastener',fabrication.ellipse(side*x,z,1.4,1.4,6),4.3,4.6,'TC_Graphite')
        for a,b in [(1575,1640)]:
            plate('Low aisle light recess',rect(a-7,b+7,20,48,4),4.7,11,'TC_Seal')
            plate('Flush warm diffuser',rect(a,b,27.5,39.5,1.5),11.1,12,'TC_Pilot')
            plate('Overhanging hood',rect(a-6,b+6,40.4,48.4,2),11,16,'TC_Graphite')
    return model

def training_surround():
    model=Asset('SM_CH_TrainingLandingFrame')
    for side in (-1,1):
        # The original upper gate is 320 x 380 cm. All jambs sit outside its clear opening.
        for name,span,cap,depth,mat in [('Dark shadow gap',37,35,6,'TC_Seal'),('Folded frame',29,27,11,'TC_Ceramic'),('Alloy rebate',10,10,14,'TC_Brushed')]:
            outline=[(160.8,.6),(160+span,.6),(160+span,379),(129,380+cap),(0,380+cap),(0,381.1),(159.4,381.1),(160.8,379.4)]
            model.prism(name,[(side*u,z) for u,z in outline],depth-3,depth,mat,.4)
    model.prism('Door controller',rect(-188,-168,140,200,2),11.1,14,'TC_Seal',.5)
    model.prism('Gate state',rect(-183,-174,146,194,1),14.2,15.2,'TC_Optic',.3)
    return model

leaf_only = '--leaves-only' in sys.argv
exports=json.loads((HERE/'panels.json').read_text(encoding='utf8'))['models'] if leaf_only else {}
models=[leaf('Left',-1),leaf('Right',1)]
if not leaf_only:
    models.extend([wings(),training_surround()])
for model in models:
    for obj in model.objects:
        for v in obj.data.vertices:
            v.co.x*=-1
            v.co.y*=-1
            if model.name.startswith('SM_CH_C0Leaf'):
                # Mesh is attached at identity to C0's moving component. Bake
                # its inverse 90° yaw/nonuniform scale and the 8.9 cm setback.
                # Blender X/-Y/Z in metres corresponds to UE X/Y/Z in cm.
                bx,by,bz=v.co
                v.co=((-by-.089)/.16,bx/4,bz/4.8)
        obj.data.update()
    entry=model.export()
    entry['fbx']=model.name+'.fbx'
    exports[model.name]=entry
slots={s:'/Game/Environment/Chapter1/TemporalCalibration/Materials/MI_'+s for v in exports.values() for s in v['slots']}
slots['TC_Pilot']='/Game/Environment/Chapter1/CentralHall/Environment/Materials/M_HallWayfindingLenses'
(HERE/'panels.json').write_text(json.dumps({'models':exports,'material_slots':slots},indent=2),encoding='utf8')
