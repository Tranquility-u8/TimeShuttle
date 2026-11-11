"""Verify editor placement and cooked-world independence on disposable geometry."""
import math
import os
from pathlib import Path
import runpy
import time
import traceback


common = runpy.run_path(str(Path(__file__).with_name('verify_plaque.py')))
ASSET = common['BLUEPRINT']
ENV_KEY = 'TIME_SHUTTLER_PLAQUE_MOUNT_QA'


def check_world(u, session):
    assert '-renderoffscreen' in u.SystemLibrary.get_command_line().lower()
    editor = u.get_editor_subsystem(u.UnrealEditorSubsystem)
    actors = u.get_editor_subsystem(u.EditorActorSubsystem)
    level = u.get_editor_subsystem(u.LevelEditorSubsystem)
    report = {'success': False, 'asset': ASSET, 'cases': {}}
    checks = report['cases']

    def stage(name):
        report['stage'] = name
        common['write_json'](session / 'verification.json', report)

    def vec(v):
        return [round(v.x, 4), round(v.y, 4), round(v.z, 4)]

    def pose(actor):
        return {'location': vec(actor.get_actor_location()), 'forward': vec(actor.get_actor_forward_vector()),
                'up': vec(actor.get_actor_up_vector()), 'scale': vec(actor.get_actor_scale3d())}

    def unchanged(actual, expected):
        for k in expected:
            assert math.dist(actual[k], expected[k]) < .03, (k, actual, expected)

    def new_actor(cls, pos, yaw=0):
        return actors.spawn_actor_from_class(cls, u.Vector(*pos), u.Rotator(yaw=yaw))

    def finish_move(actor, pos, yaw, scale=(1, 1, 1)):
        transform = u.Transform(location=u.Vector(*pos), rotation=u.Rotator(yaw=yaw),
                                scale=u.Vector(*scale))
        # This editor API calls UActorElementEditorWorldInterface::NotifyMovementEnded
        # and then AActor::PostEditMove(true), as on release of a viewport transform gizmo.
        assert actors.set_actor_transform(actor, transform)

    def wall(name, center, dimensions, yaw=0):
        actor = new_actor(u.StaticMeshActor, center, yaw)
        actor.set_actor_label(name)
        mesh = actor.static_mesh_component
        mesh.set_static_mesh(u.load_asset('/Engine/BasicShapes/Cube'))
        mesh.set_collision_profile_name('BlockAll')
        mesh.set_material(0, u.load_asset('/Engine/BasicShapes/BasicShapeMaterial'))
        surface = mesh.create_dynamic_material_instance(0)
        surface.set_vector_parameter_value('Color', u.LinearColor(.53,.51,.47,1))
        actor.set_actor_scale3d(u.Vector(*(cm / 100 for cm in dimensions)))
        return actor

    def expect_wall(actor, contact, yaw, name):
        actual = pose(actor)
        a = math.radians(yaw)
        nx, ny = math.cos(a), math.sin(a)
        x, y, z = actual['location']
        dx, dy = x - contact[0], y - contact[1]
        gap = dx * nx + dy * ny
        tangent_error = abs(-dx * ny + dy * nx)
        alignment = sum(a*b for a,b in zip(actual['forward'], (nx, ny, 0)))
        checks[name] = dict(transform=actual, surface_gap_cm=round(gap, 4),
                            tangent_error_cm=round(tangent_error, 4), facing_dot=round(alignment, 5))
        assert -.02 <= gap < .5 and tangent_error < .2 and abs(z-contact[2]) < .1, (name, checks[name])
        assert alignment > .9998 and actual['up'][2] > .9998, (name, checks[name])

    def capture_corner(world):
        # Real-size tile joints let both wall planes and the plates' lean read in one still.
        for z in (126, 188):
            for offset, size in (((.03,145,z),(.1, 314,.20)), ((145,.03,z),(314,.1,.20))):
                seam = wall('Render fixture panel joint', offset, size)
                mesh = seam.static_mesh_component
                mesh.set_collision_enabled(u.CollisionEnabled.NO_COLLISION)
                mesh.get_material(0).set_vector_parameter_value('Color', u.LinearColor(.10,.10,.09,1))
        eyes = u.Vector(157, 139, 180)
        angle = u.MathLibrary.find_look_at_rotation(eyes, u.Vector(28, 28, 158))
        camera = actors.spawn_actor_from_class(u.SceneCapture2D, eyes, angle, transient=True)
        camera_component = camera.get_component_by_class(u.SceneCaptureComponent2D)
        rt = u.RenderingLibrary.create_render_target2d(world, 1440, 840, u.TextureRenderTargetFormat.RTF_RGBA8)
        camera_component.set_editor_property('texture_target', rt)
        camera_component.set_editor_property('capture_source', u.SceneCaptureSource.SCS_FINAL_COLOR_LDR)
        camera_component.set_editor_property('fov_angle', 60)
        camera_component.set_editor_property('capture_every_frame', False)
        camera_component.set_editor_property('always_persist_rendering_state', True)
        pp = camera_component.get_editor_property('post_process_settings')
        for key, value in dict(override_auto_exposure_min_brightness=True, auto_exposure_min_brightness=8.1,
                               override_auto_exposure_max_brightness=True, auto_exposure_max_brightness=8.1,
                               override_bloom_intensity=True, bloom_intensity=0.0).items():
            pp.set_editor_property(key, value)
        camera_component.set_editor_property('post_process_settings', pp)
        light = new_actor(u.RectLight, (110, 170, 243))
        light.set_actor_rotation(u.MathLibrary.find_look_at_rotation(light.get_actor_location(), u.Vector(20,20,147)), False)
        lc = light.rect_light_component
        lc.set_attenuation_radius(900)
        lc.set_intensity_units(u.LightUnits.LUMENS)
        lc.set_intensity(26000)
        lc.set_source_width(100)
        lc.set_source_height(45)
        lc.set_light_color(u.LinearColor(1,.95,.90,1), False)
        lc.set_editor_property('specular_scale', .25)
        u.AutomationLibrary.finish_loading_before_screenshot()
        for _ in range(16):
            camera_component.capture_scene()
            yield .12
        u.RenderingLibrary.export_render_target(world, rt, str(session), 'Corner.png')
        assert (session / 'Corner.png').stat().st_size > 8000
        actors.destroy_actor(camera)

    def run():
        stage('build wall fixtures')
        world = u.EditorLoadingAndSavingUtils.new_blank_map(False)
        assert world and world.get_path_name().startswith('/Temp/')
        eye = u.Vector(170, 72, 161)
        editor.set_level_viewport_camera_info(eye, u.MathLibrary.find_look_at_rotation(eye, u.Vector(0,69,158)))
        u.GameplayStatics.get_all_actors_of_class(world, u.WorldSettings)[0].set_editor_property('default_game_mode', u.GameModeBase)
        u.SystemLibrary.execute_console_command(world, 't.IdleWhenNotForeground 0')
        u.SystemLibrary.execute_console_command(world, 'Slate.bAllowThrottling 0')
        bp = u.load_asset(ASSET)
        cls = u.EditorAssetLibrary.load_blueprint_class(ASSET)
        wall('West wall', (-6, 145, 155), (12, 314, 310))
        wall('South wall', (145, -6, 155), (314, 12, 310))
        wall('Floor', (130, 130, -5), (450, 450, 10))
        wall('Ceiling', (130, 130, 315), (450, 450, 10))
        wall('Instrument pedestal', (1250, 350, 148), (16, 18, 22))
        cabinet = wall('Calibration machine cabinet', (1450, 350, 120), (100,120,200))
        cabinet.set_editor_property('tags', ['TemporalCalibrationArt'])
        door = wall('Movable door leaf', (1750,350,120), (12, 130, 240))
        door.static_mesh_component.set_mobility(u.ComponentMobility.MOVABLE)
        wall('Thick untagged wall', (2010,350,150), (120, 350, 300))
        diagonal = 37
        nx, ny = math.cos(math.radians(diagonal)), math.sin(math.radians(diagonal))
        origin = (910, 810, 154)
        wall('Diagonal partition', (origin[0] - nx*6, origin[1] - ny*6, 150), (12, 320, 300), diagonal)
        yield .2

        stage('asset placement, edit move and duplication')
        captured = []

        def inspect_placement(asset, new_actors):
            if asset == bp:
                captured.extend(pose(a) for a in new_actors)

        # This notification runs inside TryPlacingActorFromObject, before Python's
        # placement wrapper restores its explicitly supplied transform.
        actors.on_new_actors_placed.add_callable(inspect_placement)
        try:
            first = actors.spawn_actor_from_object(bp, u.Vector(13, 69, 158), u.Rotator(yaw=-101))
        finally:
            actors.on_new_actors_placed.remove_callable(inspect_placement)
        assert first and first.get_class() == cls
        assert len(captured) == 1, captured
        factory_pose = captured[0]
        px, py, pz = factory_pose['location']
        # The viewport factory chooses its own cursor/grid location. Measure the
        # actual location against both skins of each vertical fixture at that point.
        candidate_faces = []
        if -12 <= py <= 302 and 0 <= pz <= 310:
            candidate_faces.extend([('west inner', px, (1,0,0)), ('west outer', -12-px, (-1,0,0))])
        if -12 <= px <= 302 and 0 <= pz <= 310:
            candidate_faces.extend([('south inner', py, (0,1,0)), ('south outer', -12-py, (0,-1,0))])
        assert candidate_faces, factory_pose
        face, gap, normal = min(candidate_faces, key=lambda hit: abs(hit[1]))
        facing = sum(a*b for a,b in zip(factory_pose['forward'], normal))
        checks['native_factory_placement'] = dict(transform=factory_pose, face=face, surface_gap_cm=gap,
                                                  normal=normal, facing_dot=facing)
        assert -.02 <= gap < .5 and facing > .9998 and factory_pose['up'][2] > .9998, checks['native_factory_placement']
        # The scripting spawn utility force-sets its input pose after the editor factory returns.
        # Finish that placement through the viewport's movement-end path before taking measurements.
        finish_move(first, (13,69,158), -101)
        yield .25
        expect_wall(first, (0,69,158), 0, 'initial_drop_west')
        first.set_editor_property('RoomName', 'PARTICLE LAB')
        baseline = pose(first)
        for text in ('TEST', '时序校准室', 'PARTICLE LAB'):
            first.set_editor_property('RoomName', text)
            yield .03
            unchanged(pose(first), baseline)
        checks['rename_drift_cm'] = math.dist(baseline['location'], pose(first)['location'])

        copy = actors.duplicate_actor(first, world, u.Vector(0, 35, 22))
        assert copy and copy != first
        yield .15
        expect_wall(copy, (0,104,180), 0, 'native_duplicate_on_wall')
        finish_move(copy, (69,15,158), 164)
        copy.set_editor_property('RoomName', 'TEMPORAL\nCALIBRATION')
        yield .25
        expect_wall(copy, (69,0,158), 90, 'copy_rotates_to_adjacent_wall')
        unchanged(pose(first), baseline)
        assert str(first.get_editor_property('RoomName')) == 'PARTICLE LAB'
        actors.set_selected_level_actors([])
        yield from capture_corner(world)

        stage('near, far, inside corner, and diagonals')
        finish_move(copy, (9,35,151), 80)
        yield .2
        expect_wall(copy, (0,35,151), 0, 'inside_corner_nearest_face')
        finish_move(copy, (origin[0]+15*nx, origin[1]+15*ny, origin[2]), -70, (1.25,1.25,1.25))
        yield .2
        expect_wall(copy, origin, diagonal, 'rotated_wall')
        assert pose(copy)['scale'] == [1.25]*3
        for title, z in (('floor_only', 21), ('ceiling_only', 291), ('free_space', 147)):
            requested = (167, 149, z)
            finish_move(copy, requested, -47)
            yield .12
            actual = pose(copy)
            assert math.dist(actual['location'], requested) < .05, (title, actual)
            assert abs(copy.get_actor_rotation().yaw + 47) < .05, (title, actual)
            checks[title] = actual
        finish_move(copy, (1266,350,149), 81)
        yield .12
        assert math.dist(vec(copy.get_actor_location()), [1266,350,149]) < .03, pose(copy)
        assert abs(copy.get_actor_rotation().yaw-81) < .05
        checks['small_prop'] = pose(copy)
        assert copy.get_editor_property('AutoSnapToWall')
        assert abs(copy.get_editor_property('WallSnapDistance') - 45) < .01
        copy.set_editor_property('AutoSnapToWall', False)
        finish_move(copy, (20,100,151), 103)
        yield .15
        manual = pose(copy)
        assert math.dist(manual['location'], [20,100,151]) < .03
        assert abs(copy.get_actor_rotation().yaw-103) < .05
        checks['manual'] = manual
        copy.set_editor_property('WallSnapDistance', 8.0)
        copy.set_editor_property('AutoSnapToWall', True)
        yield .15
        unchanged(pose(copy), manual)
        finish_move(copy, (6,100,151), 103)
        yield .15
        expect_wall(copy, (0,100,151), 0, 'custom_distance')
        copy.set_editor_property('WallSnapDistance', 45.0)
        finish_move(copy, (-28, 100, 151), 90)
        yield .2
        expect_wall(copy, (-12,100,151), 180, 'reverse_face')

        stage('PIE duplicate transforms and dynamic spawn')
        saved = {a.get_name(): pose(a) for a in (first, copy)}
        level.editor_request_begin_play()
        for _ in range(300):
            game = editor.get_game_world()
            if game and 'UEDPIE_' in game.get_path_name() and level.is_in_play_in_editor():
                break
            yield .15
        else:
            raise RuntimeError('No PIE world')
        placed = {a.get_name(): a for a in u.GameplayStatics.get_all_actors_of_class(game, cls)}
        assert set(saved) == set(placed)
        for n, expected in saved.items():
            unchanged(pose(placed[n]), expected)
        target = u.Transform(location=u.Vector(17, 99, 145), rotation=u.Rotator(yaw=53))
        # The Blueprint spawn node calls these two native functions. UE hides their
        # Python glue because they are BlueprintInternalUseOnly, so use reflection.
        gameplay = u.get_default_object(u.GameplayStatics)
        spawn_scale = u.SpawnActorScaleMethod.MULTIPLY_WITH_ROOT
        spawned = gameplay.call_method('BeginDeferredActorSpawnFromClass',
                                       (game, cls, target, u.SpawnActorCollisionHandlingMethod.ALWAYS_SPAWN, None, spawn_scale))
        spawned = gameplay.call_method('FinishSpawningActor', (spawned, target, spawn_scale))
        yield .15
        assert math.dist(vec(spawned.get_actor_location()), [17,99,145]) < .02, pose(spawned)
        assert abs(spawned.get_actor_rotation().yaw - 53) < .02, pose(spawned)
        checks['pie'] = {'saved_editor_transforms': saved, 'dynamic_spawn': pose(spawned)}
        level.editor_request_end_play()
        while level.is_in_play_in_editor():
            yield .1
        stage('exclude equipment and moving door, accept thick wall')
        for name, coordinate in (('known_lab_cabinet', (1512,350,148)), ('movable_door', (1770,350,148))):
            finish_move(copy, coordinate, 71)
            yield .15
            actual = pose(copy)
            checks[name] = actual
            assert math.dist(actual['location'], coordinate) < .03, (name, actual)
            assert abs(copy.get_actor_rotation().yaw-71) < .05
        finish_move(copy, (2087,350,148), 71)
        yield .15
        expect_wall(copy, (2070,350,148), 0, 'thick_untagged_wall')
        # Reproduce dropping a side-on, double-size plaque with its pivot inside a solid wall.
        for depth in (8, 15):
            finish_move(copy, (2070-depth,350,148), 90, (2,2,2))
            expect_wall(copy, (2070,350,148), 0, f'embedded_{depth}cm')
        report['success'] = True
        stage('complete')

    work = run()
    state = {'after': 0, 'busy': False}

    def tick(_):
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
            common['write_json'](session / 'verification.json', report)
            u.log_error(report['error'])
        finally:
            state['busy'] = False
        u.unregister_slate_post_tick_callback(state['handle'])
        if level.is_in_play_in_editor():
            level.editor_request_end_play()
        u.SystemLibrary.quit_editor()

    state['handle'] = u.register_slate_post_tick_callback(tick)


if ENV_KEY in os.environ:
    import unreal
    check_world(unreal, Path(os.environ[ENV_KEY]))
elif __name__ == '__main__':
    common['launch'](__file__, 'DoorPlaqueMount', ENV_KEY, ('Corner.png', 'verification.json'))
