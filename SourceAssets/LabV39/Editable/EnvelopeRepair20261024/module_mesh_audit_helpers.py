"""Independent audit of exported semantic mesh vertices, not generator claims.

No Unreal/Blender mutation. Reconstructs horizontal sections from the actual
closed triangle meshes and compares them with the old R17 surface mesh.
"""
from pathlib import Path
import sys,json,math,collections,hashlib,time
WORKSPACE=Path(__file__).resolve().parents[5]
sys.path.insert(0,str(WORKSPACE/'tmp'/'lab-v13-python'))
from shapely.geometry import LineString,Polygon,Point,box
from shapely.ops import unary_union,polygonize
from shapely import set_precision

R=Path(__file__).resolve().parent
SRC=R.parent.parent/'R17'
G=1e-5
def sub(a,b):return tuple(x-y for x,y in zip(a,b))
def cross(a,b):return (a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0])
def dot(a,b):return sum(x*y for x,y in zip(a,b))
def rnd(v):return tuple(round(x,5) for x in v)

def geomrows(rows):
 return unary_union([Polygon(p['outer'],p.get('holes',[])) for p in rows])

def triangles(mesh):
 vs=mesh.get('world_verts',mesh.get('verts'))
 for f in mesh['faces']:
  for i in range(1,len(f)-1):yield vs[f[0]],vs[f[i]],vs[f[i+1]]

def topology(mesh):
 vs=mesh.get('world_verts',mesh.get('verts'))
 edge=collections.Counter();directed=collections.Counter();seen=set();duplicate=0;zero=0;vol=0.
 for f in mesh['faces']:
  key=tuple(sorted(rnd(vs[i]) for i in f))
  duplicate+=key in seen;seen.add(key)
  for a,b in zip(f,f[1:]+f[:1]):
   pa,pb=rnd(vs[a]),rnd(vs[b]);edge[tuple(sorted((pa,pb)))]+=1;directed[(pa,pb)]+=1
 for a,b,c in triangles(mesh):
  n=cross(sub(b,a),sub(c,a));zero+=dot(n,n)<1e-18
  vol+=dot(a,cross(b,c))/6
 bad=[(e,n) for e,n in edge.items() if n!=2]
 orient=[e for e in edge if directed[e]!=1 or directed[(e[1],e[0])]!=1]
 return {'name':mesh['name'],'signed_volume_m3':vol,'unpaired_edges':len(bad),'incorrect_edge_orientation':len(orient),'duplicate_faces':duplicate,'degenerate_triangles':zero,'examples':bad[:2]}

def section(mesh,z):
 """Cut triangles, preserve boundary orientation, polygonize and winding-fill."""
 segments=[]
 for a,b,c in triangles(mesh):
  pts=(a,b,c)
  if not min(p[2] for p in pts)<z<max(p[2] for p in pts):continue
  hits=[]
  for p,q in ((a,b),(b,c),(c,a)):
   # Canonical edge direction gives identical rounding on shared diagonals.
   # Opposite traversal can differ at an exact half-grid floating-point tie.
   if tuple(p)>tuple(q):p,q=q,p
   if (p[2]<z<q[2]) or (q[2]<z<p[2]):
    t=(z-p[2])/(q[2]-p[2]);hits.append((round(p[0]+t*(q[0]-p[0]),5),round(p[1]+t*(q[1]-p[1]),5)))
   elif abs(p[2]-z)<1e-8:hits.append((round(p[0],5),round(p[1],5)))
  hits=list(dict.fromkeys(hits))
  if len(hits)!=2:continue
  p,q=hits
  if p==q:continue
  n=cross(sub(b,a),sub(c,a));t=(-n[1],n[0])
  if dot(sub(q,p),t)<0:p,q=q,p
  segments.append((p,q))
 if not segments:return Polygon()
 lines=unary_union([LineString(s) for s in segments])
 result=[]
 for poly in polygonize(lines):
  pt=poly.representative_point();x,y=pt.x,pt.y;w=0
  for (ax,ay),(bx,by) in segments:
   side=(bx-ax)*(y-ay)-(by-ay)*(x-ax)
   if ay<=y<by and side>0:w+=1
   elif by<=y<ay and side<0:w-=1
  if w:result.append(poly)
 return set_precision(unary_union(result),G)

