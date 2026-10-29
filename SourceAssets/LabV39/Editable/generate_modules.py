"""Generate editable, closed semantic modules without changing the R17 source.

Reads the source generator only up to its write-free volume declaration.
Coordinates are metres in Blender world space. Module verts are LOCAL; use
pivot + rotation_z_degrees to place them. world_verts is included explicitly.
"""
from pathlib import Path
import sys, json, math, hashlib, collections, time, argparse, importlib.util
ROOT = Path(__file__).resolve().parent
if importlib.util.find_spec('shapely') is None:
    sys.path.insert(0, str(ROOT.parents[3]/'tmp/lab-v13-python'))
from shapely.geometry import Polygon, box, Point, LineString
from shapely.geometry.polygon import orient
from shapely.ops import unary_union
from shapely import set_precision, constrained_delaunay_triangles

SOURCE = ROOT.parent/'R17'
GRID = .00001
EPS = 1e-8


def clean(g):
    return set_precision(g, GRID).buffer(0)


def polys(g):
    if g.is_empty: return []
    if g.geom_type == 'Polygon': return [g]
    return [p for q in getattr(g, 'geoms', []) for p in polys(q)]


def coords(g):
    return [xy for p in polys(g) for r in [p.exterior, *p.interiors]
            for xy in list(r.coords)[:-1]]


def serial(g):
    return [{'outer': list(p.exterior.coords),
             'holes': [list(r.coords) for r in p.interiors]} for p in polys(g)]


def digest(b): return hashlib.sha256(b).hexdigest()


def rect(g):
    return g.geom_type == 'Polygon' and not g.interiors and abs(box(*g.bounds).area-g.area) < 1e-7


def strips(component, swap=False):
    """Exact local strip decomposition; merge collinear rectangles back to runs."""
    if rect(component): return [component]
    axis = 0 if swap else 1
    levels = sorted({round(xy[axis], 5) for xy in coords(component)})
    bx = component.bounds
    pending, custom, completed = {}, [], []
    for a, b in zip(levels, levels[1:]):
        cutter = box(a, bx[1]-1, b, bx[3]+1) if swap else box(bx[0]-1, a, bx[2]+1, b)
        found = {}
        for p in polys(clean(component.intersection(cutter))):
            if p.area < EPS: continue
            if not rect(p):
                custom.append(p); continue
            bb = tuple(round(v, 5) for v in p.bounds)
            key = (bb[1], bb[3]) if swap else (bb[0], bb[2])
            old = pending.pop(key, None)
            if old is not None:
                joined = clean(old.union(p))
                if rect(joined): p = joined
                else: completed.append(old)
            found[key] = p
        completed.extend(pending.values()); pending = found
    completed.extend(pending.values())
    return completed+custom


def wall_partition(g):
    result = []
    for p in polys(g):
        choices = [strips(p), strips(p, True)]
        def score(pp):
            # Prefer fewer practical long walls; penalize almost-zero strips.
            return len(pp)+4*sum(min(q.bounds[2]-q.bounds[0], q.bounds[3]-q.bounds[1]) < .03 for q in pp)
        result.extend(min(choices, key=score))
    return sorted(result, key=lambda p: tuple(round(v, 5) for v in p.bounds))


def semantic_wall_parts(parts, nearby_rooms):
    """Split a straight run when its adjacent room changes; absorb tiny joints."""
    result=[]
    for p in parts:
        x0,y0,x1,y1=p.bounds;axis=0 if x1-x0>=y1-y0 else 1
        low,high=(x0,x1) if axis==0 else (y0,y1)
        cuts=[]
        if rect(p) and high-low>6 and min(x1-x0,y1-y0)<2:
            for rid,room in nearby_rooms:
                touch=room.intersection(p.buffer(.025))
                if touch.area<EPS:continue
                lo,hi=(touch.bounds[0],touch.bounds[2]) if axis==0 else (touch.bounds[1],touch.bounds[3])
                cuts.extend(q for q in (lo,hi) if low+1<q<high-1)
        clusters=[]
        for q in sorted(cuts):
            if clusters and q-clusters[-1][-1]<1.0:clusters[-1].append(q)
            else:clusters.append([q])
        limits=[low]+[sum(c)/len(c) for c in clusters]+[high]
        for a,b in zip(limits,limits[1:]):
            clip=box(a,y0-1,b,y1+1) if axis==0 else box(x0-1,a,x1+1,b)
            result.extend(polys(clean(p.intersection(clip))))
    # Tiny bevel/transition pieces belong to their adjoining wall, not dozens
    # of inconvenient 3cm Actors. This never fills or approximates a shape.
    for i in sorted(range(len(result)),key=lambda i:result[i].area):
        p=result[i]
        if p is None:continue
        bb=p.bounds
        if min(bb[2]-bb[0],bb[3]-bb[1])>=.15:continue
        candidates=[]
        for j,q in enumerate(result):
            if j==i or q is None:continue
            shared=p.boundary.intersection(q.boundary).length
            if shared<.005:continue
            merged=clean(p.union(q))
            if merged.geom_type!='Polygon':continue
            candidates.append((not rect(merged),-shared,-q.area,j,merged))
        if candidates:
            *_,j,merged=min(candidates,key=lambda c:c[:4])
            result[j]=merged;result[i]=None
    return sorted([p for p in result if p is not None],key=lambda p:tuple(round(v,5) for v in p.bounds))


def floor_partition(g, rooms, tile=18.):
    """Room interiors first, residual halls tiled; attach thin wall-support strips."""
    cells, remain = [], g
    for rid, room in rooms:
        take = clean(remain.intersection(room))
        if take.area > EPS:
            cells.append({'label': rid, 'rooms': [rid], 'g': take,
                          'merge_limit':box(room.bounds[0]-1,room.bounds[1]-1,room.bounds[2]+1,room.bounds[3]+1)})
            remain = clean(remain.difference(take))
    # A 18m corridor/background tile is an editing unit, not a playable room.
    x0,y0,x1,y1 = remain.bounds if not remain.is_empty else (0,0,0,0)
    fragments = []
    for ix in range(math.floor(x0/tile), math.ceil(x1/tile)):
        for iy in range(math.floor(y0/tile), math.ceil(y1/tile)):
            p = clean(remain.intersection(box(ix*tile,iy*tile,(ix+1)*tile,(iy+1)*tile)))
            for k,q in enumerate(polys(p)):
                if q.area > EPS: fragments.append((ix,iy,k,q))
    thin = []
    for ix,iy,k,q in fragments:
        if q.buffer(-.45).is_empty:
            thin.append((ix,iy,k,q))
        else:
            cells.append({'label': f'Hall_{ix}_{iy}_{k}', 'rooms': [], 'g': q})
    # These are support areas below walls, not new narrow circulation paths.
    for ix,iy,k,q in thin:
        candidates=[]
        for j,c in enumerate(cells):
            if c['rooms']:
                if q.difference(c['merge_limit']).area>EPS:continue
            else:
                merged_bounds=c['g'].union(q).bounds
                if max(merged_bounds[2]-merged_bounds[0],merged_bounds[3]-merged_bounds[1])>tile+GRID:continue
            candidates.append((q.distance(c['g']),-q.boundary.intersection(c['g'].boundary).length,j))
        if candidates:
            dist, _, j = min(candidates)
            if dist < GRID*3:
                cells[j]['g'] = clean(cells[j]['g'].union(q)); continue
        cells.append({'label': f'Support_{ix}_{iy}_{k}', 'rooms': [], 'g': q})
    return cells


def refine_ring(ring, points):
    raw=list(ring.coords);out=[]
    for a,b in zip(raw,raw[1:]):
        dx,dy=b[0]-a[0],b[1]-a[1];den=dx*dx+dy*dy
        candidates=[]
        for p in points:
            if p[0]<min(a[0],b[0])-1e-7 or p[0]>max(a[0],b[0])+1e-7 or p[1]<min(a[1],b[1])-1e-7 or p[1]>max(a[1],b[1])+1e-7:continue
            if abs(dx*(p[1]-a[1])-dy*(p[0]-a[0])) > 1e-7*max(1,math.sqrt(den)):continue
            t=((p[0]-a[0])*dx+(p[1]-a[1])*dy)/den if den else 0
            if -.0000001<=t<.9999999:candidates.append((t,p))
        out.extend(p for t,p in sorted(candidates))
    return out


def refine(g, points):
    return [orient(Polygon(refine_ring(p.exterior,points),
                           [refine_ring(r,points) for r in p.interiors]),1) for p in polys(g)]


def mesh_module(pieces):
    """A closed sectional solid PER MODULE, never a whole-map height actor."""
    levels=sorted({z for a,b,g in pieces for z in (a,b)})
    shapes=[clean(unary_union([g for a,b,g in pieces if a<=(lo+hi)/2<b]))
            for lo,hi in zip(levels,levels[1:])]
    cap_specs=[]
    for i,g in enumerate(shapes):
        prev=shapes[i-1] if i else Polygon();nxt=shapes[i+1] if i+1<len(shapes) else Polygon()
        cap_specs.extend([(clean(g.difference(prev)),levels[i],False),
                          (clean(g.difference(nxt)),levels[i+1],True)])
    points=sorted({(round(x,5),round(y,5)) for g in shapes+[x[0] for x in cap_specs] for x,y in coords(g)})
    verts=[];faces=[];index={}
    def vi(x,y,z):
        v=(round(x,5),round(y,5),round(z,5))
        if v not in index:index[v]=len(verts);verts.append(v)
        return index[v]
    for g,z,up in cap_specs:
        for p in refine(g,points):
            for t in constrained_delaunay_triangles(p).geoms:
                xy=list(orient(t,1).exterior.coords)[:-1]
                if not up:xy.reverse()
                faces.append([vi(x,y,z) for x,y in xy])
    for i,g in enumerate(shapes):
        for p in refine(g,points):
            for r in [p.exterior,*p.interiors]:
                xy=list(r.coords)
                for a,b in zip(xy,xy[1:]):
                    ids=[vi(*a,levels[i]),vi(*b,levels[i]),vi(*b,levels[i+1]),vi(*a,levels[i+1])]
                    faces.extend([[ids[0],ids[1],ids[2]],[ids[0],ids[2],ids[3]]])
    edges=collections.Counter(tuple(sorted((a,b))) for f in faces for a,b in zip(f,f[1:]+f[:1]))
    invalid=sum(count!=2 for count in edges.values())
    # Positive signed volume also checks the winding of all exposed faces.
    vol=0.
    for f in faces:
        a,b,c=[verts[i] for i in f]
        vol+=(a[0]*(b[1]*c[2]-b[2]*c[1])+a[1]*(b[2]*c[0]-b[0]*c[2])+a[2]*(b[0]*c[1]-b[1]*c[0]))/6
    return verts,faces,invalid,vol


def main():
    start=time.time();parser=argparse.ArgumentParser()
    parser.add_argument('--source',type=Path,default=SOURCE)
    parser.add_argument('--output',type=Path,default=ROOT)
    args=parser.parse_args();args.output.mkdir(parents=True,exist_ok=True)
    script=args.source/'prepare_architecture.py'
    prefix=script.read_text(encoding='utf8').split('# A continuous sectional solid',1)[0]
    # The legacy generator reads an unused OLD plan and a machine-local package
    # path. Neither is part of the current volume declarations.
    prefix='\n'.join(line for line in prefix.splitlines() if not line.startswith(('OLD=', 'sys.path.insert')))
    ns={'__file__':str(script.resolve())};exec(compile(prefix,str(script),'exec'),ns)
    D,V=ns['D'],ns['volumes'];get=ns['geom'];duct=get('duct_clear');housing=get('duct_wall_housing')
    room_meta={r['id']:r for r in D['rooms']}
    room_shapes={rid:clean(unary_union([Polygon(p['outer'],p.get('holes',[])) for p in pp]))
                 for rid,pp in D['room_shapes'].items()}
    openings={o['id']:o for o in D['openings']}
    zs=sorted({z for n,g,a,b in V for z in (a,b)}|{7.8,9.2})
    mids=[(a+b)/2 for a,b in zip(zs,zs[1:])]
    originals=[clean(unary_union([g for n,g,a,b in V if a<=mid<b]).difference(duct)
                     if 7.8<mid<9.2 else unary_union([g for n,g,a,b in V if a<=mid<b])) for mid in mids]
    groups=[]
    def add(label,kind,floor,vs,rank,part_mode='wall',opening_id=None,explicit=None):
        groups.append(dict(label=label,kind=kind,floor=floor,vs=vs,rank=rank,
                           mode=part_mode,opening_id=opening_id,explicit=explicit))
    for n,g,a,b in V:
        if n in ('A walls','B walls','Training walls','Control enclosure','Scenic outer lower','Scenic outer upper'):continue
        if n.startswith('Header '):
            kind='window_header' if openings.get(n[7:],{}).get('kind')=='window' else 'door_header'
            add(n,kind,'B' if a>=5.4 else 'A',[(g,a,b)],45,opening_id=n[7:]);continue
        if n.startswith('Sill '):add(n,'window_sill','B' if a>=5.4 else 'A',[(g,a,b)],45,opening_id=n[5:]);continue
        if n in ('A slab','B slab and lower roof consolidated'):
            floor='A' if n=='A slab' else 'B';add(n,'floor',floor,[(g,a,b)],0,'floor');continue
        if 'roof' in n.lower():add(n,'roof','CONTROL' if n=='Control roof' else 'B',[(g,a,b)],1,'floor' if n=='Main roof' else 'single');continue
        if n=='Scenic slab':add(n+' '+str(b),'scenic_floor','SCENIC',[(g,a,b)],2,'single');continue
        if n=='Duct landing platforms':add(n,'duct_platform','B',[(g,a,b)],3,'single');continue
        if n.startswith('Jump '):add(n,'jump_block','B',[(g,a,b)],3,'single');continue
        if n=='Scenic lower base':add(n,'scenic_base','A',[(g,a,b)],4,'single');continue
        raise ValueError('Unhandled source volume: '+n)
    # The wall-mounted duct has two full-height jambs and separate sill/lintel.
    bv=[(g,a,b) for n,g,a,b in V if n=='B walls']
    house=clean(unary_union([g for g,a,b in bv]).intersection(housing))
    for k,p in enumerate(wall_partition(house.difference(duct))):
        add('Duct jamb '+str(k),'duct_jamb','B',[(p,5.4,14)],26,'single')
    add('Duct lower panel','duct_sill','B',[(house.intersection(duct),5.4,7.8)],26,'single')
    add('Duct upper panel','duct_header','B',[(house.intersection(duct),9.2,14)],26,'single')
    # Control enclosure is split at its real door and window jamb coordinates.
    cv=[(g,a,b) for n,g,a,b in V if n=='Control enclosure']
    cp=clean(unary_union([g for g,a,b in cv]));c0=openings['C0']
    aperture=box(c0['x']-c0['width']/2,-11,c0['x']+c0['width']/2,-9)
    add('C0 lintel','door_header','CONTROL',[(g.intersection(aperture),a,b) for g,a,b in cv],27,'single','C0')
    c_rest=cp.difference(aperture)
    add('Control enclosure','wall','CONTROL',[(g.difference(aperture),a,b) for g,a,b in cv],28,'wall')
    for name,floor in [('Scenic outer lower','A'),('Scenic outer upper','B')]:
        add(name,'scenic_wall',floor,[(g,a,b) for n,g,a,b in V if n==name],30)
    for name,floor in [('A walls','A'),('B walls','B'),('Training walls','B')]:
        vv=[(clean(g.difference(housing)) if name=='B walls' else g,a,b) for n,g,a,b in V if n==name]
        add(name,'wall',floor,vv,40)
    groups.sort(key=lambda g:g['rank'])
    occupied=[Polygon() for _ in mids]; modules=[]; qa_groups=[]; ownership_deltas=[]
    for gi,group in enumerate(groups):
        active=[]
        for i,mid in enumerate(mids):
            raw=clean(unary_union([g for g,a,b in group['vs'] if a<=mid<b]))
            if 7.8<mid<9.2:raw=clean(raw.difference(duct))
            usable=clean(raw.difference(occupied[i]));active.append(usable)
            occupied[i]=clean(occupied[i].union(raw))
        plan=clean(unary_union(active))
        if plan.area<EPS:continue
        if group['mode']=='floor':
            choices=[(rid,p) for rid,p in room_shapes.items()
                     if (room_meta[rid].get('floor_elevation',0)>0)==(group['floor']=='B')]
            if group['kind']=='roof':choices += [(rid,p) for rid,p in room_shapes.items() if room_meta[rid].get('floor_elevation',0)==0]
            partitions=floor_partition(plan,choices)
        else:
            pp=wall_partition(plan) if group['mode']=='wall' else polys(plan)
            if group['kind']=='wall' and group['floor'] in ['A','B']:
                nearby=[(rid,p) for rid,p in room_shapes.items()
                        if (room_meta[rid].get('floor_elevation',0)>0)==(group['floor']=='B')]
                pp=semantic_wall_parts(pp,nearby)
            partitions=[{'label':str(j+1).zfill(3),'rooms':[],'g':p} for j,p in enumerate(pp)]
        partition_union=clean(unary_union([p['g'] for p in partitions]))
        qa_groups.append({'label':group['label'],'parts':len(partitions),'plan_difference_m2':plan.symmetric_difference(partition_union).area,
                          'plan_overlap_m2':sum(p['g'].area for p in partitions)-partition_union.area})
        for pj,partition in enumerate(partitions):
            p=partition['g'];pieces=[]
            for i,(a,b) in enumerate(zip(zs,zs[1:])):
                q=clean(p.intersection(active[i]))
                if q.area<EPS:continue
                if pieces and abs(pieces[-1][1]-a)<EPS and pieces[-1][2].equals(q):pieces[-1]=(pieces[-1][0],b,q)
                else:pieces.append((a,b,q))
            if not pieces:continue
            footprint=clean(unary_union([g for a,b,g in pieces]));a=min(x[0] for x in pieces);b=max(x[1] for x in pieces)
            room_ids=partition['rooms'] or [rid for rid,shape in room_shapes.items()
                     if (group['floor']=='CONTROL' or (room_meta[rid].get('floor_elevation',0)>0)==(group['floor']=='B'))
                     and footprint.buffer(.025).intersection(shape).area>EPS]
            label=''.join(c if c.isalnum() or c=='_' else '_' for c in group['label'])
            suffix=''.join(c if c.isalnum() or c=='_' else '_' for c in partition['label'])
            name=f"SM_LabEditable_{group['floor']}_{label}_{suffix}"
            module={'name':name,'module_id':name,'kind':group['kind'],'floor':group['floor'],
                    'rooms':room_ids,'opening_id':group['opening_id'],'source_volume':group['label'],
                    'footprint':serial(footprint),'z0':a,'z1':b,'pieces':pieces}
            modules.append(module)
        print(json.dumps({'phase':'partition','group':group['label'],'group_modules':len(partitions),'total':len(modules)}),flush=True)
    # Cross-source filling strips (notably the 5cm training/scenic joint)
    # attach to the neighbouring wall instead of becoming a thin Actor.
    for m in list(modules):
        if m not in modules or m['kind']!='wall':continue
        footprint=clean(unary_union([g for a,b,g in m['pieces']]));bb=footprint.bounds
        if min(bb[2]-bb[0],bb[3]-bb[1])>=.15:continue
        candidates=[]
        for j,other in enumerate(modules):
            if other is m or other['kind'] not in ['wall','scenic_wall'] or other['floor']!=m['floor']:continue
            if min(other['z1'],m['z1'])<=max(other['z0'],m['z0']):continue
            op=clean(unary_union([g for a,b,g in other['pieces']]))
            shared=footprint.boundary.intersection(op.boundary).length
            if shared>.005:candidates.append((-shared,j))
        if not candidates:continue
        _,j=min(candidates);target=modules[j];both=target['pieces']+m['pieces'];merged=[]
        for a,b in zip(zs,zs[1:]):
            p=clean(unary_union([g for lo,hi,g in both if lo<=(a+b)/2<hi]))
            if p.area<EPS:continue
            if merged and merged[-1][1]==a and merged[-1][2].equals(p):merged[-1]=(merged[-1][0],b,p)
            else:merged.append((a,b,p))
        target['pieces']=merged;target['footprint']=serial(clean(unary_union([g for a,b,g in merged])))
        target['z0']=min(a for a,b,g in merged);target['z1']=max(b for a,b,g in merged)
        target['rooms']=sorted(set(target['rooms']+m['rooms']))
        target.setdefault('absorbed_modules',[]).append(m['name']);modules.remove(m)
    # Independently recombine final module pieces per source height interval.
    union_checks=[]
    for i,(a,b) in enumerate(zip(zs,zs[1:])):
        mid=(a+b)/2;parts=[g for m in modules for lo,hi,g in m['pieces'] if lo<=mid<hi]
        combined=clean(unary_union(parts));diff=combined.symmetric_difference(originals[i]).area
        overlap=max(0,sum(p.area for p in parts)-combined.area)
        union_checks.append({'z_m':[a,b],'symmetric_difference_m2':diff,'overlap_m2':overlap})
    print(json.dumps({'phase':'geometry_validation','max_difference':max(x['symmetric_difference_m2'] for x in union_checks),
                      'max_overlap':max(x['overlap_m2'] for x in union_checks)}),flush=True)
    mesh_failures=[];dimensions=[]
    for i,m in enumerate(modules):
        pieces=m.pop('pieces');verts,faces,bad,volume=mesh_module(pieces)
        expected=sum((b-a)*g.area for a,b,g in pieces)
        if bad or abs(volume-expected)>.001:mesh_failures.append({'name':m['name'],'nonmanifold_edges':bad,'signed_volume_m3':volume,'expected_volume_m3':expected})
        bb=[min(v[j] for v in verts) for j in range(3)]+[max(v[j] for v in verts) for j in range(3)]
        dx,dy,dz=bb[3]-bb[0],bb[4]-bb[1],bb[5]-bb[2]
        rotation=90 if m['kind'] in ['wall','scenic_wall','door_header','window_header','window_sill'] and dy>dx else 0
        pivot=[(bb[0]+bb[3])/2,(bb[1]+bb[4])/2,bb[2]]
        local=[]
        for x,y,z in verts:
            x-=pivot[0];y-=pivot[1];z-=pivot[2]
            local.append([round(y if rotation else x,5),round(-x if rotation else y,5),round(z,5)])
        rectangular=len(pieces)==1 and rect(pieces[0][2])
        if m['kind']=='wall' and not rectangular:
            m['original_kind']='wall';m['kind']='special_wall'
        face_materials=[]
        for f in faces:
            va,vb,vc=[verts[k] for k in f]
            upward=(vb[0]-va[0])*(vc[1]-va[1])-(vb[1]-va[1])*(vc[0]-va[0])>1e-10
            level=max(v[2] for v in (va,vb,vc))-min(v[2] for v in (va,vb,vc))<1e-7
            floor_top=m['kind'] in ['floor','scenic_floor','duct_platform','jump_block','scenic_base'] and upward and level
            face_materials.append('Floor' if floor_top else 'Wall')
        m.update(verts=local,world_verts=verts,faces=faces,face_materials=face_materials,
                 pivot=pivot,rotation_z_degrees=rotation,
                 bbox=bb,bbox_world=bb,dimensions_m=[dy,dx,dz] if rotation else [dx,dy,dz],
                 rectangular_bool=rectangular,box_center_world=[(bb[0]+bb[3])/2,(bb[1]+bb[4])/2,(bb[2]+bb[5])/2],
                 unit_box_pivot='bottom_center',
                 edit_behavior='translate_rotate_scale_box' if rectangular else 'translate_rotate_or_edit_mesh_profile',
                 closed_manifold=bad==0,volume_m3=volume,
                 vertical_profile=[{'z0':a,'z1':b,'footprint':serial(g)} for a,b,g in pieces],
                 scale_editable_prism=rectangular)
        dimensions.append({'name':m['name'],'kind':m['kind'],'dimensions_m':m['dimensions_m']})
        if i%100==0:print(json.dumps({'phase':'closed_mesh','done':i+1,'total':len(modules)}),flush=True)
    source_plan=(args.source/'revised-layout-geometry.json').read_bytes()
    report={'passed':not mesh_failures and all(x['symmetric_difference_m2']<.01 and x['overlap_m2']<.01 for x in union_checks)
            and all(x['plan_difference_m2']<.01 and x['plan_overlap_m2']<.01 for x in qa_groups),
            'source_plan_sha256':digest(source_plan),'source_generator_sha256':digest(script.read_bytes()),
            'module_count':len(modules),'types':dict(collections.Counter(m['kind'] for m in modules)),
            'wall_prisms_scale_editable':sum(m['kind']=='wall' and m['scale_editable_prism'] for m in modules),
            'wall_modules_total':sum(m['kind'] in ['wall','special_wall'] for m in modules),
            'rectangular_module_count':sum(m['rectangular_bool'] for m in modules),
            'group_partitions':qa_groups,'height_interval_checks':union_checks,'mesh_failures':mesh_failures,
            'smallest_modules_by_plan_dimension':sorted(dimensions,key=lambda x:min(x['dimensions_m'][:2]))[:30],
            'duration_seconds':time.time()-start,'precision_m':GRID,
            'notes':['Local verts are in metres. Rotate Z then add pivot; world_verts is provided to avoid coordinate ambiguity.',
                     'A/B floor slabs are generated only once; the underside of B flooring is the A ceiling.',
                     'Separate closed modules retain buried contact caps. They have no overlapping volume or exposed coplanar face area.',
                     'Only roof and floor residual circulation is tiled. Walls are complete semantic runs, not global height slices.',
                     'No UE or Blender calls; current R17 sources and map remain unchanged.']}
    result={'schema_version':1,'coordinate_system':'Blender metres, Z up; local verts transformed by rotation_z_degrees then pivot',
            'modules':modules,'report':report}
    (args.output/'modules.json').write_text(json.dumps(result,ensure_ascii=False),encoding='utf8')
    (args.output/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
    print(json.dumps({'phase':'complete','passed':report['passed'],'modules':len(modules),'mesh_failures':len(mesh_failures),
                      'duration_seconds':report['duration_seconds']},ensure_ascii=False),flush=True)
    return 0 if report['passed'] else 1


if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf8');raise SystemExit(main())
