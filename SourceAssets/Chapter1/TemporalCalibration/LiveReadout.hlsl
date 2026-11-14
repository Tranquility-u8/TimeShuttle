// Material custom node inputs: UV, ClockTime. The lab clock shows elapsed time
// from an art-directed offset, and the digit edges soften to their screen width.
float elapsed = fmod(floor(ClockTime) + 48248.0, 86400.0);
int hour = (int)floor(elapsed / 3600.0);
int minute = ((int)floor(elapsed / 60.0)) % 60;
int second = ((int)elapsed) % 60;
float2 scaled = (UV - float2(.04,.13)) / float2(.92,.74);
if (any(scaled<0) || any(scaled>1)) return 0;
int cell = min(7, (int)floor(scaled.x * 8));
float2 p = float2(frac(scaled.x * 8), scaled.y) - .5;
float aa = clamp(max(fwidth(p.y), fwidth(scaled.x)*8)*.8,.008,.09);
if (cell==2 || cell==5) {
    float d=length(float2(p.x*.58,abs(p.y)-.16));
    return 1-smoothstep(.045-aa,.045+aa,d);
}
int digit = cell==0 ? hour/10 : cell==1 ? hour%10 : cell==3 ? minute/10 : cell==4 ? minute%10 : cell==6 ? second/10 : second%10;
int masks[10]={63,6,91,79,102,109,125,7,127,111};
float2 endsA[7]={float2(-.25,-.42),float2(.29,-.37),float2(.29,.05),float2(-.25,.42),float2(-.29,.05),float2(-.29,-.37),float2(-.25,0)};
float2 endsB[7]={float2(.25,-.42),float2(.29,-.05),float2(.29,.37),float2(.25,.42),float2(-.29,.37),float2(-.29,-.05),float2(.25,0)};
float light=0;
[unroll] for (int i=0;i<7;i++) {
    float2 ba=endsB[i]-endsA[i],pa=p-endsA[i];
    float2 nearest=pa-ba*saturate(dot(pa,ba)/dot(ba,ba));
    float d=length(nearest*float2(.68,1));
    if ((masks[digit] & (1<<i))!=0) light=max(light,1-smoothstep(.035-aa,.035+aa,d));
}
return light;
