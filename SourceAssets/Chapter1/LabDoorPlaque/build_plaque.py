"""Build the backed-glass lab plaque. Run with Blender in background mode.

Profiles below are given in millimetres. The origin is the wall-contact
surface; +X faces the corridor. Room lettering is supplied by the UE actor.
"""
import math
from pathlib import Path

import bpy


NAME = "SM_LabDoorPlaque"
OUTPUT = Path(__file__).resolve().parent / (NAME + ".fbx")
FINISHES = {
    # Linear reflectance RGB, metallic, roughness, clear coat.
    "FrameGraphite": ((0.038, 0.046, 0.049), 0.65, 0.34, 0.0),
    "SmokedGlass": ((0.013, 0.052, 0.056), 0.08, 0.19, 0.75),
    "PolishedGlassEdge": ((0.051, 0.193, 0.193), 0.08, 0.18, 0.4),
    "ClipAlloy": ((0.45, 0.47, 0.47), 0.84, 0.28, 0.0),
}


def perimeter(width, height, radius):
    y = width / 2 - radius
    z = height / 2 - radius
    profile = []
    for cy, cz, start in ((y, -z, -90), (y, z, 0), (-y, z, 90), (-y, -z, 180)):
        for i in range(5):
            angle = math.radians(start + 22.5 * i)
            profile.append((cy + radius * math.cos(angle), cz + radius * math.sin(angle)))
    return profile


def finish(name):
    color, metallic, roughness, coat = FINISHES[name]
    material = bpy.data.materials.new(name)
    material.diffuse_color = (*color, 1)
    material.use_nodes = True
    shader = material.node_tree.nodes.get("Principled BSDF")
    shader.inputs["Base Color"].default_value = (*color, 1)
    shader.inputs["Metallic"].default_value = metallic
    shader.inputs["Roughness"].default_value = roughness
    shader.inputs["Coat Weight"].default_value = coat
    shader.inputs["Coat Roughness"].default_value = 0.12
    return material


class Plaque:
    def __init__(self):
        self.vertices = []
        self.faces = []
        self.materials = []

    def face(self, indices, material):
        self.faces.append(tuple(indices))
        self.materials.append(material)

    def rings(self, profiles, band_finishes, back_finish, front_finish, center=(0, 0)):
        """Trace material bands on a rounded rectangle with a closed back."""
        first = len(self.vertices)
        for x, width, height, radius in profiles:
            contour = perimeter(width, height, radius)
            self.vertices.extend((x / 1000, (center[0] + y) / 1000, (center[1] + z) / 1000)
                                 for y, z in contour)
        count = len(contour)
        self.face(reversed(range(first, first + count)), back_finish)
        for band, material in enumerate(band_finishes):
            base = first + band * count
            for i in range(count):
                j = (i + 1) % count
                self.face((base + i, base + j, base + count + j, base + count + i), material)
        face_start = first + (len(profiles) - 1) * count
        self.face(range(face_start, face_start + count), front_finish)

    def clip(self, y, z):
        # A shallow tapered retaining shoe straddles the edge of the glass.
        self.rings(((15.52, 24.0, 18.5, 1.4), (17.98, 24.0, 18.5, 1.4)),
                   ("FrameGraphite",), "FrameGraphite", "FrameGraphite", (y, z))
        # Four sloping facets around a short ridge catch light from above.
        base = len(self.vertices)
        coords = [(x, y + dy, z + dz)
                  for x, xs, zs in ((17.99, 11.7, 8.9), (18.9, 11.35, 8.55))
                  for dy, dz in ((-xs, -zs), (xs, -zs), (xs, zs), (-xs, zs))]
        coords.extend(((20.9, y - 1.9, z), (20.9, y + 1.9, z)))
        self.vertices.extend(tuple(mm / 1000 for mm in vertex) for vertex in coords)
        for face in ((3, 2, 1, 0), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6),
                     (3, 0, 4, 7), (4, 5, 9, 8), (5, 6, 9), (6, 7, 8, 9), (7, 4, 8)):
            self.face((base + i for i in face), "ClipAlloy")

    def object(self):
        mesh = bpy.data.meshes.new(NAME)
        mesh.from_pydata(self.vertices, [], self.faces)
        assert not mesh.validate(), "Invalid geometry"
        mesh.update()
        slot_names = list(FINISHES)
        for name in slot_names:
            mesh.materials.append(finish(name))
        uv = mesh.uv_layers.new(name="Surface")
        for polygon, material in zip(mesh.polygons, self.materials, strict=True):
            polygon.material_index = slot_names.index(material)
            # An orthogonal projection per face keeps stretched side UVs off
            # the main printable plane. Materials have no texture dependencies.
            dominant = max(range(3), key=lambda index: abs(polygon.normal[index]))
            for i in polygon.loop_indices:
                x, y, z = mesh.vertices[mesh.loops[i].vertex_index].co
                uv.data[i].uv = (((y + .3) / .6, (z + .09) / .18),
                                 (x / .021, (z + .09) / .18),
                                 ((y + .3) / .6, x / .021))[dominant]
        obj = bpy.data.objects.new(NAME, mesh)
        bpy.context.collection.objects.link(obj)
        return obj


def build():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    plaque = Plaque()
    shell = ((0.0, 591, 171, 6.6), (1.7, 597, 177, 8), (4.5, 600, 180, 8.5),
             (13.8, 600, 180, 8.5), (17.4, 597, 177, 8.2), (18.0, 595, 175, 7.4),
             (18.0, 572, 152, 4.0), (17.0, 569.6, 149.6, 3.5),
             (13.7, 569.6, 149.6, 3.5))
    plaque.rings(shell, ["FrameGraphite"] * (len(shell) - 1), "FrameGraphite", "FrameGraphite")
    pane = ((13.72, 568.7, 148.7, 3.4), (14.6, 568.7, 148.7, 3.4),
            (15.5, 565.5, 145.5, 2.6))
    plaque.rings(pane, ["PolishedGlassEdge", "PolishedGlassEdge"], "SmokedGlass", "SmokedGlass")
    for y in (-277, 277):
        for z in (-68, 68):
            plaque.clip(y, z)
    obj = plaque.object()
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.context.view_layer.update()
    assert all(abs(value - target) < 1e-5 for value, target in zip(obj.dimensions, (.0209, .6, .18)))
    bpy.ops.export_scene.fbx(filepath=str(OUTPUT), use_selection=True, object_types={"MESH"},
                             axis_forward="-Y", axis_up="Z", apply_unit_scale=True,
                             apply_scale_options="FBX_SCALE_UNITS", use_triangles=True,
                             add_leaf_bones=False, bake_anim=False, mesh_smooth_type="FACE")
    obj.data.calc_loop_triangles()
    print(NAME, "triangles:", len(obj.data.loop_triangles), "material slots:", list(FINISHES))


if __name__ == "__main__":
    build()
