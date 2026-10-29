# Chapter 1 第二实验室：坍塌演出与可复用模块

2026-10-28，地图 `/Game/Maps/Map_LabV39`，主实例 `Ch1_R2_Sequence`。本页记录当前 blockout 的运行时实现和维护入口；房间的最终名称、美术模型与正式演出节奏仍可调整。

本实现承接[天花板与两阶段 blockout](chapter1-room2-ceiling.md)。本页的运行时结果更新此前静态制作阶段，不改写几何制作和备份记录。

## 当前流程

1. 玩家从紫色管道出来，落到入口管道上的 `EntryBounds` 内，且 CharacterMovement 已落地，触发一次入口镜头。锁定移动、视角和玩法输入，停止残余速度，看向锁门并由 90° 缩至 60°，随后恢复原 FOV 和控制。
2. 锁门沿用现有交互接口。玩家交互后显示 `LOCKED`；导演先调用 `PrepareNormalTime()` 结束预先手动开启的时间能力，确认正常时间后锁定输入、停止残余速度，自动回头看向爆炸区域。前三块板因此按正常物理速度下落。
3. 小爆炸、声音与镜头震动播放；遮挡柜被物理抛开，出口解除锁定。三块天花板按 `20 → 15 → 21` 顺序从原顶面释放。
4. 镜头抬头，头顶第 `33` 块板释放。等待设定时间后，四块板和柜体保存动量并冻结，同时通过游戏原有 `AC_TimeAbility.ApplyTimeState` 进入 FullStop。
5. 即时交还相机和输入。玩家离开 `DangerBounds` 后，恢复原时间能力状态和各物体保存的速度，进入完成状态。

出口在爆炸前从管口和锁门回头位置都被遮挡；柜体炸开后，从锁门回头位置可辨认出口。紫色管道、橙色结构继续承担原有路线。初始白色落板是既有破坏后的静态布置，不由本导演重新播放。

## 模块与绑定

以下五个资产均位于 `/Game/Blueprints/Cinematics/`。运行时不依赖 Python 或 `LabAuthoring`；后者只用于编辑器内生成与整理蓝图。

| 蓝图 | 责任与复用接口 |
| --- | --- |
| `BP_CinematicCameraRig` | 保留玩家原 ViewTarget。`BeginCamera()` 缓存原 CameraComponent 的 FOV 和控制器朝向；`LookAt(TargetLocation, Duration, TargetFOV)` 按真实时钟插值 ControlRotation 与原相机 FOV；`IsMoving` 表示转向/缩放是否进行；`EndCamera()` 保留最终朝向并恢复自己借用的相机状态。自身不拥有输入锁或时间状态。 |
| `BP_CinematicFallingPropDriver` | `TargetActor` 指向一个场景物体。`InitializeTarget()` 保存初始姿态；`ReleaseProp(LinearVelocity, AngularVelocity)` 启用重力和物理；`FreezeProp()` 保存动量后停止模拟；`ResumeProp()` 恢复动量；`ResetProp()` 还原初始姿态和附件关系。 |
| `BP_CinematicTimeStopController` | `PrepareNormalTime()` 返回 `Ready`，用于演出开始前退出玩家时间能力；已有本模块会话时拒绝准备。`AcquireStop()` 返回 `Acquired`，并公开 `bOwnsStop`、`LastError`；`ReleaseStop()` 还原该会话采样的能力状态。获取/释放幂等，EndPlay 尝试释放仍有效的原能力组件。 |
| `BP_Chapter1Room2Sequence` | 本房间导演，管理阶段、镜头、落板、输入锁和空间触发。用 Actor 引用和实例参数编排通用模块；其他房间可复用前三个模块，另写自己的导演。 |
| `BP_CinematicLockedDoor` | `BP_LabRoomDoor` 的专用子类。继承原门尺寸、提示和交互方式；`SequenceDirector` 指向本房间导演，交互调用 `TriggerCollapse()`。共享门蓝图不承担本章专用逻辑。 |

主实例的引用对应如下：

| 导演字段 | 当前场景绑定 |
| --- | --- |
| `CameraRig` / `TimeController` | `Ch1_R2_CameraRig` / `Ch1_R2_TimeStop` |
| `FallFirst` / `FallSecond` / `FallThird` / `FallOverhead` | `Ch1_R2_FallDriver_20` / `_15` / `_21` / `_33` |
| `BlastCover` | `Ch1_R2_FallDriver_BlastCabinet`，其 `TargetActor` 为 `Ch1_R2_BlastCabinet` |
| `LockedDoor` / `ExitDoor` | `LabR17_Door_R9-WEST-SHARED` / `LabR17_Door_R10-UP-NORTH` |
| `DoorFocus` / `BlastFocus` / `OverheadFocus` / `ExplosionOrigin` | 对应的 `Ch1_R2_…` TargetPoint；负责镜头关注点和爆炸位置 |

`Ch1_R2_Ceiling_WillFall_15` 是本轮新增到演出中的板。第三块与头顶板是不同引用，不能合并成同一个驱动器。

镜头模块另有两个可选绑定：`SourceCamera` 为原玩家的活动 CameraComponent，`FOVTimeline` 为原本写入 FOV 的 TimelineComponent。本房间导演在初始化时绑定玩家实例的 `FirstPersonCamera` 和 `TM_FOV`。未指定 SourceCamera 时，模块从玩家 Pawn 查询 CameraComponent，并验证它活动、归该 Pawn 所有，且当前 ViewTarget 正是该 Pawn；多个相机时应显式绑定，不回退到外部镜头。FOVTimeline 未指定时，只省略该 Timeline 的暂停与恢复。

## 替换白盒模型

1. 退出 PIE，再编辑关卡。优先直接替换当前 `TargetActor` 的 Static Mesh，保留 Actor、驱动器和导演引用；若更换整个 Actor，在对应驱动器的 `TargetActor` 上重新指定。
2. 被驱动对象必须有明确的 **StaticMeshComponent、有效简单碰撞、Movable**。当前驱动器取第一个 StaticMeshComponent；多网格 Actor 应只保留一个明确的物理主体，装饰作为无碰撞附件，避免意外选中其他组件。
3. 开局物理模拟保持关闭，把落板放回实际天花板出发位置。驱动器在 BeginPlay 保存初始姿态；运行中更改 `TargetActor` 不会自动重建这一快照。退出并重新开始 PIE 验证新绑定。
4. 检查简单碰撞轮廓和质量、阻尼、缩放，避免凸包包住空洞或跨过相邻顶板。当前驱动器保留原有碰撞通道及响应，不会统一改为 PhysicsBody。
5. 四块落板目前使用 `Destructible` 对象通道；固定顶板只忽略这一通道，以免碎块凸包在破裂缝隙卡住。地面、墙、紫色管道、橙色结构仍应阻挡这些物体。替换时同时核对双方响应，不要通过关闭环境碰撞解决卡顶。
6. 柜体的通风槽附件保持 `NoCollision`，随柜体移动。若换成完整模型，仍只让主体承担物理碰撞。Geometry Collection、骨骼网格和多刚体破坏不在当前驱动器接口范围内，需要另做适配。
7. 调整相关 Focus、`EntryBounds`、`DangerBounds` 和释放速度，重新验证交互前遮挡、掉落轨迹、时停逃离以及恢复后的通路。模型视觉上相似，不代表碰撞和落点等价。

## 可调参数

在关卡中选择 `Ch1_R2_Sequence` 调整实例属性。时间单位为真实秒，位置和线速度为 UE 的 cm、cm/s，角速度为度/s，FOV 为度。镜头和阶段计时读取 `GetRealTimeSeconds`，物理掉落仍接受游戏时间倍率。

| 参数 | 当前配置 / 作用 |
| --- | --- |
| `EntryLookSeconds` / `EntryHoldSeconds` / `EntryReturnSeconds` | `0.75 / 0.5 / 0.4`；入口转向、停留和恢复 FOV |
| `EntryFOV` / `SequenceFOV` | `60 / 90` |
| `TurnSeconds` / `BlastToFirstSeconds` | `0.85 / 0.25`；回头后爆炸、爆炸后首块释放 |
| `DropStaggerSeconds` | `0.35`；前三块释放间隔 |
| `WatchFallsSeconds` | **地图实例为 `2.0`**；第三块释放后观察时间 |
| `LookUpSeconds` / `OverheadFallSeconds` | `0.65 / 0.8`；抬头时间、头顶板释放至冻结的间隔 |
| `FirstVelocity` / `OverheadVelocity` | `(0,0,0)`，随后由重力下落 |
| `SecondVelocity` | **地图实例为 `(-600,-450,0)`** |
| `ThirdVelocity` | **地图实例为 `(300,-170,0)`** |
| `CoverVelocity` / `CoverAngular` | **地图实例为 `(-900,-30,850)` / `(20,70,30)`** |
| `ExplosionTemplate` / `ExplosionSound` / `ShakeClass` | 绑定项目已有爆炸、声音和镜头震动资产 |
| `ExplosionScale` / `BlastVolume` / `ShakeScale` | `0.4 / 0.45 / 0.35` |

粗体值是已保存的关卡实例覆盖，部分仍与蓝图类默认值不同。复制已调好的导演实例可保留这些值；从资产重新拖入一个导演时需重新填写，不应把生成脚本的旧默认值当成最终地图配置。

两个 Box 是导演组件，`BoxExtent` 为半尺寸；它们不参与物理碰撞，运行时按玩家 Actor 位置做盒内判断。当前导演位置为 `(-5000,-2000,540)`，下表为组件局部坐标：

| 组件 | RelativeLocation | BoxExtent |
| --- | --- | --- |
| `EntryBounds` | `(680,-129,530)` | `(140,145,130)` |
| `DangerBounds` | `(-980,740,310)` | `(420,380,400)` |

入口必须同时满足盒内和 `IsMovingOnGround`。危险区判定使用玩家中心而非完整胶囊，调整时须给头顶板落区留出玩家半径和安全余量；盒子过小会过早恢复物理，过大则使时停延迟恢复。

## 状态所有权与取消边界

当前面向**单机、玩家 0**。同一玩家在同一时刻只允许一个 `BP_CinematicTimeStopController` 会话，不支持重叠或堆栈式时停所有权，也未实现联网同步。

本房间在 `TriggerCollapse()` 开始先调用 `PrepareNormalTime()`，通过原能力逻辑结束预先手动开启的时停，避免真实时钟已推进而前三块板仍几乎不动。该准备步骤不直接修改能量、耗能或教程标志；此后正常能力 Tick 可以自然恢复能量。它是演出前的独立状态切换，不会在演出结束时重新开启玩家此前的手动时停。

到头顶板冻结时，`AcquireStop()` 才缓存当时的能量、耗能、激活状态、模式及相关教程/QTE 标志。原能力 Tick 会根据 Energy 重设模式，因此剧情时停期间暂借隐藏的满能量并将耗能设为零，释放时恢复 **AcquireStop 时的快照**；能力 Tick 保持运行，继续处理玩家和武器的时间补偿。`ReleaseStop()` 调用原 `ApplyTimeState`，保留时间弹丸恢复边沿。本房间因提前准备了正常时间，离开危险区后恢复正常；其他导演若直接使用 Acquire/Release，则仍按自己的会话前状态恢复。

输入锁使用现有 `AC_PlayerControlLocks`，Owner 为本导演，Token 为 `Chapter1Room2Camera`。释放用 `ReleaseOwner(self)`，不会清空其他任务持有的锁。入口和坍塌开始时 `StopMovementImmediately` 清除残余运动；这与输入锁是两个独立动作。

镜头会话全程保留原玩家 ViewTarget，不隐藏玩家网格，也不切到 Rig 自带的 Camera。开始时用 `PlayerController.AddTickPrerequisiteActor(Rig)` 让 Rig 的 PrePhysics Tick 先写 ControlRotation，再由控制器、玩家朝向和第一人称动画更新；结束时移除这条依赖。目标方向从原 CameraComponent 的世界位置计算；插值初值取 ControlRotation 和组件 FOV，不读取已叠加震动的 CameraManager 朝向。现有爆炸镜头震动仍由 CameraManager 添加。

会话缓存最初绑定的 `FOVTimeline`，暂停时保留播放位置和方向。每个拥有权有效的 Tick 都检查这个缓存实例；若游戏重新启动它，则保存最新播放方向并再次暂停，将新请求留待 EndCamera 继续。镜头停留时持续保持 GoalFOV，但不重写 ControlRotation。EndCamera 恢复原 FOV，只恢复此前播放中或会话内新请求播放的 Timeline；没有播放请求的 Timeline 保持停止。输入锁仍归导演管理。

即使 `IsMoving=false`，镜头会话仍逐帧检查控制器、Pawn、原活动相机和 ViewTarget 的拥有权。其他系统接管镜头、换 Pawn 或原引用失效时，模块结束并独立恢复仍存活的原 FOV、Timeline 和 Tick 依赖，不抢回 ViewTarget。EndCamera 保留最终控制器朝向并立即恢复 FOV；入口需平滑缩回时继续由 `ReturnEntry()` 调用 LookAt 完成。`ReturnBlendSeconds` 已废弃，保留字段仅兼容旧导演赋值，不再产生混合，也不受 FullStop 拉长。

`CancelSequence()` 独立尝试结束相机、释放时停和自己的输入锁，复位每个仍有效的绑定物体，恢复初始化时保存的出口锁状态，清除本地一次性标志和阶段。一个失效引用不会截断其他清理。活动阶段发现玩家死亡时取消一次；已完成的 Phase 30 不因后续死亡反复复位。玩家引用失效时清理后丢弃绑定、等待重新初始化。原 `AC_TimeAbility.EndPlay` 自身负责组件销毁后的正常时间恢复。

取消不是整张地图的存档回滚：不恢复玩家位置、生命或任务进度；不重建已经销毁的物体；不关闭已经打开的出口门；已经播放的声音、爆炸粒子和短暂震动没有独立撤销接口。当前实现对共享角色资产按类查询并缓存，未来加入多个同类玩家/替身或复杂重生流程时需调整玩家绑定策略。重复调用、外部输入锁所有者和缺失驱动器的关键取消检查已通过；完整死亡、销毁与重生流程仍未验收。

## 已验证结果与证据边界

证据目录：`Saved/Agent/Chapter1Cinematic20261028/`。下表为镜头修复前的完整流程基线；后续原生镜头修复另列于表后，不能把旧流程结果直接当成新版本的全部回归。未把布局脚本完成或代码存在视为运行验收。

| 检查 | 已记录结果 | 证据 |
| --- | --- | --- |
| 五个功能蓝图编译 | 各 `0 errors / 0 warnings`；最终编译保存状态均为 3（UpToDate） | 五个 `*_apply.json` 与 `final_compile.json` |
| 蓝图呈现整理 | 38 个图、871 个节点完成布局；五个资产均 `semantic_unchanged=true` 并保存 | `presentation_summary.json`、`presentation_report.json` |
| 入口镜头 | 实际玩家落地后进入 Phase 1、2，FOV `90 → 60 → 90`，结束回到玩家视点，移动/视角锁解除 | `entry_samples.json`；测试设置了管道落地点并调用取消以重新开始一次入口触发 |
| 交互输入与预先手动时停 | `FocusedInteractionArea` 正确取得锁门；注入 `IA_Interact` 后从预先手动时停约 `0.01` 进入 Phase 10 正常时间 `1.0`，再到 Phase 20 自动时停约 `0.01`，相机及移动/视角控制交还玩家 | `manual_active_input_collapse.json`，`passed=true`；未直接调用门接口或导演触发函数 |
| 落板与自动冻结 | 四块板和柜体均释放后 Frozen，玩家重新获得控制，原能力 Mode 1、世界倍率约 `0.01` | `collapse_samples.json`；这是物理状态采样，早期触发使用门接口调用 |
| 交互前通路与出口隐藏 | 入口至锁门站立胶囊路线通过；出口从管口与锁门回头位均 `0/9` 门面采样可见 | `qa_current_pie_phase_0.json` |
| Phase 20 通路与出口显露 | 锁门前至出口门前/门槛的连续胶囊扫掠均通过；锁门回头位 `9/9` 门面采样可见 | `qa_current_pie_phase_20.json` |
| 离开危险区恢复 | 实际移动从 Phase 20 到 30，世界倍率恢复 `1.0`，Mode 0、能力未激活、能量 `100` | `escape_diagonal.json` |
| 连续移动、开出口并穿过门槛 | 持续 `AddMovementInput`，路线中无 teleport；从锁门前出发后 2.656 秒由 Phase 20 到 30、时间恢复 `1.0`；注入 `IA_Interact` 打开出口并走至约 `(-4502,-3081,630)`，门 `OpenAlpha=1` | `walk_to_exit.json`，`passed=true` |
| Phase 30 当前玩家位置至出口 | **Baseline 不忽略任何新落板或柜体**，出口门前和门槛路线都通过 | `qa_ignore_falling_phase_30.json` 的 `Baseline` case；其余 Ignore cases 仅为诊断 |
| 取消边界 | 7/7：重复触发不重启、取消保留外部所有者输入锁、仅外部释放解除余锁、正常获取原时停、缺失中间驱动器仍清理时间/输入及后续物体、重复取消安全 | `cancel_edges.json`，`passed=true` |

### 第一人称镜头黑色细面修复

同位置 PIE 已复现回头演出的细长黑色面。`CameraFix/native_view_probe.json` 记录外部 Rig 与原控制器/玩家相机的朝向相差约 135°；只切回原玩家视点并对齐 ControlRotation、没有隐藏任何网格时，异常画面消失。运行实例的 FirstPersonFOV/Scale 与 FirstPersonPrimitiveType 标记均未启用，因此本次已确认的原因是外部视点脱离原第一人称相机与朝向，不能把它归因于项目启用了 UE 的第一人称投影设置。

原生视点初版、加入 `MaintainFOVTimeline` 之前的 `CameraFix/sequence_center.json` 已通过 7/7 检查：完整到达 FullStop、演出活动阶段始终使用玩家 ViewTarget、相机与 ControlRotation 误差小于 1°、控制交还、FOV 恢复且玩家网格未隐藏。`CameraFix/camera_apply.json` 和 `director_apply.json` 编译均为 0 errors / 0 warnings。

随后 `CameraFix/fov_writer_before_fix.json` 发现可重现的停留缺陷：在 60° 停留时重新播放原 TM_FOV，会覆盖演出 FOV，`hold_after_writer_restart=false`。补入 `MaintainFOVTimeline()` 和停留阶段的 GoalFOV 保持后，最新 `CameraFix/fov_writer.json` 已通过 7/7：原 Timeline 正在播放、接管后暂停、60° 初始停留与重启后停留均保持、结束恢复 FOV 和待播放 Timeline、全程原生视点。该测试直接重启原生 Timeline 模拟并发 FOV 请求，不等同于实际按住/松开瞄准键验证。

修复后的 `CameraFix/entry_samples.json` 记录玩家落地进入入口演出，全程 ViewTarget 为 `BP_FPCharacter0`，FOV `90 → 60 → 90`，结束后移动/视角锁均解除。最终实现的 `CameraFix/sequence_visual_center.json` 同样通过上述完整演出的 7/7 检查；此轮为便于观察画面，测试夹具临时将运行实例的 `BlastToFirstSeconds` 延长至 6 秒，不代表保存的正式节奏，也不能用其耗时评估原 `0.25` 秒间隔。

最终 `CameraFix/sequence_near_door_crouch.json` 使用正式 `0.25` 秒间隔，在贴近锁门并下蹲的初始站位通过 Enhanced Input 交互触发，7/7 检查均通过。随后 `CameraFix/walk_to_exit_crouch.json` 从该站位连续输入实际移动，离开危险区后到达 Phase 30、时间恢复 `1.0`，通过 Enhanced Input 开出口并穿过门槛，`passed=true`、`OpenAlpha=1`。初始站位由夹具设置；逃离路线中没有 teleport。这里仍是游戏输入注入，未冒充人工键盘试玩。

修复涉及的镜头和导演两个蓝图已重新整理 29 个图、689 个节点。证据为任务根目录的 `camera_fix_presentation_summary.json` 与 `camera_fix_presentation_report.json`，两资产的独立比较及保存后比较均 `semantic_unchanged=true`。`CameraFix/final_save.json` 记录两资产编译状态 3 且已保存；编辑器内也已目视 `MaintainFOVTimeline` 注释和节点并点击编译成功。`CameraFix/final_audit.json` 确认 124 个受保护对象变换一致、9 项导演绑定有效、待删文字未重新出现、没有未保存地图或资产。保存后编辑器已正常退出并以普通启动参数重开 `Map_LabV39`，未启用 `LabAuthoring`；本次重开后未重复 PIE，不能等同于下面旧版本的完整冷重载 PIE 回归。

本轮未出现蓝图运行时、`Accessed None`、脚本/Python 错误或断言，但不能据此称日志完全无错误。此前日志已存在的 AssetSearch 索引数据库 `database disk image is malformed`、`MK18_Loc/Rot` 资源缺失及 `DefaultSlot` 重复记录仍在，本次镜头修复未处理这些原有问题。收尾时全局无未保存包，临时编辑器桥接已停止。

输入测试通过游戏的 Enhanced Input `IA_Interact` 和实际 CharacterMovement 输入链路，**不是人工按物理键盘**。通路扫掠使用半径 60 cm、半高 88 cm，与上表的连续实际移动测试是不同证据。`qa_current_pie_phase_30.json` 仍从原锁门危险站位起算，记录被已落地的头顶板挡住；恢复时间后玩家已离开该站位，不能把该旧起点检查替代当前玩家位置的 Baseline 验收，也不能隐藏这条记录。一次成功运行不保证所有随机物理落点都能通过。

镜头修复前的冷重载已通过：新编辑器未加载 `LabAuthoring`，地图保留 2904 个 Actor，124 个原 Blockout/Tube 对象变换核对一致，11 个待删文字标记已不存在，全部演出引用有效。重载后的 `cold_input_collapse.json` 和 `cold_walk_to_exit.json` 均通过，再次完成交互、时停和开门离开；`cold_pie_log.json` 无新增错误，仅有原 `ABP_FP_ArmsProcedural` 重复 DefaultSlot 警告。最终退出 PIE 并保存；这条旧冷重载记录不代替镜头修复后的重载验收。

重载前主动退出编辑器时出现一次 `BlueprintEditor.cpp:10423 / PreviewScene.GetWorld()` 断言，已生成崩溃记录；当时所有地图与内容包已保存。重新启动时没有恢复旧蓝图窗口，随后上述冷重载与 PIE 验证通过。这证明保存结果可用，不代表已修复引擎蓝图编辑器的退出崩溃。

尚未据此宣称完成：人工物理键盘试玩、完整死亡重生及所有取消组合、任意初始能量与时间状态组合、打包运行、多人、所有模型替换后的碰撞、最终美术效果以及第一房间自动时停演出。

## 备份与历史预览

- 原始恢复点：`/Game/Maps/Backups/Map_LabV39_PreCinematicRaw20261028`，保留文字清理前的地图。
- 清理后、演出实现前：`/Game/Maps/Backups/Map_LabV39_PreRoom2Cinematic20261028`。
- `clean_backup.json` 记录移除两个房间内的 11 个悬浮标记 Actor；两个备份用于恢复，不应直接覆盖后续手工编辑。
- 镜头修复前的蓝图备份：`/Game/Blueprints/Cinematics/Backups/BP_CinematicCameraRig_PreCameraFix20261028` 和 `/Game/Blueprints/Cinematics/Backups/BP_Chapter1Room2Sequence_PreCameraFix20261028`；由 `CameraFix/prepare.json` 记录，保留原外部镜头版本供回退对照。

原 `LVS_Chapter1Room2` 两态 Variant 是此前静态构图预览，不驱动本演出。不要在运行验收中切换旧 Variant 来替代实际物理掉落或改变导演正在驱动的物体姿态。
