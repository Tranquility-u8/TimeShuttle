# 玩家红色暗角：平滑过渡与统一调用

2026-11-06，沿用懒人模式。受伤暗角改为渐入、渐出；任何调用方都通过同一个 Blueprint Interface 请求，不再直接写相机材质权重。

## 调用方式

接口资产：`/Game/Blueprints/Interfaces/BPI_PlayerDamageFeedback`。

获取玩家角色作为 Target，发送 **SetDamageVignette (Message)**：

| 参数 | 含义 |
| --- | --- |
| `Visible = true` | 渐入至完整受伤暗角 |
| `Visible = false` | 渐出至完全隐藏 |
| `Immediate = false` | 常规调用，使用玩家配置的平滑时长 |
| `Immediate = true` | 调用方明确要求即时重置时使用 |
| 输出 `Handled` | 玩家接受请求时为 true |

例如，显示用 `(Visible=true, Immediate=false)`，隐藏用 `(false, false)`。调用方无需转换成玩家具体类，也不需要持有 FirstPersonCamera 或材质引用。

`BP_FPCharacter` 默认配置：`DamageVignetteFadeInSeconds = 0.25`，`DamageVignetteFadeOutSeconds = 0.45`。两项可编辑；时长不大于零时安全地直接落到目标值。

## 行为与接入

- 过渡使用现实时间与 EaseInOut 曲线。FullStop 中视觉仍可平滑播放，既有 5 秒生命恢复计时继续遵守时停暂停规则。
- 反向请求从当前显示强度重新开始，不跳到旧端点。重复相同目标不会重置过渡计时。
- 玩家现有 Tick 调用 `UpdateDamageVignette`；只有过渡进行时才插值并写材质，结束后保留准确的 0 / 1 权重。
- `ApplyDamageVignetteWeight` 是唯一的暗角材质权重写入入口，只更新既有 `M_PlayerDamageVignette`，不替换相机其他 blendable。
- 原受伤、自然回血、致死清理、复活，以及 `BP_TrainingController.PrepareRetry` 均调用统一接口。生命恢复的扣血规则和计时不变。
- 原受伤分支的固定 0.06 全屏红色 Camera Fade 已移除，避免暗角渐入时仍出现另一个突变色罩。死亡淡出/复活淡入继续由原 Camera Fade 链负责，教程重试保留原相机淡出清理。

修改三个资产：接口、玩家、教程 Controller；没有修改材质、地图、输入或武器。此前自然恢复任务的未提交改动完整保留。定向恢复副本、图表导出、脚本与观测位于本机忽略目录 `Saved/Agent/DamageVignetteFade/`。

## 验证

Map_Test 的 27 项 PIE 检查覆盖接口存在与返回值、受伤渐入、中间权重与实际材质同步、精确终点、渐出、反向连续性、同目标幂等、即时重置、零时长、5 秒回血与随后渐出、FullStop 中视觉过渡和回血暂停、死亡/复活，以及其他 blendable 保留。伤害通过正式 ApplyDamage 注入；部分边界夹具只在 PIE 实例设置生命/伤害接收/能量消耗，不作为手动战斗验收。

新增节点经过尺寸刷新、首次整理、职责注释框和再次局部整理。整理前后功能连接、默认值一致；玩家 26 张原有无关图表、教程 Controller 87 张无关图表完全一致，修改图中保留下来的原节点位置也保持。

玩家视口的实际显示/隐藏画面已核对，见本机 `vignette-visible.png` / `vignette-hidden.png`；`apply-layout.png`、`interface-layout.png` 留存布局证据。早期 HighResShot 截图捕获了编辑器视角并干扰短时采样，未用作最终画面或时长验收证据。后续将数值测试与视口截图分开。

接口、玩家及教程 Controller 最终编译均为零错误、零警告，定向保存后无脏内容或地图。保存版本另在不加载 BlueprintOps 的编辑器中通过 18 项复测，最终区间没有 Blueprint Runtime Error、Accessed None 或 Python/Script 错误。后台节流最初使短过渡采样跳过中间帧，关闭节流后复测通过，验证结束后恢复该编辑器设置。完整结果留于 `cold-runtime.json` / `final.json`。未进行打包、多人或完整教程通关验收。
