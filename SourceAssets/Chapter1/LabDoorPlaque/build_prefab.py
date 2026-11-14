"""Author the glazed doorway sign with the project's editor-only LabAuthoring helper (UE 5.6)."""
import json
import os
import runpy
from pathlib import Path

import unreal as u


ROOT = "/Game/Environment/Chapter1/LabDoorPlaque"
MESH = ROOT + "/SM_LabDoorPlaque"
BLUEPRINT = ROOT + "/BP_LabDoorPlaque"
FONT = ROOT + "/F_LabDoorLettering"
INK = ROOT + "/M_LabDoorLettering"
MATH = "/Script/Engine.KismetMathLibrary"
TEXT = "/Script/Engine.TextRenderComponent"
DEFAULT_NAME = "TEMPORAL\nCALIBRATION"


def existing(path):
    return u.load_asset(path) if u.EditorAssetLibrary.does_asset_exist(path) else None


def ensure_font(rebuild=False, font_file=None):
    font = existing(FONT)
    if font and not rebuild:
        return font
    input_face = Path(font_file) if font_file else Path(os.environ["WINDIR"]) / "Fonts" / "NotoSansSC-VF.ttf"
    if not input_face.is_file():
        raise RuntimeError("Install Noto Sans SC or specify its installed TTF using font_file.")
    factory = u.TrueTypeFontFactory()
    options = factory.get_editor_property("import_options")
    data = options.get_editor_property("data")
    # Include Latin and all 6,763 GB2312 ideographs. One offline atlas family is shared
    # by every placed actor, including in packaged games without system fonts.
    han = b"".join(bytes((row, col)) for row in range(0xB0, 0xF8) for col in range(0xA1, 0xFF))
    chars = "".join(chr(i) for i in range(32, 256)) + han.decode("gb2312", errors="ignore")
    for key, value in {
        "font_name": "Noto Sans SC", "enable_bold": False, "height": 52.0,
        "chars": chars + "，。：（）《》「」／－、",
        "include_ascii_range": True, "texture_page_width": 2048, "texture_page_max_height": 2048,
        "use_distance_field_alpha": False, "enable_antialiasing": True,
    }.items():
        data.set_editor_property(key, value)
    options.set_editor_property("data", data)
    tools = u.AssetToolsHelpers.get_asset_tools()
    if font:
        # Feed the existing package through the native TrueType factory. The factory bakes
        # its configured font family and preserves the original object path for references.
        factory.set_editor_property("formats", ["ttf;TrueType Font"])
        task = u.AssetImportTask()
        task.filename = str(input_face)
        task.destination_path = ROOT
        task.destination_name = "F_LabDoorLettering"
        task.factory = factory
        task.automated = True
        task.replace_existing = True
        tools.import_asset_tasks([task])
        objects = task.get_objects()
        assert len(objects) == 1 and objects[0].get_path_name() == FONT + ".F_LabDoorLettering"
        font = objects[0]
    else:
        font = tools.create_asset("F_LabDoorLettering", ROOT, u.Font, factory)
    assert font and font.get_editor_property("import_options").get_editor_property("height") == 52.0
    assert len(font.get_editor_property("characters")) > 6700, "Incomplete plaque font atlas"
    notice = (Path(__file__).resolve().parent / "FontLicense.txt").read_text(encoding="utf-8")
    u.EditorAssetLibrary.set_metadata_tag(font, "FontLicense", notice)
    assert u.EditorAssetLibrary.save_loaded_asset(font, False)
    return font


def ensure_ink(font):
    ink = existing(INK)
    if ink:
        return ink
    ink = u.AssetToolsHelpers.get_asset_tools().create_asset(
        "M_LabDoorLettering", ROOT, u.Material, u.MaterialFactoryNew()
    )
    assert ink
    ink.set_editor_property("blend_mode", u.BlendMode.BLEND_MASKED)
    ink.set_editor_property("opacity_mask_clip_value", 0.40)
    lib = u.MaterialEditingLibrary
    pigment = lib.create_material_expression(ink, u.MaterialExpressionConstant3Vector, -240, -100)
    pigment.set_editor_property("constant", u.LinearColor(0.89, 0.86, 0.74, 1))
    font_sample = lib.create_material_expression(ink, u.MaterialExpressionFontSampleParameter, -240, 80)
    font_sample.set_editor_property("parameter_name", "Glyphs")
    font_sample.set_editor_property("font", font)
    assert lib.connect_material_property(pigment, "", u.MaterialProperty.MP_BASE_COLOR)
    assert lib.connect_material_property(font_sample, "A", u.MaterialProperty.MP_OPACITY_MASK)
    lib.recompile_material(ink)
    assert u.EditorAssetLibrary.save_loaded_asset(ink, False)
    return ink


def call(key, owner, function, x, y, **defaults):
    return dict(id=key, kind="call", **{"class": owner}, function=function, x=x, y=y, defaults=defaults)


def comment(key, title, x, y, w, h):
    return dict(id=key, kind="comment", text=title, x=x, y=y, width=w, height=h,
                color="(R=0.025,G=0.105,B=0.105,A=1)")


def prefab_spec(font, ink, mesh):
    # TextRender measures in cm, with the horizontal reading direction along local -Y.
    # Normalise only the component scale: font size and local measurement stay invariant
    # on reconstruction, so repeated edits never compound the shrink factor.
    nodes = [
        comment("print", "Print this instance's room name on the glass", -48, -80, 1056, 448),
        dict(id="entry", kind="entry", x=0, y=0),
        dict(id="label", kind="get", variable="Lettering", x=0, y=145),
        call("font", TEXT, "SetFont", 250, 0, Value={"object": font.get_path_name()}),
        dict(id="name", kind="get", variable="RoomName", x=480, y=238),
        dict(id="label_text", kind="get", variable="Lettering", x=480, y=160),
        call("text", TEXT, "K2_SetText", 706, 0),
        comment("fit", "Fit the printed name within the glass, including manual line breaks",
                1056, -80, 2470, 520),
        dict(id="label_size", kind="get", variable="Lettering", x=1100, y=320),
        call("size", TEXT, "GetTextLocalSize", 1100, 160),
        call("ratios", MATH, "Divide_VectorVector", 1380, 160, B="1.0,50.8,12.3"),
        call("largest", MATH, "GetMaxElement", 1740, 160),
        call("limit", MATH, "FMax", 2050, 160, B="1.0"),
        call("inverse", MATH, "Divide_DoubleDouble", 2350, 160, A="1.0"),
        call("uniform", MATH, "Conv_DoubleToVector", 2650, 160),
        dict(id="label_scale", kind="get", variable="Lettering", x=2810, y=65),
        call("scale", "/Script/Engine.SceneComponent", "SetRelativeScale3D", 3180, 0),
    ]
    links = [
        ["entry", "then", "font", "execute"], ["label", "Lettering", "font", "self"],
        ["font", "then", "text", "execute"], ["label_text", "Lettering", "text", "self"],
        ["name", "RoomName", "text", "Value"], ["text", "then", "scale", "execute"],
        ["label_size", "Lettering", "size", "self"], ["size", "ReturnValue", "ratios", "A"],
        ["ratios", "ReturnValue", "largest", "A"], ["largest", "ReturnValue", "limit", "A"],
        ["limit", "ReturnValue", "inverse", "B"], ["inverse", "ReturnValue", "uniform", "InDouble"],
        ["uniform", "ReturnValue", "scale", "NewScale3D"], ["label_scale", "Lettering", "scale", "self"],
    ]
    spec = {
        "asset_path": BLUEPRINT, "parent_class": "/Script/Engine.Actor", "allow_existing": False,
        "variables": [dict(name="RoomName", type="text", instance_editable=True, category="Sign",
                           default='INVTEXT("TEMPORAL\\nCALIBRATION")',
                           tooltip="Name printed on this plaque. Use <br> for an optional line break. Long names scale to fit.")],
        "components": [
            {"name": "Plaque", "class": "/Script/Engine.StaticMeshComponent",
             "properties": {"StaticMesh": {"object": mesh.get_path_name()}, "bCanEverAffectNavigation": False,
                            "bGenerateOverlapEvents": False, "BodyInstance.CollisionProfileName": "NoCollision"}},
            {"name": "Lettering", "parent": "Plaque", "class": TEXT,
             "properties": {"Font": {"object": font.get_path_name()}, "TextMaterial": {"object": ink.get_path_name()},
                            "Text": 'INVTEXT("TEMPORAL\\nCALIBRATION")',
                            "RelativeLocation": "(X=1.60,Y=25.4,Z=0.35)", "WorldSize": 6.6,
                            "XScale": 1.12, "HorizSpacingAdjust": 3.5,
                            "VerticalAlignment": "EVRTA_TextCenter", "HorizontalAlignment": "EHTA_Left",
                            "CastShadow": False, "bCanEverAffectNavigation": False}},
        ],
        "graphs": [{"name": "UserConstructionScript", "kind": "function", "clear": True,
                    "nodes": nodes, "links": links}],
        "defaults": {"bActorEnableCollision": False, "PrimaryActorTick.bCanEverTick": False},
        "compile": True, "save": False,
    }
    mounting = runpy.run_path(str(Path(__file__).with_name("wall_mount.py")))
    mounting["hook"](spec["graphs"][0])
    spec["graphs"].extend(mounting["graphs"]())
    spec["variables"].extend(mounting["variables"]())
    return spec


def apply_checked(spec):
    mounting = runpy.run_path(str(Path(__file__).with_name("wall_mount.py")))
    raw = mounting["apply_graphs"](lambda: u.LabAuthoringLibrary.apply_spec(json.dumps(spec)))
    result = json.loads(raw)
    if not result.get("ok") or result.get("compile_errors") or result.get("compile_warnings"):
        raise RuntimeError(str((result.get("errors"), result.get("compile_messages"))))


def mounted_construction(current, authored):
    """Copy saved pin values and wires before extending the original printing chain."""
    nodes, links = [], []
    comments = iter(sorted((n for n in authored["nodes"] if n["kind"] == "comment"), key=lambda n: n["x"]))
    tail = None
    for original in sorted(current["nodes"], key=lambda n: (n["x"], n["y"])):
        name, kind = original["name"], original["class"].split(".")[-1]
        node = dict(id=name, x=original["x"], y=original["y"])
        if kind == "EdGraphNode_Comment":
            node = dict(next(comments), **node)
        elif kind == "K2Node_FunctionEntry":
            node["kind"] = "entry"
        elif kind == "K2Node_VariableGet":
            node.update(kind="get", variable=next(p["name"] for p in original["pins"] if p["direction"] == "out"))
        elif kind == "K2Node_CallFunction":
            node.update(kind="call", function=original["function"])
            node["class"] = original["function_owner"]
            if original["function"] == "SetRelativeScale3D":
                tail = node
        else:
            raise RuntimeError("The plaque's lettering graph contains a new node type: " + kind)
        for p in original["pins"]:
            if p["direction"] == "out":
                links.extend([name, p["name"], target["node"], target["pin"]] for target in p["links"])
            elif not p["hidden"] and not p["links"] and (p.get("object") or p["default"]):
                node.setdefault("defaults", {})[p["name"]] = (
                    {"object": p["object"]} if p.get("object") else p["default"])
        nodes.append(node)
    if not tail or any(link[:2] == [tail["id"], "then"] for link in links):
        raise RuntimeError("Cannot identify the end of the saved lettering construction script.")
    nodes.append(dict(id="snap_wall", kind="call", function="SnapPlaqueToWall", x=tail["x"]+470, y=tail["y"]))
    links.append([tail["id"], "then", "snap_wall", "execute"])
    return dict(name="UserConstructionScript", kind="function", clear=True, nodes=nodes, links=links)


def update_existing():
    """Install or refresh placement without rewriting the plaque templates, name or unrelated graphs."""
    bp = existing(BLUEPRINT)
    if not bp:
        return ensure_prefab()
    snapshot = json.loads(u.LabAuthoringLibrary.inspect_blueprint(BLUEPRINT))
    current = next(g for g in snapshot["graphs"] if g["name"] == "UserConstructionScript")
    spec = prefab_spec(existing(FONT), existing(INK), existing(MESH))
    spec.pop("components")
    spec.pop("defaults")
    known = {v["name"] for v in snapshot["variables"]}
    spec["variables"] = [v for v in spec["variables"] if v["name"] not in known]
    authored = spec["graphs"].pop(0)
    if not any(n.get("function") == "SnapPlaqueToWall" for n in current["nodes"]):
        spec["graphs"].insert(0, mounted_construction(current, authored))
    spec["allow_existing"] = True
    name = str(u.get_default_object(bp.generated_class()).get_editor_property("RoomName"))
    apply_checked(spec)
    assert str(u.get_default_object(bp.generated_class()).get_editor_property("RoomName")) == name
    bp.set_editor_property("run_construction_script_on_drag", False)
    assert u.EditorAssetLibrary.save_loaded_asset(bp, False), BLUEPRINT
    return bp


def ensure_prefab():
    mesh = existing(MESH)
    assert isinstance(mesh, u.StaticMesh), MESH
    bp = existing(BLUEPRINT)
    if bp:
        default = u.get_default_object(bp.generated_class())
        assert isinstance(bp, u.Blueprint) and default.get_editor_property("RoomName") is not None
        fields = json.loads(u.LabAuthoringLibrary.inspect_blueprint(BLUEPRINT))["variables"]
        return bp if any(v["name"] == "AutoSnapToWall" for v in fields) else update_existing()
    font = ensure_font()
    ink = ensure_ink(font)
    apply_checked(prefab_spec(font, ink, mesh))
    bp = u.load_asset(BLUEPRINT)
    default = u.get_default_object(bp.generated_class())
    assert str(default.get_editor_property("RoomName")) == DEFAULT_NAME, "Unexpected default room name"
    bp.set_editor_property("blueprint_description", "Glazed laboratory door plaque. Edit Room Name on each placed instance.")
    bp.set_editor_property("run_construction_script_on_drag", False)
    assert u.EditorAssetLibrary.save_loaded_asset(bp, False), BLUEPRINT
    return bp


if __name__ == "__main__":
    ensure_prefab()
