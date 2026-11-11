"""Blueprint graphs for the two collisionless, room-sized Chapter 1 wall finishes.

All dimensions below are in the imported meshes' local UE centimetres. The
owning level and visible component transform are resolved afresh on placement.
"""

MATH = "/Script/Engine.KismetMathLibrary"
SYSTEM = "/Script/Engine.KismetSystemLibrary"
STRING = "/Script/Engine.KismetStringLibrary"
MESH = "/Script/Engine.StaticMeshComponent"
SCENE = "/Script/Engine.SceneComponent"

# Paths are relative to the sign's current ULevel. Resolving a soft reference only
# visits objects already loaded. An unrelated level, mesh or wall side falls back to
# the actual collision face without loading an asset or enumerating scene actors.
ROOMS = (
    ("ArtMerge_StaticMeshActor_661", "SM_LabContainmentWallLinings"),
    ("StaticMeshActor_2468", "SM_TC_RoomLining"),
)


def apply_lining_casts(callback):
    """Let the K2 schema insert its standard pure Object -> StaticMeshComponent cast."""
    import unreal as u
    settings = u.get_default_object(u.load_class(None, "/Script/BlueprintGraph.BlueprintEditorSettings"))
    key = "bAutoCastObjectConnections"
    original = settings.get_editor_property(key)
    quiet = u.PropertyAccessChangeNotifyMode.NEVER
    try:
        settings.set_editor_property(key, True, notify_mode=quiet)
        return callback()
    finally:
        settings.set_editor_property(key, original, notify_mode=quiet)


def _pin(name, kind):
    return dict(name=name, type=kind) if kind != MESH else {"name": name, "type": "object", "class": MESH}


class _Graph:
    """Place K2 nodes by dependency column; values are (node id, output pin)."""
    def __init__(self, name, inputs, outputs, pure=False):
        self.spec = dict(name=name, kind="function", pure=pure, clear=True,
                         inputs=[_pin(*p) for p in inputs], outputs=[_pin(*p) for p in outputs],
                         nodes=[dict(id="entry", kind="entry", x=0, y=0)], links=[])
        self.columns = {"entry": 0}
        self.rows = {}

    def node(self, key, kind, args=None, **attributes):
        args = args or {}
        references = {k: v for k, v in args.items() if isinstance(v, tuple)}
        col = max((self.columns[source] for source, _ in references.values()), default=0) + 1
        row = self.rows.get(col, 0)
        self.rows[col] = row + 1
        self.columns[key] = col
        self.spec["nodes"].append(dict(id=key, kind=kind, x=col*320, y=row*176,
                                       defaults={k: v for k, v in args.items() if k not in references},
                                       **attributes))
        for pin, (source, out) in references.items():
            self.spec["links"].append([source, out, key, pin])
        return key, "ReturnValue"

    def call(graph, key, function, owner=MATH, **args):
        return graph.node(key, "call", args, **{"class": owner, "function": function})

    def result(self, **inputs):
        self.node("result", "result", inputs)
        return self.spec


def _height_profile():
    graph = _Graph("LiningPanelHeightProfile", [("Height", "float"), ("ParticleLab", "bool")],
                   [("PanelThickness", "float")], pure=True)
    height = ("entry", "Height")

    def band(key, lo, hi, value, elsewhere):
        inside = graph.call(key + "Height", "InRange_FloatFloat", Value=height, Min=lo, Max=hi)
        return graph.call(key, "SelectFloat", bPickA=inside, A=value, B=elsewhere)

    particle = band("KickPanel", 3, 25, 2.9, 2.1)
    particle = band("UpperPanel", 826, 857.2, 2.8, particle)
    particle = band("KickEdge", 23.2, 24.8, 3.3, particle)
    particle = band("UpperEdge", 822.7, 824.0, 3.15, particle)
    clock = band("ClockKick", 0, 19, 1.65, 1.85)
    clock = band("ClockKickEdge", 17.5, 18.5, 1.93, clock)
    clock = band("ClockTop", 815, 850, 1.65, clock)
    selection = graph.call("WhichRoom", "SelectFloat", bPickA=("entry", "ParticleLab"),
                           A=particle, B=clock)
    return graph.result(execute=("entry", "then"), PanelThickness=selection)


def _openings():
    graph = _Graph("IsLiningOpening", [("LocalPoint", "vector"), ("ParticleLab", "bool")],
                   [("Opening", "bool")], pure=True)
    # Thin boxes capture only the authored doorway/duct opening on its correct wall.
    # Construction collision can extend through a few of these openings.
    bounds = (
        (((-946.6,-58,478),(-946.6,98,648)), ((955,821,0),(955,1159,350)),
         ((955,-1018,84),(955,-676,400)), ((-135,1174.96,555),(83,1174.96,752))),
        (((-1143.75,718,-2),(-1143.75,962,341)), ((1042.5,-208,478),(1042.5,-52,648)),
         ((458,-985,-2),(782,-985,342)), ((-244,1025,464),(-36,1025,675))),
    )
    def vector(values):
        return ",".join(str(x) for x in values)
    room_tests = []
    for r, openings in enumerate(bounds):
        flags = []
        for i, (lo, hi) in enumerate(openings):
            center = vector([(a+b)/2 for a,b in zip(lo,hi)])
            extent = vector([max(4,(b-a)/2) for a,b in zip(lo,hi)])
            flags.append(graph.call(f"Opening{r}_{i}", "IsPointInBox", Point=("entry","LocalPoint"),
                                    BoxOrigin=center, BoxExtent=extent))
        a = graph.call(f"FirstPair{r}", "BooleanOR", A=flags[0], B=flags[1])
        b = graph.call(f"SecondPair{r}", "BooleanOR", A=flags[2], B=flags[3])
        room_tests.append(graph.call(f"AnyOpening{r}", "BooleanOR", A=a, B=b))
    lab = ("entry", "ParticleLab")
    opposite = graph.call("ClockRoom", "Not_PreBool", A=lab)
    first = graph.call("ParticleCutout", "BooleanAND", A=room_tests[0], B=lab)
    second = graph.call("ClockCutout", "BooleanAND", A=room_tests[1], B=opposite)
    combined = graph.call("OpeningFound", "BooleanOR", A=first, B=second)
    return graph.result(execute=("entry","then"), Opening=combined)


def _measure():
    graph = _Graph("MeasureLiningFace", [("Skin", MESH), ("ImpactPoint","vector"),
                                         ("Normal","vector"), ("ParticleLab","bool")],
                   [("Depth","float")])
    skin = ("entry","Skin")
    graph.call("Bounds", "GetLocalBounds", MESH, self=skin)
    summed = graph.call("BoundSum","Add_VectorVector", A=("Bounds","Max"), B=("Bounds","Min"))
    center = graph.call("Center","Multiply_VectorFloat", A=summed, B=.5)
    extent = graph.call("Extent","Subtract_VectorVector", A=("Bounds","Max"), B=center)
    frame = graph.call("Frame","K2_GetComponentToWorld", SCENE, self=skin)
    point = graph.call("LocalHit","InverseTransformLocation", T=frame, Location=("entry","ImpactPoint"))
    normal = graph.call("LocalNormal","InverseTransformDirection", T=frame, Direction=("entry","Normal"))
    axis = graph.call("FaceAxis","Vector_SnappedToGrid", InVect=normal, InGridSize=1)
    axis_abs = graph.call("AxisAbs","Vector_GetAbs", A=axis)
    # Distance from the actual collision to the backing face of the lining.
    to_mid = graph.call("ToCenter","Subtract_VectorVector", A=center, B=point)
    distance = graph.call("SignedDistance","Dot_VectorVector", A=to_mid, B=axis)
    support = graph.call("Support","Dot_VectorVector", A=extent, B=axis_abs)
    base = graph.call("Backing","Subtract_DoubleDouble", A=distance, B=support)
    nearby = graph.call("SamePlane","InRange_FloatFloat", Value=base, Min=-2.5, Max=2.5)
    pad = graph.call("Tolerance","Add_VectorVector", A=extent, B="3,3,0.05")
    fits = graph.call("InsideRoom","IsPointInBox", Point=point, BoxOrigin=center, BoxExtent=pad)
    axial = graph.call("Parallel","Dot_VectorVector", A=normal, B=axis)
    parallel = graph.call("SameNormal","NearlyEqual_FloatFloat", A=axial, B=1, ErrorTolerance=.001)
    face = graph.call("NearAndInside","BooleanAND", A=nearby, B=fits)
    face = graph.call("WallFace","BooleanAND", A=face, B=parallel)
    graph.call("Cutout","IsLiningOpening","", LocalPoint=point, ParticleLab=("entry","ParticleLab"))
    solid = graph.call("Solid","Not_PreBool", A=("Cutout","Opening"))
    face = graph.call("HasPanel","BooleanAND", A=face, B=solid)
    graph.call("Height","BreakVector", InVec=point)
    graph.call("Finish","LiningPanelHeightProfile","", Height=("Height","Z"), ParticleLab=("entry","ParticleLab"))
    depth = graph.call("Thickness","Add_DoubleDouble", A=base, B=("Finish","PanelThickness"))
    graph.call("FrameParts","BreakTransform", InTransform=frame)
    scale = graph.call("NormalScale","Dot_VectorVector", A=("FrameParts","Scale"), B=axis_abs)
    world_depth = graph.call("WorldDepth","Multiply_DoubleDouble", A=depth, B=scale)
    result = graph.call("FittedDepth","SelectFloat", bPickA=face, A=world_depth, B=0)
    return graph.result(execute=("entry","then"), Depth=result)


def _skin_depth():
    graph = _Graph("ReadLiningSurface", [("Skin", MESH), ("ExpectedMesh","string"), ("ParticleLab","bool"),
                                         ("ImpactPoint","vector"), ("Normal","vector")], [("Depth","float")])
    skin = ("entry","Skin")
    valid = graph.call("Exists","IsValid", SYSTEM, Object=skin)
    graph.node("IfPresent","branch", {"execute":("entry","then"), "Condition":valid})
    graph.node("Mesh","get", {"self":skin}, **{"variable":"StaticMesh","class":MESH})
    name = graph.call("MeshName","GetObjectName",SYSTEM,Object=("Mesh","StaticMesh"))
    matches = graph.call("Matches","EqualEqual_StrStr",STRING,A=name,B=("entry","ExpectedMesh"))
    visible = graph.call("Visible","IsVisible",SCENE,self=skin)
    matches = graph.call("VisibleLining","BooleanAND",A=matches,B=visible)
    graph.node("IfCorrect","branch", {"execute":("IfPresent","then"), "Condition":matches})
    graph.call("Measure","MeasureLiningFace","",execute=("IfCorrect","then"), Skin=skin,
               ImpactPoint=("entry","ImpactPoint"), Normal=("entry","Normal"),ParticleLab=("entry","ParticleLab"))
    # Return parameters are zero-initialized per invocation, so bypasses return zero.
    graph.result(execute=("Measure","then"), Depth=("Measure","Depth"))
    graph.spec["links"].extend([["IfPresent","else","result","execute"],["IfCorrect","else","result","execute"]])
    return graph.spec


def _resolve():
    graph = _Graph("GetWallLiningDepth",[("ImpactPoint","vector"),("Normal","vector")],[("Depth","float")])
    this = graph.node("Sign","self")
    outer = graph.call("Level","GetOuterObject", SYSTEM,Object=(this[0],"self"))
    path = graph.call("LevelPath","GetPathName", SYSTEM,Object=outer)
    previous = ("entry","then")
    depths = []
    for i, (name, expected) in enumerate(ROOMS):
        child = graph.call(f"ComponentPath{i}", "Concat_StrStr",STRING,A=path,B=f".{name}.StaticMeshComponent0")
        soft = graph.call(f"SoftPath{i}", "MakeSoftObjectPath",SYSTEM,PathString=child)
        ref = graph.call(f"Reference{i}", "Conv_SoftObjPathToSoftObjRef",SYSTEM,SoftObjectPath=soft)
        obj = graph.call(f"LoadedObject{i}", "Conv_SoftObjectReferenceToObject",SYSTEM,SoftObject=ref)
        key = f"Room{i}"
        graph.call(key, "ReadLiningSurface","", execute=previous, Skin=obj, ExpectedMesh=expected,
                   ParticleLab=i==0, ImpactPoint=("entry","ImpactPoint"), Normal=("entry","Normal"))
        depths.append((key,"Depth"))
        previous = key,"then"
    maximum = graph.call("MountedDepth", "FMax", A=depths[0], B=depths[1])
    return graph.result(execute=previous,Depth=maximum)


def get_lining_graphs():
    return [_height_profile(), _openings(), _measure(), _skin_depth(), _resolve()]
