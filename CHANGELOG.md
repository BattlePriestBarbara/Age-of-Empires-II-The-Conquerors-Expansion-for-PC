# 版本历史（CHANGELOG）

本工程给《帝国时代 II HD》(AoE2 HD) 的**死亡竞赛 AI** 打补丁：让电脑玩家持续补房子、升时代、研究科技、按人口上限出兵。
所有版本的工具与日志都在本仓库；下面按时间顺序记录每次**做了什么、为什么、实测结果、以及被推翻的假设**。

---

## v3 — 修掉 v2 唯一的硬报错 ERR2011（当前版本）

**游戏内症状**（v2 安装后弹出）：

```text
AI Script Error
Player 8
File  petersen deathmatch per
Line 3021: ERR2011: Missing closing parenthesis
```

**根因（实测，不是猜测）**：`AoK HD.exe` 给每个逻辑块（`or` / `and` / `nor` / `not`）**只有两个参数槽**。
v2 的 S1 资源兜底规则写成"一个 `or` 带 4 个子节点"，解析器读完前两个就想要 `)`，撞上第三个 → 把第三个子节点的行号报成"缺右括号"。

证据：

* 全游戏 AI 脚本形状普查：**没有一个逻辑块超过 2 个子节点**（DM 脚本 `{1:31, 2:181}`、`anib_60003` `{1:31, 2:159}`、`anib_60029` `{1:9, 2:113}`、`anib_60010` `{1:5, 2:4}`、AoK DM `{1:27, 2:154}`）。
* 原作表达多条件时一律**嵌套**双子节点 `or`；死亡竞赛脚本自己就有样板：L1511-1523、L1533-1542。
* 行号精确对应：零售脚本 2883 行 + v2 追加块第 138 行 = 第 3021 行 = `(gold-amount < 5000)`（第 3 个子节点）。
* **回归基准**：把崩溃样本（`dm_block_v2_broken_fixture.txt`）接在 2883 行后重跑模型，`dm_dialect.py` 报出 `blames the child at line 3021`，与引擎的 `Line 3021` **MATCH**。

**改动**：

1. S1 的资源判断改成原作式双子节点嵌套（语义不变）；追加块 5295 → 5868 字节。
2. `dm_patch2.py` 新增两条**硬校验**（生成前断言）：任何逻辑块 ≤ 2 个子节点；每个"块形状"与"事实参数个数"都必须在原作脚本里有出处。唯一显式例外是 M1 的 `chat-to-all`（写在 `SHAPE_EXCEPTIONS` 里，附理由）。
3. 聊天自检标记改为 `DM AI fix v3 loaded [x1]` / `[aok]`，用于区分新旧文件。
4. `dm_install2.py` 新增"拒绝旧版本残留块"校验。
5. 新增工具：`dm_dialect.py`（控制组回归 + 已安装档案审计）、`dm_blockshape.py`（形状普查）、`dm_line3021.py`（行号/括号取证，原脚本的 per-rule 检查有假阳性已修正）、`dm_v2hit.py`（旧标记卫生）、`dm_git_export.py`（生成 git 快照）。
6. 修掉工具自身三个 bug：
   * `code_only()` 原实现"先删字符串再删注释"，注释里的引号（原作注释含 `"(difficulty <= moderate)"`）会与几行之后的引号配对，吞掉中间换行、整体行号偏移一行 —— 正是它让第一版校验器把 3021 报成 3020；现在改为**逐行**处理。
   * `dm_marker_check.py` 的标记匹配大小写敏感，导致对着 v3 载荷误报 `no marker`（载荷里是 `AI FIX v3`）；已改为不区分大小写。
   * `dm_apply2.py` 文档字符串里的 `\*.orig` 触发 `SyntaxWarning`；已转义。

**验证**：新工作目录复跑整条链，产出与本机已安装文件**逐字节相同**（`gamedata_x1.drs` = `59ca9130ce14f649a52d47f64b1357b3`、`gamedata.drs` = `bc3ae18a686cbd6b1804ecaa9e72d589`）；12 步验证链全部 exit 0；README 结构校验通过。

---

## v2 — 重建为"原作规则去门槛"的 14 条规则（已被 v3 取代）

**方向**：v1 的假设被推翻后（见下），改为**只做一件事**：把原作 DM 脚本里"高难度/无人类玩家时不成立"的门槛删掉，规则其余部分逐字保留。

**做了什么**：

* 追加 14 条规则（M1 标记 / H1-H4 房子 / A1-A3 升时代 / R1 出兵令 / S1 资源兜底 × 3），共 5295 字节。
* 复用两个在 DM 脚本里没人用的零售计时器名：`t-tribute`(1)、`t-attackgroup`(2)。
* 永远从 `backup_drs\*.orig` 重建 DRS；新增 token 取证（每个符号都要在原版脚本或 `AoK HD.exe` 里出现）。
* 常量脚本 `anib_60027` / `anib_60010` 不再改动（v1 的 catch-all 已从游戏文件清除）。
* 新增 `dm_marker_check.py` / `dm_dmcheck.py` / `dm_v2hit.py` 等检查，并重写 README。

**结果**：方向正确，但游戏内出现 `ERR2011: Missing closing parenthesis`（`Line 3021`）→ 由 v3 修复。

**同时确认**：`gamedata_x1_p1.drs` 里没有任何 AI 脚本，所以补丁只可能落在 `gamedata.drs` / `gamedata_x1.drs`。

---

## v1 — 追加 4 条规则 + 常量 catch-all（已废弃）

**当时的三条假设**：

* 根因 A：出兵令 `(goal secondary-build)` 被清零后不再恢复 → 追加一条 `(goal secondary-build 0) → 1`。
* 根因 B：Hard/Hardest 没有造房规则 → 追加一条造房规则。
* 根因 D（**后来被推翻**）：人口上限不是 8 个"标准值"（例如 500）时整个 DM 脚本失效 → 往常量脚本 `anib_60027` / `anib_60010` 追加 `catch-all`（覆盖未知人口上限）。

**为什么被推翻**：

* `dm_popstr.py` 解出 `AoK HD.exe` 0x0045c900 处的开关：**500 → `POPULATION-CAP-200`**，从来不会"未定义"，所以 catch-all 是**死代码**；v2 已把它从游戏文件里删干净。
* `dm_p1check.py` 证明 `gamedata_x1_p1.drs` 里没有 AI 脚本。

**结果**：行为无变化（4 条规则里除 R1 外都没打中真正原因，且 v1 的 catch-all 无效）。

---

## 工程约定（适用于所有版本）

1. **可复现**：任何产物都能从 `backup_drs\*.orig`（原始档案备份）重新生成；生成器拒绝在"未取证"的符号/形状上工作。
2. **可审计**：每一步都写日志（`*_console.txt` / `*_out.txt` / `*_report.txt`），关键数字（md5、字节数、行数、形状分布）都留在仓库里。
3. **可还原**：`python dm_restore.py`（或双击 `restore_original_AI.cmd`）用原始备份覆盖回游戏并校验 md5。
4. **不含游戏数据**：仓库只存脚本、日志与文档；`*.drs`、解包产物、可执行文件都在 `.gitignore` 中。
5. **可移植**：脚本路径基于自身目录；游戏目录读环境变量 `AOE2HD_DIR`（未设置时回退到作者本机路径）。
