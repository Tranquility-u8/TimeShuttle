# TECH-003 GetTheMeaning 启用

日期：2026-10-03（项目时区）。状态：已完成启用与实际编辑器加载验证；导出功能端到端测试未执行。

## 需求与调查

用户要求按 AGENTS.md 的工作方式启动项目中的 GetTheMeaning。沿用先读记录和源码、定向备份、构建、编辑器验证、记录证据的规则。当前 AGENTS.md 要求优先使用蓝图导出文本，但没有 GetTheMeaning 专用启动命令；该插件是本地导出工具，不是 MCP 服务，也不自动向外部 AI 发送内容。

插件版本 2.0，EngineVersion 5.6.0，Editor 模块在 PostEngineInit 加载，依赖 AssetManagerEditor。修复前源码存在、Binaries 目录缺失，项目描述文件将其设为 `Enabled=false`。

## 实施

- 在独立的全英文临时目录，以本机 UE 5.6.1 的 `RunUAT.bat BuildPlugin -HostPlatforms=Win64 -NoTargetPlatforms` 构建；9 个步骤成功，退出码 0。
- 补回 `Plugins/GetTheMeaning/Binaries/Win64/` 下的 DLL、PDB 和 `UnrealEditor.modules`；BuildId 43139311 与引擎一致，复制哈希核对通过。
- 仅将 `TimeShuttle.uproject` 中 GetTheMeaning 的 Enabled 从 false 改为 true。插件源码和描述文件哈希保持不变。
- 清理本次 UAT 自动生成的空白 `Config/FilterPlugin.ini`，备份留在本机证据目录。
- 上一轮编辑器已关闭，本轮直接启动工程，没有强制结束进程或自动保存资产。

## 验证

- UE 窗口标题为 `TimeShuttle - Unreal Editor`，进程有响应，日志记录完成编辑器启动。
- 进程模块列表确认同时加载本项目的 GetTheMeaning 和 BlueprintAssist DLL。
- 编辑器内只读 Python 确认 Window、Content Browser 和 Reference Viewer 相关 ToolMenu 对象存在；其中 Sections 属性受保护，未读取具体条目，不把这项检查称作可见菜单或点击导出验收。
- 只读检查未保存内容包和地图包均为空。没有修改、编译或保存玩法蓝图；未运行 PIE，未测试批量导出及文本完整性。
- 本机证据：`Saved/Agent/GetTheMeaningEnable/` 中的 build.log、startup.log、before-state.json、installed-files.json、menu-verification.json、process-verification.json 和项目描述文件备份。

## 使用入口（源码核对）

在内容浏览器选择蓝图、材质、材质实例或材质函数，再使用 Window 菜单或资产右键菜单中的“导出所有选中为 AI 可读文档”。引用查看器支持选择资产节点后右键导出。结果写入：

- `Saved/GetTheMeaningExports/Blueprints/*_ReadableCode.txt`
- `Saved/GetTheMeaningExports/Materials/*_ReadableMaterial.md`
- `Saved/GetTheMeaningExports/Materials/*_ReadableMaterialFunction.md`

后续调查应按任务选择必要资产，核对文本对应的保存版本和未涵盖的继承/运行时事实，不能用导出文本代替编辑器或 PIE 验证。

二进制受现有 Git 忽略规则排除，其他机器需要独立安装或构建。回退时关闭编辑器，仅把 GetTheMeaning.Enabled 设回 false；不要还原整个项目描述文件来覆盖后续无关修改。
