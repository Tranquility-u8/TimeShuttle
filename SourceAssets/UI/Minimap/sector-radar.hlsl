// Native UI material reference. Code is embedded into M_SectorRadar when authored.
// Camera-relative, clockwise bearing: north/front=0; right=4; rear=8; left=12.
// Sixteen occupied direction sectors aggregate every eligible projectile, without
// allocating per-projectile radar widgets or hiding threats at a count limit.
float2 p = UV - 0.5;
float radius = length(p);
float aa = max(fwidth(radius), 0.001);
const float diskRadius = 0.450;
const float bandInnerRadius = 0.390;
float disk = 1.0 - smoothstep(diskRadius - aa, diskRadius + aa, radius);
float angle = atan2(p.x, -p.y);
float phase = frac(angle / 6.28318530718 + 1.0) * 16.0;
// Bearings are still spaced 22.5 degrees apart. Only four nearby bearings
// can reach this pixel, including the softer light beyond either arc end.
float nearest = 16.0;
[unroll]
for (int offset = -1; offset <= 2; ++offset)
{
    int sector = ((int)floor(phase) + offset + 16) % 16;
    float4 flags = sector < 4 ? SectorsA : sector < 8 ? SectorsB :
                   sector < 12 ? SectorsC : SectorsD;
    if (flags[sector % 4] > 0.5)
        nearest = min(nearest, abs(frac(phase) - offset));
}
// Half span 21.6 degrees leaves a small gap between arcs 45 degrees apart.
float angularAA = clamp(aa / (max(radius, aa) * 0.39269908), 0.003, 0.08);
float arc = 1.0 - smoothstep(0.96 - angularAA, 0.96 + angularAA, nearest);
float band = arc * smoothstep(bandInnerRadius - aa, bandInnerRadius + aa, radius);
float sideFalloff = 1.0 - smoothstep(0.62, 1.55, nearest);
float radial = saturate(radius / bandInnerRadius);
float inwardDistance = max(bandInnerRadius - radius, 0.0);
float wash = sideFalloff * (0.24 * radial * radial + 0.10 * exp2(-24.0 * inwardDistance))
             * smoothstep(0.025, 0.095, radius) * saturate(ThreatOpacity);
float coneAngle = radians(ViewHalfAngle);
float cone = (1.0 - smoothstep(coneAngle - 0.015, coneAngle + 0.015, abs(angle))) *
             smoothstep(0.012, 0.040, radius);
float alpha = saturate(BackdropOpacity);
float3 premult = float3(0.20, 0.225, 0.255) * alpha;
float a = cone * 0.12;
premult = float3(0.68, 0.74, 0.80) * a + premult * (1.0 - a);
alpha = a + alpha * (1.0 - a);
premult = float3(0.75, 0.12, 0.12) * wash + premult * (1.0 - wash);
alpha = wash + alpha * (1.0 - wash);
a = band * saturate(ThreatOpacity);
premult = float3(1.0, 0.15, 0.115) * a + premult * (1.0 - a);
alpha = a + alpha * (1.0 - a);
float dot = 1.0 - smoothstep(0.007 - aa, 0.007 + aa, radius);
premult = float3(0.94, 0.97, 1.0) * dot + premult * (1.0 - dot);
alpha = dot + alpha * (1.0 - dot);
// Apply coverage once so the base, warning rim and spill share one silhouette.
return float4(premult / max(alpha, 0.00001), alpha * disk);
