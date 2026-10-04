// Surface Facets prototype for UE 5.6.1 Post Process Custom node (float3).
// Keep existing inputs: Origin, Radius, BandWidth, Pulse, Boundary,
// Pixels, CellSize (legacy, unused), Rotation, Chroma and existing SceneTexture dependencies.
// Add: CellSizeWorld=160 cm, ReliefDepth=22 cm, DebugWorldCells=0,
//      SurfaceNormalWS = SceneTexture:WorldNormal Color.RGB (required graph dependency).
// Prefer Scene Color Before DOF / After DOF; world reconstruction after TSR requires testing.
// This is world-anchored SURFACE COLOR REFRACTION, not mesh displacement or ray tracing.
struct TSSurfaceFacets
{
 float2 hash(float2 p)
 {
  // The input is a fixed world-cell identifier. Never include time/camera coordinates.
  return frac(sin(float2(dot(p,float2(127.1,311.7)),dot(p,float2(269.5,183.3))))*43758.5453);
 }
 float2 vertex(float2 p, float2 salt)
 {
  return p+(hash(p+salt)-.5)*.46;
 }
 float height(float2 p, float2 salt)
 {
  return hash(p+salt+float2(41.71,93.23)).x*2-1;
 }
 bool barycentric(float2 p,float2 a,float2 b,float2 c,out float3 bary)
 {
  float2 e1=b-a,e2=c-a,v=p-a;
  float det=e1.x*e2.y-e1.y*e2.x;
  if(abs(det)<.00001){bary=float3(1,0,0);return false;}
  float u=(v.x*e2.y-e2.x*v.y)/det;
  float v2=(e1.x*v.y-v.x*e1.y)/det;
  bary=float3(1-u-v2,u,v2);
  return min(bary.x,min(bary.y,bary.z))>=-.0001;
 }
 float2 heightGradient(float2 a,float2 b,float2 c,float ha,float hb,float hc)
 {
  float2 e1=b-a,e2=c-a;
  float det=e1.x*e2.y-e1.y*e2.x;
  return float2((hb-ha)*e2.y-(hc-ha)*e1.y,e1.x*(hc-ha)-e2.x*(hb-ha))/det;
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
  float destinationNear=smoothstep(100,220,sampleDepth);
  float validDepth=step(.01,sampleDepth)*(1-step(1000000,sampleDepth));
  // Soften cross-object pulls. This is depth-based, not an object identity test.
  float threshold=max(55,sourceDepth*.06);
  float sameLayer=1-smoothstep(threshold,threshold*2.5,abs(sampleDepth-sourceDepth));
  return lerp(baseUV,bounded,onScreen*destinationNear*validDepth*sameLayer);
 }
};
TSSurfaceFacets F;
float2 vuv=GetViewportUV(Parameters);
float3 source=F.color(vuv);
float z=F.depth(vuv);
float sourceNear=smoothstep(80,200,z);
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
// Strict surface wave: no full-screen 58% pulse. Pulse=0 removes all production refraction.
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
float2 cell=floor(q);
float2 a=cell,b=cell+float2(1,0),c=cell+float2(1,1);
float ha=0,hb=0,hc=0;
float3 bary=float3(1,0,0);
float2 seed=cell;
bool found=false;
[loop]for(int yy=-1;yy<=1;yy++)
{
 [loop]for(int xx=-1;xx<=1;xx++)
 {
  float2 key=cell+float2(xx,yy);
  float2 k0=key,k1=key+float2(1,0),k2=key+float2(1,1),k3=key+float2(0,1);
  float2 v0=F.vertex(k0,salt),v1=F.vertex(k1,salt),v2=F.vertex(k2,salt),v3=F.vertex(k3,salt);
  if(F.barycentric(q,v0,v1,v2,bary))
  {
   a=v0;b=v1;c=v2;ha=F.height(k0,salt);hb=F.height(k1,salt);hc=F.height(k2,salt);
   seed=key+salt+float2(.13,.71);found=true;break;
  }
  if(F.barycentric(q,v0,v2,v3,bary))
  {
   a=v0;b=v2;c=v3;ha=F.height(k0,salt);hb=F.height(k2,salt);hc=F.height(k3,salt);
   seed=key+salt+float2(.83,.29);found=true;break;
  }
 }
 if(found)break;
}
if(!found)return source;
float2 random=F.hash(seed);
float height=dot(bary,float3(ha,hb,hc));
float2 gradient=F.heightGradient(a,b,c,ha,hb,hc);
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
 float minBary=min(bary.x,min(bary.y,bary.z));
 float edgeLine=1-smoothstep(.012,.028,minBary);
 idColor=lerp(idColor,float3(.015,.02,.025),edgeLine*.85);
 // Debug deliberately ignores Pulse/Radius for fixed-time multi-camera comparisons.
 result=lerp(result,idColor,debug*sourceNear*valid);
}
return result;

