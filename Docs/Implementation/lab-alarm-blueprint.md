# 实验室警报器蓝图

任务：ART-001 / 20261111-lab-fire-alarm-concepts。2026-11-11，UE 5.6.1。状态：资产已保存，等待用户审查。

用户最新范围为只交付模型蓝图、红色发光材质和预留声音组件。本轮场景临时摆放已撤回，未保存关卡改动。

## 使用入口

- 蓝图：`/Game/Blueprints/Environment/BP_LabAlarm`
- 网格及材质：`/Game/Environment/Chapter1/ParticleLab/Alarm/`
- 可重导入源文件：`SourceAssets/Chapter1/ParticleLab/Alarm/`

蓝图组件为DefaultSceneRoot下的AlarmMesh和AlarmAudio。模型源为V3 FBX；UE网格为SM_LabAlarm，将8个源部件合并为一个静态网格并保留4个材质槽。尺寸为宽30cm、高11cm、深5cm；后背中心为原点、前方为局部+Y、上方+Z。单一完整灯罩几何和独立发光材质槽保留，未改动V3亮面轮廓。装饰网格无碰撞，不影响导航。

红灯材质实例为`MI_LabAlarmRed`，父材质`M_LabAlarmEmissive`。`EmissionColor`默认(1,0,0)，`EmissionIntensity`默认1.5。已加入EyeAdaptationInverse曝光补偿，`ExposureCompensation`默认1；此更新修复蓝图预览明亮但实际关卡内暗红的问题。发光计算为配套遮罩×颜色×强度；遮罩关闭sRGB，使用Masks压缩，保护暗红倒角与亮面分界。通过该材质实例统一调整整块灯罩。当前为常亮材质，没有添加闪烁、状态切换或关卡照明逻辑。

AlarmAudio的Sound暂为空，AutoActivate关闭，局部位置(0,5,-0.4)cm；开启空间化和距离衰减，内半径100cm、衰减距离1200cm。后续在此组件的Sound字段指定SoundWave、SoundCue或适用音频资产，再由实际警报逻辑调用Play/Stop。尚未提供或播放真实声音。

Actor默认关闭Start With Tick Enabled；编辑器图标比例0.1，避免音频图标遮住小尺寸模型。没有新增事件逻辑图。

## 验证和保存范围

已调用蓝图编译，编辑器编译按钮显示成功；生成类可实际实例化。断言组件数恰好1个StaticMeshComponent和1个AudioComponent，模型引用、4个材质引用、灯罩材质槽、关闭碰撞、空Sound与AutoActivate均通过检查。已在蓝图视口目视核对模型与发光面。此次不包含PIE交互或真实音频播放验收，由用户审查后再决定后续工作。

本轮只新增BP_LabAlarm、Alarm资产文件夹和对应源FBX/贴图。用户已有的其他修改保留。Map_LabV39文件SHA256前后均为`779AF05901EADDD58BAE62A43D5F78430F5B5E93AA54B7ED5EA830FA2E69AA3F`，本轮场景实例已移除并重载原关卡。最终编辑器dirty map/content package列表均为空。

FBX初次导入曾提示无平滑组信息和部分近零切线；当前保留源法线并设置UE重建切线，蓝图预览中未观察到明显外观缺陷。不将此记录描述为完整网格切线审计通过。

证据位于工作区`tmp/lab-alarm-import-20261111/blueprint-verification.json`；建模源与几何审计位于`output/models/lab-alarm-concept01-v3/`。本轮早期场景截图为撤回前的临时检查，不作为最终场景交付。
