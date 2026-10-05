# TECH-005：Player Start 被读档覆盖；关闭自动存档与启动读档

日期：2026-10-05。状态：**修改已保存，两个蓝图编译通过；PIE 由用户验证。**

## 原因与授权范围

用户报告 `Map_LabBridge` 中玩家不在 Player Start 出生（提问中写作 Map_LabBrideg）。独立 UE 只读检查确认：

- 地图使用 `GM_FP`，默认角色是 `BP_FPCharacter`，没有预放置 Pawn。
- 唯一 Player Start 为 `Lab_PlayerStart`，位置 `(0, -1040, 280)`。
- 本机 `Saved.sav` 保存的 `PlayerTransform` 位置约为 `(1364.06, 1167.61, 95.26)`。
- 玩家 BeginPlay 启动链执行 `Create HUD → Set Save Slot → Load → Set RespawnFallbackTransform`。`Load` 读到 `SG_Character.PlayerTransform` 后直接执行 `Set Actor Transform`，覆盖初始出生位置；这条链没有核对存档所属地图。

以上是当前保存资产与存档的只读检查，未对用户这次 PIE 过程作逐帧追踪。其逻辑足以解释存档位置覆盖 Player Start 的现象。

用户随后明确选择：**关闭游戏自动存档与启动自动读档**。UE 编辑器定时自动保存不在此次关闭范围内。

## 实际修改

1. `Content/Blueprints/Player/BP_FPCharacter.uasset`：EventGraph 的启动执行线跳过 `Load`，改为 `Set Save Slot → Set RespawnFallbackTransform`。旧 Load 调用保留但与启动执行链断开，添加 `AUTOLOAD DISABLED` 注释。由此不在启动时恢复存档位置、装备和掉落物；设置加载仍走原有独立流程。现有死亡/复活链保留，缓存本次实际出生变换。
2. `Content/Blueprints/SaveSystem/BP_AutoSavePoint.uasset`：断开 `Event ActorBeginOverlap → Save` 的执行线，添加 `AUTOSAVE DISABLED` 注释。已有自动存档点不再触发持久化保存，也不再通过该事件更新复活点缓存。

保留玩家的显式 `Save` / `Load` 实现、鼠标和音量设置保存、已有存档文件；未改关卡、Player Start、GameMode 或编辑器 Auto Save 设置。手动保存/读档仍可影响进度和位置，本次没有重新验证其 UI 全流程。

这是共用玩家类和自动存档点类的修改，适用于使用这些类的所有关卡，不仅是 Map_LabBridge。不会自动修正没有 Player Start、出生碰撞或“从摄像机位置生成”等独立问题。

## 已验证与边界

- 两个蓝图均为 `BS_UpToDate`，编译结果各为 0 错误、0 警告，已定向保存；保存后脏内容包和脏地图均为空。
- 图表比对确认只有上述执行连接变化和意图注释；现有默认属性值不变。重新编译将三个未使用的 Key 输出默认值从空值规范为 `None`，比对单独归一化此项，实际按键事件及执行连接仍严格核对。
- 保留原节点位置。尝试 Blueprint Assist 局部整理时，当前停靠图表的 handler 未就绪，未执行成功；没有因此扩大到全图重排。完整布局目视复核仍交用户完成，不声称格式化成功。
- `Map_LabBridge.umap` 与 `Saved/SaveGames/Saved.sav` 在本次修改前后 SHA-256 一致，保留用户此前的关卡修改。之前合并修复的武器/弹丸改动继续保留。
- **未运行 PIE，未实测最终出生、死亡复活或自动存档点穿越。未提交/推送 Git。**

## 用户验证步骤

1. 打开 `Map_LabBridge`。Play 下拉菜单将 Spawn Player At 设为 **Default Player Start**，不要使用 Current Camera Location 或右键 Play From Here。
2. 点击 Play，预期从 `Lab_PlayerStart` 出生，不再跳到旧存档坐标。移动一段距离后退出 PIE，再次 Play，预期仍从当前关卡 Player Start 开始。旧存档可以保留，无须删除。
3. 在有 `BP_AutoSavePoint` 的测试关卡中穿过触发区域，不主动使用手动保存，预期不显示自动保存反馈，`Saved/SaveGames/Saved.sav` 的修改时间不更新。
4. 在未手动保存/读档的本轮游戏中测试受击死亡，预期回到本次起始位置并恢复控制。穿过已禁用的自动存档点不应改变这一本轮复活位置。
5. 打开两个蓝图检查 `AUTOLOAD DISABLED` / `AUTOSAVE DISABLED` 注释及其附近连线；编译应无错误。PIE 后检查 Output Log，无新的 Blueprint Runtime Error / Accessed None。反馈通过项或错误原文。

验证结果：待用户反馈。

## 本机证据和恢复

本机忽略目录：`Saved/Agent/LabBridgeSpawn/`。

- `inspection.json`：地图、GameMode、Player Start、预放置 Pawn 和存档位置。
- `BP_FPCharacter.before.uasset`、`BP_AutoSavePoint.before.uasset`：本次禁用前的定向备份；玩家备份已经包含此前合并修复。
- `*_before.json`、`*_final.json`、`result.json`、`response_finish03.json`：图表前后状态、编译和保存证据。
- `protected-hashes.json`：关卡与旧存档的修改前哈希。
- `editor.log`：编辑器过程；`layout_error.txt` 是整理工具的失败记录，不是玩法编译错误。

若以后恢复自动功能，可在 UE 中把启动 `Load` 接回原执行链，并把自动存档点的 ActorBeginOverlap 接回 Save，再编译和定向保存。恢复前应先决定跨关卡存档隔离策略，否则旧位置仍可能覆盖其他地图的 Player Start。
