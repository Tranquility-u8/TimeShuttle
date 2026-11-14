# 第一人称弹丸枪口修复（2026-10-31）

## 原因与最终行为

用户在 FullStop 第一人称画面中看到弹丸悬浮在枪口上方。保存资产和运行数据均确认旧起点为相机瞄准射线的 `TraceStart + Direction × 40`。手枪腰射基线中，该点约在枪口后方 5 cm、上方 8 cm。武器网格 `FirstPersonPrimitiveType=None`，不是独立第一人称投影造成的偏差。

唯一修改的运行时资产为 `/Game/Blueprints/Interactables/BP_Item_Base`。

- 新函数 `PrepareTemporalMuzzleShot` 在共享命中字段写入前运行。Normal / BulletTime 返回原 HitResult，保留原射线伤害；FullStop 读取本次 `RefMesh` 的 `Muzzle` socket，用原相机射线选中的 ImpactPoint（未命中时为 TraceEnd）作为目标，从枪口朝该目标计算方向。
- `TemporalMuzzleOffset` 默认由 40 改为 **4 uu（cm）**，现在表示枪口前方的生成间距。起点、旋转和生成 Transform 在一次开火中缓存一次，Begin/Finish Deferred Spawn 共用该值。未使用枪口自身旋转，也未把其他模式改为实体弹。
- 先检查相机射线起点到枪口，再检查枪口到生成点的 Camera 通道遮挡，忽略玩家和武器。遇到阻挡时用实际遮挡 HitResult 替换共享命中数据，进入已有即时命中/贴花/弱点链，不在墙后生成弹丸。目标距枪口不超过间距时同样沿用近距回退。缺少有效网格/socket 时退回原 TraceStart。
- `SpawnHitscanTrail` 的普通/BulletTime 表现也从武器枪口向原相机命中点会聚，使用相同前移参数；目标位于枪口后方时抑制倒飞的装饰轨迹。该函数仍不查询第二次伤害。
- 时间弹丸的锁定目标/组件、释放速度、扫掠拦截、一次伤害和 12 发上限保持原链路。枪口会随程序动画及后坐力移动，已生成的悬停弹丸保留开火瞬间的世界位置。

## 验证

本地证据和脚本在 Git 忽略的 `Saved/Agent/Muzzle20261031/`。`validation.json` 汇总 **60 项有效检查**，不是把第一次测试的全部结果直接计为通过。

- 重启编辑器后，BP_Item_Base、手枪、步枪、重型手枪、霰弹枪、狙击枪和 BP_TimeBullet 共七个蓝图编译 0 errors / 0 warnings；五类枪械均实际继承 4 cm 默认值。仅重新编译未修改/保存子类。热编辑时已加载的部分子类缓存 40 cm，冷重载排除了该缓存影响。
- 真实玩家/手枪的腰射、原生 IA_Aim 输入瞄准、上仰与下俯：新弹丸均在当前枪口沿自身飞行方向前方 4 cm，生成位置误差小于 0.01 cm，弹道通过缓存的原始命中点，悬停后无位移。
- 相机到枪口遮挡、枪口到生成点遮挡、近相机大墙均阻止穿墙生成；近距阻挡收到原有命中表现，远墙未误收该次命中。
- 带默认 Controller 并停止 AI 的真实 Shooter 作为固定目标：悬停时血量保持 100，释放后 100→75，一次伤害后保持 75，弹丸销毁。接着普通射线立即 75→50，且没有时间弹；Normal 和 BulletTime 的装饰轨迹均从枪口附近开始。
- 等待原生 `IsFire=false` 冷却门后连续提出十三次开火：实体弹保持 12，第十三次不新增。
- 每类独立新 PIE，经原拾取接口和实际 PRIMARY 槽切换装备：步枪产生一枚、霰弹枪产生七枚时间弹，逐枚检查其自身枪口位置和目标会聚。重型手枪/狙击枪仅验证编译与默认值继承，未称完成它们的运行矩阵。
- 整理前后十一张图的逻辑比较通过（忽略仅整理走线的 reroute）；八张无关源图的逻辑与修改前一致。新函数使用 Blueprint Assist 刷新尺寸、首次整理、结构化注释、再次整理；旧图仅局部处理新增节点，并恢复普通轨迹原有节点位置。布局证据为 `muzzle-layout-final.png`、`trail-layout.png`，图表快照另存 JSON。
- 新的隔离 Development 包 Cook/Stage/Archive 成功，未加载临时 BlueprintOps 制作插件。训练关卡首次启动的教程输入锁会拒绝时停，故最终打包检查使用**仅限本次运行**的教程解锁、原能力切换和手枪 BeginFire/StopFire。日志确认实际能力实例 `ModeIndex=1`、实际手枪偏移 `4`、实际弹丸 `bReleased=False`；`packaged-muzzle.png` 是该次 1600×1000 第一人称画面，已目视检查枪口衔接。没有保存教程解锁或改动关卡。

## 夹具边界与保存

- 第一次上限检查按固定过短间隔调用 BeginFire，十三次调用只被原冷却门接受六次；补测等待实际冷却门。第一次跨武器拾取没有真正切换已占用的槽，实际仍是手枪；这些误标案例没有当作步枪/霰弹枪通过，补测使用全新 PIE 和实际槽切换。原始失败保留在 `runtime.json` / 早期错误文件，正确补测在 `runtime-extra.json`。
- 补测准备阶段曾误选没有物品的 SECONDARY 槽，触发原玩家换枪快照的 SpawnedItemRef / AmmoCount / MaxAmmo 空引用；正式补测改选实际有物品的 PRIMARY 槽。05:33:42–05:34:06 UTC 的最终补测区间新增 PIE Error 为 0，证据为 `final-log-check.json`。没有为夹具问题修改玩家资产。
- 早期基线墙先 SetStaticMesh、后处理 Mobility，UE 拒绝该静态夹具换网格；后续正式遮挡测试先设 Movable，再赋模型与 BlockAll。基线相机/枪口/弹丸位置不依赖那面墙。
- 被遮挡的嵌入 PIE 截图有缓存编辑视口画面的情况，不能作为瞄准画面的视觉通过证据。瞄准验收依据实际输入、动画后的 socket 和实体弹丸坐标；第一人称视觉以最终打包截图为证。首次打包尝试未解除教程输入锁，保留为 `packaged-intro-gated.png`，也没有计为时停视觉通过。
- 制作编辑器退出时出现 `BlueprintEditor.cpp` 的 `PreviewScene.GetWorld()` 断言与报告窗口；退出前定向保存已完成，随后的独立冷重载、编译和无制作插件打包运行均通过。未发送崩溃报告。
- 未覆盖所有武器配件/消音器延长口、双持、多人/分屏、完整教程手动试玩。测试使用临时无敌、零时停能量消耗及停止 AI 等运行夹具，不是原始难度的通关验收。
- 定向备份为 `BP_Item_Base.before.uasset`，任务前哈希和图表在 `preflight.json` / `item-before.json`；结束时复核仅该资产和本次说明文档改变，无关地图、玩家、时间能力、弹丸资产均未保存。旧已发布 Build 需重新打包才带入修复。
