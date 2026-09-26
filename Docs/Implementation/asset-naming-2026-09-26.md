# 命名统一与知识库刷新记录

日期：2026-09-26。恢复点：`38f0fa1`。本轮通过 Unreal 原生资产重命名接口实施，没有直接编辑二进制资产，也没有创建提交。

## 改动

- 统一 54 个常用逻辑/数据资产：近战 AI、战斗接口/组件、敌人回溯组件、StateTree 任务、相机震动、结构体、数据资产及拼写。
- 全部旧/新路径见 [逐文件清单](../Knowledge/asset-renames-2026-09-26.csv)。通过类型信息区分 PrimaryDataAsset 蓝图类与实例，消除误用的 `DT_` 前缀；结构体使用 `S_`，StateTree 保留 `ST_`。
- 原生改名流程保存 102 个资产/引用者，随后定向重存 16 个 Map_Test World Partition 外部 Actor 包，消除旧引用。两种敌人的场景位置、旋转和缩放保持不变。
- 更新配置中的兼容转向并补充新路径映射，继续支持旧存档；不能因编辑器引用清零便删除这些兼容项。
- 命名约定、遗留例外、目录职责、实际游戏入口和回溯边界集中在知识库。三个项目 skills 负责路由，协作授权以 AGENTS.md 为准，修正了旧 SOP 中重复审批的冲突。
- 本轮只刷新本地实现事实；没有刷新 Drive 设计快照或篡改其来源观察时间。

## 验证

- 新的 UE 进程加载全部 54 个新路径并编译其中的蓝图，零错误；Asset Registry 中这些旧路径的硬/软包引用者均为空，项目内 ObjectRedirector 数量为零。
- 旧 `Saved` 槽成功加载；Map_Test 保持 `GM_FP`，两种敌人加载正确的回溯组件。原玩家存档在 PIE 结束后按字节恢复。
- PIE 回溯测试共 446 次观测：Q 对应的 Enhanced Input 动作被注入；两种敌人均经历 100 → 75、致命伤害和回溯恢复至 100，三类历史数组长度始终一致。回溯时使用姿态播放 AnimBP，结束后恢复正常 AnimBP；远程恢复射击，近战恢复接近玩家和攻击表现。
- 玩家输入回归：移动位置发生变化；换弹后弹匣从 0 到 12，开火减少至 4，再次换弹恢复到 12。测试通过真实输入动作驱动，没有直接设置弹药值。
- 本轮交互编辑器日志没有 Blueprint runtime error / Accessed None；冷加载保留既有警告。未验证打包、网络或完整玩家伤害系统。
- 姿态即时采样与组件当前快照有部分非零差异，前次任务基线也存在相同现象；本轮不能据此声称骨骼逐帧零误差。历史长度、播放类切换、姿态变化和复活行为已核对。
- 工作开始前已有的三个 Control Rig 文件 SHA-256 未改变。任务改动和已有用户改动均保留在工作区，未自动提交。

本地详细证据位于忽略跟踪的 `Saved/Agent/Naming/`：`result.json`、`external_saved.json`、`validation.json/log`、`pie_test.json`、`pie_summary.json`、`input_test.json`。临时脚本和机器路径不进入项目知识层。

工作流校验和 `git diff --check` 通过。规范入口为 [asset-naming.md](../Knowledge/asset-naming.md)，架构入口为 [project-architecture.md](../Knowledge/project-architecture.md)。
