# 2026-10-24 外围围护与退让东翼屋顶修复

这是 Map_LabV39 的**增量修复源与执行记录**。基础 Editable 的 821 个模块及其 import_plan 仍保存初次迁移状态；不要重放基础迁移，也不要用旧 SceneBridge 包覆盖现在的地图。后续布局以 UE 中的实例和组员手动编辑为准。

## 本次改动

- 北西侧增加 4 个可独立移动、旋转、缩放的矩形墙段，高度 5.4–14m、厚度 0.6m。保留 UP 北门与城市观景通路，末端接保留的曲玻璃端柱。
- 按原东翼退让设计，去掉退让区域上方多余的 14–14.45m 高屋顶。36 个旧屋顶模块完全移除，13 个局部裁剪后以 15 个新网格替换；58 个原屋顶模块及其余 714 个非屋顶模块不在这份屋顶修改清单内。
- 移除高顶的投影面积为 3520.555412㎡。对应下方的低屋面保留；训练、整备室、双门通道、开放前厅、当前 B 层楼面与墙顶保留。

执行记录位于 `evidence/apply_result.json` 和 `evidence/roof_apply_result.json`。修复前地图备份为 `/Game/Maps/Backups/Map_LabV39_PreEnvelopeFix20261024`。最终 UE 保存与实机验收由主任务记录；本目录的独立网格审核不替代实机验证。

## 文件入口

| 文件 | 用途 |
| --- | --- |
| `envelope_patch.json` | 实际应用的 4 个北西墙段 ID、标签和边界，世界坐标单位为米 |
| `envelope_nw_candidates.json` | 补墙前几何校核及候选说明；其中其他外边界属于当时的调查记录，不是批量补墙指令 |
| `glass_seam_evidence.json` | 北墙与保留玻璃端柱的交接依据 |
| `roof_correction_plan.json` | 屋顶精确删除／裁剪清单、保护范围、原 Actor 预期值及源哈希 |
| `roof_correction_modules.json` | 15 个新屋顶模块的顶点、面、轴点和世界边界 |
| `roof_correction_mesh_audit.json` | 15 个网格闭合性、体积、截面一致性及低屋面覆盖审核 |
| `roof_assets.json`、`roof_meshes/` | 15 个 FBX 的相对路径与 SHA256 |
| `LabRoofEnvelopeCorrection.blend` | **仅含这 15 个修复屋顶网格**的 Blender 文件，不是更新后的完整实验室场景 |
| `evidence/` | 应用记录、原 UE 导出核查和北西侧修复前后图片 |
| `copy_sources.json`、`delivery_manifest.json` | 来源清单、便携化处理与本目录文件哈希 |

坐标约定：Blender 米制，北为 +Y；UE 厘米坐标为 `(100X, -100Y, 100Z)`。北西 4 墙复用现有 Editable 单位方块，不额外导出 4 个重复 FBX。

## 仅重建这 15 个屋顶网格

在这个文件夹中，以后台、空白 Blender 运行：

```text
blender --factory-startup --background --python build_roofs.py
```

脚本读取本目录 `roof_correction_modules.json`，重写本目录的 15 个 FBX、`roof_assets.json` 和修复专用 `.blend`，不会启动 UE、导入资产或同步整张地图。它会清空当前 Blender 会话，因此已限制为后台运行；不要把它当作完整场景同步脚本。

FBX 导出依赖工作区的 `SceneBridge/blender`。保留目前项目目录关系时自动使用相对路径；若插件在别处，可设置 `SCENE_BRIDGE_BLENDER` 指向包含 `scene_bridge` 包的目录。重新导出可能改变 FBX 文件哈希；需要重新核对资产和实例，不能据此覆盖组员后续 UE 编辑。

## 重新计算方案或审核

`plan_roof_correction.py` 是几何方案重算脚本，不是 UE 应用脚本。它读取相邻 `../modules.json`、`../import_plan.json`、`../../R17/`，以及原 R17 生成器引用的工作区 `1002/LabFlow_v39/v39-geometry.json`。这些是初始来源，并不包含后续组员在 UE 的变更。脚本只在内存中读取 R17 体积声明，不执行其导出部分。

`verify_roof_correction.py` 使用本地 `module_mesh_audit_helpers.py` 复核实际网格截面和拓扑。两者需要支持 `constrained_delaunay_triangles` 的 Shapely 2.1+；会优先尝试工作区现有 `tmp/lab-v13-python`，也可使用已安装该依赖的 Python。

本次复制的审核结果：15 个网格均闭合、无反向边或重复面，实际截面差为 0㎡，去掉高顶后缺失低屋面面积为 0㎡。原文件与地图均未由本交付整理步骤修改。
