"""dm_readme_v3b.py -- polish pass after dm_readme_v3.py

 1. the v3 intro bullet of chapter 3 sits directly above the old v2 paragraph,
    so markdown would join the two lines - put a blank line between them;
 2. the four static-verification bullets of chapter 3 are v2 numbers; give them
    a header line so nobody reads them as the current state;
 3. if the rebuild chain of chapter 5 mentions dm_install2.py exactly once, add
    the verification commands that belong to the v3 chain behind it.
"""
import os

W = os.path.dirname(os.path.abspath(__file__))
PATH = os.path.join(W, "HD_DM_AI_PATCH_README.md")

CHAIN = [
    "",
    ":: v3 的验证链（每次重装都跑一遍，全部要 exit 0；dm_dialect.py 的控制组必须报 MATCH）",
    "python dm_patch2.py       :: 形状 + 符号校验并把载荷写到 patch_out2",
    "python dm_apply2.py       :: 从 backup_drs\\*.orig 重打包到 patched_drs2",
    "python dm_install2.py     :: 备份 + 安装 + 逐条目校验（拒绝旧版本块）",
    "python dm_v2hit.py        :: 载荷里不许再出现旧版本标记",
    "python dm_dialect.py      :: 用坏样本复现 Line 3021 + 审计已安装档案",
    "python dm_line3021.py     :: 括号 / 规则闭合 / 行号取证",
]

lines = open(PATH, "rb").read().decode("utf-8").split("\r\n")


def find1(needle, start=0):
    hits = [i for i, l in enumerate(lines) if needle in l and i >= start]
    assert len(hits) == 1, "anchor %r found %d time(s) after %d" % (needle, len(hits), start)
    return hits[0]


log = []

# 1. blank line between the v3 intro and the old v2 paragraph
j = find1("## 3. ")
assert lines[j + 2].startswith("* v3"), "the v3 intro is not at heading + 2"
if lines[j + 3].strip():
    lines[j + 3:j + 3] = [""]
    log.append("inserted a blank line after the v3 intro of chapter 3")

# 2. label the v2 verification bullets as history
i = find1("dm_patch2_console.txt", start=j + 1)
assert lines[i + 2].startswith("* "), "the bullet list is not at anchor + 2"
lines[i + 2:i + 2] = ["* 下面 4 条是 **v2** 当时的实测数字（留作历史；v3 的数字见本节末尾 3 条）：", ""]
log.append("labelled the v2 verification bullets as history")

# 3. the v3 verification chain in chapter 5
try:
    i = find1("dm_install2.py     :: ")
except AssertionError:
    log.append("skipped the chapter 5 chain (no unique anchor)")
else:
    lines[i + 1:i + 1] = CHAIN
    log.append("added the v3 verification chain to chapter 5")

open(PATH, "wb").write("\r\n".join(lines).encode("utf-8"))
print("README is now %d lines" % len(lines))
for s in log:
    print("  * %s" % s)
