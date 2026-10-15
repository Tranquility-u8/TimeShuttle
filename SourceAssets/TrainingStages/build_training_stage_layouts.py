"""Build a Blender layout companion from the UE placement manifest, without editing UE."""
import bpy, json, math, hashlib
from pathlib import Path
from mathutils import Vector

SOURCE=Path(__file__).resolve().parent
OUTPUT=SOURCE.parents[1]/'Saved/Agent/TrainingStages/Assets'
manifest=json.loads((SOURCE/'layout_manifest.json').read_text(encoding='utf-8-sig'))
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.context.preferences.filepaths.save_version=0
scene=bpy.context.scene;scene.name='TrainingRoom_StageLayouts'
scene.unit_settings.system='METRIC';scene.unit_settings.scale_length=.01
with bpy.data.libraries.load(str(SOURCE/'TrainingStageProps.blend'),link=False) as (src,dst):
    dst.meshes=[name for name in src.meshes if name.startswith('SM_TS_')]
meshes={m.name:m for m in dst.meshes}
materials={m.name:m for m in bpy.data.materials}
stage_cols={}
for name in manifest['stages']+['SharedShooting']:
    c=bpy.data.collections.new(name);scene.collection.children.link(c);stage_cols[name]=c
architecture=bpy.data.collections.new('Architecture_Reference');scene.collection.children.link(architecture)
studio=bpy.data.collections.new('Preview_Cameras_Lights');scene.collection.children.link(studio)
issues=[];objects=[]

def mat(name,color,metal=.1,rough=.6,emission=0):
    m=bpy.data.materials.get(name) or bpy.data.materials.new(name);m.use_nodes=True;m.diffuse_color=color
    p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=color
    p.inputs['Metallic'].default_value=metal;p.inputs['Roughness'].default_value=rough
    p.inputs['Emission Color'].default_value=color;p.inputs['Emission Strength'].default_value=emission
    return m
floor_mat=mat('M_TS_LayoutFloor',(.18,.22,.25,1),.15,.66)
wall_mat=mat('M_TS_LayoutWall',(.65,.73,.76,1),.1,.55)
door_mat=mat('M_TS_LayoutDoor',(.08,.17,.22,1),.5,.32)
cyan=materials['M_TS_TrainingCyan'];dark=materials['M_TS_TrainingDarkMetal']

def relink(o,col):
    for c in list(o.users_collection):c.objects.unlink(o)
    col.objects.link(o)

def box(name,dims,loc,material,col=architecture,bevel=0):
    bpy.ops.mesh.primitive_cube_add(size=1,location=loc);o=bpy.context.object;o.name=name;o.dimensions=dims
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    if material:o.data.materials.append(material)
    if bevel:
        mod=o.modifiers.new('EdgeChamfer','BEVEL');mod.width=bevel;mod.segments=1
        bpy.ops.object.modifier_apply(modifier=mod.name)
    relink(o,col);return o

def thin_guide(name,loc,scale,material,col):
    # UE's small guide cubes are diagram markings, not physical obstacle geometry.
    dims=[s*100 for s in scale];axis=0 if dims[0]>=dims[1] else 1
    data=bpy.data.curves.new(name,'CURVE');data.dimensions='3D';data.resolution_u=1
    data.bevel_depth=max(.35,min(dims[1-axis],dims[2])/2);data.bevel_resolution=0
    spline=data.splines.new('POLY');spline.points.add(1)
    p0=[0,0,0];p1=[0,0,0];p0[axis]=-dims[axis]/2;p1[axis]=dims[axis]/2
    spline.points[0].co=(*p0,1);spline.points[1].co=(*p1,1)
    o=bpy.data.objects.new(name,data);col.objects.link(o);o.location=loc
    if material:data.materials.append(material)
    o['purpose']='Visual guide only; nonphysical, converted from UE guide cube.'
    return o

FRONT_FACING={'SM_TS_TrainingTarget','SM_TS_ArmoredTarget','SM_TS_ShooterProxy','SM_TS_MeleeProxy','SM_TS_SupplyTableSegment','SM_TS_AmmoPack'}
for a in manifest['actors']:
    key=a['mesh'].split('/')[-1];col=stage_cols[a['stage']]
    if a.get('collision')=='pawn_barrier':
        o=bpy.data.objects.new(a['id'],None);col.objects.link(o)
        o.empty_display_type='CUBE';o.empty_display_size=50;o.location=a['location_cm'];o.scale=a['scale']
        o.hide_render=True;o['purpose']='Invisible UE player barrier reference; not an architectural wall.'
    elif key=='Cube':
        if 'LinkToRockStem' in a['id']:
            bpy.ops.mesh.primitive_cylinder_add(vertices=8,radius=5,depth=7,location=a['location_cm'])
            o=bpy.context.object;o.name=a['id'];o.data.materials.append(dark);relink(o,col)
        else:
            o=thin_guide(a['id'],a['location_cm'],a['scale'],materials.get(a.get('material')),col)
    elif key in meshes:
        o=bpy.data.objects.new(a['id'],meshes[key]);col.objects.link(o)
        o.location=a['location_cm'];o.scale=a['scale']
        # The UE import uses the opposing Y face; recreate that visible orientation in Blender.
        o.rotation_euler[2]=math.radians(180+a['yaw'] if key in FRONT_FACING else a['yaw'])
    else:
        # This companion does not extract or duplicate existing UE-only weapon assets.
        o=bpy.data.objects.new(a['id'],None);col.objects.link(o)
        o.empty_display_type='ARROWS';o.empty_display_size=30;o.location=a['location_cm']
        o.hide_render=True;o['purpose']='UE asset placement reference; mesh is owned by the Unreal project.'
        issues.append({'id':a['id'],'note':'Existing UE pistol mesh is represented by a non-rendering placement marker.'})
    o['ue_actor_id']=a['id'];o['stage']=a['stage'];o['ue_folder']=a['folder'];o['ue_mesh_path']=a['mesh']
    o['ue_yaw_degrees']=a['yaw'];o['collision_intent']=a['collision'];objects.append(o)

# True interior footprint: X [-1000,1000], Y [-2270,1200], Z [0,800], 40 cm shell.
floor=box('Reference_Floor',(2080,3550,40),(0,-535,-20),floor_mat)
west=box('Reference_Wall_West',(40,3470,800),(-1020,-535,400),wall_mat)
east=box('Reference_Wall_East',(40,3470,800),(1020,-535,400),wall_mat)
far=box('Reference_Wall_Far',(2080,40,800),(0,-2290,400),wall_mat)
near_left=box('Reference_EntranceWall_Left',(940,40,800),(-530,1220,400),wall_mat)
near_right=box('Reference_EntranceWall_Right',(940,40,800),(530,1220,400),wall_mat)
lintel=box('Reference_EntranceWall_Lintel',(120,40,580),(0,1220,510),wall_mat)
door=box('Reference_DoorLeaf_Closed',(127,10,223),(0,1220,113.5),door_mat,bevel=1)
door['source']='Verified UE door bounds from root: 127 x 10 x 223 cm; closed center (0,1220,113.5).'
for x in [-66,66]:box('Reference_DoorFrame',(12,48,230),(x,1216,115),dark,bevel=1)
box('Reference_DoorFrame_Header',(144,48,12),(0,1216,230),dark,bevel=1)
for x in [-65,65]:box('Reference_DoorAccent',(3,1.5,205),(x,1191,115),cyan)
box('Reference_DoorAccent_Header',(125,1.5,3),(0,1191,225),cyan)
box('Reference_Threshold',(120,45,2),(0,1210,1),dark)
# Minimal wall-top light strips; no new architecture imported back into UE.
for x in [-995,995]:box('Reference_WallLight',(3,3450,4),(x,-535,745),cyan)
box('Reference_FarLight',(1990,3,4),(0,-2265,745),cyan)
ceiling=box('Reference_Ceiling',(2080,3550,40),(0,-535,820),wall_mat)
ceiling.hide_render=True;ceiling.hide_set(True)
architecture['purpose']='Simplified dimensional reference only. UE TrainingRoom geometry remains authoritative.'
architecture['door_clear_cm']=[120,220]
architecture['wall_thickness_cm']=40

# Each named View Layer shows its required stage set; S2C includes S2 and shared shooting is conditional.
layers={}
for i,stage in enumerate(manifest['stages']):
    vl=scene.view_layers[0] if i==0 else scene.view_layers.new(stage)
    vl.name=stage;layers[stage]=vl
    active={stage}
    if stage=='S2C':active.add('S2')
    if stage in manifest['shared_active_in']:active.add('SharedShooting')
    for child in vl.layer_collection.children:
        if child.name in stage_cols:child.exclude=child.name not in active
    vl['visible_stage_collections']=','.join(sorted(active))

scene.render.engine='CYCLES';scene.cycles.samples=32;scene.cycles.use_denoising=True
scene.render.resolution_x=1500;scene.render.resolution_y=1150;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG';scene.view_settings.view_transform='AgX'
scene.world=bpy.data.worlds.new('TrainingRoomPreviewWorld');scene.world.use_nodes=True
scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.24,.28,.34,1)
scene.world.node_tree.nodes['Background'].inputs[1].default_value=.45
for idx,(loc,power,size) in enumerate([((0,-400,1400),280000000,1700),((-1800,1500,1800),200000000,1700),((1000,-2200,1300),160000000,1500)]):
    data=bpy.data.lights.new(f'Preview_Area_{idx}','AREA');data.energy=power;data.shape='DISK';data.size=size
    o=bpy.data.objects.new(data.name,data);studio.objects.link(o);o.location=loc
    o.rotation_euler=(Vector((0,-535,0))-o.location).to_track_quat('-Z','Y').to_euler()
camdata=bpy.data.cameras.new('Preview_Overview');cam=bpy.data.objects.new('Preview_Overview',camdata);studio.objects.link(cam)
cam.location=(2850,3500,3250);target=Vector((0,-540,240))
cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler()
camdata.type='ORTHO';camdata.ortho_scale=4650;camdata.clip_start=1;camdata.clip_end=50000;scene.camera=cam

scene['layout_manifest']='layout_manifest.json'
scene['default_stage']='S1'
scene['readme']='Choose a View Layer named S1..S7B to display that stage and the correct shared props. All props live in separate Collections. Shell is dimensional reference only; UE level is authoritative.'
scene['stage_visibility_rule']='S2C includes S2. SharedShooting appears in S3/S4/S5/S6/S7A. S7B removes the shared table.'
scene['no_gameplay']='Static layouts only: no animations, AI, time changes, ammo refresh, or stage controller.'
readme=bpy.data.texts.new('README_StageLayouts')
readme.write('Time Shuttler training room — Blender layout companion\n\n'
 'Choose the stage in the View Layer dropdown (S1 is the default). Each stage has its own Collection; SharedShooting is separate. S2C includes S2; S3/S4/S5/S6/S7A include SharedShooting.\n\n'
 'All transforms originate from layout_manifest.json, measured in centimeters. Targets, people and counters face +Y toward the entrance. Actual Unreal imported geometry and level placement remain authoritative.\n\n'
 'Room clear dimensions: 2000 x 3470 x 800 cm. Entrance is (0,1200), door opening 120 x 220 cm, wall thickness 40 cm. Door leaf is a reference block matching measured bounds.\n\n'
 'Floor guides are thin nonphysical curves. The player barrier and existing UE-only pistol are non-rendering Empty reference objects. The ceiling is hidden for editing. No gameplay is implemented here.\n\n'
 'The preview PNG files use a cutaway of the near and east walls only; the saved source retains all full-height walls.\n')

# Render cutaway views with the front/east shell omitted solely for inspection.
cutaway=[east,near_left,near_right,lintel]+[o for o in architecture.objects if o.name.startswith('Reference_WallLight') and o.location.x>0]
for o in cutaway:o.hide_render=True
for stage in ['S1','S3','S7B']:
    for vl in scene.view_layers:vl.use=vl.name==stage
    bpy.context.window.view_layer=layers[stage]
    scene.render.filepath=str(OUTPUT/f'TrainingRoom_{stage}_Perspective.png')
    bpy.ops.render.render(write_still=True,layer=stage)
for o in cutaway:o.hide_render=False
for vl in scene.view_layers:vl.use=vl.name=='S1'
bpy.context.window.view_layer=layers['S1']
bpy.ops.object.select_all(action='DESELECT')
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type=='VIEW_3D':
            space=area.spaces.active;space.clip_end=100000
            space.region_3d.view_distance=4100;space.region_3d.view_location=(0,-535,240)
            space.region_3d.view_rotation=cam.rotation_euler.to_quaternion()
            space.region_3d.view_perspective='PERSP'
bpy.ops.wm.save_as_mainfile(filepath=str(SOURCE/'TrainingRoom_StageLayouts.blend'))
verification={'actor_count':len(objects),'manifest_actor_count':len(manifest['actors']),
 'stage_collection_counts':{k:len(c.objects) for k,c in stage_cols.items()},'default_view_layer':'S1',
 'visible_collections_per_stage':{k:v['visible_stage_collections'] for k,v in layers.items()},
 'room_clear_cm':manifest['room_clear_cm'],'entrance_cm':manifest['entrance_center_cm'],'door_clear_cm':[120,220],
 'wall_thickness_cm':40,'unresolved_external_meshes':issues,
 'manifest_sha256':hashlib.sha256((SOURCE/'layout_manifest.json').read_bytes()).hexdigest()}
(OUTPUT/'blender_layout_verification.json').write_text(json.dumps(verification,indent=2))
print('TRAINING_LAYOUT_BUILD_COMPLETE',json.dumps(verification))
