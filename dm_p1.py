"""dm_p1.py -- does Data\\gamedata_x1_p1.drs carry AI scripts that shadow the
patched gamedata_x1.drs?  (that would silently undo the whole patch)
"""
import os
import re
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from drs_lib import Drs

GAME = os.environ.get("AOE2HD_DIR") or (r"D:\新建文件夹 (10)\3DMGAME_Age_of_Empires_II_HD.CHS.Green"
        r"\Age of Empires II HD")

out = []
for name in ("gamedata.drs", "gamedata_x1.drs", "gamedata_x1_p1.drs"):
    path = os.path.join(GAME, "Data", name)
    d = Drs(path)
    out.append("\n=== %s (%d bytes)" % (name, os.path.getsize(path)))
    for ext, rows in d.tables:
        out.append("   table %-6s entries=%d" % (ext.decode("latin-1"), len(rows)))
        if ext == b"anib":
            for eid, off, size in rows:
                blob = d.payload(ext, eid)
                text = blob.decode("latin-1")
                first = next((l.strip() for l in text.split("\n") if l.strip()), "")
                out.append("      anib_%05d %7dB rules=%-4d caps=%-24s %s"
                           % (eid, size, len(re.findall(r"\(defrule", text)),
                              ",".join(map(str, sorted(set(int(c) for c in re.findall(
                                  r"POPULATION-CAP-(\d+)", text))))) or "-",
                              first[:52]))

text = open(os.path.join(GAME, "AoK HD.exe"), "rb").read()
out.append("\n=== how the exe names the data archives")
for n in (b"gamedata.drs", b"gamedata_x1.drs", b"gamedata_x1_p1.drs",
          b"gamedata_x2", b"gamedata_x1.dat", b"gamedata.dat"):
    hits = [m.start() for m in re.finditer(re.escape(n), text)]
    out.append("  %-22s %d hit(s)" % (n.decode(), len(hits)))
    for off in hits[:6]:
        ctx = text[max(0, off - 70):off + 70]
        out.append("      @0x%08x %s" % (off, "".join(
            chr(b) if 32 <= b < 127 else "." for b in ctx)))
open("dm_p1_out.txt", "w", encoding="utf-8").write("\n".join(out))
print("wrote dm_p1_out.txt")
