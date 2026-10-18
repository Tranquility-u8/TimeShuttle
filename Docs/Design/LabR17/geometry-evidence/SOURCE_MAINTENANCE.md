# R17 建筑源维护要点

详细步骤以 [SourceAssets/LabV39/R17/README.md](../../../../SourceAssets/LabV39/R17/README.md) 为准。该目录保留最终 Blender 源、FBX 导出包与脚本；这里仅提供几何证据，不重复复制源资产。

当前 Saved/SceneBridge/config.json 已指向项目 SourceAssets/LabV39/R17/patch_bundle/manifest.json，asset_root=/Game/Environment/LabV39/R17，auto_start=false。该配置已读取核对；继续禁止重新导入历史 V39 包。

1. 编辑前确认目标地图 /Game/Maps/Map_LabV39；备份地图为 /Game/Maps/Map_LabV39_1。
2. Blender 源保存为 auto_sync=false。复制到新位置不会自动修改其内部输出目录，首次导出时应明确指向当前 SourceAssets/LabV39/R17/patch_bundle。
3. SceneBridge 导入参数 asset_root 为 /Game/Environment/LabV39/R17，不要把其下自动生成的 Scene_98b3cb261e7e7b5e 再当作根目录。
4. 保留 Scene ID 97e4c34e52bd4d88a6fff48f872064a4、Scope ID 8249249e253c41a4aa0777bc8aa17814 和集合 LAB_R17_PATCH。不要清空 manifest 历史或随机重建旧对象身份。
5. 二维布局更新后先生成 architecture_meshes.json 并进行独立审核，再运行 Blender 完整生成器；该生成器已整合源 UV、POD1 家具南移和最新三维建筑数据加载。导出后再核对 manifest 几何边界。
6. POD1 第 042 件家具当前是实施覆盖。若将新位置回写平面 JSON，需同步移除或更新覆盖校验，避免二次位移。
7. 不得重新导入历史 1002/LabWhitebox_v39/lab_bundle。其内容包含已经被移除的旧墙和物体。门与 Omen Blueprint 不由建筑补丁生成，维护入口见 [runtime_authoring](../../../../SourceAssets/LabV39/R17/runtime_authoring/README.md)。

外部依赖仍包括 SceneBridge/blender、tmp/lab-v13-python 的 Shapely、1002/LabFlow_v39/v39-geometry.json，以及独立共面比较所用 1002/LabWhitebox_v39/prepared_meshes.json。换电脑需要调整相应路径或安装同版本依赖；不能把源文件夹描述为完全自包含。

复制的 QA 是已完成检查的原始证据，内含当时 Saved 源文件绝对路径和脚本 hash。维护副本的 PLAN 路径已改为本目录文件；静态检查通过不等于搬迁后已重新运行 Blender 或 UE。
