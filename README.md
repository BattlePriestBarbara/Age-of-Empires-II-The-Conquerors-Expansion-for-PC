# AoE2 HD 死亡竞赛 AI 修复补丁 · v3

> 让《帝国时代 II HD》（Age of Empires II HD）**死亡竞赛**里的电脑玩家不再"出一个兵就发呆"：
> 它会持续补房子、升级时代、研究科技、按人口上限出兵，而不是开局造一个单位就停摆。
>
> 本仓库是**纯 Python（仅标准库）工具链 + 全部证据日志**，**不含任何游戏数据**：
> 补丁是用你自己的游戏安装现场生成的，所有 `*.drs` / 解包产物都在 `.gitignore` 里。

**English.** A tiny, auditable toolkit that patches `petersen deathmatch`
(`anib_60002`) inside `Data\gamedata*.drs` of *Age of Empires II HD* so that
death-match AIs keep building houses, advancing ages and producing units instead
of stalling after the first unit. Python 3 (stdlib only). No game assets are
included - the patch is generated from the reader's own installation, and every
step prints the md5 it produced so the result can be reproduced and audited.
The centrepiece is `dm_dialect.py`, which not only checks the patch but *proves
its diagnosis* by reproducing the exact in-game error line the previous build
produced.

---

## 1. 它修的是什么

| 症状 | 原因 |
|---|---|
| AI 开局造 1 个兵（或几只羊/房子）后**再也不出兵** | 零售脚本在每条出兵规则里把出兵令 `(goal secondary-build)` 归 0，只在"城堡出特色兵"那条规则里重新置 1；死亡竞赛里 AI 不造城堡，于是出兵循环永久关闭（**根因 A**） |
| Hard / Hardest 下 AI **从不多造房子** | 三条造房规则分别被 `(difficulty <= moderate)`、`#load-if-defined DIFFICULTY-EASY`、`…-EASIEST` 包住；高难度下**一条都没被编译**（**根因 B**） |
| Hard / Hardest 下 AI **永不升时代** | 三条升时代规则被 `(or (players-current-age every-human >= <age>) (difficulty <= moderate))` 包住 —— 没有人类玩家时永远为假（**根因 C**） |
| AI 资源耗尽后**不补充** | 死亡竞赛脚本里没有任何资源补充规则（`cc-add-resource` 只出现在别的模式脚本里） |

补丁把上面三条根因对应的**原作规则逐字复制**，只删掉难度/人类玩家门槛，追加到死亡竞赛脚本末尾（14 条规则、5868 字节）。同时给 AI 加了两条**兜底**：计时器驱动的"房子 < 40 就补"和"任一资源 < 5000 就各补 10000"。

## 2. 仓库结构

| 路径 | 说明 |
|---|---|
| `README.md` | 本文件（总览 / 快速开始 / 证据索引 / 排查） |
| `CHANGELOG.md` | v1 → v2 → v3 的完整历史（含每次的失败原因） |
| `HD_DM_AI_PATCH_README.md` | **技术全文档**（528 行，章节式）：每条根因的源码证据、形状普查数据、v3 的 ERR2011 复盘、逐项验证数字 |
| `docs/FILE_MAP.md` | 文件清单（自动生成：124 个脚本各自的第一行说明 + 185 个日志清单） |
| `docs/readme_v2_history.md` | v2 时期的 README 存档 |
| `dm_*.py`、`drs_*.py`、`dump_block.py`、`extract_bina.py` … | 全部工具，**124 个脚本**，各自带文档字符串，可单独运行 |
| `*_out.txt`、`*_report.txt`、`*_console.txt` | **185 个日志/报告**：每一步的原始输出（证据链出处） |
| `dm_block_v2_broken_fixture.txt` | v2 崩溃样本的字节备份（回归基准，见 §5） |
| `restore_original_AI.cmd` | 一键还原（内部用 `%~dp0`，双击即可） |
| `.gitignore` | 游戏数据/解包产物不入库 |

被 `.gitignore` 排除、但**本地跑链需要**的目录：`x1_drs\`、`aok_drs\`、`x1p1_drs\`（从 DRS 解出来的 AI 脚本）、`backup_drs\`（原始档案备份）、`patched_drs2\`、`patch_out2\`（补丁产物）。

## 3. 五分钟快速开始（从零复现）

**前提**：自己拥有并已安装 AoE2 HD；**游戏没在运行**；Python 3.8+（本工程只用标准库）。

```bat
:: 0) 指向你的游戏目录（脚本会优先读这个环境变量）
set AOE2HD_DIR=D:\SteamLibrary\steamapps\common\Age2HD

:: 1) 一次性：备份原始档案 + 解包出脚本文本
mkdir backup_drs 2>nul
copy "%AOE2HD_DIR%\Data\gamedata.drs"    backup_drs\gamedata.drs.orig
copy "%AOE2HD_DIR%\Data\gamedata_x1.drs" backup_drs\gamedata_x1.drs.orig
python extract_bina.py "%AOE2HD_DIR%\Data\gamedata_x1.drs"    x1_drs
python extract_bina.py "%AOE2HD_DIR%\Data\gamedata.drs"       aok_drs
python extract_bina.py "%AOE2HD_DIR%\Data\gamedata_x1_p1.drs" x1p1_drs

:: 2) 生成 -> 重打包 -> 安装（任一步失败即中止，不会写出半成品）
python dm_patch2.py     :: 形状/符号校验，载荷写到 patch_out2\
python dm_apply2.py     :: 从 backup_drs\*.orig 重打包到 patched_drs2\
python dm_install2.py   :: 备份 + 安装进 Data\ + 逐条目 md5 校验

:: 3) 验证（下面的数字就是本文档里列出的那些）
python dm_v2hit.py         :: 新载荷里不许再出现旧版本标记
python dm_dialect.py       :: 必须先打印 "-> MATCH"，再审计已安装的档案
python dm_line3021.py      :: 括号 / 规则闭合 / 行号取证
python dm_dmcheck.py       :: 零售前缀逐字节保留 + 预处理器嵌套深度
python dm_marker_check.py  :: backup / patched / live 三份状态对照

:: 4) 还原（任何时候都能一键回到原版）
python dm_restore.py
```

要点：

* **永远从 `backup_drs\*.orig` 重新生成**，所以补丁不可能叠加；`dm_install2.py` 还会拒绝任何"旧版本残留块"。
* 脚本**不需要安装任何 pip 包**，也不读写注册表；只做两件事：读 `Data\gamedata*.drs`、写回同名文件。
* 脚本位置随便放：所有路径都基于脚本自身目录（`os.path.dirname(os.path.abspath(__file__))`），游戏目录由 `AOE2HD_DIR` 决定。
* `dm_restore.py` 会核对原始档案的 md5（零售 Steam HD 版：`gamedata.drs` = `be574545…`、`gamedata_x1.drs` = `f41c4183…`）。**如果你的版本不同**，把这两个期望值改成你自己的（或用 `backup_drs` 手动覆盖）。

---

## 4. 补丁内容：追加的 14 条规则

全部是**原作规则的逐字复制 + 删除门槛**，或**只用原作出现过的写法新写**（脚本会自动取证：每个符号、每个"形状"、每个"参数个数"都必须在原版脚本里出现过，否则拒绝生成）。

| # | 作用 | 来源 |
|---|---|---|
| M1 | 开局聊天栏说一句 `DM AI fix v3 loaded [x1]` —— 证明引擎确实编译执行了这份脚本 | 只用原作符号 `true` / `chat-to-all` / `disable-self` |
| H1 | `(building-type-count-total house <= fifteen-percent-pop)` + `(can-build house)` → `(build house)` | 原作 L1675-1680，去掉 `(difficulty <= moderate)` |
| H2 | `(housing-headroom < 5)` + `(population-headroom > 0)` + `(can-build house)` → 造房 | 原作 L1694-1701（`DIFFICULTY-EASY` 块），去掉 `(military-population < civ-dark-rush)` |
| H3 | 同 H2（简化版） | 原作 L1683-1690（`DIFFICULTY-EASIEST` 块），去掉 `(military-population < 10)` |
| H4 | 计时器兜底：开局 30 s 后、之后每 20 s，自家房子 `< 40` 且能造就补一个 | 新写；40 × 5 = 200 人口位，与这局引擎给的 `pop-cap 200` 对齐 |
| A1 | `(can-research feudal-age)` → 研究 + `(set-goal age-advancement NOTICE)` + `(enable-timer t-ageup 140)` | 原作 L1594-1604，去掉 `(or (players-current-age every-human >= feudal-age) (difficulty <= moderate))` |
| A2 | 封建 → 城堡（`t-ageup 170`） | 原作 L1614-1624，同样去门槛 |
| A3 | 城堡 → 帝王（`t-ageup 200`） | 原作 L1634-1647，同样去门槛 |
| R1 | `(goal secondary-build 0)` → `(set-goal secondary-build 1)`：出兵令永久解除 | 修根因 A |
| S1 | 计时器驱动的资源兜底：开局 10 s 后、之后每 60 s，四种资源任一 `< 5000` 就各 `+10000`（3 条规则） | 新写；动作 `(cc-add-resource <资源> <数量>)` 用原作写法（原作用量 100…10000） |

安全依据（都在 `dm_patch2.py` 里做断言，日志见 `dm_patch2_console.txt`）：

* **符号取证**：36 个小写符号 + 大写枚举 `NOTICE` 全部能在原版脚本或 `AoK HD.exe` 关键字表里找到，0 个未取证（这个方言里未定义符号会让整条规则**静默失效**，所以不能自创名字）。
* **不新造计时器名**：死亡竞赛脚本里没有 `(defconst …)`，`t-*` 名字全部来自常量脚本 `anib_60027`。补丁复用两个**所有 DM 脚本都没人用**的零售名字：`t-tribute`(1) 给房子计时器、`t-attackgroup`(2) 给资源计时器。
* **不会超编**：50 条出兵规则每条都自带 `(population < deathmatch-unit-max)`，所以 AI 造到 170 就自然停。
* **不碰常量脚本**：`anib_60027` / `anib_60010` 与原始档案逐字节相同。

## 5. 关键结论：引擎每个逻辑块只有两个参数槽（v3 修的 ERR2011）

v2 装好后游戏弹出：

```text
AI Script Error
Player 8
File  petersen deathmatch per
Line 3021: ERR2011: Missing closing parenthesis
```

这**不是**括号没配平（两个校验器都验过 `final depth = 0`）。真正的原因是：

> **AoK HD.exe 给每个逻辑块（`or` / `and` / `nor` / `not`）只有两个参数槽。**
> v2 的 S1 规则给了一个 `or` **四个**子节点；解析器读完前两个就想要 `)`，撞上第三个子节点，于是把**第三个子节点所在行**报成"缺右括号"。

证据（可复跑）：

| 证据 | 数字 |
|---|---|
| 全游戏逻辑块按子节点数分布（`dm_blockshape.py`） | DM 脚本 `{1:31, 2:181}`、`anib_60003` `{1:31, 2:159}`、`anib_60029` `{1:9, 2:113}`、`anib_60010` `{1:5, 2:4}`、AoK DM `{1:27, 2:154}` —— **没有一个块超过 2 个子节点** |
| 原作要表达多条件时怎么写 | **嵌套**双子节点 `or`，死亡竞赛脚本自己就有样板：L1511-1523、L1533-1542（"资源偏低"判断） |
| 行号为何正好是 3021 | `gamedata_x1.drs` 零售脚本 2883 行 → v2 追加块第 138 行 = 第 **3021** 行 = `(gold-amount < 5000)`（第 3 个子节点） |
| 回归基准（`dm_dialect.py` 控制组） | 把 v2 崩溃样本（`dm_block_v2_broken_fixture.txt`）接在 2883 行之后重跑模型 → 输出 `… blames the child at line 3021`，与引擎的 `Line 3021` **MATCH** |

v3 的修法是把同一个判断改成原作的双子节点嵌套（语义不变）：

```perl
(defrule
	(timer-triggered t-attackgroup)
	(or
		(or
			(wood-amount < 5000)
			(food-amount < 5000)
		)
		(or
			(gold-amount < 5000)
			(stone-amount < 5000)
		)
	)
=>
	(cc-add-resource wood 10000)
	(cc-add-resource food 10000)
	(cc-add-resource gold 10000)
	(cc-add-resource stone 10000)
)
```

并新增两条**硬校验**（`dm_patch2.py` 生成前断言，不通过不写文件）：

| 规则 | 内容 | v3 实测 |
|---|---|---|
| rule 1 | 任何逻辑块最多 2 个子节点 | 追加块 `{2: 3}` |
| rule 2 | 每个"块形状"与每个"事实参数个数"都必须在原作脚本里有出处 | 2 种块形状均有出处（`(or or or)` ← 原作 L1514；`(or <fact> <fact>)` ← 原作 L495）；22 种事实全部有出处；唯一显式例外：`chat-to-all`（1 个字符串参数，理由写在 `SHAPE_EXCEPTIONS` 里） |

> 排查过程中还修掉了工具自身的三个 bug，都记录在 `CHANGELOG.md`：① `code_only()` 先删字符串后删注释，导致注释里的引号（原作注释写着 `"(difficulty <= moderate)"`）跨行配对、吞掉换行、行号偏移一行（曾把 3021 报成 3020）；② `dm_marker_check.py` 标记匹配大小写敏感导致误报 `no marker`；③ `dm_apply2.py` 文档字符串的反斜杠转义告警。

---

## 6. 验证链（本仓库在新位置复跑，全部 exit 0）

| 步骤 | 结果 |
|---|---|
| `dm_patch2.py` | 追加块 **14 条规则 / 5868 B**，括号配平、`#load-*` 配平、无难度门槛；形状与符号校验通过；载荷 md5 `19898a75…`(x1) / `20e5c89f…`(aok) |
| `dm_apply2.py` | 从 `backup_drs\*.orig` 重打包，每个档案仅 2 个条目变化，其余 74/46 个逐字节相同；重打包 md5 **`59ca9130ce14f649a52d47f64b1357b3`**(x1) / **`bc3ae18a686cbd6b1804ecaa9e72d589`**(aok) |
| `dm_install2.py` | 安装后 md5 与上一步一致；标记为 `AI FIX V3` / `AI FIX BASE`；**无旧版本残留块**；零售脚本是逐字节前缀 |
| `dm_dialect.py` | 控制组 `line 3021 -> MATCH`；x1：3046 行 / 257 规则 / 块分布 `{1:31, 2:184}` / EOF depth 0；aok：2607 行 / 226 规则 / `{1:27, 2:157}` / EOF depth 0；追加块 `{2:3}`；**无未取证形状或参数个数** |
| `dm_line3021.py` | 两个档案 `final depth=0`、`negative depth: none`、无未闭合规则；x1 第 3021 行现在只是普通动作行 `(disable-self)` |
| `dm_dmcheck.py` | 预处理器 x1 25 开/25 关、aok 21 开/21 关，EOF depth 0；`prefix-ok=True` |
| `dm_v2hit.py` | 载荷里 `AI FIX V2` / `HD DEATH-MATCH AI PATCH` 出现 **0** 次 |
| `dm_marker_check.py` | backup / patched / live 三方一致；仅预期条目不同 |
| `dm_readme_verify.py` | 技术文档 528 行、纯 CRLF、无 BOM、28 个代码围栏成对、无残缺表格 |
| 重打包可复现性 | `dm_patch2.py + dm_apply2.py` 连跑 3 次，md5 恒定 |

**本次实测：补丁安装后，新的工作目录重跑整条链，产出与本机已安装文件逐字节相同**（`59ca9130…` / `bc3ae18a…`），这是"脚本可移植 + 行为未变"的最强证明。

## 7. 已安装文件的 md5（仅供对照）

| 文件 | 原始 md5 | 打完 v3 后 md5 | 条目数 | 变化 |
|---|---|---|---|---|
| `Data\gamedata.drs`（Age of Kings 数据） | `be574545e247b85a196109836a1f9d44` | `bc3ae18a686cbd6b1804ecaa9e72d589` | 48 | `anib_60002` 45718 → **51587 B**（+5869）；`anib_60001` 28550 → **28855 B**（标记） |
| `Data\gamedata_x1.drs`（Conquerors 数据，HD 默认） | `f41c418333e624b7a1077ad166f9dcb0` | `59ca9130ce14f649a52d47f64b1357b3` | 76 | `anib_60002` 54203 → **60071 B**（+5868）；`anib_60001` 29337 → **29641 B**（标记） |

`gamedata_x1_p1.drs`（1.0c 补丁数据）里没有任何 AI 脚本，**不需要改**。

## 8. 参数调校（都在 `dm_patch2.py` 顶部）

| 想改什么 | 改哪个 |
|---|---|
| 房子上限（房子数 × 5 = 人口位） | `HOUSES_MAX`（默认 40 = 200 人口位） |
| 房子检查节奏 | `HOUSE_TIMER_TIME`（30 s）/ `HOUSE_TIMER_REPEAT`（20 s） |
| 资源阈值 / 每次补多少 | S1 规则里的 `< 5000` / `10000` |
| 资源检查节奏 | `RES_TIMER_TIME`（10 s）/ `RES_TIMER_REPEAT`（60 s） |
| 计时器名字 | `HOUSE_TIMER`（`t-tribute`）/ `RES_TIMER`（`t-attackgroup`） |

改完重跑 §3 的第 2、3 步即可（生成器会重新做全部校验）。

## 9. 游戏内自检与排查

开局看聊天栏（AI 每个玩家各说一次，属正常）：

| 看到什么 | 说明 |
|---|---|
| `DM AI fix v3 loaded [x1]` | 引擎读的是 Conquerors 数据（`gamedata_x1.drs`），且这份 DM 脚本**确实被编译执行** |
| `DM AI fix v3 loaded [aok]` | 引擎读的是 AoK 数据（`gamedata.drs`） |
| `AI fix base loaded [...]` | `anib_60001`（基础 AI）的标记也生效，任何用到它的模式都会说一次 |
| 显示 `v2` / 什么都没有 | 引擎读到的不是本补丁（MOD 覆盖 / 数据没重新加载 / 装到了别的目录）→ 把 `Data\gamedata*.drs` 的 md5 与 §7 对照 |
| 弹出 `AI Script Error` | 记下 **File / Line / Player** 三个字段：现在 `dm_dialect.py` + `dm_line3021.py` 能直接从行号定位到具体构造（v2 那次就是靠 3021 定位到"一个 `or` 带 4 个子节点"） |

行为预期（人口 500 + Hard/Hardest + 8 人 DM）：房子一路补到约 40 个、农民铺开、时代升到帝王、兵持续出到 **170**（这局引擎给的上限 `deathmatch-unit-max`，因为 500 被折成 `pop-cap 200`）、资源长期贴在 1 万以上。开局经济要 1-2 分钟才铺开，先看**房子数**和**农民数**是否在涨。

## 10. 已知限制

1. **人口上限 500/400/300 都被引擎折成 `POPULATION-CAP-200`**（`dm_popswitch.py` 从 `AoK HD.exe` 0x0045c900 的开关解出来，`dm_popstr.py` 是证据）。所以 AI 的目标是 200 人口 / 170 兵 —— 它不会再罢工，但也不会填满 500。想让 AI 真用满 500，需要另改常量脚本里 `POPULATION-CAP-200` 段的数值（那会同时影响正常的 200 人口 DM 局）。
2. H4 / S1 复用的计时器 `t-tribute`(1) / `t-attackgroup`(2) 在所有 DM 脚本里都没人用，但**场景内置 AI** 可能占用它们；这个方言里自造新计时器名 = 未定义符号 = 规则静默失效，所以只能两害相权。
3. M1 的 `chat-to-all` 是本仓库唯一一条"原作没有同形状出处"的写法（原作只用本地化的 `chat-to-all-using-id`），理由与备选方案见 `dm_patch2.py` 的 `SHAPE_EXCEPTIONS`。
4. 补丁只影响 **Deathmatch** 开局；随机地图/帝王战等模式不受影响（唯一例外是 `anib_60001` 那条只说话的标记规则）。

## 11. 法律与免责

* 本仓库**不包含**任何《帝国时代 II HD》游戏资源：不含 `*.drs`、不含解包出来的脚本、不含 `AoK HD.exe`。日志里只出现**我们自己追加的规则文本**与**统计数字**。
* 使用本工具需要你自己合法拥有该游戏；工具只在你的本机读写你自己的 `Data\gamedata*.drs`。
* 改动游戏数据文件属于单机/自订用途：**HD 联机对战会校验数据一致性**，双方文件不同可能无法进入或被判定为数据不匹配 —— **联机前请先 `python dm_restore.py` 还原**。
* 工具按"原样"提供，不含任何担保；`backup_drs\*.orig` 就是你的后悔药，`dm_restore.py` 会校验 md5 后再写回。

## 12. 版本历史（详见 `CHANGELOG.md`）

| 版本 | 状态 | 一句话 |
|---|---|---|
| v1 | 已废弃 | 追加 4 条规则 + 常量 catch-all；**catch-all 被证明是死代码**（500 被折成 `POPULATION-CAP-200`），已从游戏文件清除 |
| v2 | 已废弃 | 重建为"原作规则去门槛"的 14 条规则；行为方向正确，但实测触发 `ERR2011 @ line 3021`（一个 `or` 带 4 个子节点） |
| **v3** | **当前** | 把该规则改成原作的双子节点嵌套；新增两条形状硬校验；新增控制组回归（复现 3021）；修掉工具自身 3 个 bug |

## 13. 上传到 GitHub（三步）

这个文件夹已经是一个初始化好的 git 仓库（分支 `master`，首个提交 `c60aff6`，317 个文件 / 约 2.4 MB）。换台机器或换目录都能直接跑（脚本基于自身位置定位，游戏目录读 `AOE2HD_DIR`），所以**可以随意改名/搬位置**。

```bat
cd D:\aoe2_aoefix
git remote add origin https://github.com/<你的用户名>/<仓库名>.git
git branch -M main
git push -u origin main
```

* `.gitignore` 已排除全部游戏数据（`*.drs`、`*.drs.orig`、`x1_drs\`、`aok_drs\`、`x1p1_drs\`、`backup_drs\`、`patched_drs*\`、`patch_out*\`、`patched_scripts\`）—— 推上去的只有脚本、日志与文档。
* 如果连日志也不想入库：`git rm -r --cached *_out.txt *_report.txt *_console.txt`，并在 `.gitignore` 里加 `*_out.txt` 等规则。
* 仓库里没有任何版权资源（没有 `*.drs`、没有 `AoK HD.exe`、没有解包出的游戏脚本），可以放心公开；但请保留 §11 的免责说明。
