# 按键提示：玩家组件、DataTable 与触发规则

任务：P-106。引擎：UE 5.6.1。本文描述实际蓝图实现；验证结论见文末验收记录。

本轮保持原开放角框样式：四张同尺寸白色透明 PNG、一个 `CornerColor`、原项目字体和原生 TextBlock。按键名称与说明都是 Text，不是图片。玩家只拥有一个提示 Widget；普通条件由玩法事件驱动，只有标记 `ForceDisplay` 的特殊提示允许由教学流程强制提交。

## 1. 资产与职责

| 资产 | 路径／职责 |
|---|---|
| `ENUM_KeyPromptType` | `/Game/UI/KeyPrompt/`；Interaction、Reload、QTETimeStop、Special 四类 |
| `S_KeyPromptRow` | `/Game/UI/KeyPrompt/`；表结构 |
| `DT_KeyPrompts` | `/Game/UI/KeyPrompt/`；显示文字、类型、优先级、强制标记 |
| `AC_KeyPrompt` | `/Game/Blueprints/Components/Player/`；已挂到 `BP_FPCharacter`，持有 DataTable、请求队列、当前来源和 Widget |
| `BPI_KeyPrompt` | `/Game/Blueprints/Interfaces/`；交互对象返回提示数据的蓝图接口 |
| `AC_KeyPromptInfo` | `/Game/Blueprints/Interactables/Interaction/`；实现该接口，让物品直接填写提示配置 |
| `WBP_KeyPromptHUD` | `/Game/UI/KeyPrompt/`；屏幕位置与显示／隐藏 |
| `WBP_KeyPrompt` | `/Game/UI/KeyPrompt/`；四角、按键、说明的视觉显示 |

这些都是普通 UE 蓝图、Widget、枚举、结构体和 DataTable。没有新增 C++ 插件，也不依赖制作脚本在游戏中运行。

## 2. DataTable 格式

| 字段 | 类型 | 用途 |
|---|---|---|
| KeyText | Text | 显示的按键，如 Q、R、F |
| Description | Text | 显示的说明，如 Time Stop、Reload |
| Type | ENUM_KeyPromptType | 四种提示类别；不是判断是否强制的依据 |
| Priority | Integer | 1–5，1 最高；比较时限制在此范围内 |
| ForceDisplay | Boolean | 补充的强制提示标记，默认 false；落石教学为 true |

`ForceDisplay` 将“特殊类型”和“强制显示”明确分开。Special 类型本身不会自动抢占；只有强制标记为 true 才进入强制优先组。

当前默认行如下，设计者可在表内修改文字和优先级：

| Row Name | KeyText | Description | Type | Priority | ForceDisplay |
|---|---|---|---|---:|---|
| Interaction | F | Interact | Interaction | 3 | false |
| Reload | R | Reload | Reload | 4 | false |
| TimeStop | Q | Time Stop | QTETimeStop | 2 | false |
| TutorialFallingRocks | Q | Time Stop | Special | 1 | true |
| TalkToOmen | F | Talk to Omen | Interaction | 3 | false |
| OpenDoor | F | Open the door | Interaction | 3 | false |

表中 `TimeStop` 是普通 QTE 调用方可使用的配置入口；本轮没有将所有旧 QTE 检测与旧提示迁入新系统，不将“存在一行数据”写成完成全部 QTE 接入。

## 3. 优先级与生命周期

1. 先比较 `ForceDisplay`：强制提示优先。
2. 同组比较 `Priority`：数字越小越优先。
3. 强制标记和优先级均相同时，保留当前来源，避免闪换。
4. 当前来源撤回后，自动恢复队列中下一条有效提示；没有请求则 Collapsed。

实现使用 `Map<Object, S_KeyPromptRow>`。Source 是请求所属对象；同一 Source 再次提交会更新原请求，不会重复排队。同一来源需要同时管理多个独立请求时，应分别使用各自的组件／对象作为 Source。

玩家 BeginPlay 创建一次 Widget，添加到屏幕后再隐藏，避免 Construct 的位置刷新把空闲提示重新显示。EndPlay 移除该 Widget。普通射线每次返回后只比较目标变化；目标不变时不重复读取表或提交请求。

公开蓝图函数：

| 函数 | 使用方式 |
|---|---|
| `RequestPrompt(Source, RowName, KeyOverride, DescriptionOverride)` | 查一行表并提交；非空覆盖文字优先于表文字；空覆盖文字使用表值 |
| `SubmitPrompt(Source, Data)` | 已有完整行数据时直接提交 |
| `ClearPrompt(Source)` | 撤回自己的请求，不清除其他来源 |
| `ClearPromptType(PromptType)` | 撤回指定类型；能力成功入口用于清理 QTETimeStop |
| `RefreshFocusedPrompt()` | 已瞄准对象的文字或 Enabled 在运行时变化后，由变化事件调用一次 |
| `UpdateReloadPrompt()` | 当前武器、弹药、装填或存活状态更新后复核换弹条件 |

来源应在失效／取消时主动 ClearPrompt。当前被瞄准对象销毁后，现有射线更新会撤回交互请求。不存在的表行会清除该来源请求，不沿用过期文字。

## 4. 落石教学：唯一特殊强制入口

蓝图链位于 `BP_TrainingController`：

```text
StartFallingRocks 原落石生成完成
  → SetFallingRockPrompt(true)
  → 玩家 AC_KeyPrompt.RequestPrompt
      Source = 当前 TrainingController
      RowName = TutorialFallingRocks

原任务 WaitTimeMode 确认 FullStop 成功
  → HoldIntroTimeStop
  → SetFallingRockPrompt(false)
  → ClearPrompt(同一个 TrainingController)

StopThreats（停止／取消／重置威胁）
  → SetFallingRockPrompt(false)
```

隐藏以成功进入时间停止为依据，不以“按下 Q”代替成功。落石行属于 Special，不误归到普通 QTETimeStop。普通换弹、射线互动没有添加教学阶段编号、教学任务状态或教学关卡名判断。

## 5. 普通换弹

实际条件：当前持有有效物品／武器，`AmmoCount <= 0`，`MaxAmmo > 0`，`Reloading == false`，玩家未死亡。这里沿用工程现有命名：`MaxAmmo` 是该武器的备用弹药数。

通过原有状态变化事件更新：

- `BP_Item_Base.SetAmmo`、`SetWeaponAmmoData` 完成弹药赋值后通知。
- 自动武器与霰弹枪父蓝图：消耗弹药、装填开始／结束、装入弹药后通知。
- 玩家切换 `SpawnedItem`、死亡状态改变后通知。

连续的一批 AmmoCount／MaxAmmo 赋值只在末尾通知一次，已去掉六处重复通知。`SetReloadPrompt` 再比较条件是否改变，未改变时不重复提交或撤回。

开始装填时 `Reloading` 变为 true，立即撤回 Reload 请求，不等待子弹装入。此时若仍有有效互动请求，可以继续显示互动提示。

用户确认以新提示替换旧 RELOAD：`UI_Hud` 中旧 `SetReloadAdvice` 折叠图及调用已移除，旧 RELOAD TextBlock 默认 Collapsed；不再运行原来的每帧换弹建议计算。其余弹药数、武器名、准心及 HUD 功能保留。

## 6. 给一个交互物品配置提示

推荐使用组件，避免每个物品重复编写接口函数：

1. 打开物品／NPC／门的 Actor 蓝图，添加 `AC_KeyPromptInfo`。
2. 在该组件 Details 中填写 `PromptRow`，例如 `TalkToOmen` 或 `OpenDoor`。
3. 可选填写 `KeyText`、`Description` 覆盖文字；留空则使用表内文字。
4. `Enabled` 勾选时返回可用；取消勾选时不提交该对象的提示。这四个变量均开放实例编辑。
5. 对象必须能被项目现有互动射线命中；提示组件不会自动添加碰撞体、扩大射线距离或赋予真实开门／对话能力。
6. 若对象使用 `BP_InteractionArea_Master` 子 Actor，组件放在实际交互父 Actor 上。系统沿用其 `CheckCollisionBoxPermission`／`CanFocus` 限制，并从命中区域解析父 Actor。
7. 用原互动输入与接口处理真正的互动；本组件只提供提示内容。

另一种方式：在 Actor 的 Class Settings 中实现 `BPI_KeyPrompt`，实现 `GetKeyPromptInfo`，返回 `RowName`、`KeyText`、`Description`、`Available`。Actor 自身的接口优先于信息组件；动态开锁条件等可通过 Available 返回。条件在持续瞄准期间改变时，变化事件调用玩家 `RefreshFocusedPrompt()`，无需新增 Tick。

`AC_Interaction.Trace` 复用原 `LineTraceSingle` 的 HitActor。没有新增第二条射线。遮挡物截断原射线后，旧目标提示会撤回；射线重新命中目标时重新提交。

“Talk to Omen”和“Open the door”是已提供的行配置及运行时测试例子，不表示本轮批量修改了全部 NPC／门实例或实现了其对话、开门玩法。

## 7. 修改外观与按键绑定的边界

外观继续在现有 `WBP_KeyPrompt`／`WBP_KeyPromptHUD` 中配置，详见 [开放角框 Widget 使用说明](key-prompt.md)。四角颜色始终统一；字体、字号、间距、缩放和位置保留原参数。

改 KeyText 只改变显示文字，不会重新绑定 Enhanced Input。真实 Q／R／F 仍由原玩法处理。本轮未新增按键重映射、动画、音效、额外定时器或提示轮播。

## 8. 架构参考与版本

参考 Epic 的 [事件驱动 UI 更新](https://dev.epicgames.com/documentation/unreal-engine/driving-ui-updates-with-events-in-unreal-engine?lang=en-US) 和 [Lyra 交互系统](https://dev.epicgames.com/documentation/unreal-engine/lyra-sample-game-interaction-system-in-unreal-engine?lang=en-US) 的数据提供者与交互检测分离思路。这里只采用本项目所需的 Blueprint 接口、玩家组件和现有射线，没有引入 Lyra 的完整 GAS 交互架构。

DataTable 概念参考 [Epic 数据驱动玩法文档](https://dev.epicgames.com/documentation/en-us/unreal-engine/data-driven-gameplay-elements-in-unreal-engine?application_version=5.8)。网页版本不等于本机验证版本；实际资产与 API 以本项目 UE 5.6.1 为准。

## 9. 验收

最终记录及截图归档于 [触发规则验收](KeyPromptRules/validation.md)。打包、联网及全部武器逐项试玩未作为本轮已验证范围。
