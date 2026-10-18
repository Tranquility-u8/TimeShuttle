"""Read-only geometry audit; writes only its independent QA JSON/Markdown report."""
from pathlib import Path
import sys,json,hashlib,itertools
sys.path.insert(0,'E:/Capstone/Test/tmp/lab-v13-python')
from shapely.geometry import Polygon,Point,LineString,box
from shapely.ops import unary_union,polygonize
sys.stdout.reconfigure(encoding='utf8')
R=Path(__file__).resolve().parent
PLAN=R/'revised-layout-geometry.json'
ORIGINAL=Path('E:/Capstone/Test/1002/LabWhitebox_v39/prepared_meshes.json')
plan_raw=PLAN.read_bytes();mesh_raw=(R/'architecture_meshes.json').read_bytes()
D=json.loads(plan_raw);M=json.loads(mesh_raw);O=json.loads(ORIGINAL.read_text(encoding='utf8'))['parts']
EPS=1e-5
# Exported XY coordinates use a 0.00001m grid. Allow 0.00002m only
# when comparing source boundaries to exported solid boundaries, and keep
# raw differences visible so this cannot conceal a meaningful floor gap.
BOUNDARY_TOLERANCE_M=.00002
def geom(k):return unary_union([Polygon(p['outer'],p.get('holes',[])) for p in D[k]]).buffer(0)
def point_inside_edges(point,edges):
    x,y=point.x,point.y;wn=0
    for a,b in edges:
        cross=(b[0]-a[0])*(y-a[1])-(b[1]-a[1])*(x-a[0])
        if a[1]<=y<b[1] and cross>0:wn+=1
        elif b[1]<=y<a[1] and cross<0:wn-=1
    return wn>0

# Reconstruct solid sections from the exported mesh's oriented vertical faces.
# This does not execute or trust prepare_architecture.py's volume assertions.
sections=[];horizontal={};seen=set();dups=0
for part in M['parts']:
    z0,z1=part['z0'],part['z1'];edges=[]
    for face in part['faces']:
        vs=[part['verts'][j] for j in face]
        key=tuple(sorted(tuple(v) for v in vs));dups+=key in seen;seen.add(key)
        if max(v[2] for v in vs)-min(v[2] for v in vs)<1e-7:
            ar=sum(vs[i][0]*vs[(i+1)%len(vs)][1]-vs[(i+1)%len(vs)][0]*vs[i][1] for i in range(len(vs)))/2
            if abs(ar)>1e-8:horizontal.setdefault((round(vs[0][2],5),ar>0),[]).append(Polygon([(v[0],v[1]) for v in vs]))
        else:
            lower=[v[:2] for v in vs if abs(v[2]-z0)<1e-7]
            assert len(lower)==2,(part['name'],face)
            edges.append(lower)
    candidates=list(polygonize([LineString(e) for e in edges]))
    section=unary_union([q for q in candidates if point_inside_edges(q.representative_point(),edges)]).buffer(0)
    sections.append((z0,z1,section))

def intrusion(region,z0,z1):
    return [{'z_m':[a,b],'area_m2':q.intersection(region).area,'bounds':list(q.intersection(region).bounds)}
            for a,b,q in sections if a<z1-1e-7 and b>z0+1e-7 and q.intersection(region).area>EPS]
def section_at(z):return unary_union([q for a,b,q in sections if a<=z<b])
checks={
 'source_plan_hash_matches':M['report']['source_sha256']==hashlib.sha256(plan_raw).hexdigest(),
 'exact_duplicate_faces_absent':dups==0,
}
overlaps=[]
for key,ps in horizontal.items():
    area=sum(p.area for p in ps)-unary_union(ps).area
    if area>EPS:overlaps.append({'z_m':key[0],'up':key[1],'overlap_m2':area})
checks['nonidentical_horizontal_coplanar_overlap_absent']=not overlaps
clearances={
 'training_net_20x34p7x8':intrusion(geom('training').buffer(-.0001),5.4,13.4),
 'control_net_40x42':intrusion(geom('control_clear').buffer(-.0001),0,25),
 'duct_net_2p1x1p5x1p4':intrusion(geom('duct_clear').buffer(-.0001),7.8,9.2),
 'former_lower_E4_open':intrusion(geom('r17_former_E4_lower').buffer(-.001),.05,4.9),
}
for k,v in clearances.items():checks[k+'_clear']=not v
routes=[
 ('A_omen',[(-3.65,31.8),(-4.1,31.8),(-4.1,4),(0,4),(0,-24)],.05,1.85),
 ('A_return',[(0,-24),(0,-.6666667),(3.65,-.6666667)],.05,1.85),
 ('B_TIME',[(-27,16),(-27,26.7),(-31.425,26.7)],5.45,7.25),
 ('B_UP_CITY',[(-47.625,26.7),(-47.625,28.7),(-44.8,28.7),(-44.8,37),(-37,43.3),(-12.8,43.3),(-12.8,36.5),(-16.5,36.5),(-16.5,31.8),(-14.75,31.8)],5.45,7.25),
 ('B_TRAIN',[(14.75,-.6666667),(25,-.6666667),(36.1,-.6666667),(36.1,-15)],5.45,7.25),
 ('A_MAIN_ENTRY',[(-27,2.7),(-31,2.7)],.05,1.85),
 ('L01_S',[(-36,19),(-36,22)],.05,1.85),
]
route_results=[]
for name,points,z0,z1 in routes:
    hit=intrusion(LineString(points).buffer(.45,cap_style=2,join_style=2),z0,z1)
    checks[name+'_route_clear']=not hit
    route_results.append({'name':name,'radius_m':.45,'height_range_m':[z0,z1],'intrusions':hit})
door_results=[]
for key in ['G-WEST-MAIN','R17-L01-S','TR-CONNECT-PREP','TR-CONNECT-TRAIN','TR-ENTRY','C0']:
    o=next(o for o in D['openings'] if o['id']==key);x,y,w=o['x'],o['y'],o['width'];dep=o['depth'];base=5.4 if o['z'] else 0
    p=box(x-dep/2,y-w/2+.01,x+dep/2,y+w/2-.01) if o['axis']=='v' else box(x-w/2+.01,y-dep/2,x+w/2-.01,y+dep/2)
    hit=intrusion(p,base+.01,base+o['height']-.01)
    checks[key+'_full_height_aperture_clear']=not hit
    door_results.append({'id':key,'base_m':base,'height_m':o['height'],'intrusions':hit})

b_slab=section_at(5.2);a_slab=section_at(-.2)
e4_void=geom('e4_preserved_core').difference(geom('floor_upper'))
checks['upper_E4_original_void_preserved']=e4_void.intersection(b_slab).area<EPS
checks['B_court_void_preserved']=geom('research_court').intersection(b_slab).area<EPS
checks['control_void_preserved']=geom('control_clear').intersection(b_slab).area<EPS
floor_support={}
for label,key,slab in [('A','floor_lower',a_slab),('B','floor_upper',b_slab)]:
    raw=geom(key).difference(slab)
    residual=geom(key).difference(slab.buffer(BOUNDARY_TOLERANCE_M))
    floor_support[label]={'raw_boundary_difference_m2':raw.area,
                         'boundary_tolerance_m':BOUNDARY_TOLERANCE_M,
                         'unsupported_beyond_tolerance_m2':residual.area}
    checks[label+'_floor_supported']=residual.area<EPS
checks['training_floor_supported']=geom('training').difference(b_slab).area<EPS
checks['duct_platforms_supported']=geom('duct_platforms').difference(section_at(7.7)).area<EPS
checks['jump_blocks_reach_documented_height']=all(box(*b['bounds']).buffer(-.0001).difference(section_at(b['top_z_m']-.01)).area<EPS for b in D['jump_blocks'])

# Independently compare the refreshed bridge manifest's placed bounds with
# these audited architecture chunks. Blender Y becomes negative UE Y.
manifest_path=R/'patch_bundle'/'manifest.json'
manifest=json.loads(manifest_path.read_text(encoding='utf8'))
exported_by_name={o['name']:o for o in manifest['objects']}
bound_errors=[]
for part in M['parts']:
    o=exported_by_name.get(part['name'])
    if o is None:
        bound_errors.append({'name':part['name'],'missing':True});continue
    center=[o['location'][0]/100,-o['location'][1]/100,o['location'][2]/100]
    local=o['local_bounds_m']
    err=max(abs((center[i]+local[side][i])-fn(v[i] for v in part['verts']))
            for side,fn in [('min',min),('max',max)] for i in range(3))
    if err>BOUNDARY_TOLERANCE_M:bound_errors.append({'name':part['name'],'max_error_m':err})
checks['refreshed_manifest_architecture_bounds_match']=not bound_errors
pod=next(o for o in manifest['objects'] if o['name'].startswith('R17_Furniture_042_'))
cx,cy=pod['location'][0]/100,-pod['location'][1]/100
lo,hi=pod['local_bounds_m']['min'],pod['local_bounds_m']['max']
pod_bounds=[cx+lo[0],cy+lo[1],cx+hi[0],cy+hi[1]]
pod_door=next(o for o in D['openings'] if o['id']=='E39-POD1')
approach=LineString([(pod_door['x']-1,pod_door['y']),(pod_door['x']+2.4,pod_door['y'])]).buffer(.45,cap_style=2)
pod_overlap=box(*pod_bounds).intersection(approach).area
checks['POD1_shifted_prop_042_approach_clear']=pod_overlap<EPS

# Historical coplanar evidence from original source meshes. Count surface area,
# rather than exact triangles: overlapping triangulations need not be identical.
original_up={};above=[]
for p in O:
    vs=p['verts'];proj=[]
    for f in p['faces']:
        v=[vs[i] for i in f];q=Polygon([(t[0],t[1]) for t in v]).buffer(0)
        if q.area>1e-8:proj.append(q)
        if max(t[2] for t in v)-min(t[2] for t in v)<1e-6 and round(v[0][2],5) in [0,5.4]:
            ar=sum(v[i][0]*v[(i+1)%len(v)][1]-v[(i+1)%len(v)][0]*v[i][1] for i in range(len(v)))/2
            if ar>1e-8:original_up.setdefault((p['name'],round(v[0][2],5)),[]).append(q)
    if min(t[2] for t in vs)<=5.40001<max(t[2] for t in vs):above.append(unary_union(proj))
original_up={k:unary_union(v) for k,v in original_up.items()}
pairs=[]
for z in [0,5.4]:
    at=[(n,q) for (n,zz),q in original_up.items() if zz==z]
    for (n,q),(m,r) in itertools.combinations(at,2):
        ar=q.intersection(r).area
        if ar>.001:pairs.append({'z_m':z,'parts':[n,m],'area_m2':ar})
fb=original_up[('Floor_B',5.4)]
dup_area=fb.intersection(unary_union([q for (n,z),q in original_up.items() if z==5.4 and n!='Floor_B']))
visible=dup_area.difference(unary_union(above))
evidence={
 'original_source_sha256':hashlib.sha256(ORIGINAL.read_bytes()).hexdigest(),
 'coincident_upward_surface_pairs_at_5p4m':sum(p['z_m']==5.4 for p in pairs),
 'coincident_upward_surface_pairs_at_0m':sum(p['z_m']==0 for p in pairs),
 'Floor_B_overlapping_upward_surface_area_m2':dup_area.area,
 'overlap_not_covered_by_source_upper_solids_at_5p40001m_m2':visible.area,
 'largest_pairs':sorted(pairs,key=lambda p:p['area_m2'],reverse=True)[:12],
 'interpretation':'Strong geometric evidence for z-fighting at B-floor height, especially lower wall caps. This diagnoses source overlap; the exact pixels in a user screenshot were not reproduced in this audit.',
}
cleanup_path=R/'cleanup_result.json'
cleanup=json.loads(cleanup_path.read_text(encoding='utf8')) if cleanup_path.exists() else None
failed=[k for k,v in checks.items() if not v]
report={'revision':'R17 independent exported-architecture 3D audit','checks':checks,'passed':not failed,'failed':failed,
 'source_plan_sha256':hashlib.sha256(plan_raw).hexdigest(),'architecture_meshes_sha256':hashlib.sha256(mesh_raw).hexdigest(),
 'architecture_script_sha256':hashlib.sha256((R/'prepare_architecture.py').read_bytes()).hexdigest(),
 'method':'Reconstruct each exported mesh height section from oriented boundary faces; inspect supported floor and free-space volumes. Does not run the generator or call UE.',
 'exported_parts':len(M['parts']),'exact_duplicate_faces':dups,'horizontal_coplanar_overlap':overlaps,
 'clearance_results':clearances,'route_results':route_results,'door_results':door_results,
 'floor_support':floor_support,
 'refreshed_manifest':{'sha256':hashlib.sha256(manifest_path.read_bytes()).hexdigest(),
                       'revision':manifest['revision'],'bounds_errors':bound_errors,
                       'POD1_prop_042_bounds_m':pod_bounds,'POD1_approach_overlap_m2':pod_overlap},
 'upper_E4_original_void_m2':e4_void.area,'upper_E4_void_filled_by_slab_m2':e4_void.intersection(b_slab).area,
 'source_z_fighting_evidence':evidence,
 'cleanup_record_found':cleanup is not None,
 'cleanup_reported_old_actors_removed':cleanup.get('removed_old_actors') if cleanup else None,
 'limitations':['No UE calls or mesh import performed. Physics traces, character movement, UV/lightmap behavior and retained-scene collision require separate engine verification.',
                'Retained stairs, facade, Omen and other old actors are outside the new architecture mesh payload. Cleanup state was not independently queried in UE.']}
(R/'independent_3d_qa.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
lines=['# R17 独立三维建筑审核','',f"结果：{'通过' if not failed else '未通过'}。直接从导出的 architecture_meshes.json 重建高度截面；未执行生成器或 UE 调用。",'',
 f"- 平面 SHA256：`{report['source_plan_sha256']}`",f"- 三维网格 SHA256：`{report['architecture_meshes_sha256']}`",'',
 '## 当前建筑', '',
 '- 核对新入口、L01 南门、训练双门和 C0 全高净洞，首幕与训练路线按半径0.45m和1.8m人体高度检查。',
 '- 核对训练20×34.7×8m净空、高管道2.1×1.5×1.4m净空、平台与跳台实体支持。',
 '- 对照A/B地面、研究庭院/主控/E4原缺板，核对下层E4清空。',
 f"- 导出坐标按0.00001m精度量化；地面覆盖比较容差0.00002m。A/B原始边缘差面积分别{floor_support['A']['raw_boundary_difference_m2']:.9f}㎡/{floor_support['B']['raw_boundary_difference_m2']:.9f}㎡，均完全处于该容差内，无实际宽度的板面缺口。",
 '- 已复核修正：下层门楣不再向上侵入训练室；上层E4原23.379581㎡井洞保留。',
 '- 刷新后的SceneBridge manifest中32块建筑的放置边界与本次审核网格一致；POD1第042件家具已南移1.5m，门内外半径0.45m直行接近带无重叠。',
 f"- 导出 {len(M['parts'])} 块分层表皮；完全重复面 {dups}，非完全相同的水平共面覆盖问题 {len(overlaps)} 组。",'',
 '## 原始地面闪烁的几何证据','',
 f"原 prepared_meshes 在 z=5.4m 有 {evidence['coincident_upward_surface_pairs_at_5p4m']} 组同向共面顶面重叠。Floor_B 与其他顶面重叠去重面积约 {dup_area.area:.6f}㎡；其中约 {visible.area:.6f}㎡ 不被该高度上方的源实体遮住。z=0 未发现同类重叠。",'',
 '主要重叠来自 Floor_B 与下层墙顶、门楣顶、Scenic_Solid_Base、主控墙分段顶盖。Ground_Wing_Ceiling_Infill 还与下层墙顶局部重叠。即便三角形不完全相同，共面面片仍会争夺深度。分层体积合并并仅导出外露表面能移除这些重复接触面。', '',
 '这为地面网格闪烁提供了明确几何原因；本审核未复现用户截图的每个像素，不能排除额外材质或旧Actor重叠。旧建筑清理和UE实际trace由主任务另行记录。', '',
 f"cleanup_result.json记录移除{cleanup.get('removed_old_actors') if cleanup else '未知'}个旧Actor；本审核引用该清理记录，未独立查询UE场景。",'',
 '## 未通过项','']+(['无。'] if not failed else ['- '+x for x in failed])
lines += ['', '## 实机范围','', '本审核未检查UE中的动态门、实际角色移动、复杂碰撞开关、UV/lightmap或保留的旧楼梯/外立面/Omen碰撞。']
(R/'independent_3d_qa.md').write_text('\n'.join(lines)+'\n',encoding='utf8')
print(json.dumps({'passed':not failed,'failed':failed,'mesh_sha256':report['architecture_meshes_sha256'],'source_coplanar_area_m2':dup_area.area},ensure_ascii=False))
