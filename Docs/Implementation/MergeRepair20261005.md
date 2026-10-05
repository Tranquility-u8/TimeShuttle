# TECH-004：合并后蓝图损坏修复记录

日期：2026-10-05。环境：Unreal Engine 5.6.1，分支 `dev/core-mechanics`，调查起点 `c11f8d7`。

**当前状态：修复已保存，相关蓝图编译通过；修复后的冷启动、PIE 和完整布局目视验收待用户操作。** 用户已明确接手后续验证。本记录不将历史玩法测试结果视为本次合并后的验证结果。

## 1. 现象与根因

用户合并后，Message Log 显示 7 个蓝图编译失败：`BP_AutoSavePoint`、`BP_InteractionArea_Master`、`AC_TimeAbility`、`BP_Interaction_Base`、`AC_ProceduralAnimation`、`BP_Item_Pickup`、`UI_Hud`，同时存在加载错误。

定位到 3 个损坏的 `.uasset`。文件仅约 263–265 字节，内容实际是带 `<<<<<<< HEAD`、`=======`、`>>>>>>> TA/TimeEffects` 的 Git LFS 指针冲突文本，不是有效 UE 资产包。这些冲突文本还被作为新的 LFS 对象提交，因此只重新拉取当前版本不能恢复资产。

损坏产生于合并 `TA/TimeEffects` 的提交 `3fdf267`；随后合并 `Levels` 的 `c11f8d7` 继承了损坏内容。玩家与武器基础资产无法加载，使依赖它们的多个蓝图连锁报错。此次根因与此前 BlueprintAssist 缺失 DLL 的启动故障不同。

## 2. 修改范围与恢复方式

先保留损坏原文、原日志和有效源版本备份，再从本地 Git LFS 对象恢复核心玩法分支 `f1fb985` 的有效资产。通过 UE 编辑器内的 Unreal-aware 工具合回 `79c2d1f` 的相关特效接入，没有直接修改二进制字节。

| 修改的资产（相对工程根目录） | 保留的核心玩法 | 合回的特效接入 |
|---|---|---|
| `Content/Blueprints/Player/BP_FPCharacter.uasset` | 两次受击死亡、无敌间隔、存档点复活、近战及现有图表 | `TimeStopVFX` ChildActorComponent，使用既有 `BP_TimeStopVFXController` |
| `Content/Blueprints/Interactables/BP_Item_Base.uasset` | 现有射击与弱点伤害解析、FullStop 实体弹分支 | `bNormalTrailEnabled`、`SpawnHitscanTrail`；在普通射线分支插入一次纯视觉拖尾调用 |
| `Content/Blueprints/Weapons/Player/Projectiles/BP_TimeBullet.uasset` | 开火时锁定命中目标与弱点、遮挡处理、释放与命中逻辑 | 挂在 `Collision` 下的 `BulletTrail` 组件 |

普通拖尾继续复用既有 `BP_HitscanTrail` / `AC_BulletTrail`。本次未新建玩法资产，未修改关卡、项目插件配置或其他玩法资产，也未提交或推送 Git。

## 3. 已取得的验证证据

- 恢复有效核心资产后启动编辑器，原先由这 3 个损坏包引起的加载/编译错误消失。此项发生在特效合回前，不等同于最终保存版本的冷启动验收。
- 特效合回后，截图中的 7 个蓝图全部达到 `BS_UpToDate`。同时检查了上述 3 个修复资产及 `GM_FP`、`BP_TimeStopVFXController`、`BP_HitscanTrail`、`AC_BulletTrail`、`BP_Weapon_Pistol`、`BP_Weapon_ThrowableBase`、`BP_Weapon_Grenade`，合计 17 个蓝图编译通过。
- 图表语义比对：扣除明确新增的拖尾函数和调用后，原有图表连接未发现差异；已有默认值未发现变化。玩家 GetClassDefaults 自动增加的、未连接的拖尾开关输出不视为玩法修改。此检查不能替代 PIE。
- 使用 Blueprint Assist 整理新建函数及旧图表内新增的调用节点，并添加注释。格式化前后语义一致；原 `Fire_HitScan` 节点位置未改变。局部整理检查记录为 0 编译错误、0 编译警告。
- 三个修复资产已定向保存，Git 范围核查确认只有这三个 `.uasset` 发生变化。文档在本次交接另行添加。
- 编辑器画面可见编译通过状态及旧图表局部；完整新增函数/调用区域的目视复核尚未完成。自动截图文件实际拍到关卡视口，不能用作蓝图布局验收证据。

最终编译后无脏地图；另有编辑器引擎资源 `/InterchangeAssets/gltf/M_Default` 变脏，未保存该资源。不要为本次修复对它执行 Save All。界面中原有“无需重复 Cast 到 AC_EnemyWeakPoints”的提示不是本次缺失类错误。

本次尚未完成：最终版本不加载临时编辑工具的冷启动、PIE 射击/时停/伤害/复活回归、用户外观评审、打包和多人验证。

## 4. 用户操作验证清单

按顺序执行下面 6 步。每步通过后勾选；遇到编译错误或 Blueprint Runtime Error 时记录完整文本、资产名和触发动作，再停止后续相关测试。验证时不需要修改或保存正式关卡。

1. **重新打开工程。** 先处理你自己新产生的未保存内容，再正常退出 UE；本次修复的三个资产已经保存。若仅提示上述 `M_Default`，不保存它。直接双击 `TimeShuttle.uproject` 启动，不沿用修复期间加载临时工具的命令行。打开 `/Game/Maps/Map_Test`，确认没有 Missing Modules、损坏包或缺失父类弹窗；检查本轮启动的 Output Log / Message Log，不用旧日志条目判断本轮失败。结果：☐ 通过 ☐ 失败。
2. **检查蓝图与布局。** 打开上述三个修复蓝图，分别 Compile，预期无红色编译错误。检查 `BP_Item_Base → SpawnHitscanTrail` 的节点与注释框是否可读、是否重叠；在 `Fire_HitScan` 中定位该函数调用，确认执行线连接完整。查看最初报错的 7 个蓝图，确认没有新的编译失败。只保存本次明确修改的资产，不使用全局 Save All。结果：☐ 通过 ☐ 失败。
3. **普通射击与交互。** 在 Map_Test 点击 Play，确认玩家、HUD、移动、瞄准正常；拾取手枪并完成武器切换。向敌人和墙壁各开单发，预期普通子弹有短暂拖尾，敌人正常受击，拖尾随后消失；观察不能因视觉拖尾再产生一次伤害。退出 PIE 后检查有无新的 Accessed None 或 Blueprint Runtime Error。结果：☐ 通过 ☐ 失败。
4. **时停、子弹时间与拖尾。** 重新 Play，能量充足时按 T 进入 FullStop，开几枪，预期弹丸悬停且尚未造成命中伤害，数量 UI 正常。再按 T 退出，或等待能量下降进入 BulletTime，预期弹丸释放并正常命中、拖尾清理；在 BulletTime 下再开枪确认拖尾表现。检查启停特效、HUD 能量与时间恢复，重复启停后不残留冻结。结果：☐ 通过 ☐ 失败。
5. **核心玩法未被合并覆盖。** 确保 F6 无敌已关闭，让敌人击中一次，预期出现受伤反馈；间隔超过 0.9 秒再次受击，预期死亡并在最近存档点恢复控制，生命与时间状态恢复。再检查拳头/刀近战能够正常命中与造成伤害。测试可能更新游戏存档；若不希望改变当前进度，先自行备份 `Saved/SaveGames`。结果：☐ 通过 ☐ 失败。
6. **结束并记录。** 退出 PIE，检查本轮 Output Log / Message Log，确认没有新的加载错误、编译失败或运行时蓝图错误。记录测试关卡、通过项、失败动作；若失败，提供完整错误文本和对应截图。另可打开本次 Levels 合并涉及的关卡做加载检查；这不代表所有关卡玩法已验收。结果：☐ 通过 ☐ 失败。

用户验证结果：**待反馈**。收到反馈后更新本记录和 TECH-004 状态，不提前标记修复完全验收。

## 5. 本机证据与恢复边界

以下文件位于工程的 `Saved/Agent/MergeRepair20261005/`，属于本机忽略目录，不会随普通 Git 提交同步：

| 文件 | 用途 |
|---|---|
| `before.log`、`repair-editor.log` | 修复前日志和本次编辑器日志 |
| `*.uasset.conflict.txt` | 三个损坏文件的原始冲突文本，仅用于调查 |
| `*.uasset.core-backup` | 从 `f1fb985` 恢复的有效核心版本备份，尚未合回特效 |
| `semantic-audit.json`、`audit_merge.py` | 图表与默认值差异检查及检查口径 |
| `layout_result.json` | Blueprint Assist 整理、编译与局部位置检查 |
| `compile-save.json`、`response_compile01.json` | 17 个蓝图的最终编译状态与保存后脏包清单 |
| `*_final.json` | 三个修复资产的最终导出 |
| `Saved.sav.before-tests` | 开始测试准备时复制的存档；本次尚未执行 PIE 回归 |

不要用 `git restore` 直接恢复到当前损坏的 HEAD，也不要把冲突文本备份覆盖回 `.uasset`。若需要回退修复，先关闭编辑器并备份当前成果，再按明确目标选用有效历史 LFS 资产；核心版本备份会缺少此次合回的特效接入。

后续处理 `.uasset` / `.umap` 冲突时，应选择有效资产版本作为基底，在 UE 内合并另一侧功能；不能把 LFS 指针当普通文本拼接。提交前检查暂存范围，确保不存在冲突标记或异常小的资产文件。
