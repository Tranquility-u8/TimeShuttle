"""Reproducible numerical texture; Python + NumPy + Pillow, no UE/plugin dependency.
RGBA: slope XY encoded [-4,4], interpolated height [-1,1], per-triangle ID.
Periodic Delaunay via Bowyer-Watson; points/heights repeat across 9 tiles.
Run with output directory as optional first argument. Does not edit UE assets.
"""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image,ImageDraw

OUT=Path(sys.argv[1]) if len(sys.argv)>1 else Path(__file__).parent/'NoiseSource'
OUT.mkdir(parents=True,exist_ok=True)
rng=np.random.default_rng(20261011); L=16.; N=256; RES=1024
points=[]
while len(points)<N:
 p=rng.uniform(0,L,2)
 if points:
  d=np.abs(np.asarray(points)-p);d=np.minimum(d,L-d)
  # Spatially varied exclusion radius: no grid and no regular spacing.
  radius=.38+.18*(.5+.5*np.sin(p[0]*.7)*np.cos(p[1]*.51))
  if np.min(np.sum(d*d,axis=1))<radius**2:continue
 points.append(p)
base=np.array(points); heights=rng.uniform(-1,1,N)
pts=np.concatenate([base+[x*L,y*L] for y in [-1,0,1] for x in [-1,0,1]])
heights=np.tile(heights,9)
P=np.concatenate([pts,np.array([[-500,-500],[500,-500],[0,500]])])
def circles(tris):
 a,b,c=P[tris[:,0]],P[tris[:,1]],P[tris[:,2]]
 u=b-a;v=c-a;det=2*(u[:,0]*v[:,1]-u[:,1]*v[:,0])
 u2=(u*u).sum(1);v2=(v*v).sum(1)
 center=a+np.stack([(u2*v[:,1]-v2*u[:,1])/det,(v2*u[:,0]-u2*v[:,0])/det],1)
 return center,((center-a)**2).sum(1)
tris=np.array([[len(pts),len(pts)+1,len(pts)+2]])
cc,rr=circles(tris)
for i,p in enumerate(pts):
 bad=((cc-p)**2).sum(1)<rr+1e-9
 edges=np.concatenate([tris[bad][:,[0,1]],tris[bad][:,[1,2]],tris[bad][:,[2,0]]])
 edges=np.sort(edges,axis=1);edges,count=np.unique(edges,axis=0,return_counts=True)
 edges=edges[count==1];new=np.column_stack([edges,np.full(len(edges),i)])
 nc,nr=circles(new);tris=np.concatenate([tris[~bad],new]);cc=np.concatenate([cc[~bad],nc]);rr=np.concatenate([rr[~bad],nr])
tris=tris[(tris<len(pts)).all(1)]
coords=P[tris];lo=coords.min(1);hi=coords.max(1)
tris=tris[((lo<L)&(hi>0)).all(1)]
data=np.zeros((RES,RES,4));coverage=np.zeros((RES,RES),dtype=np.uint8)
areas=[];angles=[];slopes=[];triangle_ids=[]
preview=Image.new('RGB',(RES,RES));draw=ImageDraw.Draw(preview)
for tri in tris:
 a,b,c=P[tri]; u=b-a;v=c-a;det=np.linalg.det(np.stack([u,v]))
 h=heights[tri];g=np.linalg.solve(np.stack([u,v]),h[1:]-h[0])
 # Limit unusually sharp shards without changing topology or timings.
 g_encoded=np.clip(g,-4,4)
 ident=sorted((tri%N).tolist());seed=(ident[0]*73856093 ^ ident[1]*19349663 ^ ident[2]*83492791)&0xffffffff
 color=np.random.default_rng(seed).uniform(.14,.92,3)
 tag=(seed%251+2)/255
 bounds=np.array([a,b,c]);pmin=np.maximum(np.floor(bounds.min(0)/L*RES).astype(int),0);pmax=np.minimum(np.ceil(bounds.max(0)/L*RES).astype(int),RES)
 if np.any(pmin>=pmax):continue
 xx,yy=np.meshgrid(np.arange(pmin[0],pmax[0]),np.arange(pmin[1],pmax[1]))
 q=np.stack([(xx+.5)/RES*L,(yy+.5)/RES*L],-1)-a
 s=(q[...,0]*v[1]-q[...,1]*v[0])/det;t=(u[0]*q[...,1]-u[1]*q[...,0])/det
 inside=(s>=-1e-8)&(t>=-1e-8)&(s+t<=1+1e-8)
 Y=yy[inside];X=xx[inside];hh=h[0]+s[inside]*(h[1]-h[0])+t[inside]*(h[2]-h[0])
 data[Y,X,:2]=g_encoded/8+.5;data[Y,X,2]=hh*.5+.5;data[Y,X,3]=tag;coverage[Y,X]+=1
 draw.polygon([tuple(v/L*RES) for v in bounds],fill=tuple((color*255).astype(int)),outline=(12,16,20),width=2)
 center=bounds.mean(0)
 if ((center>=0)&(center<L)).all():
  areas.append(abs(det)*.5);slopes.append(g.tolist());triangle_ids.append(ident)
  for edge in [u,v,c-b]:angles.append(float(np.arctan2(edge[1],edge[0])%np.pi))
assert (coverage==1).all(),dict(missing=int((coverage==0).sum()),overlap=int((coverage>1).sum()))
assert len(areas)==N*2,len(areas)
rgba=np.round(np.clip(data,0,1)*255).astype('uint8')
Image.fromarray(rgba).save(OUT/'T_TS_FacetNoise.png')
preview.save(OUT/'facet-topology.png')
areas=np.array(areas);hist=np.histogram(angles,bins=12,range=(0,np.pi))[0]
report=dict(seed=20261011,points=N,triangles=len(areas),resolution=RES,tile_cells=L,channels='RG slope [-4,4]; B height [-1,1]; A facet ID',uncovered_pixels=int((coverage==0).sum()),overlap_pixels=int((coverage>1).sum()),area_min=float(areas.min()),area_max=float(areas.max()),area_cv=float(areas.std()/areas.mean()),edge_direction_histogram=hist.tolist(),clipped_gradient_components=int((np.abs(slopes)>4).sum()),source_is_periodic=True)
(OUT/'generation.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report))
