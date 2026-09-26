"""dm_orstyle.py -- how does the shipped death-match script write logical
blocks such as (or ...), (and ...), (not ...)?

If every retail line is parenthesetically self-contained (delta 0) except
"(defrule" (+1) and the rule's final ")" (-1), then the engine's condition
parser expects a *line* to be a complete expression and a multi-line "(or"
block is what ERR2011 "Missing closing parenthesis" objects to.
"""
import os
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from drs_lib import Drs

W = os.path.dirname(os.path.abspath(__file__))
GAME = os.environ.get("AOE2HD_DIR") or (r"D:\新建文件夹 (10)\3DMGAME_Age_of_Empires_II_HD.CHS.Green"
        r"\Age of Empires II HD")
BACKUP = os.path.join(W, "backup_drs")

SRC = [
    ("x1 anib_60002 death match", os.path.join(BACKUP, "gamedata_x1.drs.orig"), 60002),
    ("x1 anib_60027 constants", os.path.join(BACKUP, "gamedata_x1.drs.orig"), 60027),
    ("x1 anib_60003", os.path.join(BACKUP, "gamedata_x1.drs.orig"), 60003),
    ("x1 anib_60029", os.path.join(BACKUP, "gamedata_x1.drs.orig"), 60029),
    ("x1 anib_60010", os.path.join(BACKUP, "gamedata_x1.drs.orig"), 60010),
    ("x1 anib_60008", os.path.join(BACKUP, "gamedata_x1.drs.orig"), 60008),
    ("aok anib_60002 death match", os.path.join(BACKUP, "gamedata.drs.orig"), 60002),
]


def strip_code(line):
    out, in_str = [], False
    for ch in line:
        if ch == '"':
            in_str = not in_str
            continue
        if in_str:
            continue
        if ch == ";":
            break
        out.append(ch)
    return "".join(out)


out = []
for label, path, eid in SRC:
    text = Drs(path).payload(b"anib", eid).decode("latin-1")
    rows = text.split("\n")
    if rows and rows[-1] == "":
        rows = rows[:-1]
    hist = Counter()
    odd = []
    for i, raw in enumerate(rows, 1):
        code = strip_code(raw)
        d = code.count("(") - code.count(")")
        hist[d] += 1
        if d != 0:
            odd.append((i, d, raw.rstrip("\r")))
    out.append("")
    out.append("=" * 92)
    out.append("=== %s   lines=%d" % (label, len(rows)))
    out.append("    delta histogram (delta = #'(' - #')' on the line): %s"
               % dict(sorted(hist.items())))
    # classify the nonzero deltas
    kinds = Counter()
    for i, d, raw in odd:
        s = raw.strip()
        if s.lower().startswith("(defrule"):
            kinds["(defrule (+1)"] += 1
        elif s == ")":
            kinds[") alone (-1)"] += 1
        else:
            kinds["OTHER delta %+d" % d] += 1
    for k, v in kinds.items():
        out.append("      %-22s %d" % (k, v))
    others = [(i, d, raw) for i, d, raw in odd
              if not raw.strip().lower().startswith("(defrule") and raw.strip() != ")"]
    for i, d, raw in others[:40]:
        out.append("      OTHER %5d delta %+d | %s" % (i, d, raw[:96]))

txt = "\n".join(out)
open(os.path.join(W, "dm_orstyle_out.txt"), "w", encoding="utf-8").write(txt + "\n")
print(txt)
