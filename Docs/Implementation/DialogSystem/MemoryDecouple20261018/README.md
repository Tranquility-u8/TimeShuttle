# 对话记忆接口解耦（2026-10-18）

P-008 / P-058 / GPD-026。保留 BP_TimeShuttleGameInstance 和项目配置，新增普通蓝图接口 BPI_DialogueMemory。对话管理组件与函数库不再 Cast 到具体 GI，也不再直接引用该资产。

BFL_Dialogue.ResolveDialogueMemory 获取通用 GameInstance 并检查接口；HasRememberedDialogue/RememberDialogue、SavePlayerMemory/LoadPlayerMemory 先检查服务存在和启用状态。没有接口或关闭时，查询为 false、写入/存读为 false，不妨碍播放。InitializeDialogue 仅在原有组件显式开启时调用 EnableDialogueMemory；资产和玩家组件默认仍关闭。LocalCompleted 继续负责玩家组件生命周期内的一次性记录。LoadPlayerMemory 保留既有取消对话、清除本地记录行为。

GI 的六个接口适配函数调用已有记忆实现，旧公开函数与 SG_DialogueMemory 格式保留。蓝图接口只规定调用契约，不持有状态。

验证：基础 59/59、跨关卡/训练接入 15/15、默认原生 GI 无记忆服务 21/21、接口开关 11/11 全通过；4 个修改/新增蓝图编译零错误零警告；无制作辅助工具的独立进程冷加载编译 12 个运行蓝图。保存后 Asset Registry 确认对话资产对具体项目 GI 的直接引用为零。43 张未涉及图表逐项相同；15 张修改/新增实现图表整理并注释。持久化最终关闭，正式配置未改为原生 GI，PIE 已停止，无未保存内容或地图。

默认 GI 对照只临时修改编辑器内存配置，并在 PIE 实例创建后立即恢复正式设置，未写配置文件。测试通过现有测试表、真实音频和 Enhanced Input/蓝图入口执行；跨关卡测试真实 OpenLevel，训练调用既有 BeginStage1EnergyIntro，不等于完整 S1–S7 通关。测试期间仅在 PIE 对象显式启用记忆，QA 槽独立，结束清空并关闭。

默认 GI 测试曾有三次夹具问题：编辑器属性设置导致实例重建/引用状态不一致；多句纯文字只执行一次 Next 的结束预期不正确；重试未复位上次手动模式。三份失败报告保留于 Saved 目录，与修正后通过报告分开；未为此修改产品蓝图。首次依赖审计在异步整理保存结束前读取旧注册表，完成保存后及独立冷加载再核对。Word 打包渲染器缺 LibreOffice，改用 Word 原生导出九页并逐页目视检查。

修改资产：BPI_DialogueMemory、BFL_Dialogue、AC_DialogueManager、BP_TimeShuttleGameInstance。备份与脚本、日志、截图在 Saved/Agent/DialogueBlueprint/MemoryDecouple。未改玩家/关卡资产、对白内容、播放规则或存档格式。未提交/推送 Git，未做完整 Cook/打包。
