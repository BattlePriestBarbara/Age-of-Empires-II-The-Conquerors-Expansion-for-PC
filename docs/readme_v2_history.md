# Age of Empires II HD — 死亡竞赛 (Deathmatch) AI 补丁说明

目标：让 **死亡竞赛模式的 AI 持续出兵**、**一直补房子 / 升时代 / 研究科技**，并且 **资源近似无限**。

> **当前生效 = v2 补丁**（2026-09-26 重做，取代已被数据推翻的 v1）。
> v1 的核心诊断**是错的**：人口上限 500 时引擎并不是"不定义任何 `POPULATION-CAP-*`"，而是把 500 **映射成 `POPULATION-CAP-200`**（`dm_popstr.py` → `dm_popstr_out.txt`：引擎 0x0045c900 的开关只 push 8 个 `POPULATION-CAP-*` 字符串，500 走 `sub 300 / sub 400 / sub 100` 后为 0 → push `POPULATION-CAP-200`），所以常量脚本里的 `pop-cap 200`、`deathmatch-unit-max 170`、`fifteen-percent-pop 30` **一直是定义好的**，v1 那段 catch-all 常量块其实是**死代码**（还带了一段错误的诊断进游戏文件）；另外 `gamedata_x1_p1.drs` 里根本没有 AI 脚本（`dm_p1check.py`）。
> 真正让 AI 卡死的是 §1 里的**根因 A（出兵令牌只上膛一次）+ 根因 B（Hard / Hardest 完全没有造房规则）+ 年龄规则被"有人类玩家或低难度"门槛锁死**。
> v2 因此**只改 AI 脚本、不改常量**：从 pristine 备份重建 `anib_60002` 后追加 **14 条规则**（逐字复制原作规则，只去掉难度 / 人类玩家门槛），并在基础脚本 `anib_60001` 末尾加一条"只聊天"的标记规则 —— 两个档案各只有 2 个条目变化。规则清单见 §2c，验证数字见 §3。

补丁已经写入游戏存档文件（DRS），原文（未修改）备份在 `backup_drs\*.orig`，`dm_restore.py` 可一键还原。

---

## 1. 到底为什么原来不持续出兵？（源码证据）

死亡竞赛时游戏加载的 AI 脚本链（`x1_drs/anib_60026.bin` = *petersen random game*）：

```
#load-if-defined DEATH-MATCH
  (load "petersen constants")   -> anib_60027
  (load "petersen map loads") / diplomacy / supplement / groups / resign
  (load "petersen deathmatch")  -> anib_60002   <== 补丁 A 改的就是它（补丁 B 改的是上面的常量脚本）
#end-if
```

### 根因 A：出兵循环只被"一次性触发"，触发后被永久关闭
`anib_60002`（*petersen deathmatch.per*，2884 行的 Conquerors 版）里，各族出兵规则全部长这样：

```
(defrule
	(goal secondary-build 1)          <-- 令牌
	(random-number == 1)
	(can-train elite-eagle-warrior)
	(or (population < deathmatch-unit-max) ...)
=>
	(train elite-eagle-warrior)
	(set-goal secondary-build 0)      <-- 打完一个就把令牌关掉
)
```

全脚本 **68 条** `(goal secondary-build 1)` 消费规则里有 **50 条是"造兵"**，它们**每一条都把令牌清 0**（我用脚本 `dm_scope.py` 逐条核对过）。
而原文中唯一的**条件式**重新上膛规则（第 2332-2344 行；另一处上膛在第 18 行的 `(true)` 规则里，开局只执行一次）是：

```
(defrule
	(can-train my-unique-unit-line)   <-- 需要"能训练自己的特色兵"
	...
=>
	(train my-unique-unit-line)
	(set-goal secondary-build 1)      <-- 只有这里重新上膛
)
```

绝大多数文明（不列颠、法兰克、波斯……）的特色兵要**城堡**才能训练；死亡竞赛开局没有城堡，AI 又不会先补一个城堡，于是 `(can-train my-unique-unit-line)` 永远为假 →
**令牌打过一次就永远是 0，出兵规则再也不触发 → AI 造一两个兵就"站着不动"**。这就是"AI 不持续出兵"的直接原因。

用脚本精确数过（原始 `x1_drs/anib_60002.bin`）：

| 写法 | 出现次数 | 位置 |
|---|---|---|
| `(set-goal secondary-build 1)`（**上膛**） | **2** | 第 18 行（开局 `(true)` 规则，只上膛一次）、第 2343 行（特色兵规则） |
| `(set-goal secondary-build 0)`（**清膛**） | **50** | 50 条造兵规则各自的行尾 |
| `(goal secondary-build 1)`（读取令牌） | 68 | 其中 50 条是造兵，18 条是各文明的 `(generate-random-number 2)` |

即"50 个消费者 vs 1 个有条件的上膛者" —— 令牌是**一次性**的，这就是根因。

### 根因 B：Hard / Hardest 难度下 AI 从不造房子
`anib_60002` 里全部造房子规则只有 3 条：`(difficulty <= moderate)`（第 1675 行）、`DIFFICULTY-EASIEST`（1683）、`DIFFICULTY-EASY`（1694）。
预处理器从第 1702 行 `#end-if` 直接跳到第 1704 行的采矿场规则 —— **HARD / HARDEST 完全没有造房子规则**。
所以最高难度 AI 的人口上限被开局房子锁死，兵造满就再也出不来（就算修好根因 A 也一样）。

### 根因 C：资源不会补充
`(cc-add-resource ...)`（引擎级别的"给 AI 加资源"指令）在原文里只出现在 *非* 死亡竞赛脚本中：
`anib_60001`（AI petersen rules）、`anib_60008`（difficulty loads）、`anib_60029`（wonder kill，仅 DEFEND-WONDER）。
死亡竞赛脚本 `anib_60002` 里**一次都没有**。
另外脚本第 2240-2254 行有一条一次性的规则：资源掉到 (木/食 < 5000) 或 (金 < 2000 / 石 < 700) 时把 `need-deathmatch-villagers` 设为 YES 并 `(disable-self)` 永不还原 —— 于是 AI 长期认为"我缺农民"，进入出农民的循环（也是"看起来像卡住"的另一个来源）。

### 根因 D（**已被推翻**，更正见本节末尾）：人口上限不是 8 个"标准值"时（例如 **500**），整个死亡竞赛 AI 直接失效 ← v1 当时以为你遇到的就是这个

这是你反馈"**人口上限 500，极难电脑只派一个农民干活、不造房子、不补兵**"的原因，而且是**最致命**的一条：不是"出兵慢"，而是 AI 脚本几乎全部规则被判为非法。

**证据 1 —— 引擎只认得 8 个人口档位**（`AoK HD.exe` 里的符号表，见 `dm_exe_ai.py` → `dm_exe_ai_out.txt`）：

```
LOW-RESOURCES-START. MEDIUM-… HIGH-…
POPULATION-CAP-200  POPULATION-CAP-175  POPULATION-CAP-150  POPULATION-CAP-125
POPULATION-CAP-100  POPULATION-CAP-75   POPULATION-CAP-50   POPULATION-CAP-25
DIFFICULTY-HARDEST  DIFFICULTY-HARD  DIFFICULTY-MODERATE  DIFFICULTY-EASY  DIFFICULTY-EASIEST …
```

也就是说：大厅人口上限设成 **500** 时，`POPULATION-CAP-500` 这个符号**根本不存在**，而 `POPULATION-CAP-25…200` **一个都不成立**。

**证据 2 —— 常量只在那些块里定义，块外没有任何默认值**（`dm_grep.py x1_drs/anib_60027.bin`）：

```
 243| #load-if-defined POPULATION-CAP-25      ...  552| (defconst deathmatch-unit-max 170)
 286| #load-if-defined POPULATION-CAP-50      ...  585| #end-if
 …（25/50/75/100/125/150/175/200 八段，逐段 #end-if）
```
`anib_60027`（Conquerors 的 *petersen constants*，629 行）里 `civ-dark-rush / civ-dark / civ-castle / pop-cap / deathmatch-unit-max / unit-max / five…fifty-percent-pop / feudal|castle|imperial-town-size / town-center-count` **全部**只出现在这些块里；AoK 的 `anib_60010`（674 行，同样 25…200 八段）完全一样。

**证据 3 —— 死亡竞赛脚本对它们的依赖程度**（`dm_const_audit.py` → `dm_const_audit_out.txt`）：

| 数据集 | 只在 25…200 档位里定义、却被 DM 脚本使用的常量 | 在 `anib_60002` 里的使用次数 |
|---|---|---|
| gamedata_x1.drs（HD 默认，Conquerors） | `deathmatch-unit-max` | **56** |
| | `unit-max` | **56** |
| | `five-percent-pop` / `ten-percent-pop` / `fifteen-percent-pop` | 5 / 5 / 1 |
| | `civ-dark-rush` / `civ-castle` / `imperial-town-size` | 2 / 1 / 1 |
| gamedata.drs（Age of Kings） | 同上 8 个 | 39 / 39 / 5 / 4 / 1 / 2 / 1 / 1 |

AI 语言里**引用未定义常量的规则会被判为非法**（`AoK HD.exe` 的错误表里有 `ERR2012: Constant Already Defined`、`ERR2006 Missing file name` 等一整套编译错误码），于是：
* 所有"造兵"规则都被 `(population < deathmatch-unit-max)` 一句话废掉 → **不补兵**；
* 造房子规则用 `(house <= five/ten/fifteen-percent-pop)` → **不造房子**；
* `civ-dark-rush / civ-castle`（"该出多少农民/该升到城堡"判断）也没了 → **经济几乎不动**，你看到的就是"只剩一个农民在干活"。

这三个症状和你的描述完全一致，**根因 A/B/C 只是"次要死因"**：即使把 A/B/C 全部修好，只要人口上限是 500，脚本仍然不干活。

#### 根因 D 的更正（v2 证据，2026-09-26）

上面这段是 **v1 当时的推断，已被推翻**。用 `dm_popstr.py` 把引擎那个开关引用的符号字符串直接解出来（`dm_popstr_out.txt`）：

```
   0x0045c9a5  cmp eax, 0x96 (150)                  ; 大厅人口上限
   0x0045c9c5 -> 'POPULATION-CAP-25'    ...   0x0045c9e8 -> 'POPULATION-CAP-150'
   0x0045c9f6  cmp/je  == 300  -> 0x0045ca17 -> 'POPULATION-CAP-200'
   0x0045ca10  je      == 400  -> 0x0045ca17 -> 'POPULATION-CAP-200'
   0x0045ca12  sub eax, 0x64 (100)  0x0045ca15  jne -> 不定义任何符号
   0x0045ca17 -> 'POPULATION-CAP-200'          ; 上限 500 = 300+400+100 走到这里
```

也就是说 `POPULATION-CAP-500` 确实不存在，但引擎**不会**"什么都不定义"：**300 / 400 / 500 的上限都落到 `POPULATION-CAP-200`**。于是常量脚本被编译成 `pop-cap 200`、`unit-max 190`、`deathmatch-unit-max 170`、`five/ten/fifteen-percent-pop = 10/20/30`（`dm_sim.py --caps 500 --caps 200` 复算，`dm_sim_caps_out.txt`）——**所有 DM 规则都是合法的**，v1 的 catch-all（`#load-if-not-defined` × 8）永远不会被编译，纯属死代码。

结论：**"AI 只派一个农民在干活"不是常量未定义造成的**，而是：

* 出兵令牌 `(goal secondary-build 1)` 被 50 条造兵规则清 0 后只有"能造特色兵（要有城堡）"才重新上膛 → 造一两个兵就停（根因 A）；
* Hard / Hardest 下**一条造房规则都没有**（根因 B）→ 人口被开局房子锁死；
* 三条年龄规则（L1594/1614/1634）都包在 `(or (players-current-age every-human >= …) (difficulty <= moderate))` 里 → 没有人类玩家时 AI 永远停在黑暗时代（v2 的 A1-A3 就是去这个门槛）；
* 死亡竞赛脚本里没有任何 `(cc-add-resource …)` → 资源不会补充（根因 C）。

> 另一个连带结论：引擎既把 500 映射成 `POPULATION-CAP-200`，AI 心中的目标就永远是 **200 人口 / 170 兵**。v2 能让它真的把 170 兵造出来，但**不会**让它去填满 500 人口 —— 那是引擎给的常量上限，要改只能改常量脚本（见 §6 已知限制）。

---

## 2. v1 补丁内容 A（**已废弃**，当前生效的 v2 见 §2c）：往 `anib_60002` 末尾追加 4 条规则（1725 字节）

```lisp
;---- 1) 出兵循环永久上膛 --------------------------------------------------
(defrule
	(goal secondary-build 0)
=>
	(set-goal secondary-build 1)
)

;---- 2) 高难度也要造房子（原文只有 difficulty <= moderate 才有）----------
(defrule
	(or
		(difficulty == hard)
		(difficulty == hardest)
	)
	(housing-headroom < 10)
	(population-headroom > 0)
	(can-build house)
=>
	(build house)
)

;---- 3) 资源近似无限 ------------------------------------------------------
(defrule
	(true)
=>
	(enable-timer t-production 10)
	(disable-self)
)

(defrule
	(timer-triggered t-production)
	(or
		(food-amount < 5000)
		(wood-amount < 5000)
		(gold-amount < 5000)
		(stone-amount < 5000)
	)
=>
	(disable-timer t-production)
	(enable-timer t-production 5)
	(cc-add-resource food 10000)
	(cc-add-resource wood 10000)
	(cc-add-resource gold 10000)
	(cc-add-resource stone 10000)
)
```

设计要点 / 安全性说明：

* 用的全部是原文里存在的写法：`(goal/set-goal secondary-build)`、`(difficulty == hard|hardest)`、`(housing-headroom < n)`、`(population-headroom > 0)`、`(can-build house)`、`(build house)`、`(cc-add-resource <资源> <数量>)`、`(enable-timer/disable-timer/timer-triggered/disable-self)`。
* 计时器 3（`t-production`）在**所有** AI 脚本中只以符号形式出现：Conquerors 版 `anib_60001`（1 次）、`anib_60009`（45 次）、`anib_60027`（1 次，即 `(defconst t-production 3)`）、`anib_60029`（6 次）；Age of Kings 版同理（60001:1、60009:36、60027:1）。全库**没有任何脚本用数字写法** `(enable-timer 3 …)` / `(timer-triggered 3)`（`dm_timer3_check.py` 实测），而 DM 只加载 `anib_60027`（常量）+ map loads / diplomacy / supplement / groups / resign + `anib_60002`，**原始 `anib_60002` 里 timer 3 出现 0 次** —— 所以计时器 3 在死亡竞赛里是干净的、不会被别的规则抢占。
* **根因 A 的补丁不会导致超编**：被令牌门控的 50 条造兵规则**每一条都自带** `(population < deathmatch-unit-max)` 判断（`dm_scope.py` 输出："50 train something, 50 carry (population < ...), 50 use deathmatch-unit-max"），而 `deathmatch-unit-max` 是随大厅人口上限选定的常数（`anib_60027` 第 251-552 行：人口上限 25→13、50→25、75→55、100→70、125→95、150→120、175→145、200→170）。所以 AI 会一路造到该上限就自然停下，不会刷爆。
* 计时器 3（`t-production`）在**所有** AI 脚本中只出现在 `anib_60001`（1 次）、`anib_60009`（45 次）、`anib_60027`（只有 `defconst` 1 次）、`anib_60029`（6 次）—— 这 4 个文件都不是死亡竞赛加载的（DM 只加载 60027 常量 + map loads/diplomacy/supplement/groups/resign + 60002），所以计时器 3 在死亡竞赛里是干净的。
* 补丁 3 的 `(true)` 规则只在开局设一次计时器（`disable-self`），之后每 5 秒检查一次，只有真掉到 5000 以下才补 10000；资源高于 5000 时不做任何事。
* 补丁**不区分难度**：即使把 AI 设成 Easy 也会获得资源（原作只在 Hard/Hardest 给作弊资源）。想要"会打又无限"的对手，请在开局设置里把 AI 难度选 **Hard 或 Hardest**。

---

## 2b. v1 补丁内容 B（**已废弃 / v2 已删除**）：常量 catch-all（当时以为能修"根因 D"，改的是 `anib_60027` / `anib_60010`）

> ⚠ **v2 已删除这段**：500 的上限被引擎映射到 `POPULATION-CAP-200`（见 §1 末尾"根因 D 的更正"与 §2c），所以这个 `#load-if-not-defined` 八层块**永远不会被编译**；v2 的常量脚本与 pristine 逐字节相同。以下仅作历史记录。
>
> 当时的写法：在常量脚本**末尾**追加一段"兜底"块（`dm_patch.py` 自动生成，`#load-if-not-defined` 八层嵌套，和原作 `anib_60026` 第 34-50 行用的是同一种写法）：

```lisp
#load-if-not-defined POPULATION-CAP-25
#load-if-not-defined POPULATION-CAP-50
#load-if-not-defined POPULATION-CAP-75
#load-if-not-defined POPULATION-CAP-100
#load-if-not-defined POPULATION-CAP-125
#load-if-not-defined POPULATION-CAP-150
#load-if-not-defined POPULATION-CAP-175
#load-if-not-defined POPULATION-CAP-200
(defconst civ-dark-rush 50)          ; 复制自 POPULATION-CAP-200 段，数值 ×2.5
(defconst civ-dark 63)
(defconst civ-castle 175)
(defconst pop-cap 500)
(defconst deathmatch-unit-max 425)
(defconst feudal-town-size 20)       ; 城镇距离不改（不是人口比例量）
(defconst castle-town-size 35)
(defconst imperial-town-size 40)
(defconst town-center-count 9)
#load-if-defined DIFFICULTY-EASIEST
(defconst unit-max 325)              ; 原 130×2.5
#end-if
…（EASY 325 / MODERATE 400 / HARD 475 / HARDEST 475）
(defconst five-percent-pop 25)
(defconst ten-percent-pop 50)
(defconst fifteen-percent-pop 75)
(defconst twenty-percent-pop 100)
(defconst thirty-percent-pop 150)
(defconst fifty-percent-pop 250)
#end-if
#end-if
#end-if
#end-if
#end-if
#end-if
#end-if
#end-if
```

* **逻辑**：八个人口档位**全部不成立**（也就是大厅上限不是 25/50/…/200，例如 500）时，这段才被编译；只要命中任一标准档位就完全不编译 → **对 25…200 的老玩法零影响**（也不会出现 `Constant Already Defined`）。
* 数值直接把原作 **`POPULATION-CAP-200` 那一段（原作公认最平衡的档位）整体 ×2.5**（200→500），保持 AI 内部比例不变：`deathmatch-unit-max` 170→**425**、HARD/HARDEST 的 `unit-max` 190→**475**、`five-percent-pop` 10→25 …
* 只"不缩放"的有 4 个：`feudal/castle/imperial-town-size`（那是**地图距离**，不是人口比例）、`town-center-count`（原 9 个城镇中心已经够用，改大只会浪费）。
* 生成结果（`dm_verify_out.txt` 里能看到全文）：`anib_60027` 19383 → 21924 字节，`anib_60010` 14168 → 16587 字节；括号深度 0、`#load-if-not-defined` 8 个 / `#end-if` 8 个、CRLF、纯 ASCII。
* 覆盖性自动校验（`dm_patch.py` 里内置，失败会直接报错）：把"只在人口档位块里定义、又被本数据集 `anib_60002` 使用"的常量列出来（x1 是 8 个：`deathmatch-unit-max`/`unit-max`/`civ-dark-rush`/`civ-castle`/`five`/`ten`/`fifteen-percent-pop`/`imperial-town-size`），逐个确认 catch-all 里都有定义 → 输出 `cross-check … every population-cap constant it uses is covered`。
* 想换目标上限：改 `dm_patch.py` 里的 `CAP_TARGET`（现在 500，`SCALE = CAP_TARGET/200`）后跑 `python D:\aoe2_work\dm_rebuild.py`。
* 注意：catch-all 的数值是**按 500 调的**。如果你用 250/300/400 这类非标准上限，AI 会按 500 的目标（425 兵、250 个"半价"房子指标）去铺 → 会多造房子/更贪，但**不会再罢工**（比现在这种完全不干活好得多）。想精确适配告诉我，我按你的常用上限重算。


---

## 2c. v2 补丁（当前生效）：往 `anib_60002` 追加 14 条规则（5295 字节）

生成链：`dm_patch2.py`（**调参改这里**）→ `dm_apply2.py`（从 pristine 备份重建 DRS）→ `dm_install2.py`（备份 + 安装 + 逐条目校验）。原则：**永远从 `backup_drs\*.orig` 重建**，所以补丁不可能叠加；生成器里还有 `strip_v1()`，顺手清掉可能残留的 v1 块。

追加的规则**全部是原作规则的逐字复制**，只做"删门槛"这一件事：

| # | 作用 | 来源 |
|---|---|---|
| M1 | 开局 `(chat-to-all "DM AI fix v2 loaded [x1]")` —— 在游戏里证明这份脚本确实被编译执行了 | 新写，只用原作的 `true` / `chat-to-all` / `disable-self` |
| H1 | `(building-type-count-total house <= fifteen-percent-pop)` + `(can-build house)` → `(build house)` | 原作 L1675-1680，去掉 `(difficulty <= moderate)` |
| H2 | `(housing-headroom < 5)` + `(population-headroom > 0)` + `(can-build house)` → `(build house)` | 原作 L1694-1701（`DIFFICULTY-EASY` 块），去掉 `(military-population < civ-dark-rush)` |
| H3 | 同上 | 原作 L1683-1690（`DIFFICULTY-EASIEST` 块），去掉 `(military-population < 10)` |
| H4 | 计时器驱动的房子兜底：开局 30 s 后、之后每 20 s，自家房子 `< 40` 且 `(can-build house)` 就补一个 | 新写；40 房子 ×5 = 200 人口位，和这局引擎给的 `pop-cap 200` 对齐 |
| A1 | `(can-research feudal-age)` → `(research feudal-age)` + `(set-goal age-advancement NOTICE)` + `(enable-timer t-ageup 140)` | 原作 L1594-1604，去掉 `(or (players-current-age every-human >= feudal-age) (difficulty <= moderate))` |
| A2 | 城堡时代（`t-ageup 170`） | 原作 L1614-1624，同样去门槛 |
| A3 | 帝王时代（`t-ageup 200`） | 原作 L1634-1647，同样去门槛 |
| R1 | `(goal secondary-build 0)` → `(set-goal secondary-build 1)`：出兵令牌永久上膛 | §1 根因 A |
| S1 | 计时器驱动的资源兜底：开局 10 s 后、之后每 60 s，四种资源任一 `< 5000` 就各 `+10000` | 新写；动作 `(cc-add-resource <资源> <数量>)` 是原作写法（`anib_60001` / `anib_60029`） |

要点与安全依据：

* **每个 token 都要有出处（token attestation）**：`dm_patch2.py` 会把追加块里的每个符号、数字枚举拿到出货脚本（x1 / aok 的 `60001 60002 60003 60008 60010 60026 60027 60029`）+ `AoK HD.exe` 里查证后才写文件。本次结果：**36 个小写符号 + 大写枚举 `NOTICE` 全部有出处，0 个未取证**（`dm_patch2_console.txt` L19-58）。原因：这个 AI 方言里**未定义的符号会让整条规则静默失效**，所以"自己造一个名字"等于把规则删掉。
* **不新造计时器名**：DM 脚本里**没有任何 `(defconst …)`**，所有 `t-*` 名字都来自常量脚本 `anib_60027`（`t-tribute 1`、`t-attackgroup 2`、`t-production 3`、`t-ageup 10`…，见 `dm_tconst_out.txt`）。所以 v2 复用两个 DM 脚本全程不碰的零售名字：**H4 用 `t-tribute`（索引 1）**、**S1 用 `t-attackgroup`（索引 2）**（`anib_60001`/`anib_60002` 只用 3/5/6/8/9/10）。
* **不会超编**：50 条造兵规则每条都自带 `(population < deathmatch-unit-max)`，所以 AI 造到 170 就自然停。
* **不碰常量脚本**：`anib_60027` / `anib_60010` 与 pristine 逐字节相同（v1 的改动已被删除）。
* 仅剩的理论风险：H4 / S1 用的计时器 1、2 在所有 DM 脚本里都没人用，但**场景内置 AI** 若用到它们，会互相干扰；真要规避就得新造计时器名，而新名字在这个方言里是未定义符号（会静默丢规则），两害相权取其轻。

## 3. 改动的文件与验证

v2 **只改 AI 脚本**，每个档案 2 个条目：`anib_60002`（*petersen deathmatch*，追加 14 条规则）+ `anib_60001`（*petersen rules*，只加一条聊天标记）；**常量脚本 `anib_60027` / `anib_60010` 不再改动**（与 pristine 逐字节相同）。

| 文件 | pristine md5 | 安装后 md5（当前已安装） | 条目总数 | 变化 |
|---|---|---|---|---|
| `Data\gamedata.drs`（Age of Kings 数据） | `be574545e247b85a196109836a1f9d44` | `a41f82d4b599bcb7684092220caf1445` | 48 | anib_60002 45718 → **51014 B**（+5296）；anib_60001 28550 → **28855 B**（+305，仅标记） |
| `Data\gamedata_x1.drs`（Conquerors 数据，HD 默认） | `f41c418333e624b7a1077ad166f9dcb0` | `11754b64c226c711777e354cd2a7f4c9` | 76 | anib_60002 54203 → **59498 B**（+5295）；anib_60001 29337 → **29641 B**（+304，仅标记） |

静态验证（全部通过；日志：`dm_patch2_console.txt` / `dm_repack2_report.txt` / `dm_install2_report.txt` / `dm_dmcheck_out.txt` / `dm_sim_caps_out.txt`）：

* 追加块 **14 条规则、5295 字节**，括号配平（已正确处理 `;` 注释与 `"…"` 字符串里的分号），**没有残留任何 `difficulty` / 人类玩家门槛**。
* `anib_60002` 全文 `#load-if*/#if` 25 个 / `#end-if` 25 个、**EOF 处嵌套深度 0**（`dm_dmcheck.py` 实测）；追加块里没有 `#load-*`，不会新开分支 —— 即追加的规则一定在"会被编译"的位置。
* 追加位置在**逐字节相同的零售脚本前缀之后**（`retail lines=2884 live lines=3036 (+152)`、`prefix-ok=True`）。
* `dm_sim.py --caps 500 --caps 200` 复算常量脚本：这局引擎给的档位是 `POPULATION-CAP-200` → `pop-cap 200`、`unit-max 190`、`deathmatch-unit-max 170`、`five/ten/fifteen-percent-pop = 10/20/30` 全部有定义（H1 用到的 `fifteen-percent-pop` 就是 30）。

`Data\gamedata_x1_p1.drs`（HD 的 1.0c 补丁数据）里**没有任何 AI 脚本**（只有 `pls_*` 与 `anib_54228`），所以不需要改。


* 每个档案其余 46 / 74 个条目**逐字节相同**（`dm_apply2.py` 重建 DRS 时按原样搬运，`dm_install2.py` 逐条目比对 md5，只允许上面列出的条目变化）。
* 两个档案里都还有**一个同号但属于另一套数据集的常量文件**（`gamedata.drs` 里也有 60027、`gamedata_x1.drs` 里也有 60010），它们不是本数据集的 *petersen constants*（`dm_ai_names.py` 的结论），v2 **完全不碰它们**，依然逐字节一致。
* `dm_install2.py` 安装前会把 pristine 备份成 `backup_drs\*.orig`，安装后从游戏目录读回校验：`marker present`、条目清单只有上述 2 个不同，并确认 `live` 里**已经没有 v1 块**（本次实测：`live anib_60002 currently carries the v1 block: False`）。
* 打完补丁后从游戏目录读回的 `anib_60002` 尾部确实含有 §2c 的全部规则（`dm_block_dump_out.txt` / `dm_dmcheck_out.txt`），`anib_60001` 尾部确实只有那条标记规则（`base_block_dump_out.txt`）。
* 游戏目录里没有任何"游离"的 AI 脚本会覆盖 DRS（`AI\AI.txt` 只有 8 字节内容 `AI.txt` + CRLF，`AI\`、`mods\`、`Data\` 下都没有 `.per` / `.ai` 文件）。

### 3b. v1 的历史数字（**已废弃，仅供对照**）

v1 改了 4 个条目（每档案 2 个：`anib_60002` + 常量脚本），安装后是 `gamedata.drs` = `0504f9fcaed2a1b87dde1a6db04576e7`（anib_60002 45718→47443、anib_60010 14168→16587）、`gamedata_x1.drs` = `46ebe235b2c5099b01be545ec8ae0240`（anib_60002 54203→55928、anib_60027 19383→21924）。v1 的常量 catch-all 已确认是死代码，v2 已把它从游戏文件里删干净。

## 4. 文件清单（都在 `D:\aoe2_work`）

| 文件 | 用途 |
|---|---|
| `dm_patch.py` | **v1（已废弃）** 生成补丁文本（旧调参：阈值 5000、补充量 10000、房子余量 10、`CAP_TARGET` 500） |
| `drs_lib.py` | 通用 DRS 读写库（读表 → 重建档案，其它条目原样保留） |
| `dm_apply.py` | **v1** 把补丁打进 DRS（每个档案 2 个条目）→ `patched_drs\` |
| `dm_verify.py` | 4 个文件（2 个 DM 脚本 + 2 个常量脚本）的括号与预处理器配平自检 |
| `dm_install.py` | **v1** 备份 + 安装到游戏 + 逐条目 md5 校验（只允许 `anib_60002` + 常量条目变化） |
| `dm_rebuild.py` | **v1（已废弃）** 一键：生成 → 打包 → 自检 → 常量覆盖性审计 → 安装 |
| `dm_restore.py` + `restore_original_AI.cmd` | **还原原版**（把 `backup_drs\*.orig` 拷回游戏并校验 md5） |
| `patched_scripts\*.per` | **v1** 打补丁后的可读脚本（DM 脚本 2 份 + 常量脚本 2 份）；v2 的可读产物在 `patch_out2\*.bin` + `dm_block_dump_out.txt` |
| `dm_const_audit.py` | v1 时代的"常量覆盖性"证据（结论已被 §2c 更正：500 → `POPULATION-CAP-200`） |
| `dm_pop500.py` | 扫描全部 DRS AI 脚本，列出存在哪些 `POPULATION-CAP-*` 符号（最高只到 200） |
| `dm_popstr.py` | **v2 关键证据**：解出引擎 0x0045c900 开关 push 的符号字符串，看清"500 → `POPULATION-CAP-200`" |
| `dm_exe_ai.py` | 扫描 `AoK HD.exe`：引擎支持的符号表 / 预处理器关键字 / AI 错误码 |
| `dm_ai_names.py` | 对比各档案里的两个候选常量文件，确认哪个才是本数据集的 *petersen constants* |
| `dm_grep.py` | 小工具：给一个脚本文件按正则打印带行号的命中行 |
| `dm_marker_check.py` | 一键对比 backup / patched_drs / 游戏目录 三个状态（含补丁标记是否存在） |
| `dm_timer3_check.py` | 证明计时器 3 在所有脚本里只被符号引用、没有任何数字写法 |
| `dm_patch2.py` | **v2 生成器（调参改这里）**：`HOUSES_MAX` 40、房子计时器 30/20 s、资源计时器 10/60 s；自带 token 取证、括号/预处理器自检、v1 块清除 |
| `dm_apply2.py` | v2 打包：从 `backup_drs\*.orig` 重建 DRS → `patched_drs2\`（逐条目对比 + 零售前缀断言 + 往返校验） |
| `dm_install2.py` | v2 安装：备份 `*.orig` + 安装 + md5 + 标记 + 条目比对（只允许 60001 / 60002 变化） |
| `dump_block.py` | 把追加块 dump 成可读文本（`dm_block_dump_out.txt` / `base_block_dump_out.txt`） |
| `dm_dmcheck.py` | 从游戏目录读回自检：零售前缀是否逐字节保留、EOF 括号/预处理深度、追加部分全文 |
| `dm_sim.py` | 模拟引擎的符号集，解析常量脚本会被编译成什么值（`--caps 500 --caps 200`） |
| `dm_popstr.py` / `dm_p1check.py` | 引擎开关的符号字符串 / `gamedata_x1_p1.drs` 里没有 AI 脚本（v1 被推翻的两个关键证据） |
| 其它 `dm_*.py` + `*_out.txt` + `dm_*_report.txt` | 证据与日志 |

## 5. 还原 / 重装 / 调参

v1 的老链条（**已废弃**；其中 `dm_restore.py` 是当前仍然有用的还原脚本，`dm_marker_check.py` / `dm_const_audit.py` / `dm_finalcheck.py` 可当诊断工具看）：

```bat
python D:\aoe2_work\dm_restore.py         :: 还原原版 AI
python D:\aoe2_work\dm_rebuild.py         :: 重新生成并安装（改完 dm_patch.py 后使用）
python D:\aoe2_work\dm_marker_check.py    :: 看一眼 backup / patched_drs / 游戏目录 三份状态是否一致
python D:\aoe2_work\dm_const_audit.py     :: 重新输出"常量覆盖性"证据
python D:\aoe2_work\dm_finalcheck.py      :: 从游戏目录里把打补丁后的脚本尾部读出来核对
```

v2 的完整链条（一次跑完，任一步失败会直接报错退出）：

```bat
python D:\aoe2_work\dm_patch2.py                       :: 1) 生成 14 条规则 + 自检（token 取证 / 括号 / 预处理器 / v1 清除）
python D:\aoe2_work\dm_apply2.py                       :: 2) 从 backup_drs\*.orig 重建 DRS → patched_drs2\ + 逐条目对比
python D:\aoe2_work\dm_install2.py                     :: 3) 备份 + 安装到游戏 + md5 / 标记 / 条目校验
python D:\aoe2_work\dump_block.py                      :: 4) 把追加块 dump 出来人工核对
python D:\aoe2_work\dm_dmcheck.py                      :: 5) 从游戏目录读回自检（零售前缀 / EOF 深度 / 追加内容）
python D:\aoe2_work\dm_sim.py --caps 500 --caps 200    :: 6) 复算这局常量会被编译成什么值
```

调参速查（都在 `dm_patch2.py` 顶部）：

| 想改什么 | 改哪个 |
|---|---|
| 房子上限（房子数 × 5 = 人口位） | `HOUSES_MAX`（40） |
| 房子检查节奏 | `HOUSE_TIMER_TIME`（30 s）/ `HOUSE_TIMER_REPEAT`（20 s） |
| 资源阈值 / 每次补多少 | S1 规则里的 `< 5000` / `10000` |
| 资源检查节奏 | `RES_TIMER_TIME`（10 s）/ `RES_TIMER_REPEAT`（60 s） |
| 计时器名字 | `HOUSE_TIMER`（`t-tribute`）/ `RES_TIMER`（`t-attackgroup`） |

> v1 时代的调参项（`RES_THRESHOLD` / `RES_TOPUP` / `HOUSE_HEADROOM` / `CAP_TARGET`）属于 `dm_patch.py`，**已随 v1 废弃**，改它们不会影响当前游戏文件。

## 6. 注意事项

* 修改 `gamedata.drs` / `gamedata_x1.drs` 属于**改游戏数据文件**：单机、单机战役、与朋友约定同版本时可用；**HD 联机对战会校验数据一致性**，双方文件不同时可能无法进入或被识别为数据不匹配，请先还原再联机。
* 补丁只影响 **Deathmatch** 开局（只有死亡竞赛才会 `(load "petersen deathmatch")`），随机地图 / 帝王战等模式的行为完全不受影响。**唯一例外**是 `anib_60001`（基础 AI 脚本）里那条只说话的标记规则：任何用到该 AI 的局里它都会在开局说一句 `AI fix base loaded [...]`（无行为影响）。
* 我能做的验证只到静态与二进制层面（从 pristine 重建 DRS、逐条目 md5、括号 / 预处理器配平、token 取证、常量复算）。**实战效果需要你开一局死亡竞赛确认**：
  1. **按你这次的设置**：人口上限 **500**、AI 难度 **Hard / Hardest**、8 人 DM。预期：房子一路补到 ~40 个、农民铺开、时代升到帝王、兵种持续出到 **这局引擎给的上限 `deathmatch-unit-max` = 170**（因为 `pop-cap` = 200）、资源长期贴在 1 万以上。⚠ 这里有一条**引擎层面的天花板，和补丁无关**：500 的上限被引擎折成 `POPULATION-CAP-200`，所以 AI 心中的目标就是 **200 人口 / 170 兵** —— 它不会再罢工，但也不会去填满 500。想让它真用满 500，只能另做一版改常量脚本里 `POPULATION-CAP-200` 段的数值（那会同时影响正常的 200 人口 DM 局），需要就说。
  2. 想对比的话，再开一局人口上限 **200**：这局引擎给的档位本来就是 CAP-200，编译出的常量值与上面完全一样。
* 什么时候"看起来还是不动"？DM 开局经济要 1-2 分钟才铺开；先看**房子数量**和**农民数量**是否在涨，再看时代和兵。
* **运行时的最快自检（v2 新增，秒级）**：开局看聊天栏 ——
  * 出现 `DM AI fix v2 loaded [x1]` → 用的是 Conquerors 数据集（`gamedata_x1.drs`），且这份 DM 脚本**确实被引擎编译执行了**（M1 规则跑了）；
  * 出现 `DM AI fix v2 loaded [aok]` → 引擎读的是 Age of Kings 数据集（`gamedata.drs`）；
  * 出现 `AI fix base loaded [...]` → `anib_60001` 的标记也生效（任何用到该 AI 的模式都会说一次，属正常）；
  * 三条都没有 → 说明引擎根本没读这两个档案（MOD 覆盖 / 数据没重新加载），把游戏目录里 `Data\gamedata*.drs` 的 md5 发我，我对着 §3 的表核。
* 若聊天栏出现 HD 的 `AI Script Error`（会带**文件名 + 行号 + 玩家**，格式串就在 `AoK HD.exe` 里，见 `dm_exe_logs.py`）→ 把这三个字段发我，我按行号改。
* v2 已知限制：① H4 / S1 用的计时器 1、2 是复用的零售名字（场景内置 AI 可能也用）；② 500 / 400 / 300 的上限都被引擎折成 `POPULATION-CAP-200`，AI 的目标就是 200 人口 / 170 兵；③ 标记聊天在多人局里每个 AI 各说一次，设计如此。

