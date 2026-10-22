"""Run a MissionSystem verification suite inside PIE on L_DialogueVerification.
Editor Python: exec(open('<project>/Scripts/Validation/MissionSystem/run.py').read()); run('generic')
Wait for its JSON status to finish, then run('edges'). Test assets are under /Game/MissionSystem/Tests.
"""
import pathlib, shutil, json, unreal

def run(suite='generic'):
    if suite not in ('generic','edges'):
        raise ValueError("Choose 'generic' or 'edges'.")
    world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
    if not world or 'L_DialogueVerification' not in world.get_name():
        raise RuntimeError('Start PIE in /Game/DialogSystem/Tests/L_DialogueVerification first.')
    root=pathlib.Path(unreal.Paths.project_saved_dir()).resolve()/'Agent/DialogueBlueprint'
    out=root/'MissionFlow';out.mkdir(parents=True,exist_ok=True)
    source=pathlib.Path(unreal.Paths.project_dir()).resolve()/'Scripts/Validation/MissionSystem'
    for name in ('runtime_generic_cold.py','runtime_edges_cold.py','dialogue-library-reflection.json'):
        shutil.copy2(source/name,out/name)
    script=out/('runtime_'+suite+'_cold.py')
    env={'ROOT':root,'unreal':unreal,'RESULT':{}}
    exec(compile(script.read_text(encoding='utf-8-sig'),str(script),'exec'),env)
    unreal.log('Mission validation started: '+suite+'. See Saved/Agent/DialogueBlueprint/MissionFlow/runtime-'+suite+'-cold.json')
