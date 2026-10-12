# Time Stop material source snapshots

The adjacent HLSL files are Custom expressions exported from the saved UE 5.6.1 materials, with trailing blank lines normalized. State, Facets and Grid were updated in the fourth iteration for player-identity masking and large-scene coverage. Outline retains the third iteration. These are reviewable snapshots, not external shader includes or a runtime dependency. The `.uasset` graphs in `/Game/VFX/TimeStop/` remain authoritative for inputs, settings and defaults.

- `M_PP_TS_Facets.hlsl`: fixed world-position irregular Delaunay triangles from `T_TS_FacetNoise`, world-normal dominant-axis projection, shared vertex heights/gradients and projected virtual relief. World-distance wave only; protected scene-color refraction, not actual vertex/silhouette displacement or moving-object local UVs.
- `M_PP_TS_State.hlsl`: scene-depth domain, cold grade, shadow lift, warm-color protection and four-direction depth contours.
- `M_TS_Grid.hlsl`: world-grid fade, soft occlusion, intersection intensity and foreground protection.
- `M_PP_TimeStopOutline.hlsl`: independent CustomStencil styles 224–255, 1–8 display-pixel contours, visible-depth checks and analytic soft halo. It does not use engine Bloom.

All three post-process materials run at Scene Color After Tonemapping: State priority 10, Facets 20, Outline 30. The grid is an additive instanced static mesh material with depth testing disabled; its shader restores soft world occlusion and suppresses first-person foreground pixels. Disabling depth testing without that shader mask is not equivalent.

When editing through Python, obtain the active output expression with `MaterialEditingLibrary.get_material_property_input_node(material, MaterialProperty.MP_EMISSIVE_COLOR)`. `ObjectIterator` can also return detached expressions left after graph edits; changing the first Custom expression found may change no rendered output. Compile, inspect the actual view, then save outside PIE.

See [implementation and validation](../time-stop-vfx.md) for current parameters, evidence and limitations.

The two Material Instances explicitly store the art parameters. Verify the effective values on runtime MIDs as well as the connected scalar expressions. In this local UE 5.6 source, `set_material_instance_scalar_parameter_value` can return false even when it successfully changes the parameter: the function's result flag is never assigned after the write. Read back the value, update the instance, save it, and verify a newly loaded instance; do not infer success or failure from that boolean alone.

Historical (not used by the current controller): `NS_TS_SpatialGrid` uses fixed local bounds from -1600 to +1600 cm on each axis. The visible mesh extends ±1500 cm; undersized automatic bounds made the entire grid disappear at some camera positions. Test visibility away from the snapped grid origin as well as directly above it. A correct material parameter and an active Niagara component do not prove that a particle is rendered.

Fourth iteration: `SM_TS_GridChunk` is a 60m periodic tile, instantiated around the camera on a 60m snapped world lattice. Default draw distance is 120m (125 chunks); range is clamped to 60–180m. State/Grid blend to full visible scene coverage. Stencil 1–223 is dynamically reserved for player meshes without overwriting existing CustomDepth users; Outline keeps 224–255. See the current validation record for tested bounds and limitations.


Fifth iteration (2026-10-11): entry shares `Radius`, `ScanLimit`, `EntryPhase`, `FullScene` and a 160cm feather across all three layers. Facets additionally receive latched `ScanSpeed`, `HoldSeconds`, `FadeSeconds`: local age after world-wave arrival controls decay, independent of total radius. State/Grid keep their exit coverage path; entry no longer floods the world according to global StateWeight. Runtime evidence is linked from the implementation document.

Sixth iteration (2026-10-11): the previous jittered square grid always used the same diagonal, producing aligned ridges. `NoiseSource/T_TS_FacetNoise.png` now contains a periodic, non-lattice Delaunay field: 256 scattered sites and 512 triangles, baked by `generate-facet-noise.py` (NumPy/Pillow, fixed seed 20261011). RG encodes the two planar slopes in [-4,4], B the interpolated shared-vertex height in [-1,1], A a diagnostic facet ID. The texture is linear BGRA8, sRGB off, trilinear, wrap, simple-average mips, resident (about 5.33 MiB including mips). Do not use normal-map compression or an arbitrary grayscale noise image as a drop-in replacement: the channel contract matters.

`FacetNoise` is a TextureObject parameter inherited by MI_PP_TS_Facets; `NoiseSeed` (default 0) shifts the static pattern. `CellSizeWorld` still sets the world scale (160cm default), `ReliefDepth` the virtual relief (22cm), and `FacetRotation` the slope strength (0.4). The tile spans 16 cells (25.6m at default scale), rotated 23 degrees in each projection plane with distinct axis offsets. It is periodic, not infinite unique noise. Keep NoiseSeed fixed while playing; changing it changes the world pattern. Timing/controller/outline/grid assets were not modified in this iteration. The baked borders have finite texel resolution; the debug palette interpolates IDs near borders and is not a shipped appearance.

Regenerate the source with `python generate-facet-noise.py [output-directory]`; import/reimport through UE, preserve data settings, compile and compare actual PIE before saving. The generator never writes `.uasset` bytes.
