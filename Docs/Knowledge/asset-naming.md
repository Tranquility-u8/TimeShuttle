# 资产与文件命名规范

本项目约定，2026-09-26 生效。它是团队规范，不宣称是 Unreal 强制标准。实际类型以 Asset Registry / 编辑器为准，不根据文件名前缀猜测。

## 通用规则

- 新资产使用 `类型前缀_职责或主体_可选变体`；主体使用 PascalCase，缩写如 AI、FP、TP、NPC 保持一致。
- 只使用英文字母、数字、下划线；不用空格、连字符、中文文件名。目录使用 PascalCase 复数分类，如 `Blueprints/AI/Shooter`、`Animations/Player`。
- 名字说明职责，不继续引入来源包名 `CAI_`、`ProceduralFPSKIT_`。相同语义使用同一单词，如 `Grenade`、`Strength`、`Deprecated`。
- 禁止把 `Copy`、`New`、`Final2` 当正式版本命名。测试资产放 `Developers` 或明确的测试目录；弃用资产保留 `_Deprecated` 标记，删除应另查引用。
- 不更改骨骼名、Socket、蒙太奇 Slot、枚举条目、结构体字段或蓝图公开函数来追求文件名一致；这些是运行时契约，不是本规范的批量改名对象。
- 新建 Markdown 使用 `kebab-case.md`；现有固定入口 `AGENTS.md`、`README.md`、`SKILL.md` 及已被引用的历史文档名保留。PowerShell 工具沿用 `Verb-Noun.ps1`。

## 类型前缀

| 类型 | 前缀 | 项目示例 / 说明 |
| --- | --- | --- |
| Actor、Character、AIController 蓝图 | `BP_` | `BP_FPCharacter`、`BP_MeleeNPC`、`BP_ShooterNPC`、`BP_MeleeAIController` |
| Actor Component | `AC_` | `AC_Combat`、`AC_EnemyReverse` |
| 蓝图接口 | `BPI_` | `BPI_Combat`、`BPI_RewindableEnemy` |
| GameMode、SaveGame | `GM_`、`SG_` | `GM_FP`、`SG_Character` |
| 蓝图宏库、函数库 | `ML_`、`BFL_` | 判断 Blueprint 类型，不能仅凭 ParentClass 判断宏库 |
| 枚举、结构体 | `ENUM_`、`S_` | `ENUM_StrengthSwap`、`S_Item`；保留项目已有的大多数 `ENUM_` 命名，`ST_` 留给 StateTree |
| PrimaryDataAsset 蓝图类 | `PDA_` | `PDA_Item`、`PDA_ProceduralAnimValues` |
| DataAsset 实例、真正的 DataTable | `DA_`、`DT_` | `DA_PistolAnimationValues`；不要把 DataAsset 标成 `DT_` |
| BehaviorTree、Blackboard、Task | `BT_`、`BB_`、`BTT_` | `BT_Melee`、`BB_Melee`、`BTT_Melee_Attack` |
| StateTree、Task、Condition | `ST_`、`STT_`、`STC_` | `ST_Shooter`、`STT_Shooter_SenseEnemies` |
| EQS、Query Context | `EQS_`、`EQC_` | `EQS_FindSnipingLocation`、`EQC_ShooterTarget` |
| Animation Blueprint | `ABP_` | `ABP_EnemyRewind_Shooter` |
| Anim Sequence、Montage、Notify、NotifyState | `A_`、`AM_`、`AN_`、`ANS_` | 新建资源使用；导入动画见例外 |
| CameraShake | `CS_` | `CS_WeaponFire`、`CS_Run` |
| Widget Blueprint | `WBP_` | `WBP_MeleeEnemyHealth` |
| Input Action / Mapping Context | `IA_`、`IMC_` | `IA_Reverse`、`IMC_Player` |
| Skeletal Mesh / Skeleton / Static Mesh | `SKM_`、`SK_`、`SM_` | 新资产按类型命名；Epic 和供应商资源保留来源名 |
| Material / Instance / Function / Texture | `M_`、`MI_`、`MF_`、`T_` | 纹理后缀沿用其实际用途与打包通道，不凭名字改贴图设置 |
| SoundWave / Cue、Niagara System | `SW_`、`SC_`、`NS_` | 新资源约定 |
| Map | `Map_` | `Map_Test`、`Map_Menu` |

## 明确保留的历史命名

此次统一的是常用逻辑资产，不是全库资源重命名。以下原有资源是受控例外，新增同类资产仍遵循上表：

- `TimeReverseSystem/` 中的原包核心、示例和资源保留原名，包括 `BP_ReverseTrasnsformComponent` 的历史拼写。它仍被现有系统使用；不要误当成可删除的废文件。
- Epic / 导入的模型、骨骼、动画、材质、音效保留可追溯的原名，例如 `CAI_AnimBP`、`CAI_Anim_*`、`ABP_TP_Rifle`、`*_MANNY`、`SKM_*`。
- FPS 模板现有 `UI_*` Widget、`Curve_*` 曲线、`CS_IDLE` / `CS_JUMP` 等大小写，以及导入资源目录中的 `Granade` 保留。玩法蓝图和数据目录已统一为 `Grenade`；不顺带重导入或批量改动底层资源。
- `FirstPerson/`、`LevelPrototyping/`、旧存档兼容转向不是删除候选。`__ExternalActors__`、`__ExternalObjects__` 由 UE 管理；`Collections`、`Developers` 按编辑器工作流管理。

不要通过继续添加例外来掩盖新资产不合规。新的例外须记录原因和范围。

## 安全改名流程

1. 确认提交恢复点和现有改动；读取真实资产类型，建立旧路径 → 新路径清单，检查目标重名和引用者。
2. 使用 UE AssetTools / 编辑器 Rename 或 Move，禁止在文件管理器、Git 或脚本中直接移动 `.uasset` / `.umap`。地图和 World Partition 迁移另用引擎支持的专门流程。
3. 编译并定向保存被改名资产及实际引用者；保留场景实例覆盖，保护无关用户改动。
4. 检查配置、软引用、字符串路径、存档和 Primary Asset ID。项目已有 `CoreRedirects`，旧存档需要的兼容项不可仅因资产引用清零就删除。
5. 在新的 UE 进程中加载验证，检查旧引用和 Redirector，再进行主关卡 PIE 回归。只有确认不再需要时才清理 Redirector；不要把仍依赖的旧路径直接强删。
6. 同步本目录、实现说明和实际脚本调用方。临时脚本/日志放忽略跟踪的 `Saved/Agent/`。

本轮逐文件映射见 [asset-renames-2026-09-26.csv](asset-renames-2026-09-26.csv)。

改动范围和验证边界见 [本轮实施记录](../Implementation/asset-naming-2026-09-26.md)。
