"""dm_diff.py -- byte-level comparison of my appended block vs the retail file
style (leading whitespace before '#' is the prime suspect for a naive parser).
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from drs_lib import Drs

GAME = os.environ.get("AOE2HD_DIR") or (r"D:\新建文件夹 (10)\3DMGAME_Age_of_Empires_II_HD.CHS.Green"
        r"\Age of Empires II HD")
BACKUP = os.path.join(os.path.dirname(os.path.abspath(__file__)), r"backup_drs")

LIVE = {
    "x1 -> anib_60027": (os.path.join(GAME, "Data", "gamedata_x1.drs"), 60027,
                         os.path.join(BACKUP, "gamedata_x1.drs.orig")),
    "aok -> anib_60010": (os.path.join(GAME, "Data", "gamedata.drs"), 60010,
                          os.path.join(BACKUP, "gamedata.drs.orig")),
}
out = []
for label, (live, eid, orig) in LIVE.items():
    lt = Drs(live).payload(b"anib", eid).decode("latin-1")
    ot = Drs(orig).payload(b"anib", eid).decode("latin-1")
    oll, lll = ot.split("\n"), lt.split("\n")
    out.append("\n" + "=" * 90)
    out.append("%s : retail %d lines / live %d lines (+%d)"
               % (label, len(oll), len(lll), len(lll) - len(oll)))

    def dir_info(name, lines, upto):
        info = []
        for i, l in enumerate(lines[:upto], 1):
            s = l.lstrip()
            if s.startswith("#load-if") or s.startswith("#else") \
               or s.startswith("#end-if"):
                lead = len(l) - len(s)
                info.append((i, lead, s.split()[0], s))
        return info

    for name, lines, upto in (("retail", oll, len(oll)), ("live", lll, len(lll))):
        di = dir_info(name, lines, upto)
        lead0 = sum(1 for _, lead, _, _ in di if lead == 0)
        leadn = sum(1 for _, lead, _, _ in di if lead > 0)
        out.append("  %-6s directives: %d  (col0=%d, indented=%d)"
                   % (name, len(di), lead0, leadn))
        for i, lead, tok, s in di:
            if lead:
                out.append("      !! line %d lead=%d : %r" % (i, lead, s))
    out.append("  --- retail tail (exact) ---")
    for i, l in enumerate(oll[-14:], len(oll) - 13):
        out.append("   r%5d|%s" % (i, l))
    out.append("  --- live: first 14 lines after the retail part ---")
    for i, l in enumerate(lll[len(oll):len(oll) + 14], len(oll) + 1):
        out.append("   l%5d|%s" % (i, l))
    out.append("  --- live tail (exact) ---")
    for i, l in enumerate(lll[-10:], len(lll) - 9):
        out.append("   l%5d|%s" % (i, l))
    # sanity: does the live file start with the same bytes as retail?
    out.append("  prefix identical to retail : %s" % lt.startswith(ot[:4000]))
    # any non-ascii / tab / CR in the appended part?
    app = lt[len(ot):]
    bad = sorted(set(c for c in app if not (32 <= ord(c) < 127 or c in "\r\n\t")))
    out.append("  appended bytes=%d  non-ascii=%s  CR count=%d  tabs=%d"
               % (len(app), bad, app.count("\r"), app.count("\t")))

open("dm_diff_out.txt", "w", encoding="utf-8").write("\n".join(out))
print("wrote dm_diff_out.txt")
