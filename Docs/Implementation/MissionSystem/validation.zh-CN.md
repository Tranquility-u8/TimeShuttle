# 任务流程蓝图重构验收记录

关联 LEVEL-002、P-008、P-058、P-106。2026-10-18 完成实现与本轮验收，未提交或推送 Git。

## 已实现

- 通用 BP_MissionFlow、AC_MissionTask 和可派生任务组件。支持成功/失败链接、后台任务和显式等待、目标信号、超时、检查点重试与整体重置。
- 对话等待匹配的真实完成事件；被拒绝、取消或抢占会失败。控制锁按所有者及名称隔离。Cutscene 支持 Level Sequence、角色标签替换、暂停、正常完成和中止清理。
- BP_TrainingMission 以86个组件配置8个玩法检查点。关卡蓝图移除31个阶段函数；原训练控制器的机关/敌人/能量教学操作保留，三个嵌入式对话调用拆出。重试不再把对话取消冒报为 Completed。
- 原 Game Instance 及对话记忆解耦保持，记忆和持久化关闭。新增任务无需向执行器添加类型 Switch。

## 实测证据

| 检查 | 结果 |
| --- | --- |
| 通用任务首次验证 | 29/29 |
| 信号、并发锁、角色绑定、暂停和死亡清理 | 15/15 |
| 训练8阶段连续流程、对话失败重试及整体重置 | 20/20 |
| 训练失败路由和死亡后检查点恢复 | 6/6 |
| 普通冷启动通用任务复测 | 29/29 |
| 普通冷启动边界复测 | 15/15 |
| 训练冷启动、实际触发开场对话及退出清理 | 5/5 |

普通启动未加载 TSVFXEditor 或 TSDialogEditor。73个相关蓝图冷加载编译通过，日志中未出现蓝图编译错误/警告、Accessed None、Blueprint Runtime Error 或 Ensure。原有资源/渲染警告不据此宣布全部消除。

训练验证使用真实对话、Q输入、落石、QTE与弹道运动；后半段使用明确记录的拾取/换弹观测值、KillTarget、吊板命中回调及 ApplyDamage 夹具。死亡专项注入死亡/复活状态验证生命周期，不代替死亡动画验收。这不是全程人工瞄准射击通关；未测试网络、分屏或完整Cook打包。

## 保存和范围

110张本次实现图表已整理并添加注释；大型图补做尺寸缓存与整理，关键截图已目视复核。170张图表在消除 reroute、引脚顺序以及UE序列化的布尔/数值表示差异后，连接和默认值语义一致。原训练控制器84张图中仅4张属于本次改动，其余80张保持。原地图189个Actor的类、变换和标签未变，只增加流程Actor。4份既有存档与本轮备份逐字节一致。最终PIE停止，内容和地图无未保存项。

制作过程中的失败记录保留于 Saved/Agent/DialogueBlueprint/MissionFlow：修正了原始字节枚举常量、MovieScene回调内清理及自然结束先触发OnStop的处理；整理工具的Slate回调重入经保护修复。临时工具编译生成的本机 .target 记录已备份移出，普通启动使用引擎原有记录；首次冷启动失败不计入通过证据。没有新增运行时C++插件或修改正式项目插件配置。

## 配置入口和交付

打开 Content/Environment/TrainingRoom/Mission/BP_TrainingMission，在 Components 中选择任务，在 Details 配置参数及 NextStep/FailureStep。组件列表位置不代表执行顺序。

使用说明另附Word版本，4页，经Word原生渲染逐页检查。项目内另有 Docs/Implementation/MissionSystem/authoring-guide.zh-CN.md。可复测脚本在 Scripts/Validation/MissionSystem，调用方法见 Docs/Implementation/mission-system.md。完整过程、资产备份及图表导出保留在忽略目录 Saved/Agent/DialogueBlueprint/MissionFlow。
