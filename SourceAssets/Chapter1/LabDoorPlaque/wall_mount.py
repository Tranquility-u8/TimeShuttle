"""Standard runtime K2 nodes used by the plaque's editor construction script."""
from pathlib import Path
import runpy


MATH = "/Script/Engine.KismetMathLibrary"
SYSTEM = "/Script/Engine.KismetSystemLibrary"
GAME = "/Script/Engine.GameplayStatics"
ACTOR = "/Script/Engine.Actor"
PRIM = "/Script/Engine.PrimitiveComponent"
UP = "0,0,1"


class Graph:
    """Small notation for ordinary named UE nodes. Wires point to a node's output pin."""
    def __init__(self, name, inputs=(), outputs=(), pure=False):
        self.data = {"name": name, "kind": "function", "clear": True, "pure": pure,
                     "inputs": [{"name": n, "type": t} for n, t in inputs],
                     "outputs": [{"name": n, "type": t} for n, t in outputs],
                     "nodes": [], "links": []}
        self.node("entry", "entry", 0, 0)

    def node(self, key, kind, x, y, **props):
        self.data["nodes"].append(dict(id=key, kind=kind, x=x, y=y, **props))
        return key

    def wire(self, source, dest, pin):
        source_node, _, source_pin = source.partition(".")
        self.data["links"].append([source_node, source_pin or "ReturnValue", dest, pin])

    def call(self, key, owner, function, x, y, defaults=None, **wires):
        props = dict(function=function)
        if owner:
            props["class"] = owner
        if defaults:
            props["defaults"] = defaults
        self.node(key, "call", x, y, **props)
        for pin, source in wires.items():
            self.wire(source, key, pin)
        return key

    def maths(self, key, function, x, y, defaults=None, **wires):
        return self.call(key, MATH, function, x, y, defaults, **wires)

    def gate(self, key, x, y, before, condition):
        self.node(key, "branch", x, y)
        self.wire(before, key, "execute")
        self.wire(condition, key, "Condition")
        return key + ".then"

    def get(self, key, name, x, y):
        self.node(key, "get", x, y, variable=name)
        return key + "." + name

    def set(self, key, name, x, y, before, value):
        self.node(key, "set", x, y, variable=name)
        self.wire(before, key, "execute")
        self.wire(value, key, name)
        return key + ".then"

    def note(self, key, text, x, y, w, h):
        self.node(key, "comment", x, y, text=text, width=w, height=h, color="(R=0.025,G=0.105,B=0.105,A=1)")

    def trace(self, key, x, y, before, start, end):
        self.call(key, SYSTEM, "LineTraceSingle", x, y,
                  {"TraceChannel": "TraceTypeQuery1", "bIgnoreSelf": True, "bTraceComplex": False,
                   "DrawDebugType": "None"}, execute=before, Start=start, End=end)


def support():
    g = Graph("HasWallSurfaceAt", [("Point", "vector"), ("Normal", "vector")], [("Supported", "bool")])
    g.note("comment", "Confirm support on the same plane, including across adjacent wall sections.",
           -50, -90, 2200, 700)
    g.maths("step", "Multiply_VectorFloat", 220, 195, {"B": 5}, A="entry.Normal")
    g.maths("start", "Add_VectorVector", 530, 140, A="entry.Point", B="step")
    g.maths("end", "Subtract_VectorVector", 530, 365, A="entry.Point", B="step")
    g.trace("trace", 820, 0, "entry.then", "start", "end")
    g.call("hit", GAME, "BreakHitResult", 1135, 240, Hit="trace.OutHit")
    g.maths("direction", "Dot_VectorVector", 1390, 240, A="entry.Normal", B="hit.ImpactNormal")
    g.maths("aligned", "Greater_DoubleDouble", 1610, 240, {"B": .975}, A="direction")
    g.maths("offset", "Vector_Distance", 1390, 420, V1="entry.Point", V2="hit.ImpactPoint")
    g.maths("flush", "Less_DoubleDouble", 1610, 420, {"B": .85}, A="offset")
    g.maths("plane", "BooleanAND", 1820, 300, A="aligned", B="flush")
    g.maths("ok", "BooleanAND", 1820, 95, A="trace", B="plane")
    g.node("return", "result", 2050, 0)
    g.wire("trace.then", "return", "execute")
    g.wire("ok", "return", "Supported")
    return g.data


def classify():
    g = Graph("IsMountableWall", [("Owner", "object"), ("Surface", "object")], [("Allowed", "bool")], pure=True)
    g.data["inputs"][0]["class"] = ACTOR
    g.data["inputs"][1]["class"] = PRIM
    g.note("policy", "Allow fixed architecture and generic wall geometry. Skip registered lab props and moving doors.",
           -50, -95, 1750, 970)
    def tagged(key, tag, y):
        g.call(key, ACTOR, "ActorHasTag", 270, y, {"Tag": tag})
        g.wire("entry.Owner", key, "self")
        return key
    art1 = tagged("particle_art", "Chapter1Room1Art", 160)
    art2 = tagged("clock_art", "TemporalCalibrationArt", 340)
    g.maths("art", "BooleanOR", 535, 220, A=art1, B=art2)
    g.maths("not_art", "Not_PreBool", 825, 220, A="art")
    # All doorway headers and wall skins remain valid; exclude the project's
    # explicitly classified non-wall architecture when approached at its edge.
    floor = tagged("floor", "LabEditable.Kind:floor", 520)
    roof = tagged("roof", "LabEditable.Kind:roof", 700)
    g.maths("horizontal", "BooleanOR", 535, 510, A=floor, B=roof)
    g.maths("not_horizontal", "Not_PreBool", 825, 500, A="horizontal")
    g.maths("world", "BooleanAND", 1080, 310, A="not_art", B="not_horizontal")
    g.node("mobility", "get", 580, 715, variable="Mobility", **{"class": "/Script/Engine.SceneComponent"})
    g.wire("entry.Surface", "mobility", "self")
    g.maths("movable", "EqualEqual_ByteByte", 815, 710, {"B": 2}, A="mobility.Mobility")
    g.maths("fixed", "Not_PreBool", 1080, 700, A="movable")
    g.maths("allowed", "BooleanAND", 1310, 410, A="world", B="fixed")
    g.node("result", "result", 1510, 0)
    g.wire("entry.then", "result", "execute")
    g.wire("allowed", "result", "Allowed")
    return g.data


def probe():
    g = Graph("ProbeForPlaqueWall", [("Outward", "vector"), ("RecoverEmbedded", "bool")])
    g.note("search", "Trace inward from free space. A small lead-in also handles a pivot on the wall.",
           -40, -85, 1450, 760)
    g.call("origin", ACTOR, "K2_GetActorLocation", 220, 300)
    g.maths("lead", "Multiply_VectorFloat", 350, 150, A="entry.Outward", B="lead_length")
    g.maths("start", "Add_VectorVector", 540, 170, A="origin", B="lead")
    radius = g.get("radius", "WallSnapDistance", 30, 490)
    g.maths("range", "Multiply_DoubleDouble", 250, 505, {"B": 1.09}, A=radius)
    g.maths("outside", "Add_DoubleDouble", 240, 680, {"B": .25}, A="range")
    g.maths("lead_length", "SelectFloat", 60, 920, {"B": 4.0}, A="outside", bPickA="entry.RecoverEmbedded")
    g.maths("reach", "Multiply_VectorFloat", 525, 445, A="entry.Outward", B="range")
    g.maths("end", "Subtract_VectorVector", 775, 395, A="origin", B="reach")
    g.maths("ray_end", "SelectVector", 755, 630, A="origin", B="end", bPickA="entry.RecoverEmbedded")
    g.trace("trace", 840, 0, "entry.then", "start", "ray_end")
    hit = g.gate("blocked", 1190, 0, "trace.then", "trace")
    g.note("walls", "Accept a front-facing, near-vertical static architectural surface large enough for the plaque.",
           1450, -85, 1620, 1220)
    g.call("hit", GAME, "BreakHitResult", 1480, 150, Hit="trace.OutHit")
    g.maths("parts", "BreakVector", 1725, 100, InVec="hit.ImpactNormal")
    g.maths("absz", "Abs", 1930, 125, A="parts.Z")
    g.maths("wall", "LessEqual_DoubleDouble", 2110, 125, {"B": .12}, A="absz")
    g.maths("facing", "Dot_VectorVector", 1710, 365, A="hit.ImpactNormal", B="entry.Outward")
    g.maths("forward", "Greater_DoubleDouble", 1940, 360, {"B": .15}, A="facing")
    g.maths("normal", "Vector_Normal2D", 1720, 535, A="hit.ImpactNormal")
    g.maths("not_inside", "Not_PreBool", 1700, 710, A="hit.bInitialOverlap")
    g.call("classification", None, "IsMountableWall", 1700, 890, Owner="hit.HitActor", Surface="hit.HitComponent")
    g.call("bounds", SYSTEM, "GetComponentBounds", 1730, 1090, Component="hit.HitComponent")
    g.maths("extent", "BreakVector", 1960, 1050, InVec="bounds.BoxExtent")
    g.maths("height", "GreaterEqual_DoubleDouble", 2200, 970, {"B": 48}, A="extent.Z")
    g.maths("span", "FMax", 2200, 1110, A="extent.X", B="extent.Y")
    g.maths("broad", "GreaterEqual_DoubleDouble", 2410, 1110, {"B": 30}, A="span")
    g.maths("large", "BooleanAND", 2610, 940, A="height", B="broad")
    g.maths("vertical", "BooleanAND", 2390, 155, A="wall", B="forward")
    g.maths("solid", "BooleanAND", 2220, 740, A="classification.Allowed", B="not_inside")
    g.maths("geometry", "BooleanAND", 2640, 620, A="solid", B="large")
    g.maths("eligible", "BooleanAND", 2820, 300, A="geometry", B="vertical")
    valid = g.gate("candidate", 2870, 0, hit, "eligible")
    g.note("rank", "Rank by perpendicular distance. Preserve tangential placement and mounting height.",
           3160, -85, 1270, 780)
    g.call("pivot", ACTOR, "K2_GetActorLocation", 3190, 175)
    g.maths("foot", "ProjectPointOnToPlane", 3430, 155, Point="pivot", PlaneBase="hit.ImpactPoint",
            PlaneNormal="normal")
    g.maths("distance", "Vector_Distance", 3700, 160, V1="pivot", V2="foot")
    previous = g.get("previous", "BestMountDistance", 3435, 475)
    g.maths("limit", "Add_DoubleDouble", 3660, 475, {"B": -.015}, A=previous)
    g.maths("nearer", "Less_DoubleDouble", 3990, 175, A="distance", B="limit")
    candidate = g.gate("near", 4180, 0, valid, "nearer")
    recovering = g.gate("recovery", 4330, -430, candidate, "entry.RecoverEmbedded")
    g.note("interior", "On an inside-out recovery, reject a face beyond an intervening wall or air gap.",
           4360, -1510, 2510, 825)
    # From an embedded pivot this short segment stays in the wall. From outside
    # on the far side of a thin wall it hits the opposite face before reaching it.
    g.maths("inside_offset", "Multiply_VectorFloat", 4400, -1330, {"B": .10}, A="normal")
    g.maths("inside_face", "Subtract_VectorVector", 4650, -1270, A="foot", B="inside_offset")
    g.trace("backtrack", 4920, -1420, recovering, "pivot", "inside_face")
    g.call("barrier", GAME, "BreakHitResult", 5240, -1280, Hit="backtrack.OutHit")
    g.maths("same", "EqualEqual_ObjectObject", 5500, -1220, A="hit.HitComponent", B="barrier.HitComponent")
    g.maths("within", "BooleanAND", 5780, -1170, A="same", B="barrier.bInitialOverlap")
    g.maths("clear", "Not_PreBool", 5510, -930, A="backtrack")
    g.maths("unobstructed", "BooleanOR", 6030, -1100, A="within", B="clear")
    interior = g.gate("can_recover", 6290, -1420, "backtrack.then", "unobstructed")
    g.note("footprint", "Both diagonal corners require backing. This can span seams, but cannot bridge a doorway.",
           4500, -85, 1980, 1030)
    g.maths("side", "Cross_VectorVector", 4530, 185, {"A": UP}, B="normal")
    g.call("scale", ACTOR, "GetActorScale3D", 4520, 490)
    g.maths("abs_scale", "Vector_GetAbs", 4730, 540, A="scale")
    g.maths("axes", "BreakVector", 4940, 550, InVec="abs_scale")
    g.maths("half_width", "Multiply_DoubleDouble", 5160, 440, {"B": 27.5}, A="axes.Y")
    g.maths("w", "Multiply_VectorFloat", 5385, 285, A="side", B="half_width")
    g.maths("half_height", "Multiply_DoubleDouble", 5160, 735, {"B": 6.8}, A="axes.Z")
    g.maths("h", "Multiply_VectorFloat", 5390, 670, {"A": UP}, B="half_height")
    g.maths("diagonal", "Add_VectorVector", 5610, 470, A="w", B="h")
    g.maths("left", "Subtract_VectorVector", 5820, 280, A="foot", B="diagonal")
    g.maths("right", "Add_VectorVector", 5820, 630, A="foot", B="diagonal")
    g.call("check_left", None, "HasWallSurfaceAt", 4600, 0, execute="recovery.else", Point="left", Normal="normal")
    g.wire(interior, "check_left", "execute")
    left = g.gate("on_left", 4980, 0, "check_left.then", "check_left.Supported")
    g.call("check_right", None, "HasWallSurfaceAt", 5300, 0, execute=left, Point="right", Normal="normal")
    right = g.gate("on_right", 5690, 0, "check_right.then", "check_right.Supported")
    g.note("best", "Keep the closest supported plane for this placement pass.", 6550, -85, 1060, 600)
    g.maths("rotation", "MakeRotFromX", 6600, 270, X="normal")
    g.maths("pose", "MakeTransform", 6890, 270, Location="foot", Rotation="rotation")
    pose = g.set("save_pose", "BestMountPose", 6680, 0, right, "pose")
    g.set("save_distance", "BestMountDistance", 7130, 0, pose, "distance")
    return g.data


def search_directions():
    g = Graph("SearchPlaqueWallDirections", [("RecoverEmbedded", "bool")])
    g.note("rays", "Current facing breaks ties; eight horizontal rays cover arbitrary wall orientations.",
           -40, -85, 2980, 550)
    g.call("forward", ACTOR, "GetActorForwardVector", 230, 275)
    g.maths("forward_xy", "Vector_Normal2D", 445, 285, A="forward")
    directions = [None, "1,0,0", "-1,0,0", "0,1,0", "0,-1,0",
                  ".70710678,.70710678,0", "-.70710678,.70710678,0",
                  ".70710678,-.70710678,0", "-.70710678,-.70710678,0"]
    exec_pin = "entry.then"
    for i, direction in enumerate(directions):
        key = "ray" + str(i)
        g.call(key, None, "ProbeForPlaqueWall", 510 + i * 282, 0,
               {"Outward": direction} if direction else None, execute=exec_pin,
               RecoverEmbedded="entry.RecoverEmbedded", **({} if direction else {"Outward": "forward_xy"}))
        exec_pin = key + ".then"
    return g.data


def snap():
    g = Graph("SnapPlaqueToWall")
    g.note("scope", "Only solve placement in an authoring world. Saved poses are used directly in game.",
           -40, -85, 1610, 810)
    auto = g.get("auto", "AutoSnapToWall", 70, 160)
    g.call("instance", GAME, "GetGameInstance", 60, 340)
    g.call("play", SYSTEM, "IsValid", 310, 340, Object="instance")
    g.maths("editor", "Not_PreBool", 535, 340, A="play")
    g.maths("allowed", "BooleanAND", 765, 130, A=auto, B="editor")
    radius = g.get("radius", "WallSnapDistance", 100, 570)
    g.maths("positive", "Greater_DoubleDouble", 510, 570, {"B": 0.0}, A=radius)
    g.maths("enabled", "BooleanAND", 990, 200, A="allowed", B="positive")
    allowed = g.gate("test_scope", 1230, 0, "entry.then", "enabled")
    g.maths("initial", "Add_DoubleDouble", 1000, 505, {"B": .016}, A=radius)
    exec_pin = g.set("reset", "BestMountDistance", 1240, 430, allowed, "initial")
    g.note("sweep", "Prefer normal placement. Only look back from outside if every ordinary probe missed.",
           1670, -85, 2600, 620)
    g.call("primary", None, "SearchPlaqueWallDirections", 1810, 0, execute=exec_pin)
    prior = g.get("primary_best", "BestMountDistance", 2110, 310)
    g.maths("miss", "Greater_DoubleDouble", 2400, 290, A=prior, B=radius)
    missed = g.gate("retry", 2690, 0, "primary.then", "miss")
    g.call("embedded", None, "SearchPlaqueWallDirections", 3050, -20, {"RecoverEmbedded": True}, execute=missed)
    g.note("place", "Offset the back from the finished face and rotate local +X into the room.", 4350, -85, 1700, 850)
    best = g.get("best", "BestMountDistance", 4370, 130)
    limit = g.get("max_distance", "WallSnapDistance", 4370, 285)
    g.maths("found", "LessEqual_DoubleDouble", 4630, 155, A=best, B=limit)
    found = g.gate("commit", 4660, 0, "embedded.then", "found")
    g.wire("retry.else", "commit", "execute")
    pose = g.get("pose", "BestMountPose", 4340, 500)
    g.maths("plane", "BreakTransform", 4610, 480, InTransform=pose)
    g.maths("normal", "GetForwardVector", 4850, 650, InRot="plane.Rotation")
    g.call("finish", None, "GetWallLiningDepth", 4910, 0, execute=found, ImpactPoint="plane.Location", Normal="normal")
    g.maths("gap", "Add_DoubleDouble", 5190, 230, {"B": .15}, A="finish.Depth")
    g.maths("offset", "Multiply_VectorFloat", 5400, 365, A="normal", B="gap")
    g.maths("center", "Add_VectorVector", 5600, 420, A="plane.Location", B="offset")
    g.call("mount", ACTOR, "K2_SetActorLocationAndRotation", 5740, 0, {"bTeleport": True},
           execute="finish.then", NewLocation="center", NewRotation="plane.Rotation")
    return g.data


def variables():
    return [
        dict(name="AutoSnapToWall", type="bool", instance_editable=True, default="true", category="Wall Mount",
             tooltip="Align the back to a nearby wall when placed or released in the editor."),
        dict(name="WallSnapDistance", type="float", instance_editable=True, default="45", category="Wall Mount",
             tooltip="Maximum perpendicular distance to a wall, in centimeters."),
        dict(name="BestMountDistance", type="float", category="Wall Mount Internal"),
        dict(name="BestMountPose", type="transform", category="Wall Mount Internal"),
    ]


def graphs():
    lining = runpy.run_path(str(Path(__file__).with_name("wall_lining.py")))
    return [support(), classify(), probe(), search_directions(), *lining["get_lining_graphs"](), snap()]


def apply_graphs(callback):
    lining = runpy.run_path(str(Path(__file__).with_name("wall_lining.py")))
    return lining["apply_lining_casts"](callback)


def hook(construction):
    construction["nodes"].append(dict(id="snap_wall", kind="call", function="SnapPlaqueToWall", x=3650, y=0))
    construction["links"].append(["scale", "then", "snap_wall", "execute"])
