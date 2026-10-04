
float d=length(WorldPos-Origin.xyz);
float distanceFade=1-smoothstep(1800,3500,length(WorldPos-Camera));
float front=smoothstep(-40,15,SceneZ-PixelZ);
float visibility=lerp(.20,1,front)*smoothstep(100,250,length(WorldPos-Camera));
float mask=(1-smoothstep(Radius-120,Radius+120,d))*visibility*distanceFade*smoothstep(100,220,SceneZ);
float3 cell=abs(frac(WorldPos/500+.5)-.5)*500;
float node=1-smoothstep(4,10,length(cell));
return float3(.065,.13,.52)*Alpha*mask*(2.8+node*10);
