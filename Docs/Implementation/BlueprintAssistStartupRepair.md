# TECH-002 BlueprintAssist 启动修复

日期：2026-10-03（项目时区）。状态：已完成，构建与实际编辑器启动验证通过。

## 问题与证据

用户启动工程时出现 `Missing TimeShuttle Modules / BlueprintAssist`。修复前日志记录 `Incompatible or missing module: BlueprintAssist` 后退出。

当前工程关联 UE 5.6，本机实际运行 UE 5.6.1（CL 44394996，BuildId 43139311）。项目插件 BlueprintAssist 4.9.2 的描述文件标注 EngineVersion 5.6.0，源码存在，但 `Plugins/BlueprintAssist/Binaries/Win64/` 为空，缺少 DLL 和模块清单。确认的直接原因是缺失构建产物；无法由现有证据确定是谁或什么操作移除了这些文件。

## 修复范围

使用本机 UE 5.6 的 `RunUAT.bat BuildPlugin`，只构建 Win64 编辑器模块（`-HostPlatforms=Win64 -NoTargetPlatforms`）。参考：[BlueprintAssist 作者 FAQ](https://blueprintassist.github.io/miscellaneous/faq/#building-the-plugin-for-a-custom-unreal-version)。

首次构建受工具运行账户的日志目录权限限制；在正常用户权限下重试后，中文工作路径引发 MSVC D8022，无法打开共享响应文件。改用独立的全英文临时输出目录后，91 个构建步骤完成，返回 `BUILD SUCCESSFUL`、退出码 0。没有修改插件源码来绕过错误。

仅补回以下本地构建产物，复制后 SHA-256 与构建输出一致：

- `Plugins/BlueprintAssist/Binaries/Win64/UnrealEditor-BlueprintAssist.dll`
- `Plugins/BlueprintAssist/Binaries/Win64/UnrealEditor-BlueprintAssist.pdb`
- `Plugins/BlueprintAssist/Binaries/Win64/UnrealEditor.modules`

模块清单 BuildId 与当前引擎均为 43139311。保留原插件描述文件，不修改 EngineAssociation，不禁用 BlueprintAssist。构建工具在源码插件目录自动生成的空白 `Config/FilterPlugin.ini` 已备份并清理。

## 验证与边界

- 实际启动 `TimeShuttle.uproject`，编辑器窗口标题为 `TimeShuttle - Unreal Editor`，进程有响应。
- 启动日志包含 `Registered BlueprintAssist Commands`、`Finished loaded BlueprintAssist Module` 和 `Total Editor Startup Time`，地图 `/Game/Maps/Map_Test` 完成编辑器加载。
- 读取编辑器进程模块列表，确认加载的 DLL 来自本项目插件目录。
- 插件全部 176 个源码文件、插件描述文件及项目描述文件的 SHA-256 与修复前一致。
- 修复前已有的 `GetTheMeaning.Enabled=false` 改动保留；没有修改或保存 `.uasset` / `.umap`。
- 此次验收针对启动和插件初始化，未运行 PIE，也未重排蓝图来测试所有插件功能。启动中仍有纹理虚拟化等警告，不在本次修复范围内。

## 本机证据与后续复用

证据位于忽略跟踪目录 `Saved/Agent/BlueprintAssistRepair/`：`startup-before.log`、`build-console.log`、`build-ascii-console.log`、`startup-after.log`、`before-state.json`、`installed-files.json`、`process-verification.json` 及描述文件备份。编辑器保持打开供用户继续使用。

现有 Git 规则忽略插件二进制，因此这些 DLL 不会自动随源码克隆到其他机器。其他电脑首次使用或本机清理构建目录后，应安装对应引擎版本的插件构建，或按上述方法在全英文临时目录重新构建，再核对 BuildId；不要以改写 BuildId 假装兼容。原始二进制目录为空，回退本次补文件会恢复启动故障；如需回退，应先关闭编辑器并只撤除上述三个本次生成文件。
