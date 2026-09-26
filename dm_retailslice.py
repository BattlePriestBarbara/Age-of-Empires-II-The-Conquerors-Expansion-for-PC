"""dm_retailslice.py -- print a line range of the *retail* x1 death-match
script (or any other shipped anib entry) so the exact shipped formatting of
the age gates and the house rules can be compared with what we appended."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from drs_lib import Drs

W = os.path.dirname(os.path.abspath(__file__))
BACKUP = os.path.join(W, "backup_drs")

ARCH = os.path.join(BACKUP, "gamedata_x1.drs.orig")
EID = 60002
RANGES = [(1580, 1710), (2330, 2360), (2860, 2883)]

text = Drs(ARCH).payload(b"anib", EID).decode("latin-1")
rows = text.split("\n")
if rows and rows[-1] == "":
    rows = rows[:-1]
out = []
for a, b in RANGES:
    out.append("")
    out.append("=" * 92)
    out.append("=== retail x1 anib_60002 lines %d..%d  (total %d)" % (a, b, len(rows)))
    for i in range(a - 1, min(b, len(rows))):
        out.append("  %5d | %s" % (i + 1, rows[i].rstrip("\r")))
txt = "\n".join(out)
open(os.path.join(W, "dm_retailslice_out.txt"), "w", encoding="utf-8").write(txt + "\n")
print("\n".join(out))
