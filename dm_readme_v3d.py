"""dm_readme_v3d.py -- relabel the last bullet of chapter 6 (v2 -> v3)

The known limits are properties of the *current* build, not of v2.  The line is
found positionally (last non blank line) and verified by an ASCII probe, so no
Chinese text has to be reproduced as an anchor.
"""
import os

PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), r"HD_DM_AI_PATCH_README.md")
lines = open(PATH, "rb").read().decode("utf-8").split("\r\n")

k = len(lines) - 1
while k >= 0 and lines[k].strip() == "":
    k -= 1
assert "H4 / S1" in lines[k], "the last bullet is not the known-limits bullet"
print("old: %s" % lines[k][:60])
lines[k] = ("* v3 已知限制：① H4 / S1 复用了零售计时器名 `t-tribute`(1) / `t-attackgroup`(2) —— "
            "所有 DM 脚本都没人用它们，但**场景内置 AI** 可能用；② 500 / 400 / 300 的人口上限都被引擎折成 "
            "`POPULATION-CAP-200`，所以 AI 的目标是 200 人口 / 170 兵；③ 标记聊天在多人局里每个 AI 各说一次，设计如此；"
            "④ 每局开始后会打印 `DM AI fix v3 loaded [...]`，如果看到的仍是 `v2`，说明用的是旧文件。")
open(PATH, "wb").write("\r\n".join(lines).encode("utf-8"))
print("new: %s" % lines[k][:60])
