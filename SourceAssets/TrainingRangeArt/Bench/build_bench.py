"""Build the A3 training counter modules. Blender centimetres; local -Y is the player face."""
import json
from pathlib import Path

import bpy


DEST = Path(__file__).resolve().parent
SLOTS = [
    ("M_TS_TrainingWhite", (0.72, 0.78, 0.81), 0.40, 0.25),
    ("M_TS_TrainingDarkMetal", (0.035, 0.053, 0.070), 0.32, 0.65),
    ("M_TS_TrainingRubber", (0.016, 0.023, 0.030), 0.82, 0.0),
    ("M_TS_TrainingCyan", (0.015, 0.58, 0.72), 0.25, 0.15),
]
WHITE, ALLOY, RUBBER, CYAN = range(4)
VARIANTS = {
    "SM_TS_A3_BenchSupport": False,
    "SM_TS_A3_BenchSupportLit": True,
}
ORDER = ["SupportLit" if i in (2,4,7,9) else "Support" for i in range(1,11)]


class Geometry:
    def __init__(self):
        self.vertices = []
        self.faces = []
        self.face_materials = []

    def face(self, indices, material):
        self.faces.append(tuple(indices))
        self.face_materials.append(material)

    def rings(self, rows, side_materials, first_material, last_material):
        """Closed shell. Rings are CCW looking down local Z (or the chosen extrusion axis)."""
        indices = []
        for row in rows:
            offset = len(self.vertices)
            self.vertices.extend(row)
            indices.append(list(range(offset, offset + len(row))))
        self.face(reversed(indices[0]), first_material)
        for lower, upper, material in zip(indices, indices[1:], side_materials):
            for i, v in enumerate(lower):
                j = (i + 1) % len(lower)
                self.face([v, lower[j], upper[j], upper[i]], material)
        self.face(indices[-1], last_material)

    def bevel_box(self, x, y, levels, materials, bottom, top):
        rows = []
        for z, half_x, half_y, chamfer in levels:
            c = chamfer
            outline = [(-half_x+c, -half_y), (half_x-c, -half_y),
                       (half_x, -half_y+c), (half_x, half_y-c),
                       (half_x-c, half_y), (-half_x+c, half_y),
                       (-half_x, half_y-c), (-half_x, -half_y+c)]
            rows.append([(x+dx, y+dy, z) for dx, dy in outline])
        self.rings(rows, materials, bottom, top)

    def badge(self, shape_xz, y_rear, y_front, material):
        # XZ winding gives a -Y normal; a rail front faces -Y.
        rows = [[(x, y, z) for x, z in shape_xz] for y in (y_rear, y_front)]
        self.rings(rows, [material], material, material)

    def finish(self, name, mats):
        mesh = bpy.data.meshes.new(name)
        mesh.from_pydata(self.vertices, [], self.faces)
        mesh.update()
        assert not mesh.validate(verbose=True)
        for m in mats:
            mesh.materials.append(m)
        for face, material in zip(mesh.polygons, self.face_materials):
            face.material_index = material
        obj = bpy.data.objects.new(name, mesh)
        bpy.context.collection.objects.link(obj)
        return obj


def make_segment(name, lit, mats):
    g = Geometry()
    # Rear skirt. The dark kick strip and its reveal are part of one watertight profile.
    g.bevel_box(0, 29, [
        (-0.50, 99.80, 7.60, 0.50), (6.6, 99.80, 7.60, 0.50),
        (7.4, 99.45, 6.60, 0.50), (8.8, 99.45, 6.60, 0.50),
        (9.6, 99.78, 7.70, 0.55), (94.8, 99.78, 7.70, 0.55),
        (96.0, 99.50, 7.00, 0.55)],
        [RUBBER, RUBBER, RUBBER, ALLOY, ALLOY, ALLOY], RUBBER, ALLOY)
    # A single solid white Y-shaped shoulder; the fixed S3 camera sees about five
    # of the ten supports. The rubber shoe keeps the ceramic clear of the floor.
    g.bevel_box(0, -30, [
        (-0.5, 10.0, 10.1, 0.90), (3.3, 10.0, 10.1, 0.90),
        (4.1, 9.45, 9.5, 0.65), (72.5, 9.45, 9.5, 0.65),
        (74.2, 9.7, 9.6, 0.70), (93.0, 21.2, 11.7, 1.1),
        (95.6, 22.0, 12.0, 1.10), (96.7, 21.8, 11.9, 1.10)],
        [RUBBER, RUBBER, WHITE, WHITE, WHITE, WHITE, WHITE], RUBBER, WHITE)
    # The top's X=+-100 limit occurs at a single ridge. Adjacent 2m modules meet along
    # that line instead of stacking coincident end faces.
    g.bevel_box(0, 0, [
        (95.3, 99.35, 46.60, 0.55), (96.3, 99.70, 48.10, 0.60),
        (97.3, 99.70, 48.10, 0.60), (98.4, 99.83, 49.25, 0.60),
        (100.55, 100.0, 50.0, 0.68), (100.93, 99.82, 49.87, 0.63),
        (101.52, 99.77, 49.67, 0.60), (103.70, 99.77, 49.52, 0.60),
        (104.15, 99.60, 49.30, 0.60)],
        [RUBBER, RUBBER, ALLOY, ALLOY, ALLOY, WHITE, ALLOY, ALLOY], ALLOY, ALLOY)
    # One full-height anti-slip working face per 2m segment. The bonded pad sinks
    # below its carrier; the contact surface for the native pistol remains exactly 105cm.
    g.bevel_box(0, 0, [
        (103.96, 99.43, 48.94, 1.55), (104.54, 99.43, 48.94, 1.55),
        (105.0, 99.05, 48.56, 1.40)], [RUBBER, RUBBER], RUBBER, RUBBER)
    if lit:
        # Short shielded locator centred on each of the four real refill slots.
        g.badge([(-7.0, 97.4), (7.0, 97.4), (10.4, 100.6), (-10.4, 100.6)],
                -47.7, -49.97, RUBBER)
        g.badge([(-4.8, 98.2), (4.8, 98.2), (6.4, 99.65), (-6.4, 99.65)],
                -49.85, -50.0, CYAN)
    else:
        # A pin-sized service diagnostic underneath retains the same material slots for all variants.
        g.badge([(-0.48, 92.1), (0.48, 92.1), (0.48, 92.8), (-0.48, 92.8)],
                21.40, 21.18, CYAN)
    obj = g.finish(name, mats)
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project(island_margin=0.018)
    bpy.ops.object.mode_set(mode='OBJECT')
    obj.data.uv_layers.active.name = 'UV0'
    obj.select_set(False)
    return obj


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.unit_settings.system = 'METRIC'
    scene.unit_settings.scale_length = 0.01
    bpy.context.preferences.filepaths.save_version = 0
    mats = []
    for name, rgb, rough, metal in SLOTS:
        material = bpy.data.materials.new(name)
        material.use_nodes = True
        material.diffuse_color = (*rgb, 1)
        shader = material.node_tree.nodes.get('Principled BSDF')
        shader.inputs['Base Color'].default_value = (*rgb, 1)
        shader.inputs['Roughness'].default_value = rough
        shader.inputs['Metallic'].default_value = metal
        if name.endswith('Cyan'):
            shader.inputs['Emission Color'].default_value = (*rgb, 1)
            shader.inputs['Emission Strength'].default_value = 1.1
        mats.append(material)

    for variant, lit in VARIANTS.items():
        obj = make_segment(variant, lit, mats)
        # LOD imports must contain the render mesh alone. The installer duplicates
        # the original UE mesh asset to preserve its existing box and body setup.
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        bpy.ops.export_scene.fbx(filepath=str(DEST/(variant+'.fbx')), use_selection=True,
            object_types={'MESH'}, global_scale=1, apply_unit_scale=True,
            apply_scale_options='FBX_SCALE_UNITS', axis_forward='-Y', axis_up='Z',
            use_mesh_modifiers=True, mesh_smooth_type='FACE', use_triangles=True,
            use_tspace=False, bake_anim=False, add_leaf_bones=False)
        obj.select_set(False)

    # Save an editable, assembled row. Each pair reruns the same mesh with shared data.
    original = {o.name:o for o in bpy.context.scene.objects if o.type=='MESH'}
    for i, suffix in enumerate(ORDER, start=1):
        model = original['SM_TS_A3_Bench' + suffix]
        instance = bpy.data.objects.new('Segment_%02d_%s' % (i, suffix), model.data)
        scene.collection.objects.link(instance)
        instance.location = (-1100 + i*200, 0, 0)
    for obj in original.values():
        bpy.data.objects.remove(obj, do_unlink=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(DEST/'TS_TrainingBench_A3.blend'))

    # Check the actual exported FBXs through Blender's importer, aligned with the source unit setting.
    report = {"modules": {}, "sequence": ["SM_TS_A3_Bench"+v for v in ORDER],
              "world_support_x_cm": list(range(-900,901,200)), "world_light_x_cm": [-700,-300,300,700],
              "pivot": [0,0,0], "source_front":"-Y", "ue_player_side":"+Y"}
    for name in VARIANTS:
        bpy.ops.wm.read_factory_settings(use_empty=True)
        bpy.context.scene.unit_settings.system = 'METRIC'
        bpy.context.scene.unit_settings.scale_length = 0.01
        bpy.ops.import_scene.fbx(filepath=str(DEST/(name+'.fbx')), use_custom_normals=True)
        obj = bpy.data.objects[name]
        mesh = obj.data
        mesh.calc_loop_triangles()
        co = [obj.matrix_world @ v.co for v in mesh.vertices]
        bounds = [[round(op(v[i] for v in co),3) for i in range(3)] for op in (min,max)]
        assert [o.name for o in bpy.context.scene.objects if o.type=="MESH"] == [name]
        assert bounds == [[-100.0,-50.0,-0.5],[100.0,50.0,105.0]], (name,bounds)
        materials = [mat.name for mat in mesh.materials]
        assert materials == [x[0] for x in SLOTS], (name,materials)
        assert len(mesh.uv_layers) == 1 and all(t.area>1e-5 for t in mesh.loop_triangles)
        by_slot = [sum(1 for t in mesh.loop_triangles if t.material_index == i) for i in range(len(materials))]
        report['modules'][name] = dict(bounds=bounds, collision_source="Original UE BodySetup", triangles=len(mesh.loop_triangles),
                                       triangles_by_slot=by_slot, material_slots=materials, uv=mesh.uv_layers[0].name)
    (DEST/'bench_manifest.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print('A3_TRAINING_BENCH_VERIFIED')


if __name__ == '__main__':
    main()
