// Vertex-stage WPO: shear each endpoint to its shared polyline miter plane.
// Direction and Origin are world-space; UV is the original strip UV.
float3 d = normalize(Direction.xyz);
float3 right = normalize(cross(float3(0,0,1), d));
float lateral = dot(Position.xyz - Origin.xyz, right);
return d * lateral * lerp(StartShear, EndShear, saturate(UV.x));
