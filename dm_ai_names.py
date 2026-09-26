"""dm_ai_names.py -- which DRS entry is the constants file of which data set?

Each gamedata*.drs ships *two* candidate constants scripts:
    gamedata.drs     : anib_60010 (ladder!) and anib_60027 (no ladder)
    gamedata_x1.drs  : anib_60010 (no ladder) and anib_60027 (ladder!)
and the death-match script of a data set only works if *its* constants file is
the one with the POPULATION-CAP ladder.  This script shows what each candidate
defines.
"""
import os
import re

W = os.path.dirname(os.path.abspath(__file__))
CANDIDATES = [
    ("x1_drs", "anib_60010.bin"), ("x1_drs", "anib_60027.bin"),
    ("aok_drs", "anib_60010.bin"), ("aok_drs", "anib_60027.bin"),
]
KEYS = ("deathmatch-unit-max", "unit-max", "civ-dark-rush", "civ-castle",
        "pop-cap", "five-percent-pop", "t-production", "secondary-build")


def main():
    for folder, fname in CANDIDATES:
        path = os.path.join(W, folder, fname)
        text = open(path, "rb").read().decode("latin-1")
        caps = sorted(set(int(c) for c in re.findall(r"POPULATION-CAP-(\d+)", text)))
        print("=" * 76)
        print("%s/%s : %d bytes, %d lines" % (folder, fname, os.path.getsize(path),
                                              text.count("\n") + 1))
        print("  POPULATION-CAP ladder   : %s" % (caps or "none"))
        print("  #load-if-defined blocks : %d (#else: %d, #load-if-not-defined: %d)"
              % (len(re.findall(r"#load-if-defined", text)), len(re.findall(r"#else", text)),
                 len(re.findall(r"#load-if-not-defined", text))))
        print("  (defrule count          : %d" % len(re.findall(r"\(defrule", text)))
        for k in KEYS:
            hits = [i for i, line in enumerate(text.split("\n"), 1)
                    if re.search(r"\(defconst\s+%s\b" % re.escape(k), line)]
            print("  %-20s defconst at %s" % (k, hits or "-"))
        if "deathmatch-unit-max" not in text:
            print("  first lines    : %s" % " | ".join(
                x.strip() for x in text.split("\n")[:3]))
        else:
            for i, line in enumerate(text.split("\n"), 1):
                if "(defconst deathmatch-unit-max" in line:
                    break
            print("  context around the first deathmatch-unit-max (line %d):" % i)
            rows = text.split("\n")
            for j in range(max(0, i - 4), min(len(rows), i + 1)):
                print("      %5d| %s" % (j + 1, rows[j].rstrip()))


if __name__ == "__main__":
    main()
