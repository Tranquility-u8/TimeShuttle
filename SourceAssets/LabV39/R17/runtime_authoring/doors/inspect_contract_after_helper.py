"""Coordinator-run read-only reflection after editor-only LabAuthoring is loaded."""
import json
from pathlib import Path
import unreal
OUT=Path(unreal.Paths.project_saved_dir()).resolve()/'Agent'/'LabR17'/'doors'
OUT.mkdir(parents=True,exist_ok=True)
assert hasattr(unreal,'LabAuthoringLibrary'),'LabAuthoring editor plugin not loaded'
assets=[
 '/Game/Blueprints/Interactables/Interaction/BP_Interaction_Base',
 '/Game/Blueprints/Interactables/Interaction/BP_InteractionArea_Box',
 '/Game/Blueprints/Interfaces/BPI_Interaction',
 '/Game/UI/Widgets/UI_Interaction',
]
data={}
for path in assets:
    name=path.rsplit('/',1)[-1]
    data[name]={'blueprint':json.loads(unreal.LabAuthoringLibrary.inspect_blueprint(path)),
                'class':json.loads(unreal.LabAuthoringLibrary.inspect_class(path+'.'+name+'_C'))}
    for component in data[name]['blueprint'].get('components',[]):
        template=unreal.load_object(None,component['template'])
        props={}
        if template:
            for prop in ('relative_location','relative_rotation','relative_scale3d',
                         'box_extent','sphere_radius','child_actor_class','widget_class',
                         'draw_size','collision_profile_name'):
                try: props[prop]=str(template.get_editor_property(prop))
                except Exception: pass
        component['template_properties']=props
(OUT/'reflected_interaction_contract.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
result={'read_only':True,'report':str(OUT/'reflected_interaction_contract.json')}
