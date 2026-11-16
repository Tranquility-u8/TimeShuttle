"""Install the reusable leaf and casing art on the original Lab R17 door Blueprints."""

import json
from pathlib import Path
import sys

import unreal as u


ROOM = "/Game/Environment/LabR17/Blueprints/BP_LabRoomDoor"
OMEN = "/Game/Environment/LabR17/Blueprints/BP_LabOmenDoor"
CINEMATIC = "/Game/Blueprints/Cinematics/BP_CinematicLockedDoor"
ART_FN = "ConfigureDoorAppearance"
MESH = "/Script/Engine.StaticMesh"
MESH_COMPONENT = "/Script/Engine.StaticMeshComponent"
SCENE = "/Script/Engine.SceneComponent"
MATH = "/Script/Engine.KismetMathLibrary"
TOOLS = Path(__file__).resolve().parents[3] / "LabV39/R17/runtime_authoring/doors"
CATEGORY = "Lab Door|Appearance"
SIDES = ("Left", "Right")


def describe(path):
    value = json.loads(u.LabAuthoringLibrary.inspect_blueprint(path))
    assert value["ok"], path
    return value


def apply(path, **spec):
    options = dict(asset_path=path, allow_existing=True, compile=True, save=False, **spec)
    result = json.loads(u.LabAuthoringLibrary.apply_spec(json.dumps(options)))
    if not result["ok"] or result.get("compile_errors") != 0:
        raise RuntimeError((path, result.get("errors"), result.get("compile_messages")))
    return {"errors":result["compile_errors"], "warnings":result["compile_warnings"]}


def appearance_graph(builder):
    g = builder.Graph(ART_FN)
    g.node("entry", "entry", x=0, y=0)
    chain = ["entry"]

    def position(node, x, y):
        next(n for n in g.data["nodes"] if n["id"] == node).update(x=x, y=y)

    def target(component, call, x, y):
        var = g.get(component, "target_"+call)
        position(var, x, y+120)
        g.link(var, component, call, "self")

    for index, side in enumerate(SIDES):
        x = 360 + index*480
        component = "DoorDress"+side
        call = g.call("mesh"+side, "SetStaticMesh", MESH_COMPONENT)
        position(call, x, 0)
        target(component, call, x-170, 130)
        prop = "DoorDressMesh"+side
        node = g.get(prop)
        position(node, x-150, 110)
        g.link(node, prop, call, "NewMesh")
        chain.append(call)
    for index, direction in enumerate(("Positive","Negative")):
        x = 1500 + index*1380
        component = "DoorPortal"+direction
        call = g.call("fit"+direction,"SetRelativeScale3D",SCENE)
        position(call,x,0)
        target(component,call,x-120,30)
        # Mesh local X is aperture width, local Y is casing depth.
        size = g.call("size"+direction,"MakeVector",MATH,{"Y":"1"})
        position(size,x-180,300)
        for name, dimension, pin, y in (("DoorWidth",320,"X",310),("DoorHeight",380,"Z",460)):
            factor = g.call(name+direction,"Divide_DoubleDouble",MATH,{"B":str(dimension)})
            position(factor,x-495,y)
            var = g.get(name,"get"+name+direction)
            position(var,x-740,y+18)
            g.link(var,name,factor,"A")
            g.val(factor,size,pin)
        g.val(size,call,"NewScale3D")
        chain.append(call)
        offset = g.call("offset"+direction,"K2_SetRelativeLocation",SCENE,{"bSweep":"false","bTeleport":"true"})
        position(offset,x+420,0)
        target(component,offset,x+310,30)
        point = g.call("point"+direction,"MakeVector",MATH)
        position(point,x+170,320)
        prop = "DoorFrame"+direction+"Cm"
        value = g.get(prop)
        position(value,x-85,350)
        g.link(value,prop,point,"X")
        g.val(point,offset,"NewLocation")
        chain.append(offset)
    visible = g.call("showNegative","SetVisibility",SCENE,{"bPropagateToChildren":"false"})
    position(visible,4020,0)
    target("DoorPortalNegative",visible,3890,45)
    option = g.get("bShowDoorFrameNegative")
    position(option,3790,260)
    g.link(option,"bShowDoorFrameNegative",visible,"bNewVisibility")
    chain.append(visible)
    g.flow(*chain)
    for key,x,width,note in [
        ("skins",-50,1240,"Leaf art follows the sliding collision bodies. Subclasses select their leaf meshes."),
        ("positive",1280,1300,"Fit the positive wall face to its surveyed opening and face offset."),
        ("negative",2640,1560,"Fit the opposite wall face. Its casing can be hidden for an architectural surround.")]:
        g.node("section_"+key,"comment",text=note,x=x,y=-120,width=width,height=790,
               color="(R=0.05,G=0.12,B=0.14,A=1)")
    return g.data


def construction_calls(graph):
    """Follow the existing isolated construction wrapper before replacing its two original links."""
    byname = {n["name"]:n for n in graph["nodes"]}
    noncomments = [n for n in byname.values() if not n["class"].endswith("EdGraphNode_Comment")]
    entries = [n for n in noncomments if n["class"].endswith("K2Node_FunctionEntry")]
    assert len(entries)==1, "Unexpected door construction entry"
    node = entries[0]
    calls = []
    while True:
        pin = next(p for p in node["pins"] if p["direction"]=="out" and p["name"]=="then")
        if not pin["links"]:
            break
        assert len(pin["links"])==1 and pin["links"][0]["pin"]=="execute", "Construction flow changed"
        node = byname[pin["links"][0]["node"]]
        assert node["class"].endswith("K2Node_CallFunction") and node not in calls
        assert not any(p["links"] for p in node["pins"] if p["type"]!="exec")
        calls.append(node)
    assert len(noncomments)==1+len(calls), "Unexpected non-execution construction nodes"
    assert [n["function"] for n in calls] in (["ConfigureDoor","ApplyDoorPose"],
                                              ["ConfigureDoor","ApplyDoorPose",ART_FN]), "Door construction changed"
    return entries[0],calls


def construction_wrapper(builder, live):
    entry,calls = construction_calls(live)
    g = builder.Graph("UserConstructionScript")
    g.node("entry","entry",x=entry["x"],y=entry["y"])
    chain=["entry"]
    for i,n in enumerate(calls):
        g.node("original"+str(i),"call",function=n["function"],x=n["x"],y=n["y"])
        chain.append("original"+str(i))
    for i,n in enumerate(live["nodes"]):
        if n["class"].endswith("EdGraphNode_Comment"):
            original_spec=json.loads((TOOLS/"room_door_spec.json").read_text(encoding="utf-8"))
            authored=next(c for graph in original_spec["graphs"] if graph["name"]==live["name"]
                          for c in graph["nodes"] if c["kind"]=="comment")
            g.node("existingComment"+str(i),"comment",text=authored["text"],x=n["x"],y=n["y"],
                   width=authored["width"],height=authored["height"],color=authored["color"])
    right = max(n["x"] for n in calls)+510
    g.node("appearance","call",function=ART_FN,x=right,y=calls[-1]["y"])
    g.flow(*chain,"appearance")
    return g.data


def install(meshes):
    """Apply and compile three assets. The map and other Blueprints are never saved here."""
    # Share the door author's graph DSL without running its command-line generation.
    if str(TOOLS) not in sys.path:
        sys.path.insert(0,str(TOOLS))
    import build_door_specs as builder
    assets = {k:v.get_path_name() for k,v in meshes.items()}
    assert all(n in assets for n in ("SM_LabDoorPortal320", *["SM_LabDoor"+flavour+"Leaf"+s for flavour in ("","Omen") for s in SIDES]))
    before = describe(ROOM)
    graphs = {g["name"]:g for g in before["graphs"]}
    _,calls = construction_calls(graphs["UserConstructionScript"])
    has_call = any(c["function"]==ART_FN for c in calls)
    assert not has_call or ART_FN in graphs, "Construction refers to a missing appearance function"
    variables=[]
    components=[]
    room_defaults={}
    omen_defaults={}
    for side in SIDES:
        prop="DoorDressMesh"+side
        standard=assets["SM_LabDoorLeaf"+side]
        room_defaults[prop]={"object":standard}
        omen_defaults[prop]={"object":assets["SM_LabDoorOmenLeaf"+side]}
        variables.append(dict(name=prop,type="object",**{"class":MESH},default=standard,
                              category=CATEGORY,tooltip="Leaf finish shared by all doors of this class."))
        components.append(("DoorDress"+side,"Leaf"+side,standard,0))
    for sign,direction in ((1,"Positive"),(-1,"Negative")):
        prop="DoorFrame"+direction+"Cm"
        variables.append(dict(name=prop,type="double",default=sign*25,instance_editable=True,category=CATEGORY,
                              tooltip="Signed local X at the finished wall face, in centimetres."))
        components.append(("DoorPortal"+direction,"DefaultRoot",assets["SM_LabDoorPortal320"],sign*90))
    variables.append(dict(name="bShowDoorFrameNegative",type="bool",default=True,instance_editable=True,
                          category=CATEGORY,tooltip="Show the negative-X casing. Disable when a bespoke surround occupies that face."))
    scs=[]
    for name,parent,mesh,yaw in components:
        scs.append(dict(name=name,parent=parent,**{"class":MESH_COMPONENT},properties={
            "StaticMesh":{"object":mesh},"Mobility":"Movable","BodyInstance":'(CollisionProfileName="NoCollision",CollisionEnabled=NoCollision)',
            "bGenerateOverlapEvents":"false","bCanEverAffectNavigation":"false",
            "RelativeRotation":f"(Pitch=0,Yaw={yaw},Roll=0)"}))
    changes = [appearance_graph(builder)]
    if not has_call:
        changes.append(construction_wrapper(builder,graphs["UserConstructionScript"]))
    compiled = {ROOM:apply(ROOM,variables=variables,components=scs,graphs=changes,defaults=room_defaults)}
    compiled[OMEN]=apply(OMEN,defaults=omen_defaults)
    compiled[CINEMATIC]=apply(CINEMATIC)
    after = describe(ROOM)
    current = {g["name"]:g for g in after["graphs"]}
    for name,graph in graphs.items():
        if name not in (ART_FN,"UserConstructionScript"):
            assert graph==current[name], "Unrelated gameplay graph changed: "+name
    assert [n["function"] for n in construction_calls(current["UserConstructionScript"])[1]][-1]==ART_FN
    assert {s[0] for s in components}.issubset(c["name"] for c in after["components"])
    for path in (ROOM,OMEN,CINEMATIC):
        asset=u.load_asset(path)
        cdo=u.get_default_object(asset.generated_class())
        for side in SIDES:
            expected=assets["SM_LabDoor"+("Omen" if path==OMEN else "")+"Leaf"+side]
            mesh=cdo.get_editor_property("DoorDressMesh"+side)
            assert mesh and mesh.get_path_name()==expected, (path,side,mesh,expected)
        assert cdo.get_editor_property("bShowDoorFrameNegative") and cdo.get_editor_property("DoorFramePositiveCm")==25
    for path in compiled:
        assert u.EditorAssetLibrary.save_loaded_asset(u.load_asset(path),True),path
    return {"compile":compiled, "construction_calls":[n["function"] for n in construction_calls(current["UserConstructionScript"])[1]],
            "appearance_components":[s[0] for s in components]}
