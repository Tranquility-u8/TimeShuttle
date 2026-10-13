# Training Room 使用与开发说明

适用项目：Time Shuttler / Unreal Engine 5.6。更新日期：2026-10-13。

本目录存放训练室的模型、材质和入口蓝图；实际摆放保存在 **`/Game/Maps/Map_TrainingRoom`**。所有阶段共存在这一张关卡中，按阶段显示和隐藏，不需要分别打开其他地图。

**当前完成的是场景布置和编辑器预览。自动教学推进、融化换场、移动靶、敌人战斗、落石伤害、拾取和弹药刷新尚未在这套布景中接入。** 文中“待接入”内容是后续开发任务，不能视为已经实现。

## 1. 从这里开始

1. 打开 `Map_TrainingRoom`，先停止 Play / PIE。
2. 在 UE 最上方菜单栏，点击 **Help 右侧的 `Training Stages`**。
3. 选择要编辑的阶段，例如 `03 Pickup, reload and basic shooting` 对应 S3。
4. 在 Outliner 展开 `TrainingStages`，编辑对应阶段的物件。
5. 保存关卡，再 Play 检查。保存时选中的布景会成为这张地图的初始显示状态；交付基线为 S1。

切换菜单不会移动玩家初始点，也不会重设编辑器相机位置。更换关卡布景后，应自行到对应区域查看。

### 三种“显隐”不要混淆

| 操作 | 当前效果 |
|---|---|
| `Training Stages` 菜单 | 统一设置阶段 Actor 的编辑器显隐、`Hidden In Game`、Actor 总碰撞开关，以及对应 Layer 的可见性；自动带上共享组 |
| Outliner 文件夹 / Actor 的小眼睛 | 编辑器内的临时显示控制；不会同步游戏内状态和碰撞，而且可能仍受隐藏的 Layer 限制 |
| 游戏中的阶段切换 | 目前未实现；需要后续运行时管理逻辑，不能直接调用这个 Editor Python 菜单来代替 |

**目前完整切换请使用菜单。仅把物件移动到另一个文件夹，或只点小眼睛，不会完成阶段归属和运行状态的切换。** 地图重开后，工具会依据已保存的 `Hidden In Game` 状态恢复编辑器可见性；临时眼睛状态不作为阶段配置保存。

### 菜单不见了怎么办

先确认打开的是本项目、已启用 **Python Editor Script Plugin**，并且项目中的 `Content/Python` 文件已同步。启动入口是 [init_unreal.py](../../Python/init_unreal.py)，菜单定义在 [time_shuttler_training_stages.py](../../Python/time_shuttler_training_stages.py)。

可以在 **Output Log → 命令输入类型选择 Python** 后执行下面一行，重新注册菜单：

```python
import time_shuttler_training_stages as ts; ts.register_menu()
```

如果提示找不到模块，先检查脚本是否存在、Python 插件是否启用；如果提示地图不符或正在 Play，打开 `Map_TrainingRoom` 并停止 Play 后再操作。

## 2. 阶段内容与显示组合

当前基线有 **101 个阶段物件、13 种新增静态模型和7个新增材质**。敌人和靶子目前是静态代理，显示名称不代表它们已经具备对应行为。

| 菜单阶段 | 当前布置 | 实际激活组 | 后续功能接入重点 |
|---|---|---|---|
| S1 | 入口至中央的全宽落石区域、28块悬停落石、触发带及中央完成区地线 | `S1` | 途中触发落石、自动时停、走到中央后完成；地线目前没有触发逻辑 |
| S2 | 前方射手位置，覆盖原2A–2B | `S2` | 玩家主动开启/结束时停，操作提示与完成判定 |
| S2C | 前方射手加侧方射手 | `S2` + `S2C` | 增加侧向威胁和自主判断时机 |
| S3 | 四个静止靶、全宽补给桌、手枪和弹药展示 | `S3` + `SharedShooting` | 拾取、换弹、基础射击及命中反馈 |
| S4 | 三个装甲靶及移动范围轨道 | `S4` + `SharedShooting` | 靶子移动、弱点与伤害判定 |
| S5 | 门架、吊石、独立连接点、三个装甲靶及落点边界 | `S5` + `SharedShooting` | 射断连接点、落石及环境伤害 |
| S6 | 吊石环境题、三个落点靶、两个移动靶及轨道 | `S6` + `SharedShooting` | 组合练习、完成条件、失败重试 |
| S7A | 桌子玩家侧的近战预览位置 | `S7A` + `SharedShooting` | 近战威胁教学，继续保留桌子 |
| S7B | 三低两高错落掩体，一近战三远程敌人代理 | `S7B` | 撤桌后的完整战斗、AI及训练完成判定 |

`S2C` 组本身只存新增的侧方射手，菜单会同时打开 `S2`。不要误以为前方射手遗漏了。

### 共享补给组

Outliner 路径为 **`TrainingStages/00_SHARED_S3_to_S7A`**，包含：

- `Tables`：10段封闭桌，连续接到两侧墙。
- `Ammo_Refresh_Positions`：4个弹药展示/后续刷新位置。
- `Equipment`：静态手枪展示。
- `Collision`：`PawnBarrier_NoCross_NoVault`，防止玩家穿越、跳过或翻越桌线。

这一组从 **S3到S7A** 共用。不要为每阶段再复制一整套桌子。进入 **S7B** 时撤去桌子和屏障，并在后续逻辑中停止弹药刷新、清除未拾取弹药；玩家已经取得的装备和弹药应保留。

现有弹药盒不是补给蓝图，枪也不是可拾取实例。“不断刷新弹药”仍需接入；刷新节奏、数量与容量规则应由后续实现确认，不要把展示数量当成最终玩法参数。

## 3. 文件、关卡和 Outliner 在哪里

以下文件路径均相对项目根目录，即包含 `TimeShuttle.uproject` 的目录。

| 位置 | 用途 |
|---|---|
| `Content/Maps/Map_TrainingRoom.umap` | 实际关卡与所有阶段实例；修改位置、Actor标签和显示初始状态后要保存它 |
| `Content/Environment/TrainingRoom/Meshes`、`Materials` | 原训练室墙壳、灯带和门的资源 |
| `Content/Environment/TrainingRoom/Blueprints` | `BP_TrainingDoor`、`BP_TrainingExit` |
| `Content/Environment/TrainingRoom/Stages/Meshes`、`Materials` | 新增训练道具资源；Content Browser里的目录不控制关卡显隐 |
| `Content/Python/time_shuttler_training_stages.py` | 编辑器阶段预览工具与显示组合规则 |
| `SourceAssets/TrainingStages/TrainingStageProps.blend`、`FBX` | 单件模型源文件和导出文件 |
| `SourceAssets/TrainingStages/TrainingRoom_StageLayouts.blend` | Blender完整布景参照，按 View Layer 选择阶段 |
| `SourceAssets/TrainingStages/layout_manifest.json` | 初始阶段摆放与分组清单 |

Outliner 的主要结构：

```text
TrainingRoom/                         永久房间、门、灯光和系统
  00_SYSTEMS/                        项目已有时间系统管理器
  01_ARCHITECTURE/                    墙壳及入口通道
  05_ENTRANCE_SLIDING_DOOR/            门及其运动父级
TrainingStages/
  00_SHARED_S3_to_S7A/                共用桌、弹药位置、枪与屏障
  S1/
  S2/Front_2A_2B/                    标签组为 S2
  S2/Side_2C/                        标签组为 S2C
  S3/  S4/  S5/  S6/  S7A/
  S7B/Cover_Near_Mid_Far/
  S7B/Enemy_Layout_Proxies/
```

Blender 文件、JSON 清单与 UE **不会自动双向同步**。当前 UE Level 是实际摆放依据。重新执行生成或放置脚本前，先核对组员的手工改动；直接重跑可能覆盖布局或产生重复物件。

## 4. 给某个阶段添加新物件

### 新增一个 S4 物件的例子

1. 先用菜单切到 S4，在 `TrainingStages/S4` 下放置新 Actor。
2. 在 Details 找到 **Actor Tags**，加入以下标签。注意不是组件上的 `Component Tags`。
3. 将它加入 `TS_S4` Layer，与现有组织保持一致；组件碰撞按用途设置。
4. 切到其他阶段再切回 S4，检查新物件的显示和碰撞；编译实际修改的蓝图并保存资源、关卡。

```text
TS_StageLayout
TSStage:S4
TSId:S4_MyNewTarget_01
TSCollision:solid
```

标签规则：

| 标签 | 规则与含义 |
|---|---|
| `TS_StageLayout` | 将Actor纳入当前预览工具。仅放入文件夹、没有这个标签，不会被菜单处理 |
| `TSStage:<组名>` | 必须且只能有一个；允许 `S1`、`S2`、`S2C`、`S3`、`S4`、`S5`、`S6`、`S7A`、`S7B`、`SharedShooting`。缺失会导致切换报错，未知组名不会被任何现有菜单激活 |
| `TSId:<唯一名称>` | 每个实例使用唯一ID；替换原代理时可保留原ID，但不要让新旧Actor同时拥有相同ID。菜单目前不靠ID决定阶段，放置工具和后续查找可能使用它 |
| `TSCollision:none` | 装饰地线等；菜单即使显示该Actor，也不会开启其总碰撞 |
| `TSCollision:solid` | 实体物件；菜单激活时开启Actor总碰撞，但具体组件碰撞仍需配置 |
| `TSCollision:pawn_barrier` | 现有桌线屏障使用；它是用途标记，不会自动配置Pawn-only碰撞 |

每个物件只保留一种 `TSCollision:` 标签。不要复制装饰地线的 `TSCollision:none` 给需要碰撞的目标。永久墙体、灯光、门和时间管理器不要加阶段标签，否则会被阶段切换隐藏或关闭碰撞。

**改阶段归属时，同时改 Actor Tags、Outliner 文件夹与 Layer。** 例如从 S4移到S6，应使用 `TSStage:S6`、对应的唯一ID、`TrainingStages/S6` 文件夹和 `TS_S6` Layer。

### 把静态代理替换成蓝图或 AI

保留所需位置、朝向、阶段归属和唯一ID，核对碰撞后再移除旧代理，避免新旧模型和碰撞重叠。运行时新生成的敌人、弹药或特效也必须由阶段逻辑登记并清理；文件夹和标签不会自动传给生成物。

**隐藏Actor不等于停止逻辑。** 当前菜单只处理显示与Actor碰撞，不会自动停止 AI、Tick、计时器、声音、生成器或组件注册。所有预放Actor在地图加载后都可能执行 `BeginPlay`；不要让非当前阶段的蓝图在 `BeginPlay` 无条件开始攻击、移动或刷弹药。

如果需要增加 S8 等新阶段，仅创建文件夹不够：还需扩展预览脚本的 `STAGES`、必要的共享组合规则，以及未来的运行时阶段管理逻辑。

## 5. 后续运行时阶段切换

以下是建议的接入结构，**目前没有实现这些函数或控制器**。可由团队按现有蓝图架构落地，不要将编辑器Python作为打包游戏的阶段控制器。

每阶段应有明确的进入、完成、退出和重试处理，例如团队自定义的 `EnterStage` / `ExitStage` / `ResetStage`：

1. 退出旧阶段时，停止攻击、计时器和生成器，注销完成事件，并处理该阶段生成的弹丸与临时物件。
2. 按融化效果的时序关闭旧物件碰撞、撤去旧物件；检查新道具是否与玩家当前位置重叠，再显示并启用新阶段。
3. 进入新阶段后才启动目标移动、AI、补给及完成检测，避免事件重复绑定或多次推进。
4. 跨 S3～S7A 时保留共享桌与补给组；到 S7B 才停止补给并撤组。

项目已确认的空间规则：

- 玩家不因切阶段被传送、强制转向或送回固定点。S1是从入口走到场地中央，中央不是每阶段的回位点。
- 场景切换主要表现为道具融化和替换；生成桌、掩体或恢复碰撞前，要处理玩家可能占据的位置。
- 从S3至S7A，玩家不能越过桌线；射击应能越过桌面击中训练目标。弹药补给不应直接替玩家完成换弹练习。
- S7B撤桌后开放战场，保留错落掩体的通路与近中远层次。

## 6. 房间、入口和碰撞维护

现有房间内净约 **20 × 34.7 × 8 m**；UE单位为厘米，范围 `X=-1000～1000`、`Y=-2270～1200`、`Z=0～800`。入口在短边中央 `(0,1200)`，玩家向 `-Y` 方向进场。早期20×24m设计图和旧制作记录不能直接当作当前墙体尺寸。

入口净尺寸保留为 **120 × 220 cm**。`BP_TrainingDoor` 负责接近开门，`BP_TrainingExit` 负责进入 `Map_LabBridge`。门叶挂在 **Door Motion Space** 下，运动使用旧坐标空间中的相对终点；面板和状态灯继续挂在门叶下。**不要单独解除门叶父级或只拖动门叶改入口位置。** 调整入口时，门洞、门框、运动空间和两个触发器需要一起检查。

`TrainingRoom/00_SYSTEMS` 内的 `BP_ReverseSystemManager` 是项目现有时间系统依赖，应跨阶段保留。

桌线屏障只阻挡 **Pawn**，对 **Visibility / Projectile** 忽略。不能把它改成 BlockAll，否则可能挡住射击；也不能只隐藏桌面却保留屏障碰撞。门架碰撞必须保留中间空洞，不能对整个门架套一个大包围盒。动态落石接入物理模拟时，应重新配置并验证适合模拟的简单/凸碰撞，不能直接把当前静态预览碰撞当成完成的物理设置。

## 7. 提交前检查

- 从其他阶段切到本阶段，再切走，确认新增物件能正确出现/消失，没有残留碰撞；S2C和共享桌组合正确。
- 保存并重开地图，确认默认布景和标签仍正确。只做布置时建议交接回S1；如保留其他阶段作为测试入口，在交接中注明。
- PIE中检查实际移动、碰撞、命中与完成事件；非激活阶段不得继续攻击或生成物件。测试失败重试和反复进入，避免重复计时器、事件或残留AI。
- 修改桌线后重新检查两侧绕行、跳跃/翻越和子弹通行；修改入口后检查开门、通行和实验室出口。
- 提交实际修改的 `.umap`、依赖的 `.uasset`、必要脚本/源文件及说明。地图是二进制文件，多人同时编辑前先协调，避免覆盖彼此的摆放。

交付基线曾验证9种预览组合、保存重开、门与出口、桌线碰撞和实际翻越判定；后续新增功能需要自行回归，不能直接沿用基线结果宣称新功能通过。

## 8. 相关资料

- [阶段交付记录与UE实景截图](../../../Docs/Implementation/training-room-stages.md)
- [Blender与FBX源文件说明](../../../SourceAssets/TrainingStages/README.md)
- [初始摆放清单](../../../SourceAssets/TrainingStages/layout_manifest.json)
- [早期房间制作记录（历史尺寸）](../../../Docs/Implementation/training-room-level.md)

`Saved/Agent/TrainingStages` 是原制作机器上的临时验证和恢复记录，不随Git同步，也不是运行依赖。组员应从关卡、资源、预览脚本和以上已提交的说明开始工作。
