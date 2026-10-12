# 时间停止启停特效（TA-001 / TA-002 / P-034）

2026-10-11 第六轮随机破碎已保存：新增T_TS_FacetNoise周期随机Delaunay数据纹理，替换破碎主材质同向方格三角分区，块大小、朝向及凸凹分布更不规则。保留世界锚定及第五轮时序；25项冷PIE检查、2006帧同步记录、正式输入启停、同镜头对照/近景/锚定检查通过。只改M_PP_TS_Facets并新增纹理，其他15个既有资产哈希不变。参数及边界见[第六轮验收](../../../开发文档/时间停止特效/实现验收/irregular-facets/validation.md)，完整方案见[随机噪声方案](../../../开发文档/时间停止特效/irregular-facets-plan.md)。

2026-10-11 开启时序已保存：共享线性世界波前，每表面独立镜面保留/淡出；25项冷PIE检查、正式输入和近/远表面画面已验证。见[第五轮验收](../../../开发文档/时间停止特效/实现验收/entry-transition-timing/validation.md)与[开启时序方案](../../../开发文档/时间停止特效/entry-transition-timing-plan.md)。

第四轮历史更新：2026-10-09，第四轮大场景/近景优化已实施，指定无制作模块冷PIE的53项检查和正式输入链已通过，见[第四轮验收](../../../开发文档/时间停止特效/实现验收/large-scene-near-surface/validation.md)。新增世界网格分块与玩家Stencil排除；以下第三轮验证数字仅为历史。

日期：2026-10-03。**第三轮世界表面扫描与独立描边已保存并通过指定SDR冷PIE复测：描边41项、容量/换Pawn27项检查通过，表面21张多机位图中的59项有效锚点比较均在提案阈值内。** 冷启动确认15个视觉资产、制作模块未加载和正式参数落盘。当前设计见[第三轮方案](../../../开发文档/时间停止特效/第三轮_表面扫描与独立描边方案.md)，配置见[独立描边组件使用说明](../../../开发文档/时间停止特效/独立描边组件使用说明.md)，报告与视频见[第三轮验收记录](../../../开发文档/时间停止特效/实现验收/第三轮/验收记录.md)。持续进度见[开发进度](../../../开发文档/时间停止特效/开发进度.md)。第二轮及首版证据保留为历史；HDR、打包、满载性能和最终艺术接受未认证。

## 集成范围

`BP_FPCharacter` 新增 `TimeStopVFX` ChildActorComponent，类为 `/Game/VFX/TimeStop/BP_TimeStopVFXController`。视觉控制器只读取现有 `AC_TimeAbility.ModeIndex`，不修改能力输入、能量阈值、世界倍率、弹丸或伤害链。模式 1 的进入／离开边沿触发特效，单独 Normal↔BulletTime 不触发本效果。

控制器拥有独立动态材质、PostProcessComponent和原生InstancedStaticMeshComponent。网格以60m周期块按游戏相机位置吸附，默认125块、120m绘制距离，退出隐藏、EndPlay销毁；不再生成旧Niagara线网。GetRealTimeSeconds仍驱动可中断过渡，不改变能力逻辑。玩家自身及附属装备Mesh借用动态预留的1–223 Stencil之一，按可见深度排除，不再按80–220cm距离误排除墙面。退出、丢弃和销毁时仅恢复仍归本系统所有的标记。

第三轮 Facets 继续接收该控制器的 Origin/Radius/Pulse，但三角分区改用固定世界坐标，不再使用屏幕像素分区。独立描边由目标 Actor 上的 `AC_TimeStopOutline` 注册到自动生成的 `BP_TimeStopOutlineManager`，不要求修改玩家蓝图；Manager 缓存 Player0 与其 AC_TimeAbility，并在 Pawn 改变/引用失效时重新查找。描边只读 ModeIndex==1；组件 Tick 间隔为0，不用受世界倍率缩放的 DeltaTime 累计延迟。`bEnabled` 是正式开关，原生 Activate/Deactivate 不是本实现的配置入口。没有给既有敌人自动添加组件，也没有改弱点视觉或伤害规则。

## 资产

共17个视觉资产（含保留的旧网格/NS历史资产），均位于 `/Game/VFX/TimeStop/` 及其 `Outline/` 子目录；制作辅助代码不是运行时依赖。

| 资产 | 职责 |
| --- | --- |
| BP_TimeStopVFXController | 生命周期、能力模式检测、现实时间过渡、动态参数和清理 |
| Curve_TS_Enter / Curve_TS_Exit | Exit继续驱动退出半径/权重/脉冲；Enter资产保留，开启已改用线性波前与局部消散 |
| M_PP_TS_State / MI_PP_TS_State | 场景冷色、去饱和与深度边缘，Scene Color After Tonemapping、优先级 10 |
| M_PP_TS_Facets / MI_PP_TS_Facets | 固定世界三角格、共享正负高度、扫描波带内虚拟凸凹取色与近景保护，Scene Color After Tonemapping、优先级 20 |
| T_TS_FacetNoise | 第六轮随机三角RGBA数值纹理，RG梯度/B高度/A诊断标识；512三角/周期，线性BGRA8 |
| SM_TS_GridChunk | 60m周期块、5m线间距，432线/64节点、5696三角形；27/125/343实例 |
| SM_TS_SpatialGrid | 保留历史单网格，当前控制器不使用 |
| M_TS_Grid | 蓝紫线网、亮节点、距离淡出、软遮挡和近景遮罩 |
| NS_TS_SpatialGrid | 保留历史Niagara系统，当前控制器不使用 |
| Outline/AC_TimeStopOutline | Actor级样式、目标Static/Skeletal Mesh筛选、CustomDepth借用与恢复、生命周期 |
| Outline/BP_TimeStopOutlineManager | 每世界共享PP/MID、32个Stencil槽、Player0能力引用和模式检测 |
| Outline/M_PP_TimeStopOutline | 可见外缘与解析软光晕，After Tonemapping、优先级30；不是引擎Bloom |
| Outline/BP_OutlineExample_Green / BP_OutlineExample_Red | 绿色Cube与淡红细边Manny骨骼示例；不替换正式交互物或敌人 |

网格使用周期静态几何和原生实例组件，避免固定线条的逐粒子模拟；波带固定原点与网格按相机管理的覆盖区域分离。PP 计算封装于带说明的 Custom 材质节点，参数保留给后续调色和强度调整。

## 调整入口

| 位置 | 参数与当前首值 |
| --- | --- |
| 控制器默认值 | EnterDuration=3.0 s（最短扫描时间）、ExitDuration=1.0 s、MaxVisualRadius=15000 cm |
| 控制器 Time Stop / Entry Timing | EnterScanSpeed=5000 cm/s、FacetHoldTime=0.35 s、FacetFadeTime=1.25 s |
| 控制器默认值 | GridIntensity=0.12、BoundaryIntensity=0.08 |
| 控制器默认值 | GridDrawDistance=12000 cm（运行时限制6000–18000）、FullSceneCoverage=true |
| Facets 材质／实例 | CellSizeWorld=160 cm、ReliefDepth=22 cm、BandWidth=550 cm |
| Facets 材质／实例 | DistortionPixels=48（位移上限，1080高度参考像素）、FacetRotation=0.40、ChromaticPixels=0.5、DebugWorldCells=0 |
| State 材质／实例 | TintStrength=0.72、Desaturation=0.55、EdgeIntensity=0.16 |
| AC_TimeStopOutline 实例 | OutlineColor（LinearColor颜色选择器）、Intensity≥0、Thickness=1–8显示像素、bEnabled、MeshTag |
| 描边示例 | Green：颜色(0.12,1,0.22)、Intensity=2、Thickness=2.5；Red：颜色(1,0.32,0.38)、Intensity=0.8、Thickness=1 |

MI 中显式保存美术参数，运行中 Radius/Weight/Pulse 继续由控制器更新。第三轮从场景深度重建世界表面、按世界法线主轴投影为XY/XZ/YZ三角格；格点位置、三角ID和共享正负高度由固定世界坐标散列。重心插值与高度梯度产生虚拟凸凹方向，再投影到当前屏幕取色。世界格场与扫描Origin分离；移除了第二轮58%的全屏峰值，开启时按共同波前与表面被扫过后的局部年龄显示，保留后缓慢淡出；退出仍按原波带与Pulse显示。Pulse或有效半径归零时无残留扭曲。颜色、深度和法线使用各自缓冲UV，红/蓝色散目的点同样受玩家身份与跨表面深度保护。

这是世界表面锚定的后处理视觉模拟，不移动网格顶点，不改变真实轮廓、碰撞、阴影或屏幕外几何。静态/近似冻结表面是当前适用对象；仍在移动、旋转或蒙皮变形的物体会穿过世界格场，不能称为物体局部贴附。主轴投影接缝、低屏幕百分比下的Debug格线阶梯和连续镜头稳定性需结合本轮画面复测，不能从坐标公式推导所有场景通过。

描边组件自动选择Owner的StaticMeshComponent/SkeletalMeshComponent；MeshTag非空时按Component Tags过滤，不递归ChildActor。每个登记组件独占224–255中的一个Stencil值，自己的多个Mesh共用该槽；32个float4参数的RGB为颜色×Intensity、A为像素宽度。Manager启动时扫描已存在的CustomDepth占用并保留冲突槽，可用容量因此可能少于32。已启用CustomDepth的目标Mesh默认跳过并记录；其余Mesh借用前保存Stencil/Mask，退出仅在flag、ID和mask仍归本组件时恢复，保留外部较新的改动。Normal/BulletTime不描边；组件仍启用时保留租约，bEnabled=false或销毁释放。满槽后需bEnabled关闭再开启重试。运行中其他系统新增224–255占用不会被自动重新协商，须遵守共享预留约定。

开启时State、Facets、Grid共享160cm波前羽化。FullSceneCoverage=true时各层共同将世界距离封顶为MaxVisualRadius，范围外物体在扫描到达上限时接入；不再根据StateWeight提前铺满。退出沿用原StateWeight覆盖衰减。持续状态不受MaxVisualRadius限制；天空保留较弱冷色。网格每轴以6000cm吸附相机，重复几何的世界格点不连续滑动；绘制范围75%开始淡出，远处另有密度亮度衰减，遮挡线保留8%亮度。玩家像素由CustomStencil及CustomDepth/SceneDepth比较识别，移除了所有旧近景距离抹除。

第二轮历史测试发现网格原自动包围范围会在部分相机位置错误裁掉整个效果。同机位PIE中固定±1600cm可见，缩回±100cm消失，因此将正确范围保存至系统资产；第三轮沿用该范围。

第四轮移除近景深度80–200cm保护，改用玩家身份遮罩；饱和暖色仍按相对色差衰减效果。屏幕空间弱点括号由现有 WidgetComponent 绘制；没有替换弱点材质或修改伤害。首版/第二轮指定画面中实际重型手枪镜头可读，Shooter 黄色头部与红色手臂括号可见，Melee 所测防御姿势按原遮挡规则隐藏；这些历史画面不替代第三轮新扫描的验收。未认证所有武器、姿势或近墙动作。

三个 PP 均在色调映射后，依次 State（10）、Facets（20）、Outline（30）。描边放在冷色与扫描之后，按各物体独立颜色合成；光晕由材质邻域采样解析计算，不经过引擎Bloom。各层使用 ViewportUVToSceneTextureUV 分别映射所需缓冲，不能直接复用 PostProcessInput0 的 UV 采深度。Custom节点的已归档源码入口为 [TimeStopVFX](TimeStopVFX/README.md)，本轮冷导出还在 `Saved/Agent/TimeStopVFX/SurfaceOutline/`；快照应核对轮次，uasset的实际输出连线为权威。

首版球壳候选保存在 `/Game/Developers/TimeStopVFX/`，不被正式控制器引用。224 三角形硬法线球壳、IOR 1.035、Opacity 0.04，在相机中心半径 300/700/1500 cm 的首版测试中未呈现足够明显的分面效果；当时选择了可控且具备时序/近景保护的后处理方案。此结果不是对所有球壳折射实现的否定。

## 第三轮指定验证证据

- `SurfaceOutline/verify_outline_20261003_132931/result.json`与全局`verify_outline_result.json`内容一致：无制作模块冷启动后的41项PIE检查全部通过，passed=true、error=null、restore_errors=[]。覆盖Static/Skeletal独立颜色/亮度/粗细实时更新、FullStop与BulletTime边界、既有CustomDepth保留、槽位释放/复用、bEnabled开关、组件销毁、Manager销毁重建。
- `verify_capacity_possess_20261003_134212/result.json`与全局`verify_capacity_possess_result.json`一致：27项检查全通过、error=null、restore_errors=[]。32组件取得32个独立槽，第33个不覆盖已有租约；释放槽后关闭/开启bEnabled重试成功。切换到无时间能力Pawn后清除旧的仍有效能力缓存，停止描边并恢复网格；切回原Pawn后恢复绑定和FullStop描边。该夹具使用隐藏对象，只验证状态与容量，不测32组件同时可见的渲染性能。
- `verify_layout_result.json`：两张蓝图的16张图经过Blueprint Assist整理，忽略reroute后的有效语义一致；`outline_player_patch.json`与`verify_layout_player_result.json`确认PlayerRef补图和后续单图整理保存，编译0错误/0警告。
- `action_results.json`：正式IA_TimeAbility动作注入的entered/neutral均true，验证现有输入链进入与退出归零；不代表物理T键测试，也不是描边像素断言。
- `response_outline_cold_export.json`：ok=true、tool_loaded=false、asset_count=15、CustomDepth=3、DebugWorldCells=0、dirty_content=[]、dirty_maps=[]；冷加载读到上述Facets参数、AfterTonemapping优先级20/30和红色示例Manny引用。
- `surface_camera_20261003_132837/surface_camera_result.json`与全局报告一致：冷PIE冻结AI复测21/21张完成，100/66.667/50三档、偏航和横移下59项有效锚点RGB比较均在0.08提案阈值内，restored=true、error=null、restore_errors=[]。报告仍区分采样检查与人工画面评审，不宣称自动视觉合格。旧批次84项有效/4项NPC遮挡的历史复核单独保留，不与本批次累加。
- `delivery_20261003_134018`完成99帧采集，tool_loaded=false、error=null、restore_errors=[]；已归档原1341×767的[实际开启/维持/关闭视频](../../../开发文档/时间停止特效/实现验收/第三轮/实际开启_维持_关闭.mp4)（7.288秒）和[连续移动调试视频](../../../开发文档/时间停止特效/实现验收/第三轮/世界三角锚定_连续移动调试.mp4)（4.272秒），并保存正常、波峰、两色同屏、退出和移动机位截图。
- 指定蓝图的编译零错误不代表全工程日志零错误。现有`STT_Shooter_SenseEnemies`在AI初始化/停脑时仍有空Controller错误，主验收单独记录，未作为Outline错误或在本任务修改。
- 本轮报告、视频及画面范围见[第三轮验收记录](../../../开发文档/时间停止特效/实现验收/第三轮/验收记录.md)；满载性能/HDR/打包/所有武器及最终艺术接受未认证。

## 第二轮历史证据

- 编辑器从磁盘重启，无TSVFXEditor加载；新PIE读取有效MID参数115/320/850/.40/.55，NS固定±1600cm已保存，实际FullStop画面中网格可见。
- 正式IA_TimeAbility的Enhanced Input注入进入与归零通过，8项打断/模式/生命周期断言全部通过；约5.9秒实际启停录像最终R/W/P为0、倍率1。
- 1341×767单帧GPU采样：峰值State .029ms、Facets .068ms，稳态.029+.032ms，关闭时两个PP遍消失。不是总GPU增量或1080p/打包性能保证，Niagara未单独计时。
- 10资产依赖检查、dirty_content=[]、dirty_maps=[]，AC_TimeAbility哈希不变，本轮起始存档已恢复。最终6个正式资产变化已按备份哈希核对。
- 原AI感知Controller为空、EmptyHands骨骼和武器动画警告另行记录，没有把全项目日志写为无错误。临时拾取夹具UI错误与脚本API错误不归因于正式VFX。
- 完整记录与图像在工作区专题的 `实现验收/第二轮/验收记录.md`；首版数字和截图仅作为历史，不替代本轮证据。

## 首版历史证据

- 控制器编译 0 error / 0 warning；玩家挂接后 BS_UpToDate。定向保存时无脏资产／地图。
- 独立逐帧周期测试：0.01 世界倍率下约 0.75 现实秒完成进入，退出约 0.70 秒；最终 Radius、StateWeight、FacetPulse 全零、全局倍率 1。
- 快速反复切换、FullStop→BulletTime、单独 BulletTime 开关、Health=0 以及视觉 Actor 销毁清理，共 8 项自动夹具断言通过。夹具只修改 PIE 实例。
- 初轮 Niagara 系统图不完整与 Mesh Renderer 第 0 槽为空均已修复。系统 Valid/Ready 为 true，唯一有效网格槽，运行时单粒子与线网/交点实际可见。
- 8 张控制器图完成 Blueprint Assist 尺寸刷新、整理、结构化注释、再整理及编辑器目视复核；忽略 reroute 后的有效连接与默认值比较一致。随后正常周期与 8 项边界断言重跑通过。
- 不加载临时 TSVFXEditor 的编辑器冷启动，10 个正式资产加载、两张蓝图编译、保存状态检查通过；真实 IA_TimeAbility 的 Enhanced Input 注入验证进入与归零通过。最后 UV 修正也在无辅助模块的编辑器中编译、保存并运行。
- GPU 历史采样：约 1280×722 单帧中 Facets 0.026 ms、State 0.024 ms，关闭时两遍处理均消失。采样在最终深度 UV 修正之前；不能当作最终材质基准或总 GPU 增量，也未单独测量 Niagara 成本。
- 现有 EmptyHands 的 `GetSocketInfoByName(slide)` 警告在测试期间出现，尚未将其归因于本任务。

本机原始证据在忽略跟踪的 `Saved/Agent/TimeStopVFX/`，包括生成脚本、备份、编译日志、图表导出、周期记录、边界测试与截图。不同机器克隆不会自动获得该临时目录。

## 验证边界与后续

物理键 T 的桌面短按注入未稳定触发，已用实际 Enhanced Input 动作验证链路，未修改输入绑定。HDR、打包、网络/分屏、所有武器/敌人姿势、大场景性能、最终艺术验收仍未认证。第二轮天空参与较弱冷色但不折射；视觉传播半径不改变原玩法的世界时间倍率。无音频资源新增，不默认加入侦测红标记。

第三轮没有重验整套弹丸伤害或回溯玩法。当前描边按单人Player0实现，最多32个登记组件；透明材质须自己支持CustomDepth写入，材质不写深度时不能保证轮廓。邻域采样最坏8方向×12步，尚无第三轮大场景性能预算；多重重叠目标受单层CustomDepth/Stencil可见信息限制。不要用原生组件Deactivate代替bEnabled。

首版包含玩家ChildActor接入；第二轮更新三个材质、两个实例及Niagara包围盒。第三轮更新Facets及实例、新增5个Outline资产，并将CustomDepth配置设为3；未改能力核心、既有敌人/弱点、伤害或地图。三份旧材质保存在Developers/TimeStopVFX/CompareV1，不被正式资产引用。临时制作模块不写入uproject，冷导出确认未加载；恢复采用实施前定向备份，不能使用整库reset覆盖用户工作。正式开发计划/Excel保持原值。

## 2026-10-11 开启时序参数

在 `/Game/VFX/TimeStop/BP_TimeStopVFXController` 的 Class Defaults 搜索参数名。`EnterScanSpeed` 控制扩张速度上限（cm/现实秒），降低它会放慢破碎与遮罩；`EnterDuration` 是最短完整扫描时间。实际速度取 `min(EnterScanSpeed, MaxVisualRadius/EnterDuration)`（并有正值保护）。默认150m扫描3秒，300m扫描6秒。

`FacetHoldTime` 是波前经过每个表面后完整镜面的保留时间；`FacetFadeTime` 是之后的平滑淡出时间。想让镜面消失更慢，优先增大 FadeTime，不需要扩大 BandWidth；BandWidth现在主要控制退出波带。默认每个表面保留0.35秒再用1.25秒淡出。最后一圈也完整消散后，FacetPulse才归零。冷色/网格持续到退出时停。

`Radius` 现在包含镜面尾段，可能大于 MaxVisualRadius；这不是扩大玩法作用范围。默认波前到150m为3秒，全部镜面清理约4.632秒。快速退出仍按当前权重及原退出曲线，不等尾段结束。所有时长使用现实时间，不延迟ModeIndex进入、不改变能量或世界时停倍率。中途调节时序参数建议退出后重新开启，使一次进入使用一致的速度与保留/淡出值。
