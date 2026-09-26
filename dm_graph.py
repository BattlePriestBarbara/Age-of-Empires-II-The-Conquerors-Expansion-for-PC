"""dm_graph.py -- the whole AI load graph of both data sets.

For every `anib` entry: id, size, rule count, first line, the scripts it loads,
the constants it defines and how often it uses the population-cap constants.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from drs_lib import Drs

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
BACKUP = os.path.join(os.path.dirname(os.path.abspath(__file__)), r"backup_drs")
CAPCONST = ["pop-cap", "unit-max", "deathmatch-unit-max", "five-percent-pop",
            "ten-percent-pop", "fifteen-percent-pop", "twenty-percent-pop",
            "thirty-percent-pop", "fifty-percent-pop", "town-size",
            "feudal-town-size", "castle-town-size", "imperial-town-size",
            "civ-dark", "civ-feudal", "civ-castle", "civ-dark-rush"]


def main():
    out = open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            "dm_graph_out.txt"), "w", encoding="utf-8")
    for drs_name in ("gamedata_x1.drs.orig", "gamedata.drs.orig"):
        d = Drs(os.path.join(BACKUP, drs_name))
        out.write("\n" + "#" * 100 + "\n# %s\n" % drs_name + "#" * 100 + "\n")
        for ext, eid, size, md5 in d.entries():
            if ext != b"anib" or eid < 60000:
                continue
            text = d.payload(ext, eid).decode("latin-1")
            first = next((l.strip() for l in text.split("\n") if l.strip()), "")
            loads = []
            for m in re.findall(r'\(load\s+"([^"]+)"\)', text, re.I):
                if m not in loads:
                    loads.append(m)
            defines = re.findall(r"\(defconst\s+([A-Za-z0-9\-_]+)\s+(-?\d+)\)", text)
            dn = [n for n, _ in defines]
            caps = sorted(set(n for n, _ in defines if n.lower() in CAPCONST))
            gated = sorted(set(s.upper() for s in
                               re.findall(r"#load-if-defined\s+([A-Za-z0-9\-_]+)", text)
                               if s.upper().startswith(("DEATH", "POPULATION"))))
            out.write("\n anib_%05d %7dB rules=%-4d def=%-3d %s\n"
                      % (eid, size, len(re.findall(r"\(defrule", text)),
                         len(defines), first[:70]))
            if loads:
                out.write("     -> loads : %s\n" % "; ".join(loads)[:150])
            if caps:
                out.write("     = defines: %s\n" % ", ".join(caps))
            if gated:
                out.write("     * gate   : %s\n" % ", ".join(gated))
            used = {k: v for k, v in
                    ((c, len(re.findall(r"[\s\(" + re.escape(c) + r"[\s\)]", text)))
                     for c in CAPCONST) if v}
            if used:
                out.write("     ! uses   : %s\n" % ", ".join(
                    "%s x%d" % kv for kv in sorted(used.items())))

    out.write("\n\n=== who defines the cap constants ===\n")
    for drs_name in ("gamedata_x1.drs.orig", "gamedata.drs.orig"):
        d = Drs(os.path.join(BACKUP, drs_name))
        out.write("-- %s\n" % drs_name)
        for ext, eid, size, md5 in d.entries():
            if ext != b"anib":
                continue
            text = d.payload(ext, eid).decode("latin-1")
            for key in ("town-size", "pop-cap", "deathmatch-unit-max", "unit-max"):
                hits = [i for i, l in enumerate(text.split("\n"), 1)
                        if re.search(r"\(defconst\s+" + re.escape(key) + r"\s", l)]
                if hits:
                    out.write("   anib_%05d defines %-20s lines %s\n"
                              % (eid, key, hits[:12]))
    out.close()
    print("wrote dm_graph_out.txt")


if __name__ == "__main__":
    main()
