// UV-space analytic geometry: direction is camera-yaw relative, Y is screen-down.
float2 d = Direction.xy / max(length(Direction.xy), 0.0001);
float2 p = (UV - .5) * 2;
float2 q = float2(dot(p,float2(-d.y,d.x)),dot(p,d));
float u = saturate(Urgency);
float beat = .5 + .5*sin(RealTime*(8.5+u*4.0));
float entrance = 1.0 + .07*exp(-Age*22.0);
q /= entrance;
// A concave dart, filled and faceted, pointing inward toward the threatened player.
float2 v[4] = {float2(0,.59),float2(.215,.825),float2(0,.758),float2(-.215,.825)};
float dist2=100; float signv=1;
[unroll] for(int i=0;i<4;i++) {
 float2 a=v[i], b=v[(i+1)%4], e=b-a, w=q-a;
 float2 z=w-e*saturate(dot(w,e)/dot(e,e)); dist2=min(dist2,dot(z,z));
 bool c1=q.y>=a.y,c2=q.y<b.y,c3=e.x*w.y>e.y*w.x;
 if((c1&&c2&&c3)||(!c1&&!c2&&!c3))signv=-signv;
}
float sd=sqrt(dist2)*signv;
float aa=max(fwidth(sd)*.8,.0015);
float body=1-smoothstep(-aa,aa,sd);
float rim=exp(-abs(sd)*330)*body;
float glow=exp(-max(sd,0)*95)*(1-body);
float shadow=exp(-max(sd-.005,0)*160)*(1-body);
float r=length(q), angle=atan2(q.x,q.y);
float cap=saturate(1-abs(angle)/.53);
float arcD=abs(r-.478)-(.006+.012*pow(cap,1.2));
float arc=(1-smoothstep(-.002,.002,arcD))*smoothstep(0,.14,cap);
float arcGlow=exp(-max(arcD,0)*130)*smoothstep(0,.2,cap);
float inner=(1-smoothstep(.001,.003,abs(r-.435)-.0014))*smoothstep(.12,.6,cap)*.24;
// A restrained amber-to-vermilion body, with an ivory hot edge and darker second facet.
float3 warm=lerp(float3(1,.20,.025),float3(1,.025,.018),u);
float facet=lerp(.60,1,smoothstep(-.16,.16,q.x));
float3 fill=warm*(.68+.32*saturate((.85-q.y)/.24))*facet;
float3 hot=lerp(float3(1,.60,.22),float3(1,.31,.16),u);
float seam=exp(-abs(q.x)*260)*body*.30;
float3 color=fill*body+hot*(rim*.78+seam)+warm*(glow*.40+arc*.94+arcGlow*.12+inner);
// FullStop retains danger-red but adds a narrow cold edge to acknowledge suspended time.
color+=float3(.13,.78,1)*rim*Frozen*.42;
float alpha=max(max(body*.95,arc*.86),max(glow*.27,arcGlow*.12));
alpha=max(alpha,shadow*.34);
color=lerp(float3(.025,.007,.008),color,saturate(body+glow+arc+arcGlow+inner));
float pulse=.90+.10*beat;
return float4(color,saturate(alpha*Presence*pulse));
