"""Original Time Shuttler training-stage blockout assets. Run with Blender --background.

All geometry is authored in centimeters, with local X width, Y depth, Z up.
Target fronts face -Y. Assets are static layout proxies, not gameplay actors.
"""
import bpy, math, json, random, hashlib
from pathlib import Path
from mathutils import Vector

SOURCE = Path(__file__).resolve().parent
PROJECT = SOURCE.parents[1]
OUTPUT = PROJECT / 'Saved/Agent/TrainingStages/Assets'
FBX = SOURCE / 'FBX'
PREVIEWS = OUTPUT / 'Previews'
for p in [OUTPUT, FBX, PREVIEWS]: p.mkdir(parents=True, exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.context.preferences.filepaths.save_version = 0
scene = bpy.context.scene
scene.unit_settings.system = 'METRIC'
scene.unit_settings.scale_length = 0.01
scene.render.engine = 'CYCLES'
scene.cycles.samples = 24
scene.cycles.use_denoising = True
scene.render.resolution_x = 720
scene.render.resolution_y = 600
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'PNG'
scene.view_settings.view_transform = 'AgX'
scene.world = bpy.data.worlds.new('TrainingAssetStudio')
scene.world.use_nodes = True
scene.world.node_tree.nodes['Background'].inputs[0].default_value = (0.22,0.26,0.32,1)
scene.world.node_tree.nodes['Background'].inputs[1].default_value = .35

MAT_SPEC = {
 'M_TS_TrainingWhite': {'base_color':[.72,.78,.81,1], 'roughness':.4,'metallic':.25,'emission':[0,0,0,1],'emission_strength':0},
 'M_TS_TrainingDarkMetal': {'base_color':[.035,.053,.07,1], 'roughness':.32,'metallic':.65,'emission':[0,0,0,1],'emission_strength':0},
 'M_TS_TrainingCyan': {'base_color':[.015,.58,.72,1], 'roughness':.25,'metallic':.15,'emission':[.015,.58,.72,1],'emission_strength':1.1},
 'M_TS_TrainingAmber': {'base_color':[.96,.29,.025,1], 'roughness':.4,'metallic':.18,'emission':[.96,.15,.01,1],'emission_strength':.16},
 'M_TS_TrainingWeakpoint': {'base_color':[1,.69,.025,1], 'roughness':.27,'metallic':.2,'emission':[1,.42,.005,1],'emission_strength':.6},
 'M_TS_TrainingRock': {'base_color':[.22,.255,.28,1], 'roughness':.92,'metallic':.03,'emission':[0,0,0,1],'emission_strength':0},
 'M_TS_TrainingRubber': {'base_color':[.016,.023,.03,1], 'roughness':.82,'metallic':0,'emission':[0,0,0,1],'emission_strength':0},
}
MATS = {}
for name, spec in MAT_SPEC.items():
    m=bpy.data.materials.new(name); m.use_nodes=True; m.diffuse_color=spec['base_color']
    p=m.node_tree.nodes.get('Principled BSDF')
    p.inputs['Base Color'].default_value=spec['base_color']
    p.inputs['Roughness'].default_value=spec['roughness']
    p.inputs['Metallic'].default_value=spec['metallic']
    p.inputs['Emission Color'].default_value=spec['emission']
    p.inputs['Emission Strength'].default_value=spec['emission_strength']
    MATS[name]=m
WHITE=MATS['M_TS_TrainingWhite']; DARK=MATS['M_TS_TrainingDarkMetal']
CYAN=MATS['M_TS_TrainingCyan']; AMBER=MATS['M_TS_TrainingAmber']
YELLOW=MATS['M_TS_TrainingWeakpoint']; ROCK=MATS['M_TS_TrainingRock']; RUBBER=MATS['M_TS_TrainingRubber']

PARTS=[]
def box(name, dims, loc, mat=WHITE, bevel=1):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    o=bpy.context.object; o.name=name; o.dimensions=dims
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    o.data.materials.append(mat)
    if bevel:
        mod=o.modifiers.new('SmallEdgeChamfer','BEVEL'); mod.width=bevel; mod.segments=1
        bpy.ops.object.modifier_apply(modifier=mod.name)
    PARTS.append(o);return o

def cyl(name, radius, depth, loc, mat=DARK, vertices=12, front=False):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=depth, location=loc)
    o=bpy.context.object;o.name=name
    if front: o.rotation_euler[0]=math.pi/2
    bpy.ops.object.transform_apply(location=False,rotation=True,scale=True)
    o.data.materials.append(mat);PARTS.append(o);return o

def bar(name,start,end,width,depth,mat=DARK):
    delta=Vector(end)-Vector(start)
    o=box(name,(width,depth,delta.length),(Vector(start)+Vector(end))/2,mat,.7)
    o.rotation_euler=delta.to_track_quat('Z','Y').to_euler()
    bpy.context.view_layer.objects.active=o
    bpy.ops.object.transform_apply(location=False,rotation=True,scale=True)
    return o

def finish(name, purpose, expected, collision='convex decomposition recommended'):
    bpy.ops.object.select_all(action='DESELECT')
    for p in PARTS:p.select_set(True)
    bpy.context.view_layer.objects.active=PARTS[0]
    bpy.ops.object.join();o=bpy.context.object;o.name=name;o.data.name=name
    scene.cursor.location=(0,0,0)
    bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
    # Ensure the exact bottom-center origin and a deterministic material-slot list.
    coords=[v.co.copy() for v in o.data.vertices]
    mn=Vector(tuple(min(v[i] for v in coords) for i in range(3)))
    mx=Vector(tuple(max(v[i] for v in coords) for i in range(3)))
    shift=Vector(((mn.x+mx.x)/2,(mn.y+mx.y)/2,mn.z))
    for v in o.data.vertices:v.co-=shift
    o.data.update()
    bpy.context.view_layer.update()
    unique=[];old=list(o.data.materials)
    for m in old:
        if m not in unique:unique.append(m)
    remap={i:unique.index(m) for i,m in enumerate(old)}
    inds=[remap[p.material_index] for p in o.data.polygons]
    o.data.materials.clear()
    for m in unique:o.data.materials.append(m)
    for p,i in zip(o.data.polygons,inds):p.material_index=i
    dims=[round(v,4) for v in o.dimensions]
    if any(abs(a-b)>.05 for a,b in zip(dims,expected)):
        raise RuntimeError(f'{name} dimensions {dims} expected {expected}')
    bpy.ops.export_scene.fbx(filepath=str(FBX/(name+'.fbx')),use_selection=True,
        object_types={'MESH'},global_scale=1,apply_unit_scale=True,apply_scale_options='FBX_SCALE_UNITS',
        axis_forward='-Y',axis_up='Z',use_mesh_modifiers=True,mesh_smooth_type='FACE',
        use_tspace=False,bake_anim=False,add_leaf_bones=False,path_mode='AUTO')
    o.data.calc_loop_triangles()
    result={'name':name,'file':'FBX/'+name+'.fbx','dimensions_cm':dims,'pivot':'bottom_center',
        'front_axis':'-Y','vertices':len(o.data.vertices),'polygons':len(o.data.polygons),
        'triangles':len(o.data.loop_triangles),'material_slots':[m.name for m in unique],
        'purpose':purpose,'collision':collision}
    o['purpose']=purpose;o['front_axis']='-Y';o['static_layout_proxy']=True
    o.hide_render=True;o.hide_set(True)
    PARTS.clear();ASSETS.append((o,result));return o

ASSETS=[]
# 1. Solid modular supply counter. Full body blocks the player; no open table legs.
box('ClosedCounter',(198,98,94),(0,0,47),WHITE,2)
box('Top',(200,100,9),(0,0,100.5),DARK,1.5)
box('Foot',(198,98,6),(0,0,3),RUBBER,1)
box('FrontInset',(176,1.2,64),(0,-49.2,47),DARK,.5)
box('FrontCyan',(176,1.2,3),(0,-49.3,83),CYAN,.4)
box('FrontStripe',(8,1.2,64),(-80,-49.4,47),WHITE,.5)
finish('SM_TS_SupplyTableSegment','Solid modular supply barrier; two ends must seal against room walls.',(200,100,105),'single box')

# 2. Ammo pack with a closed case and an exposed row of brass cartridge silhouettes.
box('Case',(28,17.6,9),(0,0,4.5),DARK,.7)
box('FrontLabel',(19,.8,4.5),(0,-8.6,5.5),AMBER,.2)
box('RearLid',(28,5,3),(0,6.5,10.5),WHITE,.5)
for x in [-9,-4.5,0,4.5,9]:
    cyl('Round',1.5,3,(x,-1.5,10.5),YELLOW,8)
finish('SM_TS_AmmoPack','Static ammo pickup placeholder; refill/reload logic must be implemented separately.',(28,18,12),'single box')

def target_base(armored=False):
    box('Base',(60,37.6,7),(0,.2,3.5),DARK,1.6)
    box('BaseBand',(52,1,2),(0,-18.5,5),CYAN,.2)
    box('Pedestal',(10,12,68),(0,3,41),DARK,1)
    box('Hip',(30,18,19),(0,0,82.5),WHITE,2)
    box('Torso',(48,20,58),(0,0,121),WHITE,4)
    box('Neck',(11,12,7),(0,0,153.5),DARK,.8)
    box('Head',(26,20,28),(0,0,171),WHITE,3)
    box('FacePlate',(20,1.2,12),(0,-10.2,173),DARK,1)
    if armored:
        box('ChestArmor',(42,6,39),(0,-11,123.5),DARK,2)
        for x in [-25,25]:box('ShoulderArmor',(10,25,19),(x,0,141),DARK,2)
        for x in [-19,19]:box('BellyArmor',(10,4,15),(x,-10,99),DARK,1)
        cyl('WeakPointRing',11,3,(0,-15,130),AMBER,16,True)
        cyl('WeakPoint',7.5,3.4,(0,-16,130),YELLOW,16,True)
    else:
        cyl('TargetRing',16,2,(0,-11,123),DARK,20,True)
        cyl('TargetFace',13,2.6,(0,-11.5,123),AMBER,20,True)
        cyl('Bullseye',5,3,(0,-12,123),WHITE,16,True)

target_base()
finish('SM_TS_TrainingTarget','Stationary training target; static placement mesh, not damage/AI logic.',(60,38,185))
target_base(True)
finish('SM_TS_ArmoredTarget','Armored training target with a visible yellow chest weakpoint; static placement only.',(60,38,185))

def rock(name,dims,seed):
    random.seed(seed)
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2,radius=1,location=(0,0,0))
    o=bpy.context.object;o.name=name
    for v in o.data.vertices:
        v.co *= random.uniform(.79,1.21)
        v.co.x += .10*v.co.z
    mn=[min(v.co[i] for v in o.data.vertices) for i in range(3)]
    mx=[max(v.co[i] for v in o.data.vertices) for i in range(3)]
    for v in o.data.vertices:
        for i in range(3):v.co[i]=(v.co[i]-mn[i])/(mx[i]-mn[i])*dims[i] - (dims[i]/2 if i<2 else 0)
    o.data.materials.append(ROCK);PARTS.append(o)
    finish(name,'Low-poly suspended/falling rock; physics and time behavior are external.',dims,'convex hull')
rock('SM_TS_Rock_A',(130,120,135),17)
rock('SM_TS_Rock_B',(118,130,122),54)
rock('SM_TS_SuspendedRock',(340,240,150),99)

# Overhead gantry is intentionally separate from the breakable hanging link.
for x in [-280,280]:
    box('GantryFoot',(40,60,12),(x,0,6),DARK,2)
    box('GantryPillar',(23,36,560),(x,0,292),WHITE,2)
    box('PillarInset',(10,2,495),(x,-18,307.5),DARK,.7)
    box('PillarLight',(3,1.5,440),(x,-19.2,325),CYAN,.3)
    box('PillarBumper',(36,46,90),(x,0,57),DARK,2)
box('TopBeam',(600,52,35),(0,0,582.5),WHITE,2)
box('UndersideRail',(550,30,9),(0,0,560.5),DARK,1)
box('RailAmber',(150,1.6,5),(0,-26.2,580),AMBER,.4)
finish('SM_TS_Gantry','Six-meter overhead support frame; keep central opening free. Link is separate.',(600,60,600),'convex decomposition; do not use one bounding box')

box('LinkCore',(10,10,66),(0,0,35),DARK,.8)
for z in [6,35,64]:box('LinkCollar',(18,18,12),(0,0,z),AMBER,1.2)
box('LinkFrontMark',(5,1,28),(0,-5.5,35),YELLOW,.2)
finish('SM_TS_BreakableLink','Independent orange breakable connection; attach above suspended rock.',(18,18,70),'single box')

def cover(name,dims):
    x,y,z=dims
    box('CoverBody',(x,y-2,z-2),(0,0,(z-2)/2),WHITE,2.5)
    box('CoverFoot',(x-4,y-4,10),(0,0,5),RUBBER,1)
    box('CoverTop',(x-4,y-4,6),(0,0,z-3),DARK,1)
    for sign in [-1,1]:
        box('FaceInset',(x-20,1,30),(0,sign*(y/2-.7),z-32),DARK,.4)
        box('FaceCyan',(x-24,1,3),(0,sign*(y/2-.5),z-19),CYAN,.3)
    finish(name,'Closed solid cover; collision and gameplay height must be verified in Unreal.',dims,'single box')
cover('SM_TS_LowCover',(300,100,120))
cover('SM_TS_HighCover',(100,300,220))

def humanoid_base():
    box('ProxyFootPlate',(68,54,6),(0,0,3),DARK,1.5)
    for x in [-15,15]:
        box('Boot',(18,32,13),(x,-4,12.5),DARK,1.5)
        box('Leg',(17,19,67),(x,0,50.5),WHITE,2)
    box('Pelvis',(44,24,20),(0,0,91),DARK,2)
    box('Body',(50,28,48),(0,0,125),WHITE,3)
    box('ChestPlate',(39,4,29),(0,-15,128),DARK,2)
    box('ProxyChest',(25,1.5,4),(0,-17.5,134),AMBER,.3)
    box('Neck',(13,14,6),(0,0,152),DARK,.7)
    box('Head',(27,25,27),(0,0,169.5),WHITE,3)
    box('Visor',(22,2,10),(0,-12.6,173),AMBER,1)

humanoid_base()
bar('LeftUpperArm',(-29,0,143),(-37,-13,117),14,17,WHITE)
bar('LeftForearm',(-37,-13,117),(-6,-33,119),13,14,DARK)
bar('RightUpperArm',(29,0,143),(37,-11,122),14,17,WHITE)
bar('RightForearm',(37,-11,122),(8,-31,119),13,14,DARK)
box('RifleStock',(13,24,13),(7,-24,125),DARK,1)
box('RifleReceiver',(12,40,15),(5,-44,124),DARK,1)
box('RifleBarrel',(5,28,5),(5,-76,126),DARK,.5)
box('RifleAccent',(13,13,3),(5,-45,133),CYAN,.3)
box('RifleMagazine',(9,13,17),(5,-44,109),AMBER,.8)
# Proxy dimensions are measured rather than constrained to the base footprint.
coords=[p.matrix_world@v.co for p in PARTS for v in p.data.vertices]
proxy_dims=tuple(max(v[i] for v in coords)-min(v[i] for v in coords) for i in range(3))
finish('SM_TS_ShooterProxy','Static ranged-enemy layout proxy with rifle silhouette; no AI, animation or damage.',proxy_dims)

humanoid_base()
bar('LeftUpperArm',(-29,0,143),(-39,0,114),14,17,WHITE)
bar('LeftForearm',(-39,0,114),(-32,-10,91),13,14,DARK)
bar('RightUpperArm',(29,0,143),(42,-5,124),14,17,WHITE)
bar('RightForearm',(42,-5,124),(38,-21,111),13,14,DARK)
bar('BatonHandle',(38,-21,105),(43,-27,124),6,6,DARK)
bar('TrainingBaton',(43,-27,124),(54,-41,163),9,9,AMBER)
coords=[p.matrix_world@v.co for p in PARTS for v in p.data.vertices]
proxy_dims=tuple(max(v[i] for v in coords)-min(v[i] for v in coords) for i in range(3))
finish('SM_TS_MeleeProxy','Static melee-enemy layout proxy with short training baton; no AI or attacks.',proxy_dims)

manifest={'schema_version':1,'title':'Time Shuttler Training Stage Props','units':'centimeters',
 'geometry_axes':{'width':'X','depth':'Y','up':'Z','front':'-Y'},
 'fbx_export':{'axis_forward':'-Y','axis_up':'Z','apply_unit_scale':True,'apply_scale_options':'FBX_SCALE_UNITS','scene_scale_length':.01,'global_scale':1},
 'source_blend':'TrainingStageProps.blend','generator':'build_training_props.py',
 'provenance':'Original geometric models created for the Time Shuttler project; no third-party or generated-provider assets.',
 'notes':['Static layout mesh assets only. No AI, pickups, timers, stage sequencing, damage, melting, or time-system logic.','Gantry collision must retain its central opening.','Each FBX contains one mesh at origin with bottom-center pivot.'],
 'materials':MAT_SPEC,'assets':[item for _,item in ASSETS]}
for o,item in ASSETS:item['sha256']=hashlib.sha256((SOURCE/item['file']).read_bytes()).hexdigest()
(SOURCE/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')

# Render one neutral three-quarter studio frame per asset. Preview helpers never export.
bpy.ops.object.camera_add(location=(0,0,0));cam=bpy.context.object;cam.name='PreviewCamera';scene.camera=cam
cam.data.type='ORTHO';cam.data.lens=50;cam.data.clip_end=100000
lights=[]
for name,loc,power,size in [('Key',(450,-500,800),24000000,600),('Fill',(-450,-100,400),12000000,500),('Rim',(50,600,700),20000000,450)]:
    data=bpy.data.lights.new(name,'AREA');data.energy=power;data.shape='DISK';data.size=size
    obj=bpy.data.objects.new(name,data);scene.collection.objects.link(obj);obj.location=loc
    obj.rotation_euler=(Vector((0,0,150))-obj.location).to_track_quat('-Z','Y').to_euler();lights.append(obj)
bpy.ops.mesh.primitive_plane_add(size=200000,location=(0,0,-.15));floor=bpy.context.object;floor.name='PreviewGround'
ground=bpy.data.materials.new('PreviewGroundMaterial');ground.diffuse_color=(.055,.07,.09,1);floor.data.materials.append(ground)

for o,item in ASSETS:
    o.hide_render=False;o.hide_set(False)
    dims=Vector(item['dimensions_cm']);size=max(dims);target=Vector((0,0,dims.z*.48))
    cam.location=target+Vector((.9,-1.6,1.05))*size
    cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler()
    cam.data.ortho_scale=size*1.48
    scene.render.filepath=str(PREVIEWS/(o.name+'.png'))
    bpy.ops.render.render(write_still=True)
    o.hide_render=True;o.hide_set(True)

# Readable editable source library: arranged in rows, with each object's local bottom pivot retained.
for i,(o,item) in enumerate(ASSETS):
    o.location=((i%4)*750,(i//4)*800,0);o.hide_render=False;o.hide_set(False)
for o in [cam,floor]+lights:bpy.data.objects.remove(o,do_unlink=True)
bpy.ops.object.select_all(action='DESELECT')
ASSETS[0][0].select_set(True);bpy.context.view_layer.objects.active=ASSETS[0][0]
bpy.ops.wm.save_as_mainfile(filepath=str(SOURCE/'TrainingStageProps.blend'))
print('TRAINING_ASSET_BUILD_COMPLETE',json.dumps({'asset_count':len(ASSETS),'total_triangles':sum(i['triangles'] for _,i in ASSETS)}))
