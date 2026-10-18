"""Coordinator-run read-only PIE input inventory; no injected input here."""
import json
from pathlib import Path
import unreal
OUT=Path(unreal.Paths.project_saved_dir()).resolve()/'Agent'/'LabR17'/'doors'
world=unreal.EditorLevelLibrary.get_game_world()
assert world,'Start PIE first'
pc=unreal.GameplayStatics.get_player_controller(world,0)
assert pc,'PIE local player controller missing'
lib=unreal.get_default_object(unreal.load_class(None,'/Script/Engine.SubsystemBlueprintLibrary'))
sub=lib.call_method('GetLocalPlayerSubSystemFromPlayerController',args=(pc,unreal.EnhancedInputLocalPlayerSubsystem.static_class()))
assert sub,'EnhancedInput local player subsystem missing'
action=unreal.load_asset('/Game/Input/Actions/IA_Interact')
mapping=unreal.load_asset('/Game/Input/IMC_Player')
keys=[]
for m in mapping.get_editor_property('mappings'):
    if m.get_editor_property('action')==action:
        k=m.get_editor_property('key')
        row={'display':str(unreal.InputLibrary.key_get_display_name(k))}
        try:row['key_name']=str(k.get_editor_property('key_name'))
        except Exception:pass
        keys.append(row)
result={'world':world.get_path_name(),'controller':pc.get_path_name(),'subsystem':sub.get_path_name(),
        'action':action.get_path_name(),'mappings':keys,
        'injection_methods':{n:str(getattr(sub,n).__doc__) for n in dir(sub) if 'inject' in n.lower()},
        'pawn':str(unreal.GameplayStatics.get_player_pawn(world,0))}
(OUT/'pie_input_probe.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
