"""dm_sim.py -- run the game's preprocessor over the *installed* constants
files and print the values the engine would end up with.

usage: python dm_sim.py [--caps 500] [--symbols POPULATION-CAP-200,DIFFICULTY-HARD]
"""
import argparse
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from drs_lib import Drs

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
GAME = os.environ.get("AOE2HD_DIR") or (r"D:\新建文件夹 (10)\3DMGAME_Age_of_Empires_II_HD.CHS.Green"
        r"\Age of Empires II HD\Data")
BACKUP = os.path.join(os.path.dirname(os.path.abspath(__file__)), r"backup_drs")
KEYS = ["pop-cap", "unit-max", "deathmatch-unit-max", "five-percent-pop",
        "ten-percent-pop", "fifteen-percent-pop", "civ-dark-rush",
        "civ-dark", "civ-feudal", "civ-castle", "imperial-town-size",
        "t-production", "secondary-build", "town-size"]

EXTRA_DEFAULT = ["GAME-SPEED-LOCKED", "DEATH-MATCH", "DIFFICULTY-HARD",
                 "DIFFICULTY-HARDEST", "DEATHMATCH", "REVEAL-MAP"]


def simulate(text, symbols):
    """Return (defined{name: (value, line)}, duplicates, errors)."""
    stack = []                      # list of [active, taken, parent_active]
    defined, dups, errors = {}, [], []
    for ln, raw in enumerate(text.split("\n"), 1):
        line = raw.strip()
        parent = stack[-1][0] if stack else True
        m = re.match(r"#load-if-defined\s+([A-Za-z0-9\-_]+)", line, re.I)
        if m:
            cond = m.group(1).upper() in symbols
            stack.append([parent and cond, cond, parent])
            continue
        m = re.match(r"#load-if-not-defined\s+([A-Za-z0-9\-_]+)", line, re.I)
        if m:
            cond = m.group(1).upper() not in symbols
            stack.append([parent and cond, cond, parent])
            continue
        if re.match(r"#else\b", line, re.I):
            if not stack:
                errors.append("line %d: #else without #if" % ln)
                continue
            top = stack[-1]
            top[0] = top[2] and (not top[1])
            continue
        if re.match(r"#end-if\b", line, re.I):
            if not stack:
                errors.append("line %d: #end-if without #if" % ln)
                continue
            stack.pop()
            continue
        if line.startswith("#"):
            continue                # #include / #load handled elsewhere
        if not (stack[-1][0] if stack else True):
            continue
        for name, value in re.findall(r"\(defconst\s+([A-Za-z0-9\-_]+)\s+"
                                      r"(-?\d+)\)", line):
            key = name.lower()
            if key in defined:
                dups.append((key, defined[key], (value, ln)))
            defined[key] = (value, ln)
    if stack:
        errors.append("%d unclosed #load-if block(s) at EOF" % len(stack))
    return defined, dups, errors


def entry(path, eid):
    d = Drs(path)
    return d.payload(b"anib", eid).decode("latin-1")


def report(label, text, symbols):
    print("\n" + "=" * 78)
    print("%s  (symbols=%s)" % (label, ",".join(sorted(symbols)) or "<none>"))
    defined, dups, errors = simulate(text, symbols)
    print("  defconst total : %d   duplicates: %d   errors: %s"
          % (len(defined), len(dups), errors or "none"))
    for d in dups:
        print("     !! duplicate %s : %s line %d  ->  %s line %d"
              % (d[0], d[1][0], d[1][1], d[2][0], d[2][1]))
    for k in KEYS:
        if k in defined:
            print("   %-24s = %-6s (line %d)" % (k, defined[k][0], defined[k][1]))
        else:
            print("   %-24s = ** UNDEFINED **" % k)
    return defined


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--caps", type=int, action="append", default=[])
    ap.add_argument("--symbols", default="")
    args = ap.parse_args()
    symbols = set(x.upper() for x in args.symbols.split(",") if x)
    symbols |= set(EXTRA_DEFAULT)
    for c in args.caps:
        symbols.add("POPULATION-CAP-%d" % c)

    targets = [
        ("LIVE  gamedata_x1.drs  anib_60027 (patched, Conquerors)",
         os.path.join(GAME, "gamedata_x1.drs"), 60027),
        ("LIVE  gamedata.drs     anib_60010 (patched, AoK)",
         os.path.join(GAME, "gamedata.drs"), 60010),
        ("RETAIL gamedata_x1.drs anib_60027",
         os.path.join(BACKUP, "gamedata_x1.drs.orig"), 60027),
        ("RETAIL gamedata.drs    anib_60010",
         os.path.join(BACKUP, "gamedata.drs.orig"), 60010),
    ]
    for label, path, eid in targets:
        text = entry(path, eid)
        report(label, text, symbols)
        if "tail" not in label:
            pass
    print("\n(tail of the live x1 constants file -- the appended catch-all)")
    text = entry(os.path.join(GAME, "gamedata_x1.drs"), 60027).split("\n")
    for i in range(max(0, len(text) - 46), len(text)):
        print("%5d| %s" % (i + 1, text[i].rstrip()))


if __name__ == "__main__":
    main()
