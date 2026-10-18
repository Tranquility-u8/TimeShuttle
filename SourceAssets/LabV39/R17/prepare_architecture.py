"""R17 union-of-volumes construction: no coincident caps or overlapping wall faces."""
from pathlib import Path
import sys,json,math,collections,hashlib
sys.path.insert(0,'E:/Capstone/Test/tmp/lab-v13-python')
from shapely.geometry import Polygon,box,LineString
from shapely.geometry.polygon import orient
from shapely.ops import unary_union
from shapely import constrained_delaunay_triangles,set_precision
R=Path(__file__).resolve().parent
SRC=R/'revised-layout-geometry.json'
D=json.loads(SRC.read_text(encoding='utf8'))
OLD=json.loads(Path('E:/Capstone/Test/1002/LabFlow_v39/v39-geometry.json').read_text(encoding='utf8'))
def geom(k):return unary_union([Polygon(p['outer'],p.get('holes',[])) for p in D[k]]).buffer(0)
def polys(g):
 if g.is_empty:return []
 if g.geom_type=='Polygon':return [g]
 return [p for q in getattr(g,'geoms',[]) for p in polys(q)]
volumes=[];report={'source_sha256':hashlib.sha256(SRC.read_bytes()).hexdigest(),'opening_profiles':[],'warnings':[]}
def vol(name,g,z0,z1):
 g=set_precision(g,.00001).buffer(0)
 if not g.is_empty and z1>z0:volumes.append((name,g,round(z0,5),round(z1,5)))
f0=geom('floor_lower').union(geom('control_clear'))
f1=geom('floor_upper')
w0=geom('walls_lower');w1=geom('wallPolygons')
control=geom('control_clear');cring=control.buffer(.75,join_style=2).difference(control)
sc0=geom('scenic_lower');sc1=geom('scenic_upper')
so0=geom('scenic_outer_lower');so1=geom('scenic_outer_upper')
court=geom('research_court');trainenv=geom('training').buffer(.6,join_style=2)
vol('A slab',f0.union(w0).union(cring).union(sc0).union(so0),-.45,0)
public_voids=unary_union([box(-29.4,-10,29.4,53.1),box(-80,37,80,54),control.buffer(5.3,join_style=2),court])
infill=f0.difference(f1).difference(public_voids)
slabB=unary_union([f1,infill,geom('retired_roof'),sc1]).difference(control).difference(court)
slabB=slabB.difference(geom('e4_preserved_core').difference(f1))
vol('B slab and lower roof consolidated',slabB,4.95,5.4)
vol('A walls',w0,0,5.4)
vol('B walls',w1.difference(trainenv),5.4,14)
vol('Training walls',w1.intersection(trainenv),5.4,13.4)

def lines(g):
 if g.is_empty:return []
 if g.geom_type in ('LineString','LinearRing'):return [g]
 return [p for q in getattr(g,'geoms',[]) for p in lines(q)]
def profile(o):
 wall=w1 if o['z'] else w0
 vertical=o['axis']=='v';normal=o['x'] if vertical else o['y'];t=o['y'] if vertical else o['x'];found=[]
 for side in [-1,1]:
  for offset in [.015,.04,.10,.25,.5,1.]:
   at=t+side*(o['width']/2+offset)
   ln=LineString([(normal-2,at),(normal+2,at)]) if vertical else LineString([(at,normal-2),(at,normal+2)])
   cand=[]
   for q in lines(wall.intersection(ln)):
    a,b=(q.bounds[0],q.bounds[2]) if vertical else (q.bounds[1],q.bounds[3])
    if b-a>.02 and a-.4<=normal<=b+.4:cand.append((abs((a+b)/2-normal),a,b))
   if cand:
    _,a,b=min(cand);found.append((a,b));break
 if not found:return None
 a=max(q[0] for q in found);b=min(q[1] for q in found)
 if b-a<.02:a,b=found[0]
 if b-a>1.3:a,b=normal-.3,normal+.3
 report['opening_profiles'].append({'id':o['id'],'range':[a,b]})
 return box(a,t-o['width']/2-.002,b,t+o['width']/2+.002) if vertical else box(t-o['width']/2-.002,a,t+o['width']/2+.002,b)

for o in D['openings']:
 if o['id']=='C0':continue
 p=profile(o)
 if p is None:report['warnings'].append('No header profile '+o['id']);continue
 base=5.4 if o['z'] else 0;top=14 if o['z'] else 5.4
 if o['z'] and p.intersection(trainenv).area>p.area*.5:top=13.4
 sill=o.get('sill',.9 if o['kind']=='window' else 0)
 vol('Header '+o['id'],p,base+sill+o['height'],top)
 if sill:vol('Sill '+o['id'],p,base,base+sill)
 # The service duct is an elevated aperture, cut separately below.

c0=next(o for o in D['openings'] if o['id']=='C0')
gap=box(c0['x']-c0['width']/2,-10.8,c0['x']+c0['width']/2,-9.15)
win=unary_union([box(w['x']-.6,w['y1'],w['x']+.6,w['y2']) for w in D['control_windows']])
for a,b in [(0,4.8),(4.8,6.3),(6.3,9.3),(9.3,12.3),(12.3,15.3),(15.3,25)]:
 p=cring.difference(gap) if a<4.8 else cring
 if a in (6.3,12.3):p=p.difference(win)
 vol('Control enclosure',p,a,b)
vol('Control roof',control.union(cring),25,25.4)
vol('Scenic lower base',sc0,0,5.4)
vol('Scenic outer lower',so0,0,5.4)
vol('Scenic outer upper',so1,5.4,17.4)
for z in [11.4,17.4]:vol('Scenic slab',sc1,z-.3,z)
roof=unary_union([f0,f1,w0,w1,court,geom('retired_roof')]).difference(control.buffer(5.3,join_style=2)).difference(trainenv)
vol('Main roof',roof,14,14.45)
vol('Training roof',trainenv,13.4,13.8)
platform=geom('duct_platforms')
vol('Duct landing platforms',platform,7.6,7.8)
for b in D['jump_blocks']:vol('Jump '+b['id'],box(*b['bounds']),5.4,b['top_z_m'])

# A continuous sectional solid removes all contact caps, including floor/wall
# intersections and adjacent door lintels. No offset-band trick is used.
zs=sorted(set(z for n,g,a,b in volumes for z in [a,b]+([7.8,9.2] if n=='B walls' else [])))
layers=[]
duct=geom('duct_clear')
for a,b in zip(zs,zs[1:]):
 mid=(a+b)/2
 p=unary_union([g for n,g,z0,z1 in volumes if z0<=mid<z1]).buffer(0)
 if 7.8<mid<9.2:p=p.difference(duct)
 layers.append(set_precision(p,.00001))
parts=[]
for i,(z0,z1,g) in enumerate(zip(zs,zs[1:],layers)):
 if g.is_empty:continue
 verts=[];faces=[];mats=[];index={}
 def vi(x,y,z):
  v=(round(x,5),round(y,5),round(z,5))
  if v not in index:index[v]=len(verts);verts.append(v)
  return index[v]
 def cap(p,z,up,mat):
  for q in polys(set_precision(p,.00001)):
   for t in constrained_delaunay_triangles(q).geoms:
    xy=list(orient(t,1).exterior.coords)[:-1]
    if not up:xy.reverse()
    faces.append([vi(x,y,z) for x,y in xy]);mats.append(mat)
 prev=layers[i-1] if i else Polygon();nxt=layers[i+1] if i+1<len(layers) else Polygon()
 cap(g.difference(nxt),z1,True,'Floor' if z1 in (0,5.4,6.,6.6,7.2,7.8) else 'Wall')
 cap(g.difference(prev),z0,False,'Wall')
 for p in polys(g):
  p=orient(p,1)
  for ring in [p.exterior,*p.interiors]:
   pts=list(ring.coords)
   for a,b in zip(pts,pts[1:]):
    faces.append([vi(*a,z0),vi(*b,z0),vi(*b,z1),vi(*a,z1)]);mats.append('Wall')
 parts.append({'name':f'SM_LabR17_Structure_{i:02d}','verts':verts,'faces':faces,'face_materials':mats,'z0':z0,'z1':z1})

# Since layers are disjoint and caps only cover differences, interiors have no
# coplanar faces. Validate duplicate exact faces across all export chunks.
seen=set();dups=0
for p in parts:
 for f in p['faces']:
  key=tuple(sorted(tuple(p['verts'][j]) for j in f))
  dups+=key in seen;seen.add(key)
assert dups==0
report.update(parts=len(parts),vertices=sum(len(p['verts']) for p in parts),faces=sum(len(p['faces']) for p in parts),exact_duplicate_faces=dups,slab_A_area=f0.area,slab_B_area=slabB.area,method='Boolean union per height interval; only exposed caps and boundary walls are emitted',duct_clear=[2.1,1.5,1.4],training_clear=[20,34.7,8])
(R/'architecture_meshes.json').write_text(json.dumps({'parts':parts,'report':report},ensure_ascii=False),encoding='utf8')
(R/'architecture_report.json').write_text(json.dumps(report,indent=2),encoding='utf8')
print(json.dumps({k:v for k,v in report.items() if k!='opening_profiles'},ensure_ascii=False))
