"""Pure-Python manifest validation; deliberately independent of Unreal."""
import hashlib
import json
import math
import re
from pathlib import Path

SCHEMA_VERSION = 1
COLLISIONS = {"complex", "box", "convex", "custom", "none"}


class BridgeError(RuntimeError):
    pass


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                                     separators=(",", ":")).encode("utf-8")).hexdigest()


def token(value, length=24):
    """A name is presentation; stable IDs, not renamed labels, determine paths."""
    return hashlib.sha256(str(value).encode("utf-8")).hexdigest()[:length]


def package_path(value, label="package path"):
    if not isinstance(value, str) or not re.fullmatch(r"/Game(?:/[A-Za-z0-9_]+)+", value):
        raise BridgeError(f"Invalid {label}: {value!r}; use a /Game/ English asset path.")
    return value


def _vector(value, size, label):
    if not isinstance(value, (list, tuple)) or len(value) != size:
        raise BridgeError(f"{label} must contain {size} numbers")
    if any(isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v)
           for v in value):
        raise BridgeError(f"{label} contains a non-finite or nonnumeric value")


def read_manifest(manifest_path):
    path = Path(manifest_path).expanduser().resolve()
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError) as error:
        raise BridgeError(f"Cannot read complete manifest {path}: {error}") from error
    if not isinstance(data, dict) or data.get("schema_version") != SCHEMA_VERSION:
        raise BridgeError("SceneBridge requires manifest schema_version 1")
    if data.get("complete") is not True:
        raise BridgeError("Refusing a partial snapshot: complete must be true")
    if data.get("unit") != "cm":
        raise BridgeError("Manifest actor transforms must already be in UE centimeters")
    for field in ("scene_id", "scene_name"):
        if not isinstance(data.get(field), str) or not data[field].strip():
            raise BridgeError(f"Missing manifest {field}")
    if isinstance(data.get("revision"), bool) or not isinstance(data.get("revision"), (str, int)):
        raise BridgeError("revision must be a string or an integer")
    if len(data["scene_id"]) > 128 or any(c in data["scene_id"] for c in "\r\n"):
        raise BridgeError("scene_id is too long or contains line breaks")
    if not isinstance(data.get("objects"), list):
        raise BridgeError("objects must be a complete list (empty is permitted)")
    ids, meshes = set(), {}
    for obj in data["objects"]:
        if not isinstance(obj, dict):
            raise BridgeError("Each object must be a dictionary")
        is_mesh = obj.get("object_type", "MESH") == "MESH"
        if obj.get("object_type", "MESH") not in {"MESH", "EMPTY"}:
            raise BridgeError("Supported object_type values are MESH and EMPTY")
        required = ("id", "name", "transform_hash")
        if is_mesh:
            required += ("mesh_id", "geometry_hash", "material_hash", "fbx")
        for field in required:
            if not isinstance(obj.get(field), str) or not obj[field]:
                raise BridgeError(f"Invalid {field} on object {obj.get('id', '?')}")
        oid = obj["id"]
        if oid in ids or len(oid) > 128 or any(c in oid for c in "\r\n"):
            raise BridgeError(f"Duplicate or invalid object ID: {oid}")
        ids.add(oid)
        _vector(obj.get("location"), 3, f"{oid}.location")
        _vector(obj.get("quaternion"), 4, f"{oid}.quaternion")
        _vector(obj.get("scale"), 3, f"{oid}.scale")
        norm = math.sqrt(sum(v * v for v in obj["quaternion"]))
        if abs(norm - 1.0) > 0.001:
            raise BridgeError(f"{oid}: quaternion must be normalized")
        if min(abs(v) for v in obj["scale"]) < 1e-8:
            raise BridgeError(f"{oid}: zero scale cannot produce reliable collision")
        if obj.get("collision", "complex") not in COLLISIONS:
            raise BridgeError(f"{oid}: unknown collision policy")
        obj.setdefault("collision", "complex")
        obj.setdefault("collision_profile", "BlockAll")
        if not isinstance(obj["collision_profile"], str) or not obj["collision_profile"]:
            raise BridgeError(f"{oid}: collision_profile must be a preset name")
        if is_mesh:
            rel = Path(obj["fbx"])
            resolved = (path.parent / rel).resolve()
            if rel.is_absolute() or path.parent not in resolved.parents or resolved.suffix.lower() != ".fbx":
                raise BridgeError(f"{oid}: FBX must be inside the manifest export folder")
            if not resolved.is_file():
                raise BridgeError(f"{oid}: missing FBX {resolved}")
            obj["_fbx_path"] = str(resolved)
        else:
            if obj.get("mesh_id") is not None or obj.get("fbx") is not None:
                raise BridgeError(f"{oid}: EMPTY cannot have a mesh_id or FBX")
            obj["mesh_id"] = None
            obj["geometry_hash"] = obj["material_hash"] = ""
            obj["collision"] = "none"
        materials = obj.get("materials", [])
        if not isinstance(materials, list):
            raise BridgeError(f"{oid}: materials must be a list")
        for mat in materials:
            if not isinstance(mat, dict):
                raise BridgeError(f"{oid}: invalid material")
            _vector(mat.get("base_color", [0.7, 0.7, 0.7, 1]), 4, f"{oid}.base_color")
            for field, default in (("roughness", .8), ("metallic", 0)):
                value = mat.get(field, default)
                if not isinstance(value, (int, float)) or not math.isfinite(value) or not 0 <= value <= 1:
                    raise BridgeError(f"{oid}: material {field} must be 0..1")
        if is_mesh:
            asset_signature = (obj["geometry_hash"], obj["material_hash"], obj["collision"],
                               obj.get("collision_options", {}), obj.get("collision_hash"), obj["fbx"])
            if obj["mesh_id"] in meshes and meshes[obj["mesh_id"]] != asset_signature:
                raise BridgeError(f"Shared mesh_id has inconsistent geometry/material/collision: {obj['mesh_id']}")
            meshes[obj["mesh_id"]] = asset_signature
    for obj in data["objects"]:
        pid = obj.get("parent_id")
        if pid is not None and pid not in ids:
            raise BridgeError(f"{obj['id']}: parent_id {pid} is absent from the snapshot")
        seen, cursor = {obj["id"]}, pid
        parents = {o["id"]: o.get("parent_id") for o in data["objects"]}
        while cursor is not None:
            if cursor in seen:
                raise BridgeError(f"Parent cycle involving {obj['id']}")
            seen.add(cursor)
            cursor = parents[cursor]
    return path, data


def object_fingerprint(obj):
    return digest({k: v for k, v in obj.items() if not k.startswith("_")})


def asset_signature(obj):
    return digest({"geometry": obj["geometry_hash"], "collision": obj["collision"],
                   "options": obj.get("collision_options", {}), "collision_hash": obj.get("collision_hash")})


def transforms_close(a, b, position_tolerance=.02, scale_tolerance=.0001):
    if not a or not b:
        return False
    if max(abs(x-y) for x, y in zip(a["location"], b["location"])) > position_tolerance:
        return False
    if max(abs(x-y) for x, y in zip(a["scale"], b["scale"])) > scale_tolerance:
        return False
    # q and -q are the same orientation.
    return abs(sum(x*y for x, y in zip(a["quaternion"], b["quaternion"]))) >= .999999
