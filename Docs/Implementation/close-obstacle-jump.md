# 贴边跳跃输入修复

2026-10-24，UE 5.6.1；在 `/Game/Maps/Map_Test` 复现和验证。

## 原因与修改

`BP_FPCharacter.EventGraph` 的 IA_Jump 先调用 `AC_Vault.CanVault`。检测通过后，原分支将 `Reloading OR IsSprint` 为真直接结束，没有调用 Vault 或 Jump。因此持续前进并保留冲刺状态时，接近障碍物会从普通跳跃分支进入这个空分支，看起来像贴边后不能起跳。

只修改 `/Game/Blueprints/Player/BP_FPCharacter`：安全翻越检测通过时，冲刺状态允许使用原有翻越；Reloading 为真则回退到原生 Jump。保留已有的动画选择、输入锁和落地逻辑。局部移动 Reloading Getter，扩充原 JUMP 注释框，并目视复核。

没有调整 JumpZVelocity=510、GravityScale=1.9、AirControl=0.05、MaxStepHeight=45 或站立胶囊半径/半高 48/88 cm；没有修改 `AC_Vault` 的高度、表面和完整胶囊空间检查。原有不能翻越的高墙、低顶仍受碰撞约束。

## 验证

- 修复前：60 cm 临时障碍物贴边，IsSprint=true 时，IA_Jump 注入后最高位置与起跳前相同，未进入翻越。对照普通行走可以翻越。状态诊断使用显式设置 IsSprint 的测试夹具。
- 修复后：50、60、100、160 cm 临时障碍物，行走/冲刺状态的 8 组贴边测试均越过；200 cm 高墙的 2 组测试保持阻挡；装填状态回退到普通跳跃，不进入翻越。此矩阵使用显式状态夹具。
- 通过 Enhanced Input 注入 IA_Move、IA_Run 双击/保持和 IA_Jump，在原有 `SM_Cube21`（约 60 cm 高）验证普通行走及冲刺后持续顶住边缘起跳，两组均越过；冲刺组实际记录 IsSprint=true。
- 同样的真实输入链验证 60 cm 临时障碍物成功、低顶覆盖的障碍物拒绝翻越。初次 Run 注入发生在已被墙挡停后，未进入冲刺，不计入冲刺验收；最终测试从后方接近后进入冲刺，核对了起跳时状态。
- 保存后的新一轮 PIE 复测 60 cm 冲刺贴边场景成功。共 16 组修复后场景通过；玩家及 AC_Vault 编译 0 错误、0 警告。仅保存玩家资产。
- 新一轮 PIE 最初的输入测试选中了上一轮遗留的 LocalPlayer 子系统，未实际提交跳跃；这次失败仅计为测试夹具问题。改用 `subsystem.get_world()==当前 PIE World` 绑定后重新验证，原结果保留为 `saved-smoke-stale-input.json`，不计入通过数。
- 图表比较确认仅删除该分支的 OR/IsSprint Getter、改接 Reloading 条件并补上 Jump 回退；其他图表、输入默认值与连接保持不变。忽略编译器对未使用 Key 输出默认值的空值规范化。

本机证据位于忽略跟踪的 `Saved/Agent/CloseJump/`：`baseline-sprint.json`、`after-matrix.json`、`real-input.json`、`saved-smoke.json`、`scope-verification.json`、`jump-layout.png` 及 `delivery.json`。修改前保存版本的定向备份在其中的 `Recovery/`。所有平台、障碍物、低顶和玩家状态夹具仅存在于 PIE；没有保存 Map_Test、外部 Actor 或测试布置。未进行打包和多人验证。
