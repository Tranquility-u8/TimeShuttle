# 第一实验室残余亮度检查

2026-11-11，ART-001 / 20261111-lab-fire-alarm-concepts。当前编辑器Map_LabV39读取与可逆对照，未保存关卡改变。

主因：全局天空光LabV39_Sky，强度0.7。保持其他光源、曝光、机位不变，仅短暂将此值设0，墙面、地面和设备明显变黑。测试后恢复0.7。证据room-sky-on.png、room-sky-off.png和room-sky-result.json，restored=true。

次因：房间范围与若干邻区、其他楼层光源的衰减球相交。20盏26000/60000lm灯关闭CastShadows，存在穿墙/楼板照明贡献；将这组灯暂时设0后，柜体顶部和部分设备反光变暗，但房间整体仍亮。全部恢复原值，见room-ab-result.json及on/off图。范围相交并不代表每一盏都有同等贡献，不将候选数量当作直接照入房间的精确光源数量。

排查实值：全局PostProcessVolume LabV39_Exposure开启，MinEV100=MaxEV100=10，Exposure Compensation=+0.85。sg.GlobalIlluminationQuality=1（Medium），r.Lumen.DiffuseIndirect.Allow=0，r.DistanceFieldAO=1，r.AllowStaticLighting=0。固定曝光范围不支持“越暗自动抬亮”的判断；当前没有运行Lumen漫反射间接照明，也不能归因为静态烘焙照明残留。

后续处理选择：如果整张关卡都应更暗，可降低LabV39_Sky的Intensity；若只让第一实验室变暗，应检查天空光的室内遮蔽、目标光照质量与相关网格遮蔽，同时约束邻区无阴影灯的影响范围，避免用全局Sky强度影响其他房间。当前只完成原因检查，没有实施这些持久改动。灯具本身的自发光仍需在材质中单独调节。

证据根目录：工作区tmp/lab-alarm-import-20261111/。
