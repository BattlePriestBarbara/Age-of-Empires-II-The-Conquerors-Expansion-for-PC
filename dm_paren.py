"""Find where an AI script's paren depth drifts (depth should be 0 at every top-level (defrule)."""
import os
import sys

W = os.path.dirname(os.path.abspath(__file__))
path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(W, "x1_drs", "anib_60002.bin")
rows = open(path, encoding="latin-1").read().split("\n")
depth = 0
prev = 0
out = []
for i, r in enumerate(rows, 1):
    code = r.split(";")[0]
    stripped = r.strip()
    if stripped.startswith("(defrule") and depth != 0:
        out.append("### %s line %d: (defrule) opened while depth=%d (prev rule ended at %d)" % (path, i, depth, prev))
        out.append("    context:")
        for j in range(max(0, i - 6), min(len(rows), i + 1)):
            out.append("      %5d| %s" % (j + 1, rows[j].rstrip("\r")))
        prev = depth
    for ch in code:
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
out.append("final depth = %d" % depth)
open(os.path.join(W, "dm_paren_out.txt"), "w", encoding="utf-8").write("\n".join(out) + "\n")
print("\n".join(out[:80]))
