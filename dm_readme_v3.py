"""dm_readme_v3.py -- add the v3 chapter and refresh the numbers in the README.

Design notes:
  * line based, CRLF preserved byte for byte (the file must stay pure CRLF and
    UTF-8 without BOM - the v2 README was written the same way);
  * every anchor is pure ASCII and must occur exactly once, so the script cannot
    hit the wrong place and fails loudly instead;
  * Chinese is only ever written, never used as an anchor.
"""
import os

W = os.path.dirname(os.path.abspath(__file__))
PATH = os.path.join(W, "HD_DM_AI_PATCH_README.md")

# the pristine backup md5s must still be in the table - the script refuses to
# touch a README that describes a different base
PRISTINE = ("be574545e247b85a196109836a1f9d44",          # gamedata.drs
            "f41c418333e624b7a1077ad166f9dcb0")          # gamedata_x1.drs

V3_CHAPTER = [
    "## 2d. v3 补丁（**当前生效**）：修掉 v2 唯一的硬报错 ERR2011",
    "",
    "你在 Hard / Hardest + 人口 500 的死亡竞赛里看到的弹窗：",
    "",
    "```",
    "AI Script Error",
    "Player 8",
    "File  petersen deathmatch per",
    "Line 3021: ERR2011: Missing closing parenthesis",
    "```",
    "",
    "这**不是**\"少打一个右括号\"：整份脚本的括号是配平的（`dm_patch2.py` 与 `dm_dialect.py` 都验证 depth = 0，"
    "且没有一行的深度会掉到负数）。真正的原因是**引擎给每个逻辑块（`or` / `and` / `nor` / `not`）只有两个参数槽**。"
    "这不是猜的，而是把全游戏 AI 脚本做了一遍形状普查得出的（`dm_blockshape.py`）：",
    "",
    "| 脚本 | 逻辑块按子节点数的分布 |",
    "|---|---|",
    "| `gamedata_x1.drs` → `anib_60002`（死亡竞赛） | `{1: 31, 2: 181}` |",
    "| `gamedata_x1.drs` → `anib_60003` | `{1: 31, 2: 159}` |",
    "| `gamedata_x1.drs` → `anib_60029` | `{1: 9, 2: 113}` |",
    "| `gamedata_x1.drs` → `anib_60010` | `{1: 5, 2: 4}` |",
    "| `gamedata.drs` → `anib_60002`（AoK 死亡竞赛） | `{1: 27, 2: 154}` |",
    "| `gamedata.drs` → `anib_60003` | `{1: 16, 2: 122}` |",
    "",
    "**这些脚本里 800 多个逻辑块没有一个超过 2 个子节点**。原作要表达\"三个以上条件\"时用的是**嵌套两个子块的 `or`**，"
    "而死亡竞赛脚本**自己**就有现成样板（第 1511-1523 行与 1533-1542 行的\"资源偏低\"判断）：",
    "",
    "```perl",
    "(defrule",
    "\t(strategic-number sn-percent-civilian-gatherers == 85)",
    "\t(or",
    "\t\t(or",
    "\t\t\t(wood-amount < 500)",
    "\t\t\t(food-amount < 500)",
    "\t\t)",
    "\t\t(or",
    "\t\t\t(gold-amount < 500)",
    "\t\t\t(stone-amount < 100)",
    "\t\t)",
    "\t)",
    "=>",
    "```",
    "",
    "而 v2 的 S1 资源兜底规则把同一个判断写成了**一个 `or` 带 4 个子节点**：",
    "",
    "```perl",
    "(defrule",
    "\t(timer-triggered t-attackgroup)",
    "\t(or",
    "\t\t(wood-amount < 5000)",

    "\t\t(food-amount < 5000)",
    "\t\t(gold-amount < 5000)      ; <- 第 3 个子节点，引擎就在这一行报 ERR2011",
    "\t\t(stone-amount < 5000)",
    "\t)",
    "=>",
    "```",
    "",
    "解析器读完前 2 个子节点就想要 `)`，结果撞上第 3 个子节点，于是**把第 3 个子节点所在的行号报成\"缺右括号\"**：`Line 3021`。"
    "行号精确对得上：`gamedata_x1.drs` 里的零售脚本共 2883 行，v2 追加块的第 138 行 = 全局第 **3021** 行 = `(gold-amount < 5000)`。",
    "",
    "这段坏样本已按字节保存为 `dm_block_v2_broken_fixture.txt` 作**回归基准**：`dm_dialect.py` 每次运行都会把它接在 2883 行"
    "零售行之后重跑一遍模型，必须报出 `blames the child at line 3021`（实测 MATCH）—— 这就是\"模型成立\"的证明。",
    "",
]



V3_CHAPTER += [
    "### v3 的修法：照抄原作的双子节点嵌套",
    "",
    "```perl",
    "(defrule",
    "\t(timer-triggered t-attackgroup)",
    "\t(or",
    "\t\t(or",
    "\t\t\t(wood-amount < 5000)",
    "\t\t\t(food-amount < 5000)",
    "\t\t)",
    "\t\t(or",
    "\t\t\t(gold-amount < 5000)",
    "\t\t\t(stone-amount < 5000)",
    "\t\t)",
    "\t)",
    "=>",
    "\t(cc-add-resource wood 10000)",
    "\t(cc-add-resource food 10000)",
    "\t(cc-add-resource gold 10000)",
    "\t(cc-add-resource stone 10000)",
    ")",
    "```",
    "",
    "语义完全不变（任一资源偏低就四样各补 10000），形状与原作 1533-1542 行逐层同构：",
    "外层 `(or (or ...) (or ...))`、内层 `(or <事实> <事实>)`。",
    "",
    "### 新增两条\"形状\"硬校验（让同类错误不可能再溜过去）",
    "",
    "`dm_patch2.py` 在写文件之前会断言下面两条，不通过就直接报错、不生成文件：",
    "",
    "| 规则 | 内容 | v3 实测 |",
    "|---|---|---|",
    "| rule 1 | 任何逻辑块最多 2 个子节点 | 追加块 `{2: 3}`（3 个块，各 2 个子节点） |",
    "| rule 2 | 每个\"块形状\"与每个\"事实参数个数\"都必须在原作脚本里有出处 | 块形状 2 种均有出处：`(or or or)` ← 原作 L1514，`(or <fact> <fact>)` ← 原作 L495；22 种事实也全部有出处 |",
    "",
    "唯一一条有记录的例外是 M1 的 `chat-to-all`（1 个参数）：原作只用本地化写法 `chat-to-all-using-id`，所以没有脚本能给"
    "出处。它被显式写进代码里的 `SHAPE_EXCEPTIONS` 并注明理由（引擎自带 `ERR2010: Missing closing quote`，说明它确实能 lex "
    "字符串字面量；而且 v2 那次报错行是 3021，比 M1 所在的约 2890 行更靠后，说明 M1 没被引擎判错）。",
    "",
    "顺手还修掉**自己工具里的一个坑**：`code_only()` 原先\"先删字符串、再删注释\"，于是注释里的引号（原作注释就写着 "
    "`\"(difficulty <= moderate)\"`）会和几行之后的引号配对，把中间所有换行整段吞掉、行号整体偏移一行 —— 正是这个 bug 让 "
    "第一版校验器把 3021 报成 3020。现在改成**逐行**处理，行数不可能再变。",
    "",
    "### v3 的数字",
    "",
    "* 追加块 5295 → **5868 字节**（x1）/ **5869 字节**（aok，tag 多 1 字节），仍是 **14 条规则**；"
    "`gamedata_x1.drs` 的 `anib_60002` 54203 → **60071 B**，`gamedata.drs` 的 45718 → **51587 B**。",
    "* 开局聊天自检标记改成 **`DM AI fix v3 loaded [x1]` / `[aok]`**：看到 `v2` 说明游戏读到的还是旧的坏文件；"
    "`AI fix base loaded [...]`（`anib_60001`）不变。",
    "* 零售脚本依旧**逐字节**是补丁脚本的前缀；两个档案各只有 2 个条目变化。",
    "",
    "### v3 的静态验证结果",
    "",
    "| 检查 | 命令 | 结果 |",
    "|---|---|---|",
    "| 回归基准复现引擎报错行 | `python dm_dialect.py` | `(or ...) has 4 children ... blames the child at line 3021`，与引擎报的 `Line 3021` **MATCH** |",
    "| 已安装档案形状审计 | `python dm_dialect.py` | x1: 3046 行 / 257 规则 / 块分布 `{1: 31, 2: 184}` / EOF depth 0；aok: 2607 行 / 226 规则 / `{1: 27, 2: 157}` / EOF depth 0；追加块 `{2: 3}`；**无任何未取证的形状或参数个数** |",
    "| 括号与行号取证 | `python dm_line3021.py` | 两个档案 `final depth=0`、`negative depth: none`、无\"规则未闭合\"；x1 第 3021 行现在只是普通动作行 `(disable-self)` |",
    "| 标记文本干净 | `python dm_v2hit.py` | 新载荷里 `AI FIX V2` / `HD DEATH-MATCH AI PATCH` 出现次数 = 0（v2 的注释曾引用旧标记，已改写） |",
    "| 预处理器嵌套 | `python dm_dmcheck.py` | x1 25 开 / 25 关，aok 21 开 / 21 关，EOF depth 0；`prefix-ok=True`，`retail lines=2884 live lines=3047 (+163)` |",
    "| 重打包可复现 | `dm_patch2.py` + `dm_apply2.py` 连跑 3 次 | `gamedata_x1.drs` md5 恒为 `de096260b6140e3842ae0817b9e62e9f`，`gamedata.drs` 恒为 `2159dca1867a42c689bb4dc01ba771c0` |",
    "",
]
V3_VERIFY_BULLETS = [
    "* v3 追加块 **14 条规则 / 5868 字节**，14 条规则全部闭合，`(defrule` 之前深度必为 0（`dm_dialect.py`）。",
    "* v3 形状审计：追加块逻辑块子节点数 `{2: 3}`，最深块 4 个叶事实（原作最深 7 个），既没超槽也没超深度。",
    "* v3 的 `anib_60001` 只多一条聊天标记（29337 → 29641 B / 28550 → 28855 B），与 v2 相同。",
]

NEW_FILE_ROWS = [
    "| `dm_line3021.py` | **v3 取证工具**：给定\"文件 + 行号\"弹窗，算出该行落在零售前缀还是追加块，并逐规则检查闭合与负深度 |",
    "| `dm_blockshape.py` | **v3 关键证据**：全脚本逻辑块形状普查（子节点数 / 叶事实数 / 嵌套深度 / 形状清单） |",
    "| `dm_dialect.py` | **v3 回归 + 审计**：用坏样本复现引擎的 `Line 3021`，再审计游戏目录里已安装的两个档案 |",
    "| `dm_v2hit.py` | **v3 卫生检查**：确认新载荷里不再出现旧版本标记（否则 `strip_v1()` 会在错误位置切断脚本） |",
    "| `dm_block_v2_broken_fixture.txt` | **v3 回归基准**：v2 追加块的字节备份（5295 B），`dm_dialect.py` 的控制组输入 |",
]

MD5_ROWS = {
    "be574545e247b85a196109836a1f9d44":
        r"| `Data\gamedata.drs`（Age of Kings 数据） | `be574545e247b85a196109836a1f9d44` | "
        r"`bc3ae18a686cbd6b1804ecaa9e72d589` | 48 | anib_60002 45718 → **51587 B**（+5869）；"
        r"anib_60001 28550 → **28855 B**（+305，仅标记） |",
    "f41c418333e624b7a1077ad166f9dcb0":
        r"| `Data\gamedata_x1.drs`（Conquerors 数据，HD 默认） | `f41c418333e624b7a1077ad166f9dcb0` | "
        r"`59ca9130ce14f649a52d47f64b1357b3` | 76 | anib_60002 54203 → **60071 B**（+5868）；"
        r"anib_60001 29337 → **29641 B**（+304，仅标记） |",
}

V3_INTRO = ("* v3（**当前生效**）：唯一的行为改动是把 S1 的资源判断从\"一个 `or` 带 4 个子节点\"改成原作的"
            "双子节点嵌套写法，原因是引擎每个逻辑块只有两个参数槽 —— 详见 §2d；v3 追加块 5868 B，"
            "安装后的 md5 见下表。")

V3_MARKERS = [
    "* 出现 `DM AI fix v3 loaded [x1]` → 用的是 Conquerors 数据集（`gamedata_x1.drs`），且这份 DM 脚本**确实被引擎编译执行了**（M1 规则跑了）；",
    "* 出现 `DM AI fix v3 loaded [aok]` → 引擎读的是 Age of Kings 数据集（`gamedata.drs`）；",
    "* **若这里显示的是 `v2`**，说明游戏读到的还是旧的坏文件（它会在第 3021 行报 ERR2011），把 `Data\\gamedata*.drs` 的 md5 发我对着 §3 表核；",
    "* 若再出现 `AI Script Error`：把 `File` / `Line` / `Player` 三个字段发我 —— 现在 `dm_dialect.py` + `dm_line3021.py` 能直接从行号定位到具体构造（v2 那次就是靠行号 3021 定位到\"一个 `or` 带 4 个子节点\"）；",
]


def load():
    raw = open(PATH, "rb").read()
    assert not raw.startswith(b"\xef\xbb\xbf"), "the README has a BOM"
    text = raw.decode("utf-8")
    assert text.count("\n") == text.count("\r\n"), "the README is not pure CRLF"
    return text.split("\r\n")


def save(lines):
    open(PATH, "wb").write("\r\n".join(lines).encode("utf-8"))


def find1(lines, needle):
    hits = [i for i, line in enumerate(lines) if needle in line]
    assert len(hits) == 1, "anchor %r found %d time(s)" % (needle, len(hits))
    return hits[0]


def main():
    lines = load()
    before = len(lines)
    log = []

    for md5sum in PRISTINE:
        find1(lines, md5sum)                      # the README base is unchanged
    assert not any(l.startswith("## 2d.") for l in lines), \
        "chapter 2d is already in the README - refusing to insert it twice"

    # 1. the v2 chapter is history now
    i = find1(lines, "## 2c. v2 ")
    lines[i] = ("## 2c. v2 补丁（**已被 §2d 的 v3 取代**，此处留作历史）："
                "往 `anib_60002` 追加 14 条规则（5295 字节）")
    log.append("marked chapter 2c as superseded")

    # 2. insert the v3 chapter in front of chapter 3
    j = find1(lines, "## 3. ")
    lines[j:j] = V3_CHAPTER
    log.append("inserted chapter 2d (%d lines)" % len(V3_CHAPTER))

    # 3. refresh the installed md5 / size rows of chapter 3
    for md5sum, row in MD5_ROWS.items():
        lines[find1(lines, md5sum)] = row
    log.append("updated the md5 table of chapter 3")

    # 4. one v3 line right behind the chapter 3 intro paragraph
    j = find1(lines, "## 3. ")
    assert lines[j + 2].startswith("v2 "), "chapter 3 intro is not where it was"
    lines[j + 2:j + 2] = [V3_INTRO]
    log.append("added the v3 intro line of chapter 3")

    # 5. v3 bullets at the end of the chapter 3 verification list
    j = find1(lines, "### 3b.")
    lines[j:j] = V3_VERIFY_BULLETS + [""]
    log.append("added the v3 verification bullets")

    # 6. chapter 3b now covers the whole history
    i = find1(lines, "### 3b.")
    lines[i] = "### 3b. v1 / v2 的历史数字（**已废弃，仅供对照**）"
    log.append("renamed the history chapter")

    # 7. the new tools in the file list of chapter 4
    i = find1(lines, "| `dm_marker_check.py` |")
    lines[i + 1:i + 1] = NEW_FILE_ROWS
    log.append("added %d rows to the file list" % len(NEW_FILE_ROWS))

    # 8. runtime self test: v3 markers instead of the v2 ones.  The anchors
    #    carry the closing backtick so that the table row of chapter 2c (which
    #    quotes the old chat text inside a code span) cannot be hit.
    i = find1(lines, "fix v2 loaded [x1]`")
    j = find1(lines, "fix v2 loaded [aok]`")
    lo, hi = min(i, j), max(i, j)
    assert hi == lo + 1, "the two v2 marker bullets are not adjacent any more"
    lines = lines[:lo] + V3_MARKERS + lines[hi + 1:]
    log.append("rewrote the runtime marker bullets")

    save(lines)
    print("README %d -> %d lines" % (before, len(load())))
    for s in log:
        print("  * %s" % s)


if __name__ == "__main__":
    main()
