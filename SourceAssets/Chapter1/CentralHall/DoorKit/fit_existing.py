"""Fit the shared door casing to both measured wall faces in the original laboratory."""
import unreal as u

DEST = '/Game/Environment/LabR17/DoorKit'

def install():
    actors=u.get_editor_subsystem(u.EditorActorSubsystem)
    world=u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
    assert world.get_name()=='Map_LabV39'
    base={a.get_actor_label():a for a in actors.get_all_level_actors()}
    doors={n.removeprefix('LabR17_Door_'):a for n,a in base.items() if n.startswith('LabR17_Door_')}
    assert len(doors)==78
    lift_mesh=u.load_asset(DEST+'/SM_LabLiftFront160')
    assert lift_mesh
    report={'doors':{},'lifts':{},'retired':[]}
    with u.ScopedEditorTransaction('Fit laboratory door frames and lift fronts'):
        for id,door in doors.items():
            axis=door.get_actor_forward_vector()
            pos=door.get_actor_location()
            columns=[base[f'R17_Frame_{id}_{bank}_{side}'] for bank in (0,1) for side in (-1,1)]
            distances=[]
            for post in columns:
                center,extent=post.get_actor_bounds(False)
                d=center-pos
                offset=d.x*axis.x+d.y*axis.y
                half_depth=abs(axis.x)*extent.x+abs(axis.y)*extent.y
                distances.append(offset-half_depth if offset>0 else offset+half_depth)
            pos_side,neg_side=max(distances),min(distances)
            assert pos_side>0>neg_side,(id,distances)
            door.modify()
            door.set_editor_property('DoorFramePositiveCm',pos_side)
            door.set_editor_property('DoorFrameNegativeCm',neg_side)
            door.set_editor_property('bShowDoorFrameNegative',id!='C0')
            # Refit only the presentation. It is safe to rerun while the owner is at rest.
            door.call_method('ConfigureDoorAppearance')
            for post in columns:
                post.modify()
                comp=post.static_mesh_component
                comp.modify()
                comp.set_visibility(False,False)
                comp.set_hidden_in_game(True,False)
                comp.set_cast_shadow(False)
            report['doors'][id]={'positive_cm':round(pos_side,3),'negative_cm':round(neg_side,3)}
        for label,mesh_name in {'Art_CH_C0LeafLeft':'SM_CH_C0LeafLeft','Art_CH_C0LeafRight':'SM_CH_C0LeafRight','Art_CH_TrainingLandingFrame':'SM_CH_TrainingLandingFrame'}.items():
            a=base.get(label)
            if a:
                assert a.static_mesh_component.static_mesh.get_name()==mesh_name
                assert actors.destroy_actor(a)
                report['retired'].append(label)
        for label,a in base.items():
            if not label.startswith('LiftDoor::'):continue
            _,shaft,level=label.split('::')
            center,extent=a.get_actor_bounds(False)
            shaft_center,shaft_ext=base['LiftShaft::'+shaft].get_actor_bounds(False)
            assert abs(extent.x-80)<.5 and abs(extent.z-135)<.5 and shaft_center.y<center.y
            location=u.Vector(center.x,shaft_center.y+shaft_ext.y+.5,center.z-extent.z)
            name='Art_LabLiftFront_'+shaft+('_Lower' if level=='0' else '_Upper')
            art=base.get(name) or actors.spawn_actor_from_class(u.StaticMeshActor,location,u.Rotator())
            art.modify()
            art.set_actor_label(name)
            art.set_folder_path('LabV39/R17/LiftFronts')
            art.set_actor_location_and_rotation(location,u.Rotator(),False,True)
            c=art.static_mesh_component
            c.modify()
            c.set_static_mesh(lift_mesh)
            c.set_collision_profile_name('NoCollision')
            c.set_editor_property('can_ever_affect_navigation',False)
            art.set_actor_enable_collision(False)
            report['lifts'][label]=name
    assert len(report['lifts'])==20
    return report
