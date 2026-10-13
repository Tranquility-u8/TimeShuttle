"""Centimetre placements fitted to the existing 20 x 34.7 x 8 m room."""
import json,math
from pathlib import Path
ROOT=Path(__file__).resolve().parent
items=[]
def point(x,y,z=0):return [(x-10)*100,1200-y*3470/24,z]
def add(stage,name,mesh,loc,scale=(1,1,1),yaw=0,material=None,collision='solid',folder=None):
    row=dict(id=stage+'_'+name,stage=stage,label=name,mesh=mesh,location_cm=loc,scale=list(scale),yaw=yaw,collision=collision,folder=folder or stage)
    if material:row['material']=material
    items.append(row)
def prop(stage,name,mesh,x,y,z=0,**kw):add(stage,name,'SM_TS_'+mesh,point(x,y,z),**kw)
def line(stage,name,loc,dims,material='M_TS_TrainingCyan'):
    add(stage,name,'/Engine/BasicShapes/Cube',loc,[v/100 for v in dims],material=material,collision='none',folder=stage+'/FloorGuides')
def outline(stage,name,x0,y0,x1,y1,material):
    a,b=point(x0,y0,1),point(x1,y1,1)
    for suffix,loc,dims in [('Near',[(a[0]+b[0])/2,a[1],1],[b[0]-a[0],3,1]),('Far',[(a[0]+b[0])/2,b[1],1],[b[0]-a[0],3,1]),('Left',[a[0]+2,(a[1]+b[1])/2,1],[3,abs(b[1]-a[1]),1]),('Right',[b[0]-2,(a[1]+b[1])/2,1],[3,abs(b[1]-a[1]),1])]:line(stage,name+'_'+suffix,loc,dims,material)
outline('S1','FallingRockArea',0,2,20,10,'M_TS_TrainingAmber')
outline('S1','CentralCompletionArea',5,11,15,14,'M_TS_TrainingCyan')
line('S1','FullWidthTriggerBand',point(10,4,1),[1998,6,1],'M_TS_TrainingWeakpoint')
for row,y in enumerate([2.8,4.8,6.8,8.8]):
    for col,x in enumerate([1.5,4.3,7.1,10,12.9,15.7,18.5]):
        z=[270,90,360,220,140,410,300][(col+row*2)%7]
        prop('S1',f'FrozenFallingRock_{row+1}{col+1}','Rock_A' if (row+col)%2==0 else 'Rock_B',x,y,z,scale=(1,1,.9+(row%2)*.2),yaw=(row*19+col*31)%180)
prop('S2','FrontShooter_2A_2B','ShooterProxy',10,21,folder='S2/Front_2A_2B')
prop('S2C','SideShooter_2C','ShooterProxy',16,14,yaw=45,folder='S2/Side_2C')
table_y=point(10,14.5)[1]
for i in range(10):
    add('SharedShooting',f'SealedTable_{i+1:02}','SM_TS_SupplyTableSegment',[-900+200*i,table_y,0],folder='00_SHARED_S3_to_S7A/Tables')
for i,x in enumerate([-700,-300,300,700]):
    add('SharedShooting',f'AmmoRefreshSlot_{i+1}_StaticDisplay','SM_TS_AmmoPack',[x,table_y+25,105],folder='00_SHARED_S3_to_S7A/Ammo_Refresh_Positions')
add('SharedShooting','Pistol_StaticDisplay','/Game/Weapons/Pistol/Meshes/SM_Pistol',[-75,table_y+25,109],folder='00_SHARED_S3_to_S7A/Equipment')
add('SharedShooting','PawnBarrier_NoCross_NoVault','/Engine/BasicShapes/Cube',[0,table_y,400],[20,.6,8],collision='pawn_barrier',folder='00_SHARED_S3_to_S7A/Collision')
for i,x in enumerate([5,8.5,12,15.5]):prop('S3',f'StaticTarget_{i+1}','TrainingTarget',x,20)
for i,(x,lo,hi) in enumerate([(6,4,8),(10,8.7,11.3),(14,12,16)]):
    prop('S4',f'MovingArmorTarget_{i+1}_Layout','ArmoredTarget',x,20)
    line('S4',f'MovementRail_{i+1}',point((lo+hi)/2,20,2),[(hi-lo)*100,10,3],'M_TS_TrainingDarkMetal')
def suspended(stage,y):
    prop(stage,'SuspensionGantry','Gantry',10,y)
    prop(stage,'ShootableLink_Layout','BreakableLink',10,y,507)
    prop(stage,'SuspendedRock_Layout','SuspendedRock',10,y,350)
    # A slim stem closes the link/rock gap while leaving the orange target exposed.
    line(stage,'LinkToRockStem',point(10,y,503.5),[10,10,7],'M_TS_TrainingDarkMetal')
    outline(stage,'RockImpactFootprint',8.3,y-.83,11.7,y+.83,'M_TS_TrainingAmber')
suspended('S5',18)
for i,(x,y) in enumerate([(9,18),(10,18.3),(11,18)]):prop('S5',f'ResistantTarget_{i+1}_Layout','ArmoredTarget',x,y)
suspended('S6',18)
for i,(x,y) in enumerate([(9,17.5),(10,18.5),(11,17.5)]):prop('S6',f'RockTarget_{i+1}','TrainingTarget',x,y)
for i,x in enumerate([5,15]):
    prop('S6',f'MovingTarget_{i+1}_Layout','TrainingTarget',x,21)
    line('S6',f'MovementRail_{i+1}',point(x,21,2),[300,10,3],'M_TS_TrainingDarkMetal')
prop('S7A','MeleePreview_PlayerSideOfTable','MeleeProxy',5.5,12.4,yaw=-45)
for name,kind,x,y in [('L1','LowCover',8,13.5),('H1','HighCover',5,17),('H2','HighCover',13,16),('L2','LowCover',16,18.5),('L3','LowCover',9.5,20.5)]:
    prop('S7B',name+'_'+kind,kind,x,y,folder='S7B/Cover_Near_Mid_Far')
for name,kind,x,y,yaw in [('M','MeleeProxy',10.5,16.5,0),('R1','ShooterProxy',2.5,19,-20),('R2','ShooterProxy',17,20,25),('R3','ShooterProxy',12,22.5,8)]:
    prop('S7B',name+'_EnemyLayoutProxy',kind,x,y,yaw=yaw,folder='S7B/Enemy_Layout_Proxies')
data={'version':1,'room_clear_cm':[2000,3470,800],'entrance_center_cm':[0,1200,0],'diagram_to_ue':'X=(x-10)*100; Y=1200-y*3470/24; Z=cm. Prop dimensions are not stretched.','default_stage':'S1','stages':['S1','S2','S2C','S3','S4','S5','S6','S7A','S7B'],'shared_active_in':['S3','S4','S5','S6','S7A'],'actors':items,'scope':'Static mesh staging and editor/PIE preview states. Gameplay triggers, AI, moving targets, time/fall/damage, pickups, ammo respawn and melt transitions remain integration work.'}
(ROOT/'layout_manifest.json').write_text(json.dumps(data,indent=2),encoding='utf-8')
print(json.dumps({'actors':len(items),'stages':data['stages']}))
