"""dm_dmcheck.py -- show the preprocessor nesting of the death-match script
around the rules we appended (patch A) and at EOF.

Hypothesis under test: patch A's rules were appended *inside* a
#load-if-defined block that is false at 500 pop, so they never compile.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from drs_lib import Drs

GAME = os.environ.get("AOE2HD_DIR") or (r"D:\新建文件夹 (10)\3DMGAME_Age_of_Empires_II_HD.CHS.Green"
        r"\Age of Empires II HD")
BACKUP = os.path.join(os.path.dirname(os.path.abspath(__file__)), r"backup_drs")

out = []


def walk(label, text):
    out.append("\n" + "=" * 92)
    out.append("%s   (%d lines)" % (label, len(text.split("\n"))))
    stack, lines = [], text.split("\n")
    for i, raw in enumerate(lines, 1):
        s = raw.strip()
        m = re.match(r"#(load-if-defined|load-if-not-defined)\s+(\S+)", s, re.I)
        if m:
            stack.append((m.group(1), m.group(2), i))
            continue
        if re.match(r"#end-if", s, re.I):
            if stack:
                stack.pop()
            continue
        if s.startswith("#else"):
            continue
    out.append("  nesting depth at EOF = %d" % len(stack))
    for kind, sym, i in stack:
        out.append("     !! still open: line %d  #%s %s" % (i, kind, sym))
    return lines


LIVE = [("LIVE x1  anib_60002 (DM script, patched)",
         os.path.join(GAME, "Data", "gamedata_x1.drs"), 60002),
        ("RETAIL x1 anib_60002 (DM script)",
         os.path.join(BACKUP, "gamedata_x1.drs.orig"), 60002),
        ("LIVE aok anib_60002 (DM script?, patched)",
         os.path.join(GAME, "Data", "gamedata.drs"), 60002),
        ("RETAIL aok anib_60002",
         os.path.join(BACKUP, "gamedata.drs.orig"), 60002)]

for label, path, eid in LIVE:
    text = Drs(path).payload(b"anib", eid).decode("latin-1")
    lines = walk(label, text)
    ret = Drs(os.path.join(BACKUP,
                           os.path.basename(path).replace(".orig", "") + ".orig")
              ).payload(b"anib", eid).decode("latin-1").split("\n")
    n = len(ret)
    out.append("  retail lines=%d live lines=%d (+%d)  prefix-ok=%s"
               % (n, len(lines), len(lines) - n,
                  "\n".join(lines).startswith("\n".join(ret[:2000]))))
    out.append("  --- last 8 retail lines ---")
    for i, l in enumerate(ret[-8:], n - 7):
        out.append("   r%5d| %s" % (i, l.replace("\r", "")))
    out.append("  --- live lines %d..%d (the appended part) ---"
               % (n, min(n + 60, len(lines))))
    for i, l in enumerate(lines[n - 1:min(n + 60, len(lines))], n):
        out.append("   l%5d| %s" % (i, l.replace("\r", "")))

open("dm_dmcheck_out.txt", "w", encoding="utf-8").write("\n".join(out))
print("wrote dm_dmcheck_out.txt")
