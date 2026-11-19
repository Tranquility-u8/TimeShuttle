"""Extend the existing upper slab to the new equal-bay observation guard (UE cm)."""
from bisect import bisect_right
import json
import math
from pathlib import Path
import runpy

import bpy

HERE = Path(__file__).resolve().parent
GLAZING = runpy.run_path(str(HERE / 'build_glazing.py'))
Frame = GLAZING['Frame']
GUARD = 46.0
EDGE = 39.0
DECK_SLOTS = ['Graphite', 'Floor', 'FloorAlt', 'Joint', 'Alloy', 'Soffit']
GUARD_SLOTS = ['Graphite', 'GuardGlass', 'Alloy', 'Seal']


def y_at(points, x):
    i = min(max(bisect_right(points, (x, math.inf))-1, 0), len(points)-2)
    (a,b),(c,d) = points[i:i+2]
    return b + (d-b)*(x-a)/(c-a)


def clip_line(points, limit, sign):
    if not points:
        return []
    result = []
    for a,b in zip(points[-1:]+points[:-1],points):
        ina, inb = sign*(a[1]-limit)>=0, sign*(b[1]-limit)>=0
        if ina != inb:
            result.append((a[0]+(b[0]-a[0])*(limit-a[1])/(b[1]-a[1]),limit))
        if inb:
            result.append(b)
    return result


def horizontal(mesh, polygon, z, material, top=True):
    clean = []
    for p in polygon:
        if not clean or math.dist(clean[-1], p)>.003:
            clean.append(p)
    if len(clean)>2 and math.dist(clean[0], clean[-1])<.003:
        clean.pop()
    if len(clean)<3:
        return
    area = sum(x*Y-X*y for (x,y),(X,Y) in zip(clean,clean[1:]+clean[:1]))
    if abs(area)<.01:
        return
    if (area>0) != top:
        clean.reverse()
    mesh.face([(x,y,z) for x,y in clean],material)


def build_deck(mesh, old, outer, left, right):
    """Intersect the linear surveyed curves exactly. Keep existing slab wherever it extends further."""
    def outside(x):
        return y_at(outer,x) if outer[0][0]<=x<=outer[-1][0] else y_at(old,x)
    cuts={left,right,*[x for x,y in old+outer if left<x<right]}
    for i in range(-29,30):
        for inset in (-.25,.25):
            x=i*188.4+inset
            if left<x<right:
                cuts.add(x)
    initial=sorted(cuts)
    for a,b in zip(initial,initial[1:]):
        if not outer[0][0]<=.5*(a+b)<=outer[-1][0]:
            continue
        d1,d2=y_at(old,a)-outside(a),y_at(old,b)-outside(b)
        if d1*d2<0:
            cuts.add(a+(b-a)*d1/(d1-d2))
    cuts=sorted(cuts)
    # The edge profile also follows the short areas where the old slab returns
    # closer to the curtain at the two ends. There is no overlapping top deck.
    rim_xyz=[]
    for a,b in zip(cuts,cuts[1:]):
        mid=(a+b)*.5
        if b-a<.0005:
            continue
        p,q=y_at(old,a),y_at(old,b)
        is_extension=(outer[0][0]<mid<outer[-1][0] and y_at(old,mid)>outside(mid))
        l,r=(outside(a),outside(b)) if is_extension else (p,q)
        rim_xyz.extend([(a,l),(b,r)])
        if not is_extension:
            continue
        poly=[(a,l),(b,r),(b,q),(a,p)]
        horizontal(mesh,poly,540,'Joint')
        horizontal(mesh,poly,496,'Soffit',False)
        # The pre-existing interior tiles stop three centimetres back from the
        # surveyed slab lip. A recessed gasket bridges that reveal without
        # sharing either the old finish backing (+0.34) or tile plane (+0.72).
        horizontal(mesh,[(a,p-.9),(b,q-.9),(b,q+3.4),(a,p+3.4)],540.52,'Joint')
        ix=math.floor((mid+.25)/188.4)
        if abs(mid-round(mid/188.4)*188.4)<.25:
            continue
        for j in range(math.floor((min(l,r)+4900)/187.5),1+math.floor((max(p,q)+4900)/187.5)):
            y0=-4900+187.5*j
            panel=clip_line(clip_line(poly,y0+.25,1),y0+187.25,-1)
            horizontal(mesh,panel,540.72,'FloorAlt' if (ix*7+j*5)%17==3 else 'Floor')
    # Deduplicate all stations before making the continuous, chamfered slab nose.
    xy=[]
    for p in rim_xyz:
        if not xy or math.dist(xy[-1],p)>.003:
            xy.append(p)
    # signed profile depth is positive towards the occupied floor.
    rim=GLAZING['Curtain']([(x*.01,-y*.01) for x,y in xy])
    profile=[(-4.8,495.7),(0.6,495.7),(0.6,495.95),(-.35,497),
             (-.35,539),(0.6,540.60),(-3.5,540.60),(-5.7,538.3),
             (-5.7,535.2),(-4.8,533.9),(-4.8,504),(-6.2,502.7),(-6.2,498)]
    mesh.rail(rim,0,rim.s[-1],profile,
              ['Graphite','Graphite','Graphite','Graphite','Graphite','Alloy','Graphite',
               'Alloy','Graphite','Soffit','Graphite','Graphite','Alloy'])


def build_guard(mesh, arc, stations, first, last):
    # The section is supported at every half bay. Each butt joint has one post.
    rail=[(GUARD-4,646),(GUARD+4,646),(GUARD+4,650.4),(GUARD+2.7,652.0),
          (GUARD-2.7,652.0),(GUARD-4,650.4)]
    mesh.rail(arc,stations[first],stations[last],rail,
              ['Seal','Graphite','Alloy','Alloy','Alloy','Graphite'],(first==0,last==len(stations)-1))
    for i in range(first,last):
        a,b=stations[i:i+2]
        for s,t in ((a,(a+b)/2),((a+b)/2,b)):
            left,right=s+2.1,t-2.1
            mesh.rail(arc,left,right,[(GUARD-.8,545.3),(GUARD+.8,545.3),
                       (GUARD+.8,647),(GUARD-.8,647)],['GuardGlass']*4)
        for s,primary in ((a,True),((a+b)*.5,False)):
            post(mesh,arc,s,primary)
    if last==len(stations)-1:
        post(mesh,arc,stations[last],True)


def post(mesh,arc,s,primary):
    w=2.9 if primary else 1.9
    depth=3.2 if primary else 2.4
    # Keep the end foot attached to the surveyed concrete wall return.
    def shell(z,half_span,d):
        anchor=max(half_span,min(arc.s[-1]-half_span,s))
        corners=[(-half_span,-d),(half_span,-d),(half_span,d),(-half_span,d)]
        return [arc.at(anchor+t,GUARD+v,z) for t,v in corners]
    for z0,z1,width,d,slot in [(540.65,544.3,w+1.8,depth+1.8,'Graphite'),
                                (544.3,646.2,w,depth,'Graphite')]:
        mesh.loft([shell(z0,width,d),shell(z1,width,d)],[slot]*4)


def build():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.context.scene.unit_settings.system='METRIC'
    bpy.context.scene.unit_settings.scale_length=.01
    arc=GLAZING['load_curtain']()
    stations=GLAZING['bay_stations'](arc)
    layout=json.loads(GLAZING['LAYOUT'].read_text(encoding='utf8'))
    old=sorted(set((100*x,-100*y) for x,y in layout['floor_upper'][0]['outer']
                   if abs(x)<=49.0251 and y>=37))
    outer=[arc.at(s,EDGE,540)[:2] for s in arc.s]
    manifest={}
    middle=(len(stations)-1)//2
    for side,start,end in [('West',0,middle),('East',middle,len(stations)-1)]:
        pivot=((-1 if side=='West' else 1)*2450.,-4630.,540.)
        deck=Frame('SM_HallGlazingDeck'+side,pivot,DECK_SLOTS)
        guard=Frame('SM_HallGlazingGuard'+side,pivot,GUARD_SLOTS)
        l,r=(old[0][0],0.) if side=='West' else (0.,old[-1][0])
        build_deck(deck,old,outer,l,r)
        build_guard(guard,arc,stations,start,end)
        for mesh in [deck,guard]:
            manifest[mesh.name]=mesh.export()
    (HERE/'gallery_edge.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf8')

if __name__=='__main__':
    build()
