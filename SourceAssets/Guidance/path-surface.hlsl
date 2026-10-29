// Custom-expression source used to author the corresponding Guidance material.

float s = StartDistance + UV.x * SegmentLength;
float y = (UV.y - .5) * 30.0;
float aa = max(fwidth(y), .10);
float core = 1.0-smoothstep(4.0-aa,4.0+aa,abs(y));
float halo = exp(-abs(y)*.28);
float x = frac((s-GuidanceTime*ArrowSpeed)/max(ArrowSpacing,1.0))*ArrowSpacing;
// Both chevrons point toward increasing path distance. Smooth masks preserve fine edges.
float a = abs(x-(22.0-abs(y)*1.05));
float b = abs(x-(33.0-abs(y)*1.05));
float edge = min(a,b);
// Derivatives must use continuous distance, never the frac-wrapped x.
// Bound the filter footprint so a distant or grazing pixel cannot fill the gap.
float arrowAA = clamp(fwidth(s) + 1.05*fwidth(y), .30, 2.0);
float arrows=(1.0-smoothstep(1.2,1.2+arrowAA,edge))*(1.0-smoothstep(6.0,7.2,abs(y)));
float aglow=exp(-edge*.55)*exp(-abs(y)*.07)*(1.0-smoothstep(9.0,14.0,abs(y)));
float ends=smoothstep(5.0,55.0,s)*(1.0-smoothstep(max(PathLength-35.0,0.0),max(PathLength,1.0),s));
float reveal=1.0-smoothstep(max(RevealDistance-180.0,0.0),RevealDistance,s);
return Color.rgb * ((core*.72+halo*.28)*LineIntensity+(arrows+aglow*.12)*ArrowIntensity)*Fade*ends*reveal;
