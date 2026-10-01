"""Opt-in, editor-thread polling. Never mutates a PIE world or switches maps."""
import time
from pathlib import Path

import unreal

from .importer import (import_scene, is_playing, read_json, saved_root,
                       world_path, write_json)
from .schema import BridgeError, package_path

_HANDLE = None
_STARTUP_HANDLE = None
_LAST_POLL = 0.0
_LAST_STAMP = None
_STATUS = None
_CONFIG = None


def config_path():
    return saved_root() / "config.json"


def configure(manifest_path, target_map=None, asset_root="/Game/SceneBridge", **options):
    """Persist machine-local settings in Saved, never in tracked project files."""
    global _CONFIG, _LAST_STAMP
    path = Path(manifest_path).expanduser().resolve()
    if not path.is_file():
        raise BridgeError(f"Manifest does not exist: {path}")
    if target_map is not None:
        package_path(target_map, "target_map")
    package_path(asset_root, "asset_root")
    _CONFIG = {"manifest_path": str(path), "target_map": target_map,
               "asset_root": asset_root, "options": options,
               "poll_seconds": 1.0, "auto_start": False}
    write_json(config_path(), _CONFIG)
    _LAST_STAMP = None
    unreal.log("SceneBridge configuration saved. Use Sync once, then Watch to follow Blender snapshots.")
    return _CONFIG


def _config():
    config = read_json(config_path())
    if not config.get("manifest_path"):
        raise BridgeError("SceneBridge is not configured. Call scene_bridge.configure(manifest_path, target_map) once.")
    return config


def sync_configured(dry_run=False):
    global _LAST_STAMP
    config = _config()
    options = dict(config.get("options", {}))
    options["dry_run"] = bool(dry_run)
    report = import_scene(config["manifest_path"], config.get("target_map"),
                          config.get("asset_root", "/Game/SceneBridge"), options)
    if not dry_run:
        _LAST_STAMP = _stamp(config["manifest_path"])
    else:
        write_json(saved_root() / "preview.json", report)
        unreal.log("SceneBridge preview: " + str(report["plan"]["counts"]))
    return report


def _stamp(path):
    stat = Path(path).stat()
    return (stat.st_mtime_ns, stat.st_size)


def _status(status, detail=None):
    global _STATUS
    value = (status, detail)
    if value != _STATUS:
        _STATUS = value
        write_json(saved_root() / "watch-status.json", {"status": status, "detail": detail,
                                                       "time": time.time(), "running": _HANDLE is not None})
        unreal.log("SceneBridge Watch: " + status + (" — " + detail if detail else ""))


def _tick(delta):
    global _LAST_POLL, _LAST_STAMP
    now = time.monotonic()
    if now - _LAST_POLL < 1.0:
        return
    _LAST_POLL = now
    try:
        config = _config()
        stamp = _stamp(config["manifest_path"])
        if stamp == _LAST_STAMP:
            return
        if is_playing():
            _status("queued_until_PIE_finishes")
            return
        target = config.get("target_map")
        if not target:
            _status("paused", "Run Sync once and configure an explicit target map before Watch.")
            return
        if world_path() != target:
            _status("waiting_for_target_map", target)
            return
        _status("syncing")
        report = sync_configured()
        _LAST_STAMP = stamp
        _status("watching", str(report["status"]))
    except Exception as error:
        # Do not run a broken batch every second. A new atomic snapshot or an
        # explicit Sync/Watch request is the retry trigger.
        try:
            _LAST_STAMP = _stamp(_config()["manifest_path"])
        except Exception:
            pass
        _status("error", str(error))
        unreal.log_error("SceneBridge Watch paused this revision: " + str(error))


def start_watch():
    global _HANDLE, _LAST_STAMP, _LAST_POLL
    config = _config()
    config["auto_start"] = True
    write_json(config_path(), config)
    if _HANDLE is None:
        _HANDLE = unreal.register_slate_post_tick_callback(_tick)
    _LAST_STAMP = None
    _LAST_POLL = 0.0
    _status("watching")
    return {"watching": True}


def stop_watch():
    global _HANDLE
    if _HANDLE is not None:
        unreal.unregister_slate_post_tick_callback(_HANDLE)
        _HANDLE = None
    config = read_json(config_path())
    if config.get("manifest_path"):
        config["auto_start"] = False
        write_json(config_path(), config)
    _status("stopped")
    return {"watching": False}


def _menus():
    menus = unreal.ToolMenus.get()
    parent = menus.find_menu("LevelEditor.MainMenu.Tools")
    if parent is None:
        return False
    submenu = parent.add_sub_menu("SceneBridge", "SceneBridge", "SceneBridge", "SceneBridge",
                                  "Synchronize an owned Blender scene snapshot")
    for key, label, command in [
        ("Preview", "Preview changes", "scene_bridge.sync_configured(dry_run=True)"),
        ("Sync", "Sync Blender scene", "scene_bridge.sync_configured()"),
        ("Watch", "Watch saved Blender snapshots", "scene_bridge.start_watch()"),
        ("Stop", "Stop watching", "scene_bridge.stop_watch()"),
    ]:
        entry = unreal.ToolMenuEntry(name="SceneBridge." + key, type=unreal.MultiBlockType.MENU_ENTRY)
        entry.set_label(label)
        entry.set_string_command(unreal.ToolMenuStringCommandType.PYTHON, "",
                                  "import scene_bridge; " + command)
        submenu.add_menu_entry("SceneBridge", entry)
    menus.refresh_all_widgets()
    return True


def startup():
    global _STARTUP_HANDLE
    try:
        if _menus():
            config = read_json(config_path())
            if config.get("auto_start"):
                start_watch()
            return
    except Exception as error:
        unreal.log_warning("SceneBridge menu startup deferred: " + str(error))
    if _STARTUP_HANDLE is None:
        def deferred(delta):
            global _STARTUP_HANDLE
            try:
                if _menus():
                    unreal.unregister_slate_post_tick_callback(_STARTUP_HANDLE)
                    _STARTUP_HANDLE = None
                    if read_json(config_path()).get("auto_start"):
                        start_watch()
            except Exception as error:
                unreal.unregister_slate_post_tick_callback(_STARTUP_HANDLE)
                _STARTUP_HANDLE = None
                unreal.log_warning("SceneBridge menus could not register: " + str(error))
        _STARTUP_HANDLE = unreal.register_slate_post_tick_callback(deferred)
