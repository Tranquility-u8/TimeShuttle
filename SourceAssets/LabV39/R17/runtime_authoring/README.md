# R17 门与 Omen 蓝图维护源

此目录保存可重复生成的蓝图规格、编辑器摆放脚本及维护说明。实际游戏资产仍在 `Content`，Python 和 `LabAuthoring` 都只用于编辑器工作。已完成结果和图片见[正式运行证据](../../../../Docs/Design/LabR17/runtime-evidence/README.md)。

- [门使用与参数说明](doors/README.md)：普通门 F 交互、实例锁定、双侧提示、占门保护、Omen 自动门。
- [Omen 使用与参数说明](omen/README.md)：原有六件模型整体平滑注视、离开后回位。
- [门蓝图规格](doors/room_door_spec.json)、[自动门子类规格](doors/omen_door_spec.json)、[78 扇门摆放表](doors/door_placement_plan.json)。
- [Omen 蓝图规格](omen/BP_OmenObserver.spec.json)。

43 扇门初始锁定来自当前阶段计划。门的锁定参数与剧情任务解锁是两层职责；此实现没有新增剧情自动解锁。

## 路径与依赖

需要 Unreal Engine 5.6、项目已有交互蓝图/输入资产、现有 Omen 六件模型，以及已编译并加载的[编辑器专用 LabAuthoring 插件](../../../../Plugins/LabAuthoring/README.md)。插件只包含 Editor 模块；生成资产的运行节点没有依赖该模块，也没有新建运行时 C++ 门或角色类。

归档版 UE 脚本从 `unreal.Paths.project_dir()` 定位本目录，**读本目录的 spec 和门表**；`Saved/Agent/LabR17` 只用来存放本次执行产生的检查报告和截图，不作为默认规格来源。需要其他维护目录时，可以在启动编辑器前设置环境变量 `TS_LAB_R17_AUTHORING_ROOT`，指向包含 `doors/` 和 `omen/` 的维护根目录。

普通 Python 生成器按自身文件位置读取/写入文件。`doors/prepare_door_placement.py` 读取上两级 R17 目录中的 `revised-layout-geometry.json`、`architecture_report.json` 和 `patch_bundle/manifest.json`，不读取工作区 tmp 中可能变化的图纸。门表中的几何路径以项目目录为基准。

## 生成与实施顺序

日常调整已有实例时，直接按各维护说明在 UE 中修改即可。下述脚本用于明确需要重建时，不应在组员已手改蓝图之后无检查覆盖。

在项目目录的普通终端中，以下操作只生成 JSON，不修改 UE 资产：

```powershell
python -B SourceAssets/LabV39/R17/runtime_authoring/doors/build_door_specs.py
python -B SourceAssets/LabV39/R17/runtime_authoring/doors/prepare_door_placement.py
python -B SourceAssets/LabV39/R17/runtime_authoring/omen/build_omen_spec.py
```

门规格包含最新的执行链/数据分区布局与说明注释。`door_graph_layout.py` 只负责节点位置；不能把未经审核的坐标改动混入功能接线或默认值修改。

在 UE 编辑器内，退出 PIE、打开 `Map_LabV39` 并确认本次恢复点后，使用 Python 执行源脚本。例如：

```python
import runpy
from pathlib import Path
import unreal
source = Path(unreal.Paths.project_dir()) / 'SourceAssets/LabV39/R17/runtime_authoring'
runpy.run_path(str(source / 'doors/apply_doors.py'), run_name='__main__')
```

1. 门先运行 `doors/inspect_contract_after_helper.py` 核对父类；再执行 `doors/apply_doors.py`。默认拒绝覆盖已有目标，需要明确重建时在脚本中设置 `ALLOW_EXISTING=True`。
2. 检查两份蓝图编译报告后，执行 `doors/spawn_doors.py`。摆放脚本会核对刚生成报告中的 spec 哈希，拒绝使用与当前维护源不一致的旧 Saved 报告；只替换本任务标签对应的门实例。
3. Omen 执行 `omen/probe_omen_contract.py`，核对原六件模型后执行 `omen/apply_omen_observer.py`。只允许重建带自有元数据的目标蓝图，保留原模型和附着关系。
4. 上述脚本选择性保存目标蓝图，**不自动保存地图**。检查实例、编译和实际画面后，再定向保存当前地图。

## 验证与范围

PIE 中串行执行 `doors/qa_doors_pie.py`、`doors/qa_all_door_fit.py`、`omen/pie_check_omen.py`；等待每项报告完成后才运行下一项。不能同时运行会移动玩家、注入输入或控制相机的脚本。

门功能测试使用实际 EnhancedInput Action，覆盖 F 交互与时停状态；全门净空检查会临时命令门打开，仅证明几何通行，不冒充输入测试。Omen 测试用临时玩家位置检查注视与回位，不替代完整导航。捕图脚本位于各功能目录，捕图期间不保存 PIE 状态。

本维护副本已完成 16 个 Python 文件的语法检查；两套生成器重新输出的 spec 与已审核源完全一致，摆放表重新生成仍为 78 扇门/43 扇初始锁定。这里的路径适配没有重新执行 UE 实施。已完成的实际编译、功能与图片结果保留在正式运行证据目录；最终蓝图展示修订和地图保存由总任务记录补充。
