# LabV39 独立建筑构件初始源

日期：2026-10-24。本目录为将 R17 的 32 个全场高度切片拆成独立建筑构件所用的初始源，目标地图 `/Game/Maps/Map_LabV39`。已完成导入、保存重载与实际角色通行；[验收及限制](../../../Docs/Design/LabR17/editable-architecture.md)记录本轮结果。

日常 UE 操作见[独立构件编辑指南](../../../Docs/Design/LabR17/editable-architecture.md)。新资产目录为 `/Game/Environment/LabV39/Editable/Meshes`；Outliner 按 `LabEditable/楼层/房间或Shared_…/kind` 组织，包含 A、B 及特殊 CONTROL、SCENIC 分组。

**后续修复：** [EnvelopeRepair20261024](EnvelopeRepair20261024/README.md)记录北西 4 段外墙补齐及退役东翼高顶裁剪。当前地图为 791 个建筑构件；本目录的 821 模块 JSON、Blender 全场文件仍是初始迁移快照，不能重放覆盖当前地图。

## 数据内容

| 文件 | 用途 |
| --- | --- |
| [LabV39_EditableArchitecture.blend](LabV39_EditableArchitecture.blend) | 本次迁移起始的 Blender 构件与实例排布。 |
| [modules.json](modules.json) | 821 个模块的局部 / 世界坐标、枢轴、轮廓、关联房间、洞口与类型。 |
| [import_plan.json](import_plan.json) | 初始 UE 放置清单：821 实例、279 网格、位置、朝向、Scale 与文件夹。 |
| [geometry-report.json](geometry-report.json) | 生成器的分区、体积与闭合检查；不是 UE 测试。 |
| [independent-audit.json](independent-audit.json) | 独立的几何 / 语义数据审核；不是 UE 测试。 |
| [generate_modules.py](generate_modules.py) | 从修复屋顶后的 R17 结构体产生独立构件。 |
| [build_assets.py](build_assets.py) | 生成本目录 Blender 文件、FBX 和初始导入清单，不同步 UE。 |
| [meshes](meshes/) | 279 份 FBX。 |

构件包括 328 普通矩形 `wall`、44 `special_wall`、12 `scenic_wall`、188 楼板、107 屋顶、78 门楣、22 窗楣、22 窗台和 20 件其他结构。普通矩形墙可以用实例 Scale 改尺寸；特殊墙、景观墙以及不规则楼板/屋顶的局部改形应通过专用网格和 Modeling 完成。

279 份新网格中，`SM_LabEditable_WallUnit` 与 `SM_LabEditable_SlabUnit` 为两个共享基础盒，供 544 个矩形实例使用；其余 277 份为专用构件。不要编辑共享基础盒的顶点或全局材质来改某一面墙。

原 32 份 R17 资产不改写，新实例替换原结构实例。原门 Blueprint、Omen、楼梯、框条、玻璃、家具和其他非结构 Actor 不属于本目录的替换清单。本轮恢复地图是 `/Game/Maps/Backups/Map_LabV39_PreEditable20261024`；原 Map_LabV39 已保存重载，821 新构件及 1924 原 Actor 的变换保持已确认。

## 维护边界

迁移验收后，以 UE 中保存的实例为当前布局权威。本目录是初始迁移源，不是持续同步源。后续移动墙段、改门洞或房间不会自动反向写回 Blender / JSON；重新运行生成器也不会读取那些手工修改。

不要对当前地图重放初始 `import_plan.json`，也不要再导入旧 R17 SceneBridge 结构 manifest 或历史 V39 包，否则可能恢复旧布局、覆盖手工调整或产生重复结构。本机旧 SceneBridge `manifest_path` 已清空，监听停止，自动启动关闭。

如果需要从源重新生成，先明确哪些 UE 修改要保留并另存初始源，生成到隔离位置后对比；不要直接当作日常更新命令。`build_assets.py` 会重建当前 Blender 场景并写出源文件，应在隔离的后台 / factory-startup Blender 进程运行。

`generate_modules.py` 相对定位同级 R17 源，需要支持 `constrained_delaunay_triangles` 的 Shapely；优先使用已安装依赖，本机可回退到工作区 `tmp/lab-v13-python`。`build_assets.py` 复用工作区 SceneBridge 的 FBX 写出函数，这不启用 SceneBridge 同步。以上脚本不是完全自包含工具。通过 Unreal 编辑器导入或修改资产，不直接操作 `.uasset` / `.umap` 二进制。
