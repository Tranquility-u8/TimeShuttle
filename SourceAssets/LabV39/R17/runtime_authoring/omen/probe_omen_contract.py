"""Read-only editor probe. Root agent runs this through the existing UE bridge."""
import json
from pathlib import Path
import unreal

OUT = Path(unreal.Paths.project_saved_dir()).resolve()/'Agent'/'LabR17'/'omen'
OUT.mkdir(parents=True, exist_ok=True)

def path(obj):
    return obj.get_path_name() if obj else None

def vec(v):
    return [float(v.x), float(v.y), float(v.z)]

def rot(r):
    return [float(r.pitch), float(r.yaw), float(r.roll)]

def attempt(fn):
    try:
        return fn()
    except Exception as exc:
        return {'error': str(exc)}

world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
rows = []
for actor in actors:
    tags = [str(x) for x in actor.tags]
    if 'OmenV4' not in tags:
        continue
    comp = actor.get_component_by_class(unreal.StaticMeshComponent)
    root = actor.root_component
    row = {
        'path': path(actor), 'name': actor.get_name(), 'label': actor.get_actor_label(),
        'tags': tags, 'class': path(actor.get_class()),
        'location': vec(actor.get_actor_location()), 'rotation': rot(actor.get_actor_rotation()),
        'scale': vec(actor.get_actor_scale3d()),
        'attach_parent': path(actor.get_attach_parent_actor()),
        'root_relative_location': vec(root.get_editor_property('relative_location')),
        'root_relative_rotation': rot(root.get_editor_property('relative_rotation')),
        'root_relative_scale': vec(root.get_editor_property('relative_scale3d')),
        'root_absolute_rotation': bool(root.get_editor_property('absolute_rotation')),
    }
    if comp:
        row.update({
            'mesh': path(comp.static_mesh), 'mobility': str(comp.mobility),
            'materials': [path(comp.get_material(i)) for i in range(comp.get_num_materials())],
            'collision_profile': str(comp.get_collision_profile_name()),
            'collision_enabled': str(comp.get_collision_enabled()),
            'simulating_physics': comp.is_simulating_physics(),
        })
    rows.append(row)

names = [
    ('KismetMathLibrary', 'rinterp_to'), ('KismetMathLibrary', 'compose_rotators'),
    ('KismetMathLibrary', 'is_point_in_box_with_transform'),
    ('Actor', 'set_actor_rotation'), ('Actor', 'get_actor_rotation'),
    ('BoxComponent', 'get_unscaled_box_extent'),
    ('SceneComponent', 'get_component_to_world'),
]
result = {
    'map': world.get_path_name(),
    'pie': unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).is_in_play_in_editor(),
    'read_only': True, 'actors': rows,
    'api_docs': {f'{c}.{f}': attempt(lambda c=c, f=f: getattr(getattr(unreal, c), f).__doc__)
                 for c, f in names},
    'authoring_classes': [n for n in dir(unreal) if 'LabAuthor' in n],
}
expected = {'ShellUpper', 'ShellLower', 'Eye', 'InnerRing', 'OuterRing', 'Pupil'}
found = {t.split('.', 1)[1] for a in rows for t in a['tags'] if t.startswith('OmenPart.')}
upper = next((a for a in rows if 'OmenPart.ShellUpper' in a['tags']), None)
result['checks'] = {
    'six_unique_expected_parts': len(rows) == 6 and found == expected,
    'current_center_matches_v39': all(a['location'] == [0.0, 3700.0, 700.0] for a in rows),
    'five_parts_attach_to_shell_upper': bool(upper) and all(
        a['attach_parent'] == upper['path'] for a in rows if a is not upper),
    'children_inherit_rotation': all(not a['root_absolute_rotation'] for a in rows),
    'no_simulating_parts': all(not a.get('simulating_physics', True) for a in rows),
}
(OUT / 'omen_contract_probe.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps({'output': str(OUT / 'omen_contract_probe.json'), 'checks': result['checks']}, ensure_ascii=False))
