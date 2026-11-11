"""Run with --launch to inspect the saved prefab in an independent, unsaved editor world and PIE."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import traceback
import uuid


BLUEPRINT = '/Game/Environment/Chapter1/LabDoorPlaque/BP_LabDoorPlaque'
TEST_NAMES = ('PARTICLE LAB', '时序校准室')
RESOLUTION = (1440, 900)


def write_json(path, value):
    tmp = path.with_suffix('.tmp')
    tmp.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')
    tmp.replace(path)


def launch(source_file=__file__, session_family='DoorPlaque', env_key='TIME_SHUTTLER_PLAQUE_QA',
           evidence=('DefaultPlaque.png', 'Editor.png', 'PlayInEditor.png', 'verification.json')):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--launch', action='store_true', required=True)
    parser.add_argument('--editor', type=Path, required=True)
    parser.add_argument('--project', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    source, project = Path(source_file).resolve(), args.project.resolve()
    output = args.output.resolve()
    session = project.parent / 'Saved' / 'Agent' / session_family / uuid.uuid4().hex
    session.mkdir(parents=True)
    output.mkdir(parents=True, exist_ok=True)
    command = [str(args.editor.resolve()), str(project), '/Engine/Maps/Entry', '-RenderOffscreen',
               '-windowed', '-ResX=1440', '-ResY=900', '-NoSplash', '-unattended', '-nosound',
               '-NoLiveCoding', '-NoAutoReimport', '-NoSourceControl', '-NoAssetRegistryCacheWrite',
               '-NoRestoreOpenAssetTabs', '-DisablePlugins=AssetSearch', '-UserDir=' + str(session / 'user'),
               '-ini:Engine:[/Script/EngineSettings.GameMapsSettings]:GameInstanceClass=/Script/Engine.GameInstance',
               '-AbsLog=' + str(session / 'editor.log'), '-ExecCmds=py ' + source.as_posix()]
    env = dict(os.environ)
    env[env_key] = str(session)
    print('Session: ' + str(session), flush=True)
    window_options = {}
    if sys.platform == 'win32':
        startup = subprocess.STARTUPINFO()
        startup.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startup.wShowWindow = 0
        window_options.update(startupinfo=startup, creationflags=subprocess.CREATE_NO_WINDOW)
    with subprocess.Popen(command, env=env, **window_options) as proc:
        try:
            proc.wait(timeout=380)
        except subprocess.TimeoutExpired:
            proc.terminate()
            proc.wait(timeout=20)
            raise RuntimeError('Dedicated editor timed out; see ' + str(session))
    report = json.loads((session / 'verification.json').read_text(encoding='utf-8'))
    if not report['success']:
        raise RuntimeError(report.get('error', 'Verification failed; see ' + str(session)))
    for filename in evidence:
        shutil.copyfile(session / filename, output / filename)
    print('Passed: ' + str(output), flush=True)


def run_editor(u, session):
    if '-renderoffscreen' not in u.SystemLibrary.get_command_line().lower() or not session.is_dir():
        raise RuntimeError('Requires its own offscreen verification process')
    editor = u.get_editor_subsystem(u.UnrealEditorSubsystem)
    level = u.get_editor_subsystem(u.LevelEditorSubsystem)
    actors = u.get_editor_subsystem(u.EditorActorSubsystem)
    report = {'success': False, 'prefab': BLUEPRINT, 'checks': {}}
    eyes = u.Vector(104, 7, 160)
    look_at = u.Vector(0, 0, 160)
    view = u.MathLibrary.find_look_at_rotation(eyes, look_at)

    def stage(phase):
        report['phase'] = phase
        write_json(session / 'verification.json', report)

    def spawn(cls, location, rotation=None):
        return actors.spawn_actor_from_class(cls, u.Vector(*location), rotation or u.Rotator())

    def box(location, size, color):
        actor = spawn(u.StaticMeshActor, location)
        component = actor.static_mesh_component
        component.set_static_mesh(u.load_asset('/Engine/BasicShapes/Cube'))
        actor.set_actor_scale3d(u.Vector(*[value / 100 for value in size]))
        component.set_material(0, u.load_asset('/Engine/BasicShapes/BasicShapeMaterial'))
        mid = component.create_dynamic_material_instance(0)
        mid.set_vector_parameter_value('Color', u.LinearColor(*color, 1))
        return actor

    def light(location, target, lumens, size, color):
        rotation = u.MathLibrary.find_look_at_rotation(u.Vector(*location), u.Vector(*target))
        source = spawn(u.RectLight, location, rotation).rect_light_component
        source.set_intensity_units(u.LightUnits.LUMENS)
        source.set_intensity(lumens)
        source.set_attenuation_radius(850)
        source.set_source_width(size[0])
        source.set_source_height(size[1])
        source.set_light_color(u.LinearColor(*color, 1), False)
        source.set_editor_property('specular_scale', .16)

    def caption(actor):
        return str(actor.get_editor_property('RoomName'))

    def rendered(actor):
        labeling = actor.get_components_by_class(u.TextRenderComponent)
        assert len(labeling) == 1, 'Expected one live text component'
        label = labeling[0]
        raw = str(label.get_editor_property('text'))
        cleaned = ''.join(raw.replace('<br>', '\n').split())
        desired = ''.join(caption(actor).split())
        assert cleaned == desired, f'Instance name {desired!r} is rendered as {raw!r}'
        bounds = label.get_text_world_size()
        scale = actor.get_actor_scale3d()
        assert 0.5 < bounds.y / abs(scale.y) < 58 and 0.5 < bounds.z / abs(scale.z) < 17.5, (raw, bounds, scale)
        return {'display': raw, 'width_cm': round(bounds.y,2), 'height_cm': round(bounds.z,2),
                'font': label.get_editor_property('font').get_path_name()}

    def inspect(world, cls, context):
        placed = sorted(u.GameplayStatics.get_all_actors_of_class(world, cls), key=lambda a: -a.get_actor_location().z)
        names = [caption(a) for a in placed]
        assert names == list(TEST_NAMES), (context, names)
        assert len({a.get_path_name() for a in placed}) == len(TEST_NAMES)
        meshes = [[c.static_mesh.get_path_name() for c in a.get_components_by_class(u.StaticMeshComponent)
                   if c.static_mesh and c.static_mesh.get_name() == 'SM_LabDoorPlaque'] for a in placed]
        assert all(len(row) == 1 for row in meshes), (context, meshes)
        assert meshes[0] == meshes[1]
        report['checks'][context] = {'room_names': names, 'mesh': meshes[0][0], 'world': world.get_path_name(),
                                     'display': [rendered(a) for a in placed],
                                     'instance_paths': [a.get_path_name() for a in placed]}

    def photograph(world, photo):
        cameras = u.GameplayStatics.get_all_actors_of_class(world, u.SceneCapture2D)
        assert len(cameras) == 1, 'Missing verification camera'
        camera = cameras[0]
        component = camera.get_component_by_class(u.SceneCaptureComponent2D)
        target = u.RenderingLibrary.create_render_target2d(world, *RESOLUTION, u.TextureRenderTargetFormat.RTF_RGBA8,
                                                            u.LinearColor(0.025, 0.025, 0.025, 1))
        component.set_editor_property('texture_target', target)
        component.set_editor_property('capture_source', u.SceneCaptureSource.SCS_FINAL_COLOR_LDR)
        component.set_editor_property('fov_angle', 48.0)
        component.set_editor_property('always_persist_rendering_state', True)
        component.set_editor_property('capture_every_frame', False)
        post = component.get_editor_property('post_process_settings')
        post.set_editor_property('override_auto_exposure_min_brightness', True)
        post.set_editor_property('override_auto_exposure_max_brightness', True)
        post.set_editor_property('auto_exposure_min_brightness', 10.0)
        post.set_editor_property('auto_exposure_max_brightness', 10.0)
        post.set_editor_property('override_bloom_intensity', True)
        post.set_editor_property('bloom_intensity', 0.0)
        component.set_editor_property('post_process_settings', post)
        u.AutomationLibrary.finish_loading_before_screenshot()
        for _ in range(20):
            component.capture_scene()
            yield .12
        u.RenderingLibrary.export_render_target(world, target, str(session), photo)
        path = session / photo
        assert path.is_file() and path.stat().st_size > 4096, 'Empty capture: ' + str(path)
        component.set_editor_property('capture_every_frame', False)
        component.set_editor_property('texture_target', None)

    def run():
        stage('load prefab')
        cls = u.EditorAssetLibrary.load_blueprint_class(BLUEPRINT)
        assert cls, 'Missing Blueprint: ' + BLUEPRINT
        world = u.EditorLoadingAndSavingUtils.new_blank_map(False)
        assert world and not world.get_path_name().startswith('/Game/')
        settings = u.GameplayStatics.get_all_actors_of_class(world, u.WorldSettings)[0]
        settings.set_editor_property('default_game_mode', u.GameModeBase)
        u.SystemLibrary.execute_console_command(world, 't.IdleWhenNotForeground 0')
        u.SystemLibrary.execute_console_command(world, 'Slate.bAllowThrottling 0')
        editor.set_level_viewport_camera_info(eyes, view)
        box((-2, 0, 150), (4, 330, 320), (.36, .35, .32))
        box((0, 87, 145), (2, 93, 300), (.034, .041, .046))
        box((1, 40, 145), (3, 2, 300), (.22, .23, .22))
        light((95, -42, 235), (0, 0, 166), 7600, (94, 36), (1, .94, .88))
        light((78, 57, 145), (0, 0, 155), 3000, (70, 35), (.83,.94,1))
        camera = actors.spawn_actor_from_class(u.SceneCapture2D, eyes, view)

        first = spawn(cls, (0, 0, 173))
        second = spawn(cls, (0, 0, 147))
        default = caption(first)
        assert default == caption(second)
        assert 'TEMPORAL' in default.upper() and 'CALIBRATION' in default.upper(), default
        report['checks']['default'] = rendered(first)
        # The fixed-size photography wall and camera are framed for a unit-scale instance.
        for subject in (first, second):
            subject.set_actor_scale3d(u.Vector(1, 1, 1))
        hero_eye = u.Vector(88, 13, 176)
        hero_view = u.MathLibrary.find_look_at_rotation(hero_eye, u.Vector(0, 1, 173))
        camera.set_actor_location_and_rotation(hero_eye, hero_view, False, True)
        second.set_actor_hidden_in_game(True)
        stage('capture default')
        yield from photograph(world, 'DefaultPlaque.png')
        second.set_actor_hidden_in_game(False)
        camera.set_actor_location_and_rotation(eyes, view, False, True)
        first.set_editor_property('RoomName', 'TEMPORAL PARTICLE CONTAINMENT AND CALIBRATION')
        report['checks']['long_name'] = rendered(first)
        first.set_editor_property('RoomName', TEST_NAMES[0])
        assert caption(second) == default, 'Editing one instance changed its sibling'
        second.set_editor_property('RoomName', TEST_NAMES[1])
        assert caption(u.get_default_object(cls)) == default, 'Editing an instance changed the CDO'
        actors.set_selected_level_actors([])
        inspect(world, cls, 'editor')
        stage('capture editor')
        yield from photograph(world, 'Editor.png')
        stage('begin PIE')
        level.editor_request_begin_play()
        start = time.monotonic()
        while time.monotonic()-start < 60:
            game = editor.get_game_world()
            if game and level.is_in_play_in_editor() and 'UEDPIE_' in game.get_path_name():
                break
            yield .15
        else:
            raise RuntimeError('PIE world unavailable')
        inspect(game, cls, 'play_in_editor')
        stage('capture PIE')
        yield from photograph(game, 'PlayInEditor.png')
        level.editor_request_end_play()
        while level.is_in_play_in_editor():
            yield .1
        report['success'] = True
        stage('complete')

    work = run()
    state = {'after': 0, 'busy': False}

    def tick(delta):
        if state['busy'] or time.monotonic() < state['after']:
            return
        state['busy'] = True
        try:
            state['after'] = time.monotonic() + next(work)
            return
        except StopIteration:
            pass
        except Exception:
            report['error'] = traceback.format_exc()
            stage('failed')
            u.log_error(report['error'])
        finally:
            state['busy'] = False
        u.unregister_slate_post_tick_callback(state['handle'])
        if level.is_in_play_in_editor():
            level.editor_request_end_play()
        u.SystemLibrary.quit_editor()

    state['handle'] = u.register_slate_post_tick_callback(tick)


if 'TIME_SHUTTLER_PLAQUE_QA' in os.environ:
    import unreal
    run_editor(unreal, Path(os.environ['TIME_SHUTTLER_PLAQUE_QA']))
elif __name__ == '__main__':
    launch()
