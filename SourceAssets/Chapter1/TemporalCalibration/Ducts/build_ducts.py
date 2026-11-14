"""Room 2 return-air ducts. Run in Blender with --python; optionally pass -- <QA manifest>.

Input is the saved original UE component layout, in centimetres; output FBXs
retain each component's pivot, scale, and octagonal clocking. Adjacent short
sections share their midpoint ring. The two large disaster gaps stay open.
"""
import json
import math
import sys
from collections import Counter
from pathlib import Path

import bpy
from mathutils import Quaternion, Vector


ROOT = Path(__file__).resolve().parent
SLOTS = ["Metal", "Graphite", "Seal", "Panel"]
UP = Vector((0, 0, 1))
EIGHTH = math.tau / 8
RADIUS_CM = 102
BODY = .957
BORE = .897


def numbers(v):
    return [round(float(c), 6) for c in v]


def frame(axis):
    top = (UP - axis * UP.dot(axis)).normalized()
    return top, axis.cross(top).normalized()


def direction(axis, phase, slot):
    top, side = frame(axis)
    corner = slot // 8
    a = phase + corner * EIGHTH
    v0 = top * math.cos(a) + side * math.sin(a)
    v1 = top * math.cos(a + EIGHTH) + side * math.sin(a + EIGHTH)
    return v0.lerp(v1, (slot % 8) / 8)


def load_layout():
    data = json.loads((ROOT / 'duct_layout.json').read_text())
    rows = {}
    for number, pose in data.items():
        n = int(number)
        center, scale = Vector(pose['center']), Vector(pose['scale'])
        x, y, z, w = pose['quaternion']
        m = Quaternion((w, x, y, z)).to_matrix()
        start, end = (Vector(v) for v in pose['endpoints'])
        if n in (8, 9):
            start, end = end, start
        axis = (end - start).normalized()
        top, side = frame(axis)
        lx = m.col[0]
        phase = (math.atan2(lx.dot(side), lx.dot(top)) + EIGHTH/2) % EIGHTH - EIGHTH/2
        rows[n] = dict(n=n, center=center, scale=scale, inverse=m.transposed(),
                       start=start, end=end, axis=axis, phase=phase, length=(end-start).length)
    for left, right in ((8, 9), (9, 11)):
        a, b = rows[left], rows[right]
        b['phase'] = a['phase'] + (b['phase']-a['phase']+EIGHTH/2) % EIGHTH-EIGHTH/2
    return rows


def straight(row, begin, end, inlet, outlet):
    rings = [(begin, BODY, BORE, 'Graphite'), (end, BODY, BORE, 'Graphite')]
    if inlet:
        rings[:1] = [(0, .971, .901, 'Metal'), (2.2, 1., .884, 'Graphite'),
                     (8, 1., .884, 'Graphite'), (11.4, .971, BORE, 'Seal'),
                     (13.6, BODY, BORE, 'Graphite')]
    if outlet:
        rings[-1:] = [(end-14.8, BODY, BORE, 'Graphite'), (end-12, .974, .895, 'Seal'),
                      (end-10, 1., .880, 'Graphite'), (end-2, 1., .880, 'Metal'),
                      (end, .977, BORE, 'Graphite')]
    # First-room shell has a recessed narrow sheet-metal seam inside longer straights.
    if end-begin > 72:
        mid = begin + (end-begin)*.45
        rings += [(mid-1.15, BODY, BORE, 'Panel'), (mid-.42, .951, BORE, 'Seal'),
                  (mid+.48, .951, BORE, 'Seal'), (mid+1.15, BODY, BORE, 'Graphite')]
    def record(s, outer, inner, slot):
        center = row['start'] + row['axis']*s
        def sample(g, inside):
            rad = RADIUS_CM*(inner if inside else outer)
            return center + direction(row['axis'], row['phase'], g)*rad
        return dict(center=center, axis=row['axis'], sample=sample, material=lambda g: slot)
    return [record(*ring) for ring in sorted(rings)]


def bend(a, b, trim_ratio, control, tear_cm, facing):
    trim = min(a['length'], b['length'])*trim_ratio
    p, s = a['end']-a['axis']*trim, b['start']+b['axis']*trim
    distance = (s-p).length
    q, r = p+a['axis']*distance*control[0], s-b['axis']*distance*control[1]
    def curve(t):
        v = 1-t
        center = p*v**3+q*(3*v*v*t)+r*(3*v*t*t)+s*t**3
        d = (q-p)*(3*v*v)+(r-q)*(6*v*t)+(s-r)*(3*t*t)
        dd = (r-2*q+p)*(6*v)+(s-2*r+q)*(6*t)
        radius = d.length**3 / max(d.cross(dd).length, 1.e-12)
        phase = a['phase']+(b['phase']-a['phase'])*t*t*(3-2*t)
        return center, d.normalized(), phase, radius
    def station(t):
        center, axis, _, _ = curve(t)
        return dict(center=numbers(center), axis=numbers(axis))
    mid, axis, phase, _ = curve(.5)
    damaged = max(range(8), key=lambda g: direction(axis,phase,8*g+4).dot(Vector(facing)))
    # Recess a jagged fold into one outward-facing sheet, keeping its return and the
    # bore intact. A second, rolled sheet edge curls over the narrow dark seal.
    times = [0,.13,.26,.37,.415,.455,.479,.492,.5,.508,.521,.545,.585,.63,.74,.87,1]
    weights = [0,.44,.81,1,1,1,.88,.49,0]
    skew = [0,-.084,-.070,-.106,-.010,.058,.033,.084,0]
    opens = [0,.030,.068,.030,.088,.045,.075,.023,0]
    folded = [0,.12,.68,.19,1,.19,.61,.14,0]
    opposing = [0,.11,.16,.58,.12,.53,.25,.12,0]
    secondary = a['n'] == 8
    if secondary:
        # At the first coupling only a short tongue of the upper sheet peeled.
        # The other edge is still held by its sleeve; the slab joint farther
        # along the run carries the broad two-sided failure.
        weights = [0,0,0,.28,1,.86,.18,0,0]
        skew = [0,0,0,-.021,-.038,.014,.018,0,0]
        opens = [0,0,0,.007,.027,.017,.004,0,0]
        folded = [0,0,0,.10,1,.69,.13,0,0]
        opposing = [0,0,0,.06,.07,.05,.018,0,0]
    radius = [BODY,BODY,BODY,BODY,BODY,.958,.965,.976,.969,.976,.965,.958,BODY,BODY,BODY,BODY,BODY]
    def record(i):
        ct, tangent, _, _ = curve(times[i])
        def sample(g, inside):
            h = g % 8
            amount = weights[h] if g//8 == damaged and not inside else 0
            pos = times[i]
            fac = BORE if inside else radius[i]
            if amount:
                ctr = .5+skew[h]
                left, right = ctr-opens[h]-.004, ctr+opens[h]+.004
                warped = [0,.13,.25,left-.08,left-.05,left-.002,left+.002,left+.012,ctr,
                          right-.012,right-.002,right+.002,right+.047,right+.085,.77,.87,1]
                # Tip and backfold stay separate even after UE quantizes the imported mesh.
                h1, h2 = tear_cm*folded[h], tear_cm*opposing[h]
                trough = -2.15 if secondary else -4.85
                lift = [0,0,0,0,h1*.16,h1,h1-.82,trough,trough,trough,h2-.82,h2,h2*.19,0,0,0,0]
                pos += amount*(warped[i]-pos)
                fac += amount*(BODY+lift[i]/RADIUS_CM-fac)
            cc, dr, twist, _ = curve(pos)
            return cc+direction(dr,twist,g)*RADIUS_CM*fac
        def material(g):
            if g//8 == damaged and max(weights[g%8:g%8+2]) > .12:
                if secondary:
                    if i == 5 and g%8 in (3,4,5): return 'Metal'
                    return 'Seal' if i in (7,8) else 'Graphite'
                if i in (5,10): return 'Metal'
                if i in (4,11) and g%8 in (2,4,5): return 'Panel'
            return 'Seal' if i in (7,8) else 'Graphite'
        return dict(center=ct, axis=tangent, sample=sample, material=material)
    minimum = min(curve(i/200)[3] for i in range(201))
    assert minimum > RADIUS_CM*1.15, minimum
    info = dict(name=f"{a['n']}-{b['n']}", pieces=[f"Art_R2_Duct_{row['n']}" for row in (a,b)],
                trim_cm=trim, original_endpoint_gap_cm=(a['end']-b['start']).length,
                min_bend_radius_cm=minimum, damaged_facet=damaged, max_fold_cm=tear_cm,
                stations=[station(t) for t in (.04,.16,.36,.44,.50,.56,.64,.84,.96)])
    return [record(i) for i in range(len(times))], info


def export_mesh(row, rings, samples, mats, inlet, outlet):
    count = len(samples)
    world = [ring['sample'](g,inside) for ring in rings for inside in (False,True) for g in samples]
    verts = []
    for p in world:
        v = row['inverse'] @ (p-row['center'])
        v = [v[i]/row['scale'][i]*.01 for i in range(3)]
        verts.append((v[0],-v[1],v[2]))
    faces, slots = [], []
    def face(vertices, slot):
        faces.append(vertices[::-1])
        slots.append(SLOTS.index(slot))
    for i, ring in enumerate(rings[:-1]):
        a, b = i*count*2, (i+1)*count*2
        for g, sample in enumerate(samples):
            h = (g+1)%count
            face([a+g,a+h,b+h,b+g],ring['material'](sample))
            face([a+count+h,a+count+g,b+count+g,b+count+h],'Seal')
    for end, cap in ((False,inlet),(True,outlet)):
        if cap:
            offset = (len(rings)-1)*count*2 if end else 0
            for g in range(count):
                h = (g+1)%count
                f = [offset+g,offset+count+g,offset+count+h,offset+h]
                face(f[::-1] if end else f, 'Graphite')
    name = f"SM_TC_VentRun{row['n']:02d}"
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(verts, [], faces)
    assert not mesh.validate(), name
    uv = mesh.uv_layers.new(name='UVMap')
    for mat in mats: mesh.materials.append(mat)
    for poly, slot in zip(mesh.polygons,slots):
        poly.material_index = slot
        for i, xy in zip(poly.loop_indices, ((0,0),(1,0),(1,1),(0,1))):
            uv.data[i].uv = xy
    mesh.update()
    mesh.calc_loop_triangles()
    assert min(t.area for t in mesh.loop_triangles) > 1.e-8
    assert set(slots)==set(range(len(SLOTS))), name
    obj = bpy.data.objects.new(name,mesh)
    bpy.context.collection.objects.link(obj)
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.export_scene.fbx(filepath=str(ROOT/(name+'.fbx')),use_selection=True,object_types={'MESH'},
                             axis_forward='-Y',axis_up='Z',mesh_smooth_type='FACE',bake_anim=False)
    info = dict(label=f"Art_R2_Duct_{row['n']}",asset=name,scale_xyz=numbers(row['scale']),
                source_endpoints_ue_cm=[numbers(row[k]) for k in ('start','end')],
                triangles=len(mesh.loop_triangles), terminal_start=inlet,terminal_end=outlet)
    # Count edge incidence in world space across separate mesh boundaries.
    positions = [tuple(round(n,3) for n in p) for p in world]
    edges = Counter(tuple(sorted((positions[x],positions[y])))
                    for f in faces for x,y in zip(f, f[1:]+f[:1]))
    return info, edges


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    rows = load_layout()
    mats = [bpy.data.materials.new(s) for s in SLOTS]
    for mat, rgb in zip(mats, ((.51,.49,.45),(.105,.116,.124),(.020,.026,.029),(.22,.23,.23))):
        mat.diffuse_color = (*rgb,1)
    first,j0 = bend(rows[8],rows[9],.255,(.40,.37),6.5,(.12,-.99,.14))
    second,j1 = bend(rows[9],rows[11],.40,(.26,.46),15,(-.65,-.74,.12))
    t0,t1 = j0['trim_cm'],j1['trim_cm']
    L = {k:v['length'] for k,v in rows.items()}
    parts = {
        8: straight(rows[8],0,L[8]-t0,True,False)[:-1]+first[:9],
        9: first[8:-1]+straight(rows[9],t0,L[9]-t1,False,False)[:-1]+second[:9],
        11: second[8:-1]+straight(rows[11],t1,L[11],False,True),
        12: straight(rows[12],0,L[12],True,True),
        10: straight(rows[10],0,L[10],True,True)}
    linked_samples = [g for g in range(64) if g%8==0 or g//8 in (j0['damaged_facet'],j1['damaged_facet'])]
    edge_counts, result = Counter(), []
    for n in (8,9,11,12,10):
        detail, edges = export_mesh(rows[n],parts[n],linked_samples if n in (8,9,11) else range(0,64,8),
                                   mats,n in (8,10,12),n in (10,11,12))
        result.append(detail)
        edge_counts.update(edges)
    assert set(edge_counts.values()) == {2}, Counter(edge_counts.values())
    manifest = dict(instances=result, joints=[j0,j1], mesh_slots=SLOTS, body_outer_radius_cm=RADIUS_CM*BODY,
                    inner_radius_cm=RADIUS_CM*BORE, radius_at_collar_cm=RADIUS_CM, manifold=True,
                    deliberate_gaps=[dict(pieces=[a,b],distance_cm=(rows[a]['end']-rows[b]['start']).length)
                                     for a,b in ((11,12),(12,10))])
    if '--' in sys.argv:
        Path(sys.argv[sys.argv.index('--')+1]).write_text(json.dumps(manifest,indent=2),encoding='utf8')
    print('Validated five ducts, two mated elbows, and two retained gaps.')


if __name__=='__main__':
    main()
