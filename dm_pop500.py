"""dm_pop500.py -- why does the DM AI die at population limit 500?

The Deathmatch AI chain loads `anib_60027` ("petersen constants") which defines
`deathmatch-unit-max`, `pop-cap`, `unit-max`, `civ-*`, `*-percent-pop` ONLY inside
`#load-if-defined POPULATION-CAP-<n>` blocks.  This script lists which caps exist,
in which script, and how many rules of `anib_60002` depend on those constants.
"""
import collections
import glob
import os
import re

ROOTS = ["x1_drs", "aok_drs", "x1p1_drs"]
CONST_RE = re.compile(r"POPULATION-CAP-([0-9]+)")
BLOCK_RE = re.compile(r"^\s*#load-if-(?:not-)?defined\s+(\S+)", re.I)
KEY_CONSTS = ["deathmatch-unit-max", "pop-cap", "unit-max", "civ-dark-rush",
              "civ-dark", "civ-feudal", "civ-castle", "fifteen-percent-pop",
              "fifty-percent-pop", "feudal-town-size", "town-center-count"]


def text(path):
    with open(path, "rb") as fh:
        return fh.read().decode("latin-1")


def main():
    caps = collections.defaultdict(set)
    for root in ROOTS:
        for path in sorted(glob.glob(os.path.join(root, "*"))):
            if not os.path.isfile(path):
                continue
            for m in CONST_RE.finditer(text(path)):
                caps[int(m.group(1))].add("%s/%s" % (root, os.path.basename(path)))
    print("== POPULATION-CAP-* symbols used anywhere in the DRS AI scripts ==")
    for cap in sorted(caps):
        print("  POPULATION-CAP-%-4d -> %s" % (cap, ", ".join(sorted(caps[cap]))))
    print("  => highest cap any script knows about: %d" % max(caps))

    for name in ("x1_drs/anib_60027.bin", "aok_drs/anib_60027.bin"):
        if not os.path.exists(name):
            continue
        lines = text(name).split("\n")
        print("\n== %s (%d lines) ==" % (name, len(lines)))
        depth = 0
        for i, line in enumerate(lines, 1):
            m = BLOCK_RE.match(line)
            if m:
                if "not-" in line.lower():
                    print("  %5d| #load-if-NOT-defined %s" % (i, m.group(1)))
                else:
                    depth += 1
                    print("  %5d| #load-if-defined %s" % (i, m.group(1)))
            elif line.strip().lower().startswith("#end-if"):
                depth -= 1
        inside = False
        for i, line in enumerate(lines, 1):
            if BLOCK_RE.match(line):
                inside = "not-" not in line.lower()
            s = line.strip()
            for key in KEY_CONSTS:
                if re.match(r"\(defconst\s+%s\b" % re.escape(key), s):
                    tag = "in a #load-if block" if inside else "OUTSIDE any block (default!)"
                    if key in ("deathmatch-unit-max", "pop-cap"):
                        print("  %5d| %-46s %s" % (i, s, tag))

    dm = "x1_drs/anib_60002.bin"
    if os.path.exists(dm):
        body = text(dm)
        print("\n== %s ==" % dm)
        for key in KEY_CONSTS:
            print("  rules/uses of %-22s : %d" % (key, len(re.findall(re.escape(key), body))))
        print("  (an undefined constant makes every rule that mentions it invalid,")
        print("   so the whole DM AI script stops firing.)")


if __name__ == "__main__":
    main()
