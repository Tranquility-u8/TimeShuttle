# P-106 按键提示规则验收

日期：2026-10-28；UE 5.6.1。指定实现与验证已完成，最终美术接受度仍由用户试玩确认。未提交或推送 Git，未修改正式排期。

## 已交付

新增六个资产：`AC_KeyPrompt`、`AC_KeyPromptInfo`、`BPI_KeyPrompt`、`ENUM_KeyPromptType`、`S_KeyPromptRow`、`DT_KeyPrompts`。玩家持有管理组件和表引用；一个 Widget 显示获胜请求。四种类型、优先级 1–5、ForceDisplay、同级保留当前来源均已实现。

修改八个既有资产：玩家、互动组件、时间能力组件、物品父类、自动武器父类、霰弹枪父类、教学控制器及原 HUD。原四角 PNG、唯一颜色参数、字体与 Widget 外观资产未改；地图、工程插件配置和输入配置未改。

落石以 Special + ForceDisplay 请求显示 Q / Time Stop，真实时间停止成功后撤回。普通换弹以空弹匣且有备用弹药触发，开始装填立即撤回；互动优先于换弹。经用户确认，旧 HUD 的 RELOAD 显示判断已移除。

## 证据与范围

| 验证 | 结果 | 证据 |
|---|---|---|
| 实际落石教学与跨帧 Q 输入 | 12/12 | [rocks-validation.json](rocks-validation.json) |
| 普通规则、真实 R／开火、既有射线、遮挡／目标销毁、旧文字替换 | 27/27 | [general-validation.json](general-validation.json) |
| 当前物品文字刷新、同级保留、Enabled 切换、缺失表行 | 9/9 | [refresh-stability-validation.json](refresh-stability-validation.json) |
| 最终相关蓝图编译 | 11 个，0 错误／0 警告 | [final-static.json](final-static.json) |
| 首次整理语义核验 | 166 张图一致；29 张目标图整理 | [format-validation.json](format-validation.json) |
| 最后刷新函数修复后的整理 | 管理组件 12 张图语义一致，修复图重新整理 | [refresh-format-validation.json](refresh-format-validation.json) |
| 最终普通编辑器冷加载、表数据、接口、Tick 与测试资产清理 | 19/19，无制作辅助模块 | [cold-static.json](cold-static.json) |
| 普通编辑器实际落石流程与 Enhanced Input 动作注入 | 10/10 | [cold-rocks-validation.json](cold-rocks-validation.json) |
| 最终修复版普通编辑器原生手枪、弹药事件、装填输入及队列 | 12/12 | [cold-final-runtime.json](cold-final-runtime.json) |
| 收尾状态 | PIE 停止、原 MainMenu 地图与相机恢复、无脏内容／地图、五个原存档哈希不变 | [handoff-state.json](handoff-state.json) |

“166 张图一致”包括被修改资产的未改动图。三处未连接的 Key 输出默认值在引擎刷新中由空字符串规范为 None，已逐项记录；没有忽略输入默认值或功能连线差异。最终同级刷新修复之后，另对管理组件重新比较与验证。

落石测试使用原教学任务流；测试脚本只定位玩家进入原触发区，之后通过实际 Q 输入或引擎 Enhanced Input 动作进入 FullStop。普通规则测试先停止教学流程，证明换弹与互动不依赖教学阶段。手枪由原拾取对象的原生接口装备；交互测试用临时碰撞方块和信息组件走现有射线，不能表述为已经给所有 NPC／门实例接入。测试专用蓝图已删除，没有写入地图或交付目录。

冷落石测试发生在最后一处 RefreshFocusedPrompt 文本刷新修复之前；该修复未改落石或能力路径。修复后有 9 项定向回归、最终 19 项冷加载和 12 项冷运行检查，不将旧结果冒充重跑全部场景。

## 实机截图

以下均来自 UE 教学场景运行画面，不是合成图：

- [落石下坠：Q / Time Stop](falling-prompt.png)
- [成功时间停止：提示隐藏](time-stopped-hidden.png)
- [空弹匣且有备用弹药：R / Reload](reload-visible.png)
- [装填开始：提示隐藏](reload-start-hidden.png)
- [交互接口：F / Talk to Omen](interaction-talk.png)
- [物品文字覆盖：F / Open the door](interaction-door.png)

已经目视核对文字、统一青色边角、准心下方位置、右侧说明和旧 RELOAD 不再重复显示。蓝图的 SetReloadPrompt 与最终 RefreshFocusedPrompt 也已在编辑器中展开检查；界面证据保留在本次对话工具记录，未冒充另存的图片文件。

## 过程问题与日志

- 初版在 AddToPlayerScreen 之前隐藏，随后被 Construct 恢复可见；已将隐藏移到添加之后，重测通过。
- 信息组件初版只有同名函数而未正确实现 BPI；已移除冲突函数并按引擎接口机制重建，DoesImplementInterface 和真实射线测试通过。
- 组件配置变量已开放实例编辑；测试脚本对实例连续使用编辑器属性修改时会重建组件，后改为运行时赋值以准确测试蓝图行为。
- 发现同级刷新先撤回再提交可能换源；改为有效请求原位更新、不可用时才撤回，9 项专项检查通过。
- 临时碰撞夹具的早期制作曾触发 StaticMesh 直接属性赋值的 handled ensure；随后改进夹具且最终删除该资产。这不是正式运行组件的网格操作。
- 22:49 左右第一次退出制作编辑器出现 `PreviewScene.GetWorld()` 断言（BlueprintEditor.cpp:10423）。资产已保存且无脏内容；之后普通编辑器冷加载、运行和再次正常退出通过。最终编辑器保持打开，没有把这次退出异常隐瞒成全程无错误。
- 制作期间，霰弹枪编辑器缩略图／预览世界记录 PlayerRef 为空警告；新增通知函数已有有效性检查。该日志来自 `/Engine/Transient` 预览世界，未据此宣称全工程日志零警告。既有 MK18 曲线引用、动画重复槽位和虚拟阴影页池告警也未扩展修改。
- 最终普通编辑器验证日志未检出 Error、Blueprint Runtime Error 或 Accessed None。早期脚本 API／引脚适配错误和桥接文件读写竞争已与最终运行结果区分。

原始脚本、逐轮导出、日志和备份保留在工程本机 `Saved/Agent/KeyPromptRules/`（Git 忽略）。本目录只归档最终选定结果。

## 尚未声称完成的范围

没有新增或改写所有物品的真实交互行为；开发者需给目标 Actor 配置组件／接口。普通 QTETimeStop 提供表行及通用入口，旧 QTE 检测提示没有全面迁移。没有认证打包、联网、分屏、全部武器逐项试玩或按键重映射。

使用说明：[按键提示规则与接入](../key-prompt-rules.md)。
