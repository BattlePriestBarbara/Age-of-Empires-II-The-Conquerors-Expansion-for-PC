"""dm_readme_v3c.py -- last polish pass of the README

 1. the four marker bullets inserted by dm_readme_v3.py are sub bullets of the
    "runtime self test" item, so they need the two space indent of their
    siblings (the first two siblings are already indented that way); the third
    of them is rewritten, because the file already explains AI Script Error two
    lines further down;
 2. the rebuild chain of chapter 5 gets the v3 verification steps.
"""
import os

W = os.path.dirname(os.path.abspath(__file__))
PATH = os.path.join(W, "HD_DM_AI_PATCH_README.md")
lines = open(PATH, "rb").read().decode("utf-8").split("\r\n")


def find1(needle, start=0):
    hits = [i for i, l in enumerate(lines) if needle in l and i >= start]
    assert len(hits) == 1, "anchor %r found %d time(s) after %d" % (needle, len(hits), start)
    return hits[0]


log = []

# ---- 1. indent (and fix) the four marker bullets ---------------------------
j6 = find1("## 6. ")
i = find1("DM AI fix v3 loaded [x1]", start=j6)
assert lines[i].startswith("* ") and lines[i + 1].startswith("* "), \
    "the marker bullets are not where they were"
assert "DM AI fix v3 loaded [aok]" in lines[i + 1]
lines[i + 3] = ("  * v3 的工具能直接按行号定位：`dm_dialect.py`（用坏样本复现引擎报错行）+ "
                "`dm_line3021.py`（括号 / 规则闭合 / 行号取证）—— 把 `File` / `Line` / `Player` 发我即可；")
for k in range(i, i + 4):
    if not lines[k].startswith("  "):
        lines[k] = "  " + lines[k]
log.append("indented the 4 marker bullets as sub bullets of the self test item")

# the item label above them should say v3, not v2
lines[i - 1] = "* **运行时的最快自检（v3 标记，秒级）**：开局看聊天栏 ——"
log.append("relabelled the runtime self test item")

# ---- 2. the v3 verification steps in the chapter 5 chain -------------------
j5 = find1("## 5. ")
anchor = find1("dm_patch2.py                       :: 1)", start=j5)
fence = anchor - 1
assert lines[fence].strip() == "```bat", "the chain fence is not at anchor - 1"
label = fence - 1                                  # skip blank lines upwards
while label > 0 and lines[label].strip() == "":
    label -= 1
assert lines[label].startswith("v2 "), "the chain label was not found"
lines[label] = "v3 的完整链条（含 v2 的全部步骤；一次跑完，任一步失败会直接报错退出）："
last = find1("dm_sim.py --caps 500 --caps 200", start=j5)
lines[last + 1:last + 1] = [
    "python dm_v2hit.py                        :: 7) 载荷里不许再出现旧版本标记",
    "python dm_dialect.py                      :: 8) 用坏样本复现引擎报错行 + 审计已安装档案",
    "python dm_line3021.py                     :: 9) 括号 / 规则闭合 / 行号取证",
    "python dm_blockshape.py                   :: 10)（可选）重出形状普查证据",
]
log.append("added steps 7-10 to the rebuild chain")

open(PATH, "wb").write("\r\n".join(lines).encode("utf-8"))
print("README is now %d lines" % len(lines))
for s in log:
    print("  * %s" % s)
