// Independent display-space outline and analytic soft halo; not engine Bloom.
// 224..255 are leased IDs. Palette RGB = LinearColor * Intensity, A = width in display pixels.
float4 palette[32] = {
  Outline0,Outline1,Outline2,Outline3,Outline4,Outline5,Outline6,Outline7,
  Outline8,Outline9,Outline10,Outline11,Outline12,Outline13,Outline14,Outline15,
  Outline16,Outline17,Outline18,Outline19,Outline20,Outline21,Outline22,Outline23,
  Outline24,Outline25,Outline26,Outline27,Outline28,Outline29,Outline30,Outline31
};
float2 vp = GetViewportUV(Parameters);
float2 sceneUV = ViewportUVToSceneTextureUV(vp,14);
float3 source = SceneTextureLookup(ClampSceneTextureUV(sceneUV,14),14,false).rgb;
float2 stencilUV = ViewportUVToSceneTextureUV(vp,25);
int centerID = (int)round(SceneTextureLookup(ClampSceneTextureUV(stencilUV,25),25,false).r);
if(centerID>=224 && centerID<=255) {
  if(palette[centerID-224].a>0.0) return source;
}
float sceneDepth = SceneTextureLookup(ClampSceneTextureUV(ViewportUVToSceneTextureUV(vp,1),1),1,false).r;
// Post-process input view dimensions, not View.ViewSize, because this pass runs after TSR.
float2 pixelUV = GetSceneTextureViewSize(14).zw;
float bestCore=0.0, bestGlow=0.0;
float3 coreColor=0.0, glowColor=0.0;
const float2 rays[8] = {
  float2(1,0),float2(-1,0),float2(0,1),float2(0,-1),
  float2(.70710678,.70710678),float2(-.70710678,.70710678),
  float2(.70710678,-.70710678),float2(-.70710678,-.70710678)
};
[unroll] for(int ri=0;ri<8;++ri) {
  [loop] for(int stepIndex=1;stepIndex<=12;++stepIndex) {
    float distancePx=(float)stepIndex;
    float2 tapVP=vp+rays[ri]*distancePx*pixelUV;
    if(any(tapVP<0.0)||any(tapVP>1.0)) continue;
    int sid=(int)round(SceneTextureLookup(ClampSceneTextureUV(ViewportUVToSceneTextureUV(tapVP,25),25),25,false).r);
    if(sid<224||sid>255) continue;
    float4 style=palette[sid-224];
    float width=clamp(style.a,0.0,8.0);
    if(width<=0.0||distancePx>width+4.0) continue;
    float objectDepth=SceneTextureLookup(ClampSceneTextureUV(ViewportUVToSceneTextureUV(tapVP,13),13),13,false).r;
    float tapDepth=SceneTextureLookup(ClampSceneTextureUV(ViewportUVToSceneTextureUV(tapVP,1),1),1,false).r;
    float tolerance=max(1.0,objectDepth*0.0002);
    if(objectDepth>tapDepth+tolerance || objectDepth>sceneDepth+tolerance) continue;
    float3 radiance=max(style.rgb,0.0);
    float peak=max(max(radiance.r,radiance.g),radiance.b);
    // Hue-preserving display compression keeps brightness independent of line width.
    float3 color=radiance/(1.0+peak);
    float opacity=1.0-exp(-peak*1.5);
    float core=(1.0-smoothstep(width-.5,width+.5,distancePx))*opacity;
    float outer=max(0.0,distancePx-width);
    float glow=exp(-0.65*outer*outer)*0.24*opacity;
    if(core>bestCore){bestCore=core;coreColor=color;}
    if(glow>bestGlow){bestGlow=glow;glowColor=color;}
  }
}
return lerp(source,coreColor,bestCore)+glowColor*bestGlow*(1.0-bestCore);
