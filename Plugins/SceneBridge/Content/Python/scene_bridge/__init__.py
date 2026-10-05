"""SceneBridge editor API. Import does not load a map or synchronize a scene."""
from .importer import import_scene


def startup():
    from .watcher import startup as run
    return run()


def configure(manifest_path, target_map=None, asset_root="/Game/SceneBridge", **options):
    from .watcher import configure as run
    return run(manifest_path, target_map, asset_root, **options)


def sync_configured(dry_run=False):
    from .watcher import sync_configured as run
    return run(dry_run)


def start_watch():
    from .watcher import start_watch as run
    return run()


def stop_watch():
    from .watcher import stop_watch as run
    return run()
