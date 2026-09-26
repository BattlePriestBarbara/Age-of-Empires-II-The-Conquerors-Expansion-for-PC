"""dm_inv.py -- compact one-line-per-entry inventory of every anib script."""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from drs_lib import Drs

BACKUP = os.path.join(os.path.dirname(os.path.abspath(__file__)), r"backup_drs")
CAP = ["pop-cap", "unit-max", "deathmatch-unit-max", "five-percent-pop",
       "ten-percent-pop", "fifteen-percent-pop", "twenty-percent-pop",
       "thirty-percent-pop", "fifty-percent-pop", "town-size",
       "feudal-town-size", "castle-town-size", "imperial-town-size",
       "civ-dark", "civ-feudal", "civ-castle", "civ-dark-rush"]
out = []
for drs_name in ("gamedata_x1.drs.orig", "gamedata.drs.orig"):
    d = Drs(os.path.join(BACKUP, drs_name))
    out.append("\n### %s" % drs_name)
    for ext, eid, size, md5 in d.entries():
        if ext != b"anib" or eid < 60000:
            continue
        text = d.payload(ext, eid).decode("latin-1")
        rules = len(re.findall(r"\(defrule", text))
        first = next((l.strip() for l in text.split("\n") if l.strip()), "")
        loads = sorted(set(re.findall(r'\(load\s+"([^"]+)"\)', text, re.I)))
        gates = sorted(set(s.upper() for s in
                           re.findall(r"#load-if-defined\s+([A-Za-z0-9\-_]+)", text)
                           if s.upper().startswith(("DEATH", "POPULATION",
                                                    "DIFFICULTY"))))
        uses = {c: len(re.findall(r"(?<![A-Za-z0-9\-])" + re.escape(c) +
                                 r"(?![A-Za-z0-9\-])", text)) for c in CAP}
        used = ", ".join("%s=%d" % kv for kv in sorted(uses.items()) if kv[1])
        out.append("\nanib_%05d %7dB rules=%-4d gates=%-34s | %s"
                   % (eid, size, rules, ",".join(gates) or "-", first[:64]))
        if loads:
            out.append("    loads : %s" % "; ".join(loads))
        if used:
            out.append("    uses  : %s" % used)
open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "dm_inv_out.txt"), "w",
     encoding="utf-8").write("\n".join(out))
print("wrote dm_inv_out.txt")
