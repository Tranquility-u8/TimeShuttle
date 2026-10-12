// Surface Facets prototype for UE 5.6.1 Post Process Custom node (float3).
// Keep existing inputs: Origin, Radius, BandWidth, Pulse, Boundary,
// Pixels, CellSize (legacy, unused), Rotation, Chroma and existing SceneTexture dependencies.
// Add: CellSizeWorld=160 cm, ReliefDepth=22 cm, DebugWorldCells=0,
//      SurfaceNormalWS = SceneTexture:WorldNormal Color.RGB (required graph dependency).
// Validated project setting: Scene Color After Tonemapping. FacetNoise is linear RGBA data.
// FacetNoise RG = slope [-4,4], B = height [-1,1], A = ID; NoiseSeed = static offset.
// This is world-anchored SURFACE COLOR REFRACTION, not mesh displacement or ray tracing.
struct TSSurfaceFacets
{
 float playerId;
 float isPlayer(float2 v,float sceneDepth)
 {
  float sid=SceneTextureLookup(ClampSceneTextureUV(ViewportUVToSceneTextureUV(v,25),25),25,false).r;
  float customZ=SceneTextureLookup(ClampSceneTextureUV(ViewportUVToSceneTextureUV(v,13),13),13,false).r;
  return step(.5,playerId)*(1-step(.5,abs(round(sid)-playerId)))*(1-step(max(2,sceneDepth*.002),abs(customZ-sceneDepth)));
 }
 float2 hash(float2 p)
 {
  // The input is a fixed world-cell identifier. Never include time/camera coordinates.
  return frac(sin(float2(dot(p,float2(127.1,311.7)),dot(p,float2(269.5,183.3))))*43758.5453);
 }
 float2 projectedUV(float3 p)
 {
  float4 clip=mul(float4(p,1),PrimaryView.TranslatedWorldToClip);
  return (clip.xy/max(clip.w,.001))*float2(.5,-.5)+.5;
 }
 float depth(float2 v)
 {
  return SceneTextureLookup(ClampSceneTextureUV(ViewportUVToSceneTextureUV(v,1),1),1,false).r;
 }
 float3 color(float2 v)
 {
  return SceneTextureLookup(ClampSceneTextureUV(ViewportUVToSceneTextureUV(v,14),14),14,false).rgb;
 }
 float2 protectedUV(float2 baseUV,float2 candidate,float sourceDepth)
 {
  // Reject out-of-frame samples instead of smearing the clamped screen edge.
  float onScreen=step(.001,candidate.x)*step(candidate.x,.999)*step(.001,candidate.y)*step(candidate.y,.999);
  float2 bounded=clamp(candidate,.001,.999);
  float sampleDepth=depth(bounded);
  float destinationNear=1-isPlayer(bounded,sampleDepth);
  float validDepth=step(.01,sampleDepth)*(1-step(1000000,sampleDepth));
  // Soften cross-object pulls. This is depth-based, not an object identity test.
  float threshold=max(55,sourceDepth*.06);
  float sameLayer=1-smoothstep(threshold,threshold*2.5,abs(sampleDepth-sourceDepth));
  return lerp(baseUV,bounded,onScreen*destinationNear*validDepth*sameLayer);
 }
};
TSSurfaceFacets F;
F.playerId=PlayerMaskId;
float2 vuv=GetViewportUV(Parameters);
float3 source=F.color(vuv);
float z=F.depth(vuv);
float sourceNear=1-F.isPlayer(vuv,z);
float valid=step(.01,z)*(1-step(1000000,z));
if(valid*sourceNear<.0001)return source;

float2 screenXY=vuv*float2(2,-2)+float2(-1,1);
float4 hp=mul(float4(GetScreenPositionForProjectionType(screenXY,z),z,1),PrimaryView.ScreenToTranslatedWorld);
float3 pT=hp.xyz/max(hp.w,.00001);
float3 originT=DFFastToTranslatedWorld(Origin.xyz,PrimaryView.PreViewTranslation);
float3 zeroT=DFFastToTranslatedWorld(float3(0,0,0),PrimaryView.PreViewTranslation);
float3 pWorld=pT-zeroT;
float distanceToOrigin=length(pT-originT);
float band=max(BandWidth,1);
float wave=1-smoothstep(band*.35,band,abs(distanceToOrigin-Radius));
// Entry uses the same world wave and 160 cm feather in all three layers.
float effectiveD=lerp(distanceToOrigin,min(distanceToOrigin,max(ScanLimit,1)),saturate(FullScene));
float entryRadius=lerp(min(Radius,max(ScanLimit,1)),Radius,saturate(FullScene));
float entryFront=(1-smoothstep(entryRadius-160,entryRadius+160,effectiveD))*step(1,Radius);
// Surface-local decay: changing total scan range never shortens this lifetime.
float localAge=max(0,(Radius-effectiveD)/max(ScanSpeed,1));
float hold=max(HoldSeconds,0);
float trail=1-smoothstep(hold,hold+max(FadeSeconds,.05),localAge);
wave=lerp(wave,entryFront*trail,saturate(EntryPhase));
// Pulse only gates entry activation/reset; local age owns entry decay.
float amp=saturate(Pulse)*wave*sourceNear*valid*step(1,Radius);
float debug=saturate(DebugWorldCells);
if(amp<.0001 && debug<.0001)return source;

float normalLength=dot(SurfaceNormalWS,SurfaceNormalWS);
if(normalLength<.01)return source;
float3 n=SurfaceNormalWS*rsqrt(normalLength);
float3 an=abs(n);
// Dominant WORLD normal chooses the projection; never use CameraVector or screen normals.
float3 axisU=float3(1,0,0),axisV=float3(0,1,0);
float2 salt=float2(19.1,71.7);
if(an.x>=an.y && an.x>=an.z)
{
 axisU=float3(0,1,0);axisV=float3(0,0,1);salt=float2(113.2,241.8);
}
else if(an.y>=an.z)
{
 axisU=float3(1,0,0);axisV=float3(0,0,1);salt=float2(367.3,419.6);
}
float size=max(CellSizeWorld,20);
float2 q=float2(dot(pWorld,axisU),dot(pWorld,axisV))/size;
// Periodic Delaunay texture: 256 random sites / 512 irregular triangles.
// Fixed world rotation/offset only: no camera, time, or scan-origin noise input.
float cs=.920504853, sn=.390731128; // 23 degrees
float2 qr=float2(cs*q.x-sn*q.y,sn*q.x+cs*q.y);
float2 noiseUV=(qr+salt+float2(NoiseSeed*1.618,NoiseSeed*.731))/16;
float4 facet=Texture2DSample(FacetNoise,FacetNoiseSampler,noiseUV);
float2 bakedGradient=(facet.rg-.5)*8;
float2 gradient=float2(cs*bakedGradient.x+sn*bakedGradient.y,-sn*bakedGradient.x+cs*bakedGradient.y);
float height=facet.b*2-1;
float2 seed=float2(round(facet.a*255),13.71);
float2 random=F.hash(seed);
float3 gradientWS=axisU*gradient.x+axisV*gradient.y;
gradientWS-=n*dot(gradientWS,n);
float relief=max(ReliefDepth,0);
float tilt=max(Rotation,0)/.4;
float3 fakeNormal=normalize(n-gradientWS*(relief/size)*tilt);
// Fixed shared-vertex heights produce both positive and negative relief and flat facet slopes.
// Project both original and virtual displaced positions; the UV subtraction cancels base offsets.
float3 displacement=(n*height*.30-gradientWS*.85*tilt)*relief*amp;
float2 offset=F.projectedUV(pT+displacement)-F.projectedUV(pT);
float aspect=View.ViewSizeAndInvSize.x/View.ViewSizeAndInvSize.y;
float2 refSize=float2(1080*aspect,1080);
float2 pixelOffset=offset*refSize;
float maxPixels=max(Pixels,0);
pixelOffset*=min(1,maxPixels/max(length(pixelOffset),.001));
offset=pixelOffset/refSize;
float border=min(min(vuv.x,1-vuv.x),min(vuv.y,1-vuv.y));
float edgeFade=smoothstep(0,.035,border);
offset*=edgeFade;
float2 sampleV=F.protectedUV(vuv,vuv+offset,z);
float3 warped=F.color(sampleV);
// Chroma follows the same world-projected direction and independently protects destination depth.
float2 chromaDirection=pixelOffset/max(length(pixelOffset),.001);
float2 chroma=chromaDirection*max(Chroma,0)*amp*edgeFade/refSize;
float2 redUV=F.protectedUV(vuv,sampleV+chroma,z);
float2 blueUV=F.protectedUV(vuv,sampleV-chroma,z);
warped.r=F.color(redUV).r;
warped.b=F.color(blueUV).b;
// A fixed world light cue emphasizes slope; it does not replace scene lighting or modify normals.
float3 cue=normalize(float3(.37,-.48,.79));
float normalCue=dot(fakeNormal,cue)-dot(n,cue);
float shade=clamp(1+amp*(normalCue*.85+height*.07),.72,1.28);
float3 result=max(0,warped*shade);
if(debug>.0001)
{
 float3 idColor=.18+.72*float3(random,F.hash(seed+float2(83,11)).x);
 float edgeLine=saturate(length(fwidth(bakedGradient))*.35);
 idColor=lerp(idColor,float3(.015,.02,.025),edgeLine*.85);
 // Debug deliberately ignores Pulse/Radius for fixed-time multi-camera comparisons.
 result=lerp(result,idColor,debug*sourceNear*valid);
}
return result;

