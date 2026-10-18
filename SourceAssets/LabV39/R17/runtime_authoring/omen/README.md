# Omen 平滑注视玩家 — Lab R17

本目录是项目内维护源，安装脚本读取本目录的 spec，执行报告输出至 `Saved/Agent/LabR17/omen`。已完成结果见[正式运行证据](../../../../../Docs/Design/LabR17/runtime-evidence/README.md)，重建调用方式见[总说明](../README.md)。

已在 `Map_LabV39` 实现并通过实际 PIE 验证。玩家进入 Omen 房间后，原有 Omen 整体平滑朝向玩家；离开后平滑回到开场姿态。该功能不新增输入或剧情逻辑。

## 场景与蓝图

- 蓝图：`/Game/Characters/Omen/Blueprints/BP_OmenObserver`。
- 场景控制器：`LabV39_OmenObserver`；Outliner 文件夹：`Characters/Omen/OmenV4`。
- `OmenRoot` 引用原有 `LabV39_Omen_ShellUpper`。其余五件模型保持原有附着关系，不复制模型、不重新挂接。
- 六件 StaticMeshComponent 改为 **Movable**；网格、材质、碰撞设置和缩放 1.2 均保留，没有开启物理模拟。
- 当前 V39 模型中心为 UE `(0,3700,700) cm`，开场旋转为 pitch 0 / yaw 180 / roll 0。旧 `OmenLabPlacement.md` 中 y2900 属于 `Map_LabBridge`，不用于本地图。
- 运行逻辑全部由原生 Engine 蓝图节点组成。`LabAuthoring` 仅用于编辑器生成蓝图，不是此功能的运行时依赖。

## 组员可调整的内容

选中 `LabV39_OmenObserver`，在 Details 修改设置；`RoomBounds` 是独立于转动模型的范围组件。

| 设置 | 当前值 | 用途 |
| --- | --- | --- |
| OmenRoot | 原 ShellUpper actor | 被整体旋转的父物体 |
| TrackingEnabled | true | 关闭后平滑回到初始姿态 |
| FollowSpeed | 1.8 | 注视玩家的插值速度；越大响应越快 |
| ReturnSpeed | 2.0 | 回到初始姿态的插值速度 |
| ModelForwardOffset | pitch 0 / yaw −90 / roll 0 | 原模型正面是局部 +Y，转换成 LookAt 的 +X 约定 |
| RoomBounds | 中心 `(0,3100,1150)`，半尺寸 `(2000,2100,1150)` cm | 玩家位置进入此范围开始注视 |

范围对应世界坐标 x −2000..2000、y 1000..5200、z 0..2300 cm。判定使用**玩家 Pawn 的中心位置**，朝向目标使用玩家摄像机位置。移动 Omen 或修改房间时，要分别检查模型位置和范围；不要把控制器附着到旋转模型上。

## 行为规则

1. BeginPlay 只缓存一次 Omen 的原始旋转，作为回位目标。
2. 玩家在范围内且 Pawn、Camera 有效时，计算面向摄像机的目标旋转。
3. 玩家离开范围、TrackingEnabled 关闭或玩家/摄像机暂时无效时，选择缓存的原始旋转。
4. 两条路径共用 RInterpTo，从当前旋转继续平滑变化；回位途中重新入场也不跳变。
5. OmenRoot 无效时不写入旋转。运行中不改动模型位置、尺寸或材质。

使用 Tick DeltaSeconds，没有修改现有时间能力。插值速度 ≤0 会被钳制为 0.01，避免原生 RInterpTo 在速度为 0 时直接跳到目标。`IsTrackingPlayer`、`Initialized`、`RestRotation` 等位于 `Omen|Runtime` 分类，供运行时调试。

**维护注意：**Python 中构造旋转必须写明关键字，例如 `unreal.Rotator(pitch=0, yaw=-90, roll=0)`，不要使用易混淆的三个位置参数。ComposeRotators 保持 A=模型偏移、B=LookAt；本地 UE5.6 源实现为 BQuat × AQuat。

## 本次验证证据

2026-10-17：

- `omen_contract_probe.json`：确认六件原模型及五件子物体附着、材质和碰撞状态。
- `omen_blueprint_apply.json`：编译 **0 错误、0 警告**；EventGraph 55 节点，包含 6 个带说明的逻辑分组。
- `omen_observer_apply_result.json`：原模型位置、旋转、缩放、父子关系、网格、材质、碰撞及无物理模拟状态全部保持。
- `omen_pie_check.json`：278 个实际 PIE 样本，全部自动检查通过。左侧注视末误差 0.064°，右侧 0.109°，回位途中重新进入后 0.205°；最终回原姿态误差 0.00386°。六件位置/缩放保持，子物体旋转同步。
- 已实际查看 [左侧 PIE 截图](../../../../../Docs/Design/LabR17/runtime-evidence/images/Omen_Look_Left.png) 与 [右侧 PIE 截图](../../../../../Docs/Design/LabR17/runtime-evidence/images/Omen_Look_Right.png)：Eye/Pupil 均朝向对应玩家位置，外形正常。

自动测试使用临时传送设置独立测试位置，证明范围状态、轴向、插值和回位，不替代完整行走碰撞或最终保存重载检查。地图保存与其他 R17 功能由主任务统一处理；本目录安装脚本不会保存地图。

## 重建与复测脚本

| 文件 | 作用 |
| --- | --- |
| `probe_omen_contract.py` | 编辑器只读检查当前六件模型 |
| `build_omen_spec.py` | 普通 Python 生成 `BP_OmenObserver.spec.json`，仅检查结构 |
| `apply_omen_observer.py` | 通过 LabAuthoring 生成/更新自有蓝图、编译、设置控制器与 Movable；只保存该 BP |
| `pie_check_omen.py` | PIE 中约 17.4 秒异步采样，完成后恢复玩家位置和开关 |
| `set_pie_omen_view.py` | PIE 可视视角；`OMEN_VIEW='left'/'right'/'restore'` |

所有角色移动测试必须串行执行。编辑器重建前退出 PIE；安装脚本拒绝覆盖无 `AuthoringOwner=LabR17.OmenObserver` 标记的同名资产。复测期间查看 Output Log；修改后需要重新检查蓝图编译、真实画面和预期保存范围。
