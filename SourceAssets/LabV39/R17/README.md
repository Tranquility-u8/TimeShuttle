# Time Shuttler · LabV39 R17 建筑源

**2026-10-24 起，本目录的全场高度切片仅作历史恢复源。** 当前 Map_LabV39 已使用 [Editable 独立构件](../Editable/README.md)，组员直接在 UE 编辑。不要将本目录旧 SceneBridge manifest 导入当前地图；本机旧同步入口已断开，避免重建高度切片并覆盖手工调整。下文记录原实施与屋顶修复过程。

本目录是2026-10-17最终R17建筑源的维护副本，从 `Saved/Agent/LabR17` 复制；原Saved文件保持不动。当前工作地图为 `/Game/Maps/Map_LabV39`，改造前地图备份为 `/Game/Maps/Map_LabV39_1`。本包不包含完整关卡的楼梯、外立面、城市背景、Omen美术或运行时Blueprint；这些是地图中保留/另行管理的资产，不能把本包当成完整新地图导入。

## 文件

| 内容 | 文件 |
|---|---|
| 最终可编辑Blender建筑源 | [TimeShuttler_LabV39_R17_Patch.blend](TimeShuttler_LabV39_R17_Patch.blend) |
| 当前完整SceneBridge导出包 | [patch_bundle/manifest.json](patch_bundle/manifest.json)，含引用FBX及版本历史 |
| 已审核三维建筑数据 | [architecture_meshes.json](architecture_meshes.json)、[architecture_report.json](architecture_report.json) |
| R17二维布局快照 | [revised-layout-geometry.json](revised-layout-geometry.json) |
| 三维实体生成器 / Blender完整生成器 | [prepare_architecture.py](prepare_architecture.py)、[build_patch_blender.py](build_patch_blender.py) |
| 独立三维审核脚本与记录 | [independent_3d_qa.py](independent_3d_qa.py)、[报告](independent_3d_qa.md)、[数据](independent_3d_qa.json) |
| 二维与脚本静态检查证据 | [二维报告](qa/r17_local_check.md)、[静态检查](build_repeatability_static_check.json) |

没有复制helper编译目录、大日志或临时修复脚本。`cleanup_result.json` 是旧建筑清理证据。复制的QA JSON/Markdown保留原审核记录；其中脚本hash与绝对路径指向当时的Saved源，复制后路径调整不等于重新执行了审核。

## 同步身份和目标

- 导入参数 `target_map` 必须为 `/Game/Maps/Map_LabV39`。
- 导入参数 `asset_root` 使用 `/Game/Environment/LabV39/R17`。SceneBridge实际资产子目录为 `Scene_98b3cb261e7e7b5e`；不要把这一子目录再次当作asset_root造成多层目录。
- 保留Scene ID：`97e4c34e52bd4d88a6fff48f872064a4`。
- 保留Scope ID：`8249249e253c41a4aa0777bc8aa17814`，集合 `LAB_R17_PATCH`。
- 当前manifest revision为3（2026-10-24屋顶修复），734个网格对象；其中32个为合并建筑网格。不要重建随机ID或清空manifest历史后向同一地图重新导入。

最终 `.blend` 保存时 `auto_sync=false`。复制不会改写其内部输出路径，UI中的输出目录可能仍是原 `Saved/Agent/LabR17/patch_bundle`；第一次从维护副本导出时，将输出目录明确设为本目录的 `patch_bundle`，同时保持上述身份与目标。现manifest的 `source_file` 也保留原Saved来源，后续正常导出才更新此元数据。

SceneBridge 配置已核对：`Saved/SceneBridge/config.json` 的 `manifest_path` 指向项目 `SourceAssets/LabV39/R17/patch_bundle/manifest.json`，`asset_root=/Game/Environment/LabV39/R17`，`auto_start=false`。不要导入历史 `1002/LabWhitebox_v39/lab_bundle`，避免已清理的旧墙、门和道具重新生成。 最终 .blend 的 auto_sync=false 仍保持；如需手动同步，使用上述 R17 包与既有地图。

## 可重复生成

复制版三个脚本均读取同目录 `revised-layout-geometry.json`：builder的 `PLAN`、prepare的 `SRC`、独立审核的 `PLAN` 已调整。原Saved脚本未改动。现二维hash保持：`ae19133c9448e61e2afea88d99c67afe8946a9990ec590634bba19bcdf23a2d9`。

1. 若修改二维布局，先在设计流程中更新图纸与布局快照；本目录没有复制R9–R17完整二维图纸生成链，其来源仍在工作区 `tmp/v39-training-direct`。
2. 在有Shapely依赖的普通Python中运行 `prepare_architecture.py`，生成当前建筑体积合并数据。
3. 运行 `independent_3d_qa.py`。建筑几何检查必须通过；若新几何尚未导出，manifest放置边界检查可暂时不一致，完整生成器会把这类导出后检查与几何门槛分开处理。
4. 在Blender中运行本目录 `build_patch_blender.py`。它加载与平面hash一致且已审核的建筑数据，生成源UV，应用POD1家具实施修正，并沿用现有scene/scope/object身份。不需要再运行旧refresh脚本。
5. 导出后重新运行独立审核，确认manifest边界与新几何一致，再将包导入上述既有工作地图。动态门和Omen功能属于其他Blueprint资产，建筑包不能代替其功能验证。

这次维护副本只经过复制、语法检查与文件一致性核对，没有运行Blender、UE或重新导出。生成器的最新整合版本此前通过了静态检查；现有最终 `.blend`/manifest仍是已验证的最终实施版本。

## 外部依赖

脚本仍保留当前工作区依赖路径，搬到其他电脑时需修改这些路径，或把对应依赖加入Python/Blender环境：

- SceneBridge Blender addon：`E:/Capstone/Test/SceneBridge/blender`。
- Shapely等Python依赖：`E:/Capstone/Test/tmp/lab-v13-python`。生成器使用 `constrained_delaunay_triangles` 与 `set_precision`，应使用支持这些函数的同版本环境。
- prepare保留的V39源记录：`E:/Capstone/Test/1002/LabFlow_v39/v39-geometry.json`。
- 独立审核的原始共面比较数据：`E:/Capstone/Test/1002/LabWhitebox_v39/prepared_meshes.json`。
- Blender必须可加载SceneBridge addon；UE导入需项目已安装的SceneBridge插件。这些工具不在本目录内重复打包。

## 实施修正与验收范围

地图已保存并重载；编辑器辅助插件 LabAuthoring 默认关闭且未加载，游戏蓝图无运行时辅助插件依赖。重载后门交互 32/32、Omen 21/21 再次通过；详见[最终保存与重载记录](../../../Saved/Agent/LabR17/final_save_reload_result.json)。总维护入口见 [LabR17](../../../Docs/Design/LabR17/README.md)。

POD1第042件家具相对二维快照南移1.5m，实际bounds为 `[85.1,-13.0,85.8,-10.1]`。builder通过原bounds及楼层校验后才应用这项覆盖。下次将家具位置正式同步到二维图纸时，应同步QA并移除覆盖，避免再移一次。UV投影、A层门楣止于A层、B层E4井洞保留及无重复共面建筑均已落实。

建筑独立QA与UE93项碰撞通过；四座楼梯上下8项、高管道双向蹲行2项、两侧地面起步四级跳台接穿管2条均使用真实项目角色通过。运行记录位于 `Saved/Agent/LabR17` 和工作区 `1002/LabWhitebox_v39/ue-pie-r17-*.json`，未将所有运行日志复制进源目录。Omen追踪已通过功能与左右截图检查；78扇门已放置并编译零错误，[32项真实EnhancedInput交互](../../../Docs/Design/LabR17/runtime-evidence/door_pie_qa.json)与[78扇全开胶囊净空](../../../Docs/Design/LabR17/runtime-evidence/all_door_fit.json)均通过。净空检查临时命令开门，独立于F绑定动作与时间能力的功能输入检查；剧情自动解锁未新增。完整图片和证据见[运行证据索引](../../../Docs/Design/LabR17/runtime-evidence/README.md)，可维护生成源见[门与Omen蓝图维护](runtime_authoring/README.md)。

三维网格hash：`35a35a39cd5bd9e4d6c8ed22a6c453b7eb73c390577cdda3968c24c7c053d37d`。复制时manifest hash：`c3584cab697229d3dc118eb403ff3918beca4ce4b42c3a51fdcd7199a1b9d3db`。

## 2026-10-24 屋顶缺口修复

主屋顶原先按主控室外扩5.3m的矩形整体挖空，造成上层南侧联络廊顶部缺失。生成器改为按主控室真实外包、景观区及其外墙扣除；保留原楼板挑空规则。只更新 `SM_LabR17_Structure_25/26`，其他732个导出对象及所有变换不变。新屋顶实体增加231.868㎡，B层原198.9188685㎡高位漏顶归零。

当前三维网格SHA256：`9452d6555ac88edc2561023ced5ccd0f1dfce5e042bb3f22b11f3bc4c13ef50b`；当前manifest SHA256：`838839f6933857093515391d20d999a7e8969b03caf4f8ee42dfd4bea29b881b`。上文旧hash为初次R17交付历史记录。维护源 `.blend`、FBX、manifest及生成器已同步。详见[屋顶修复与恢复方法](../../../Docs/Design/LabR17/roof-repair-2026-10-24.md)。
