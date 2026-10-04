# Time Stop material source snapshots

The adjacent HLSL files are Custom expressions exported from the saved UE 5.6.1 materials. Facets and Outline were updated in the third iteration; State and Grid retain the second iteration. These are reviewable snapshots, not external shader includes or a runtime dependency. The `.uasset` graphs in `/Game/VFX/TimeStop/` remain authoritative for inputs, settings and defaults.

- `M_PP_TS_Facets.hlsl`: fixed world-position triangles, world-normal dominant-axis projection, shared vertex heights/gradients and projected virtual relief. World-distance wave only; protected scene-color refraction, not actual vertex/silhouette displacement or moving-object local UVs.
- `M_PP_TS_State.hlsl`: scene-depth domain, cold grade, shadow lift, warm-color protection and four-direction depth contours.
- `M_TS_Grid.hlsl`: world-grid fade, soft occlusion, intersection intensity and foreground protection.
- `M_PP_TimeStopOutline.hlsl`: independent CustomStencil styles 224–255, 1–8 display-pixel contours, visible-depth checks and analytic soft halo. It does not use engine Bloom.

All three post-process materials run at Scene Color After Tonemapping: State priority 10, Facets 20, Outline 30. The grid is an additive Niagara mesh material with depth testing disabled; its shader restores soft world occlusion and suppresses first-person foreground pixels. Disabling depth testing without that shader mask is not equivalent.

When editing through Python, obtain the active output expression with `MaterialEditingLibrary.get_material_property_input_node(material, MaterialProperty.MP_EMISSIVE_COLOR)`. `ObjectIterator` can also return detached expressions left after graph edits; changing the first Custom expression found may change no rendered output. Compile, inspect the actual view, then save outside PIE.

See [implementation and validation](../time-stop-vfx.md) for current parameters, evidence and limitations.

The two Material Instances explicitly store the art parameters. Verify the effective values on runtime MIDs as well as the connected scalar expressions. In this local UE 5.6 source, `set_material_instance_scalar_parameter_value` can return false even when it successfully changes the parameter: the function's result flag is never assigned after the write. Read back the value, update the instance, save it, and verify a newly loaded instance; do not infer success or failure from that boolean alone.

`NS_TS_SpatialGrid` uses fixed local bounds from -1600 to +1600 cm on each axis. The visible mesh extends ±1500 cm; undersized automatic bounds made the entire grid disappear at some camera positions. Test visibility away from the snapped grid origin as well as directly above it. A correct material parameter and an active Niagara component do not prove that a particle is rendered.
