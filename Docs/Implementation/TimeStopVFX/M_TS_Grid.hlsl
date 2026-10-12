// World-aligned repeated geometry; camera only controls residency and distant fade.
float d=length(WorldPos-Origin.xyz);
float cameraDistance=length(WorldPos-Camera);
float range=max(GridDrawDistance,6000);
float distanceFade=1-smoothstep(range*.75,range,cameraDistance);
float front=smoothstep(-40,15,SceneZ-PixelZ);
float visibility=lerp(.08,1,front);
float playerPixel=step(.5,PlayerMaskId)*(1-step(.5,abs(round(SceneStencil.r)-PlayerMaskId)))*(1-step(max(2,SceneZ*.002),abs(MaskDepth.r-SceneZ)));
float domain=(1-smoothstep(Radius-120,Radius+120,d))*step(1,Radius);
domain=lerp(domain,1,saturate(FullScene)*smoothstep(.65,1,StateWeight));
// Entry uses the same world wave and 160 cm feather in all three layers.
float effectiveD=lerp(d,min(d,max(ScanLimit,1)),saturate(FullScene));
float entryRadius=lerp(min(Radius,max(ScanLimit,1)),Radius,saturate(FullScene));
float entryFront=(1-smoothstep(entryRadius-160,entryRadius+160,effectiveD))*step(1,Radius);
domain=lerp(domain,entryFront,saturate(EntryPhase));
float densityAttenuation=.08+.92/(1+pow(cameraDistance/1800,2));
float mask=domain*visibility*distanceFade*densityAttenuation*(1-playerPixel);
float3 cell=abs(frac(WorldPos/500+.5)-.5)*500;
float node=1-smoothstep(4,10,length(cell));
return float3(.065,.13,.52)*Alpha*mask*(2.8+node*10);
