"""Editor-only preview of Training Room mesh sets. Does not implement tutorial gameplay."""
import unreal

STAGES={
    'S1':'01  Entry to center / frozen rocks',
    'S2':'02A-B  Manual time control / front shooter',
    'S2C':'02C  Front and side shooters',
    'S3':'03  Pickup, reload and basic shooting',
    'S4':'04  Moving armored targets',
    'S5':'05  Suspended rock and breakable link',
    'S6':'06  Combined shooting exercise',
    'S7A':'07A  Melee preview / table retained',
    'S7B':'07B  Combat / table removed',
}
SHARED={'S3','S4','S5','S6','S7A'}

def _actors():
    world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    if not world or world.get_path_name()!='/Game/Maps/Map_TrainingRoom.Map_TrainingRoom':
        raise RuntimeError('Open Map_TrainingRoom before using Training Stages.')
    if unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).is_in_play_in_editor():
        raise RuntimeError('Stop Play before changing a stage preview.')
    return [a for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors() if a.actor_has_tag('TS_StageLayout')]

def show_stage(stage):
    """Set a review/PIE starting layout; never moves the player or the editor camera."""
    if stage not in STAGES:raise ValueError(stage)
    actors=_actors()
    active={stage}
    if stage=='S2C':active.add('S2')
    if stage in SHARED:active.add('SharedShooting')
    layers=unreal.get_editor_subsystem(unreal.LayersSubsystem)
    groups=set()
    count=0
    with unreal.ScopedEditorTransaction('Preview Training '+stage):
        for a in actors:
            tags=[str(t) for t in a.tags]
            group=next(t[8:] for t in tags if t.startswith('TSStage:'))
            groups.add(group)
            on=group in active
            a.modify()
            a.set_actor_hidden_in_game(not on)
            a.set_actor_enable_collision(on and 'TSCollision:none' not in tags)
            a.set_is_temporarily_hidden_in_editor(not on)
            count+=int(on)
        for g in groups:layers.set_layer_visibility('TS_'+g,g in active)
    unreal.EditorLevelLibrary.editor_invalidate_viewports()
    unreal.log('Training '+stage+': '+str(count)+' layout actors active. Save the level to retain this PIE starting state.')
    return {'stage':stage,'active_actors':count,'shared_table':stage in SHARED}

def restore_editor_visibility():
    """Recover editor visibility from saved runtime hidden flags after reopening the map."""
    actors=_actors()
    groups={}
    for a in actors:
        hidden=a.get_editor_property('hidden')
        a.set_is_temporarily_hidden_in_editor(hidden)
        group=next(str(t)[8:] for t in a.tags if str(t).startswith('TSStage:'))
        groups[group]=groups.get(group,False) or not hidden
    layers=unreal.get_editor_subsystem(unreal.LayersSubsystem)
    for g,on in groups.items():layers.set_layer_visibility('TS_'+g,on)

def register_menu():
    menus=unreal.ToolMenus.get()
    name='LevelEditor.MainMenu.TrainingStages'
    if menus.is_menu_registered(name):menus.remove_menu(name)
    root=menus.extend_menu('LevelEditor.MainMenu')
    menu=root.add_sub_menu('TimeShuttler','TrainingStages','TrainingStages','Training Stages','Preview tutorial meshes; save the level to retain the selected starting layout.')
    for stage,label in STAGES.items():
        entry=unreal.ToolMenuEntry(name='TS_Preview_'+stage,type=unreal.MultiBlockType.MENU_ENTRY)
        entry.set_label(label)
        entry.set_tool_tip('Switch meshes, collision and the shared table. Player position is unchanged. Static layout preview only.')
        entry.set_string_command(unreal.ToolMenuStringCommandType.PYTHON,'',"import time_shuttler_training_stages as ts; ts.show_stage('"+stage+"')")
        menu.add_menu_entry('Stages',entry)
    menus.refresh_all_widgets()

_restore_tick_handle=None

def _restore_on_tick(delta):
    global _restore_tick_handle
    handle=_restore_tick_handle
    _restore_tick_handle=None
    if handle is not None:unreal.unregister_slate_post_tick_callback(handle)
    world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    playing=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).is_in_play_in_editor()
    if not playing and world and world.get_path_name()=='/Game/Maps/Map_TrainingRoom.Map_TrainingRoom':
        restore_editor_visibility()

def _schedule_restore():
    global _restore_tick_handle
    if _restore_tick_handle is None:
        _restore_tick_handle=unreal.register_slate_post_tick_callback(_restore_on_tick)

def _on_map_opened(filename,as_template):
    _schedule_restore()

def _on_map_changed(change_type):
    _schedule_restore()

register_menu()
unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).on_map_opened.add_callable_unique(_on_map_opened)
unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).on_map_changed.add_callable_unique(_on_map_changed)
_schedule_restore()
