"""Where is secondary-build used *outside* the per-civ dice/unit blocks?"""
import os
import re

W = os.path.dirname(os.path.abspath(__file__))
out = []
for d, civnames in (("x1_drs", 18), ("aok_drs", 13)):
    f = "anib_60002.bin"
    rows = [x.rstrip("\r") for x in open(os.path.join(W, d, f), "rb").read().decode("latin-1").split("\n")]
    # mark civ-block ranges
    stack = []
    blocks = []
    for i, r in enumerate(rows):
        s = r.strip()
        if s.startswith("#load-if-defined") and s.endswith("-CIV"):
            stack.append(i)
        elif s.startswith("#end-if") and stack:
            blocks.append((stack.pop(), i))
    inside = [False] * len(rows)
    for a, b in blocks:
        for i in range(a, b + 1):
            inside[i] = True
    out.append("### %s/%s : %d civ blocks, %d lines" % (d, f, len(blocks), len(rows)))
    cond_in = sum(1 for i, x in enumerate(rows) if inside[i] and re.search(r"\(\s*goal\s+secondary-build\s+1", x))
    cond_out = [i for i, x in enumerate(rows) if not inside[i] and re.search(r"\(\s*goal\s+secondary-build", x)]
    act_in = sum(1 for i, x in enumerate(rows) if inside[i] and re.search(r"\(\s*set-goal\s+secondary-build", x))
    act_out = [i for i, x in enumerate(rows) if not inside[i] and re.search(r"\(\s*set-goal\s+secondary-build", x)]
    out.append("  civ blocks      : (goal secondary-build ..) conditions = %d,  (set-goal secondary-build ..) actions = %d"
               % (cond_in, act_in))
    out.append("  outside blocks  : conditions at %s" % [i + 1 for i in cond_out])
    out.append("  outside blocks  : actions at %s" % [i + 1 for i in act_out])
    for i in cond_out + act_out:
        a = i
        while a > 0 and "(defrule" not in rows[a]:
            a -= 1
        b = i
        while b < len(rows) - 1 and rows[b].strip() != ")":
            b += 1
        out.append("  --- enclosing rule lines %d-%d ---" % (a + 1, b + 1))
        for j in range(a, min(b + 1, a + 24)):
            out.append("  %6d| %s" % (j + 1, rows[j].strip()))
    out.append("")
open(os.path.join(W, "dm_sb_summary_out.txt"), "w", encoding="utf-8").write("\n".join(out))
print("ok", len(out))
