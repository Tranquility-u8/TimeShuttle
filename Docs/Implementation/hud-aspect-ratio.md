# HUD 宽高比裁切修复（2026-10-31）

## 问题与范围

用户报告打包版在 16:10 下，右下角弹药数字的右半部分越过屏幕边缘；原 PIE 窗口未复现。当前资产确认 `/Game/UI/Widgets/UI_Hud` 的弹药列、武器名称列和存档提示均使用中心锚点与按 1920×1080 设计的固定偏移。项目使用 ShortestSide DPI 缩放；相同比例缩放下，16:10 的有效设计宽度比 16:9 小，因此中心偏移不再保持右侧边距。

只修改该 Widget Blueprint 的三处 CanvasPanelSlot。未修改游戏图表、DPI 配置、关卡、武器数值或其他 UI。

## 最终布局

Alignment、Size、AutoSize 和控件层级保持原值。以 1920×1080 为参照转换锚点，保留原有 16:9 位置。

| 控件 | 原锚点 | 原位置 X/Y | 新锚点 | 新位置 X/Y |
| --- | --- | --- | --- | --- |
| VerticalBox_1（AmmoCount / MaxAmmo） | 0.5 / 0.5 | 839.039062 / 419.459473 | 1 / 1 | −120.960938 / −120.540527 |
| VerticalBox_313（WeaponName / IsAuto） | 0.5 / 0.5 | 675.039062 / 427.459473 | 1 / 1 | −284.960938 / −112.540527 |
| SaveHint | 0.5 / 0.5 | 818 / −460 | 1 / 0 | −142 / 80 |

存档提示是检查时确认的另一处同类缺陷。在 1728×1080 设计空间中，原弹药容器右侧约超出 16 单位，存档提示约超出 54 单位；新布局分别保留约 80 / 42 单位的右边距。

## 验证与边界

- UE 5.6.1 编辑器重新加载、编译并定向保存 UI_Hud，结束时无 dirty content / map packages。修改仅涉及 Designer 布局，无新增或修改逻辑图表，因此无图表重排范围。236 个实际源图表对象的导出属性一致；编译清理的八个临时对象没有 NodeGuid、连接或源图表 Nodes 引用。
- 独立 PIE 预览曾以实测 1280×803 显示手枪 12 / 120、时间能量面板及临时可见的存档提示，均在屏幕内。手枪由测试拾取物的现有交互接口取得；存档提示仅在测试实例上显示，没有执行真实存档。
- 后续自动 PIE 多比例夹具使用的 EditorRequestBeginPlay 实际固定启动嵌入视口，三个案例均为 1922×975。该批结果已标记 INVALID，**不作为多比例通过证据**。Python 返回的 Slate 缓存几何为零，也未作为边界通过证据。
- 新建隔离 Development 测试包，Cook / Stage / Archive 成功。首次使用旧二进制的 staging 因旧 receipt 引用已移除的 TimeShuttleDialog 插件而失败；重新 build 更新生成记录后通过，未恢复该插件或改动运行时代码。
- 打包版通过引擎原生延迟命令，在实际游戏中依次截图 **1600×1000、1600×900、1680×720**。逐张目视确认 12 / 120 弹药数字、武器名称及左侧时间面板完整显示。测试使用 Summon + 原有拾取接口和 SetTutorialEnergyVisibility 夹具；没有代替完整教程、瞄准射击或所有菜单功能验收。
- 只读导出检查了 16 个相关 Widget：HUD、任务追踪及行、字幕、按键提示、回溯 HUD、交互、暂停/设置/控制、武器改装及新旧主菜单。任务追踪和回溯计时器已有正确边缘锚点，字幕和按键提示以中心布局，当前菜单和改装面板在 16:10 的固定布局内。未确认另一处相同的 16:10 内容越界；装饰背景超出 Canvas 不等同于交互内容被裁切。未宣称逐项运行了所有菜单、任意长文本、4:3、分屏或移动端。
- 20 项归一化设计边界检查通过，属于布局计算，独立于打包截图。
- 测试以 `-NoSound` 运行，BP_FPCharacter 的 SpawnSoundAtLocation 空返回值触发音效访问警告；不是 UI_Hud 编译错误，亦不能据此断言普通带音频运行也会报错。无 UI_Hud 运行错误被观测到。

## 本地证据与恢复

脚本、导出、日志、截图和测试包均在 Git 忽略的 `Saved/Agent/HUDAspect20261030/`。

- `apply.json`、`final-editor.json`：锚点修改、编译保存和未保存资产检查。
- `audit-summary.json`、`graph-compare.json`：源图表及静态布局检查。
- `PIE_*.png` / `pie-matrix.json`：后续无效比例夹具，已明确标记，不作为多比例验收。
- `package-retry-console.log`：最终 BUILD SUCCESSFUL。
- `packaged-matrix-final.log`、`Packaged_16x10.png`、`Packaged_16x9.png`、`Packaged_21x9.png`：打包运行和截图。
- `Packaged/Windows/TimeShuttle.exe`：本地隔离测试包；原有外部 Build 目录未覆盖。
- `UI_Hud.before.uasset`：任务前定向备份；也可在 UE Designer 按上表原值回退三处 Slot，再编译保存。

后续重新打包会带入修复；此前已分发的旧包不会随源资产自动更新。
