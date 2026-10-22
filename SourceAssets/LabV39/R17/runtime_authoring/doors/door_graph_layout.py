"""Position-only Blueprint layout: execution spine with nearby data subgraphs.

No nodes, links, defaults, or function metadata are created/modified here.
Get/Self sources sit below their direct consumers instead of a giant left column.
"""
from collections import defaultdict, deque


def height(node, executable=False):
    kind=node['kind']
    if kind in ('get','self'):return 48
    if kind in ('entry','event','result'):return 100
    if kind in ('set','branch'):return 110
    fn=node.get('function','')
    if fn=='K2_SetTimer':return 300
    if fn=='K2_SetRelativeLocation':return 230
    if fn=='MakeVector':return 150
    if fn in ('FInterpTo_Constant',):return 190
    if executable:return 170
    if fn in ('IsOverlappingActor','GetPlayerPawn'):return 120
    return 100


def layout_group(graph,ids,top):
    nodes={n['id']:n for n in graph['nodes'] if n['id'] in ids and n['kind']!='comment'}
    incoming=defaultdict(list);outgoing=defaultdict(list);exec_links=[]
    for a,ap,b,bp in graph['links']:
        if a not in nodes or b not in nodes:continue
        incoming[b].append((a,ap,bp));outgoing[a].append((b,ap,bp))
        if bp=='execute':exec_links.append((a,b))
    executable={a for a,b in exec_links}|{b for a,b in exec_links}
    executable|={k for k,n in nodes.items() if n['kind'] in ('entry','result','event','set','branch','call_parent')}
    # Pure function graphs still have an entry/result spine in their source spec.
    if not executable:executable={next(iter(nodes))}
    rank={k:0 for k in executable}
    for _ in range(len(executable)):
        changed=False
        for a,b in exec_links:
            if rank[b]<rank[a]+1:rank[b]=rank[a]+1;changed=True
        if not changed:break
    assert not changed,'Execution cycle requires an explicit layout, not rank growth'
    # Every pure producer belongs to its earliest executable consumer. Shared
    # values remain shared; layout must not duplicate them or change evaluation.
    owner={}
    for k in nodes.keys()-executable:
        queue=deque([k]);seen={k};targets=[]
        while queue:
            a=queue.popleft()
            for b,ap,bp in outgoing[a]:
                if b in executable:targets.append(b)
                elif b not in seen:seen.add(b);queue.append(b)
        owner[k]=min(targets,key=lambda t:(rank[t],t)) if targets else min(executable,key=lambda t:(rank[t],t))
    owned=defaultdict(list)
    for k,v in owner.items():owned[v].append(k)
    core_rank={};widths={}
    for e in executable:
        core={k for k in owned[e] if nodes[k]['kind'] not in ('get','self')}
        cr={k:0 for k in core}
        for _ in range(len(core)):
            changed=False
            for a in core:
                for b,ap,bp in outgoing[a]:
                    if b in core and cr[b]<cr[a]+1:cr[b]=cr[a]+1;changed=True
            if not changed:break
        core_rank.update(cr)
        widths[e]=max(420,(max(cr.values(),default=-1)+1)*340+80)
    columns=defaultdict(list)
    for e in executable:columns[rank[e]].append(e)
    # Preserve source order within branch columns. Different branches get local
    # data lanes; straight execution chains stay on a common horizontal line.
    source_order={k:i for i,k in enumerate(nodes)}
    for members in columns.values():members.sort(key=lambda k:source_order[k])
    xstart={};x=0
    for r,members in sorted(columns.items()):
        xstart[r]=x;x+=max(widths[e] for e in members)+80
    boxes=[]
    def place(k,x,y):
        n=nodes[k];w=180 if n['kind'] in ('get','self') else (300 if k not in executable else 380)
        h=height(n,k in executable)
        # Getter/pure overlap avoidance, with clearance for native SGraph labels.
        while any(x < bx+bw+32 and x+w+32 > bx and y < by+bh+32 and y+h+32 > by for bx,by,bw,bh in boxes):
            y+=80
        n['x']=int(x);n['y']=int(y);boxes.append((x,y,w,h))
    for r,members in sorted(columns.items()):
        y=top
        for e in members:
            start=xstart[r];end=start+widths[e]-420
            place(e,end,y)
            core=[k for k in owned[e] if nodes[k]['kind'] not in ('get','self')]
            core_columns=defaultdict(list)
            for k in core:core_columns[core_rank[k]].append(k)
            local_bottom=y+height(nodes[e],True)
            for cr,items in sorted(core_columns.items()):
                items.sort(key=lambda k:source_order[k])
                cy=y+height(nodes[e],True)+90
                for k in items:
                    place(k,start+cr*340,cy)
                    cy=nodes[k]['y']+height(nodes[k])+80
                    local_bottom=max(local_bottom,cy)
            # Place root getters only after all their local consumers exist.
            for k in sorted((k for k in owned[e] if nodes[k]['kind'] in ('get','self')),key=lambda k:source_order[k]):
                consumers=[b for b,ap,bp in outgoing[k] if b in nodes and ('x' in nodes[b]) and (b==e or owner.get(b)==e)]
                if consumers:
                    consumer=min(consumers,key=lambda b:(nodes[b]['x'],nodes[b]['y']))
                    cn=nodes[consumer];gx=cn['x']+20;gy=cn['y']+height(cn,consumer in executable)+48
                else:gx=start;gy=local_bottom+60
                place(k,gx,gy);local_bottom=max(local_bottom,nodes[k]['y']+height(nodes[k])+48)
            y=max(y+420,local_bottom+180)
    left=min(n['x'] for n in nodes.values());right=max(n['x']+(180 if n['kind'] in ('get','self') else 380) for n in nodes.values())
    bottom=max(n['y']+height(n,k in executable) for k,n in nodes.items())
    return {'x':left-100,'y':top-100,'width':right-left+200,'height':bottom-top+200},bottom+360
