# 教程武器台接触面与移动靶渐入修复

日期：2026-10-28。分支：`dev/Dialogue`，起点 `8ffd473a`。任务：`20261028-tutorial-table-reveal`。用户已确认执行；本轮不推送。

## 已验证原因与改动

### 武器台下部闪烁

十段武器台共用 `SM_TS_SupplyTableSegment`。原模型底面与 Z=0 的地板共面；模型内白色柜体与橡胶底座也有共面的外侧面。三角形几何检查发现 16 对有面积的共面重叠，其中 12 对位于侧面。首次仅处理地板交界后，近距离画面仍有横向条纹，因此继续处理底座外沿。

通过编辑器内 StaticMeshDescription 修改底层顶点：底面下沉 0.5 cm，橡胶底座外沿向外错开约 0.25 cm。保留 144 顶点、264 三角形、四个材质槽、原 UV、LOD 和简单碰撞配置；桌面仍为 Z=105 cm，十段 Actor 的变换不变。最终剩余的四对底面重叠全部位于地板下方 Z=-0.5 cm，可见侧面的共面重叠已消除。近距离 PIE 画面不再出现原条纹。

### 手枪与桌面之间的空隙

`EnableSupply` 根据静态展示物生成正式的 `BP_Weapon_Pickup_Pistol`。运行时的 `Weapon` 骨骼模型在物理初始化中脱离根组件；实测移动 Actor 4 cm 时，模型世界高度不变。因此仅调 Actor 高度不能可靠修复。

- 将关卡静态展示物的 Z 从 109 调至约 111.325836，使其静态模型最低点与 Z=105 桌面接触。
- 在教程控制器新增 `SeatSupplyPistol`，于生成完成后、`AddVisual` 缓存渐入边界前，将实际骨骼模型最低点对齐到展示物的接触平面。
- 只移动教程生成实例的模型组件，不修改共用拾取蓝图、武器模型、交互组件或其他武器。

PIE 测得运行时模型与桌面的边界间隙为零，重复校正保持幂等。普通拾取仍可装备手枪；已装备时重试不重复生成。另用销毁瞬态测试拾取物的夹具检查重新生成分支，新的实例仍正确贴合桌面。

### 移动弱点靶渐入后才移动

修复前逐帧记录表明：位置与 `TargetMotionClock` 已等待场景 `Ready`，但 `BS_TrainingStrafe` 在渐入期间以播放倍率 1 运行，导致提前踏步。

- `UpdateSmoothWalker` 在原有条件之外，显式要求所选靶自身 `Visibility >= 1`，再推进路径时钟和行走混合。
- `UpdateRangeTarget` 在移动靶渐入未完成或场景未 Ready 时保持播放倍率 0，并用原生 `bNoSkeletonUpdate` 固定真实骨骼缓存；FullStop 共用该暂停条件，结束后解除。
- `RestoreRangeLocomotion` 立即将移动靶的 BlendSpace 设为中立采样并暂停，避免重试残留步态或第一帧更新前抢跑。渐入和场景准备完成后由正常更新释放。

严格骨骼检查发现，单独将播放倍率设为零不能停止 BlendSpace 姿态变化；`bPauseAnims` 也仍允许首次显现时的一次骨骼刷新。最终使用 `bNoSkeletonUpdate`，在可见渐入期间保持真实姿态，完成后同时释放骨骼、动画时间与路径更新。静止靶、弱点显示/命中规则、路径幅度与速度、受击和死亡逻辑保持原语义。

## 验证与范围

- 主 PIE 夹具 41 项通过，覆盖手枪贴合/幂等/普通拾取、静止靶、普通进入、重试、FullStop、BulletTime、恢复时间、中断渐入以及不重复生成，并逐帧检查脚和手的真实骨骼。
- 保存后的补充夹具 8 项通过，覆盖重新生成拾取物、靶子渐入前后姿态、解除暂停后的真实腿部运动与受击恢复，结果见本机 `extra.json`。额外五骨骼姿态保持检查 2 项通过，渐入期间漂移均为 0，见 `pose-hold.json`。共计 51 项。
- 四个相关蓝图在编辑器中编译零错误、零警告。独立命令行进程不加载 BlueprintOps，加载并编译六个相关蓝图：零错误，14 条已有 Manny PoseAsset 过期警告。
- 仅保存四个资产：武器台静态模型、`BP_TrainingController`、`BP_TrainingTarget`、`Map_TrainingRoom`。目标子类 `BP_TrainingWeakTarget` 与 `AC_TrainingVisual` 文件哈希保持不变。
- 图表差异限于控制器的 `EnableSupply`、`UpdateSmoothWalker`、新增 `SeatSupplyPistol`，以及靶子基类的 `UpdateRangeTarget`、`RestoreRangeLocomotion`。局部布局与五个结构化注释已收尾，布局前后功能签名一致，并目视检查新增门控模块。
- 关卡 Actor 数量不变，仅静态手枪展示物位置改变；其他 Actor 的位置、旋转、缩放逐项保持。保存后编辑器无未保存包。

验证方法是调用现有教程入口的隔离 PIE 场景，不代表连续通关。时间状态夹具将测试实例的能量消耗/恢复暂设为零，防止状态在渐入期间自然切换；原生时间模式、世界倍率和角色更新照常运行。拾取使用正式交互接口；受击恢复使用注入 25 点伤害的夹具。截图短暂停世界以留住姿态，不参与未暂停的时序检查。未验证打包、联网或完整教程通关。

## 证据与恢复

本机忽略目录 `Saved/Agent/TutorialTableReveal/` 包含定向资产备份、原始/最终图表、三角形重叠审计、逐帧运行数据、编译日志和图片：

- `qa.json`、`extra.json`、`cold-compile.json`、`cold.log`
- `table-edit.json`、`plinth-edit.json`、`overlap-before.json`、`overlap-after.json`
- `save.json`、`layout.json`、`comments.json`、`layout-reveal.png`
- `pistol-contact.png`、`table-floor.png`、`walker-revealing.png`、`walker-revealed-moving.png`

早期夹具问题单独保存在 `qa-fixture-*.json`；旧的能量状态自然退出不计为靶子冻结失败。实现返工三次：补齐底座侧面、停止 BlendSpace 姿态变化、消除首次显现的骨骼刷新；均已重新验证。

恢复时使用该目录 `Backup/` 中四个任务资产的定向备份，或任务起点对应版本；先关闭相关编辑器资源并保留此后用户的改动，不重置其他项目内容。
