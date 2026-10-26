# Guidance material sources

These HLSL fragments are the Custom-expression source used to author `M_GuidancePath` and `M_GuidanceMarker`. They are readable source records, not runtime file includes. Edit and compile the corresponding material in Unreal Editor to change the game.

`path-surface.hlsl` expects UV, StartDistance, SegmentLength, GuidanceTime, ArrowSpeed, ArrowSpacing, Fade, LineIntensity, ArrowIntensity, Color, PathLength and RevealDistance. UV X follows strip length; UV Y crosses its width. Default strip width is 30 cm. The material is Unlit, Additive, two-sided, enabled for Spline Meshes, with normal depth testing.

See [mission guidance](../../Docs/Implementation/mission-guidance.md) for Blueprint contracts and verification boundaries. Local helpers and observed frames remain in ignored `Saved/Agent/Guidance` and are not runtime dependencies.

`path-miter.hlsl` is the vertex-stage World Position Offset expression. `StitchJoin` supplies world-space Direction/Origin and StartShear/EndShear; adjacent strips share a miter cross-section. It closes the outside corner without additive cap overlap. The default core width is 8 cm and runtime LineIntensity is 0.30; arrow width, intensity, spacing and speed are unchanged.
