"""dm_look.py -- dump the exact text of the rules that gate houses / tech / ages.

Reads the patched (not-yet-installed) scripts so we see what the engine sees.
"""
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
PS = os.path.join(os.path.dirname(os.path.abspath(__file__)), r"patched_scripts")
DM = os.path.join(PS, "petersen deathmatch (Conquerors).per")
CONST = os.path.join(PS, "petersen constants (Conquerors).per")

WANT = ["house", "can-research", "research", "build ", "housing-headroom"]


def main():
    dm = open(DM, "rb").read().decode("latin-1").split("\r\n")
    print("DM script lines:", len(dm))
    print("\n########## TAIL (patch A) ##########")
    for i in range(max(0, len(dm) - 62), len(dm)):
        print("%5d| %s" % (i + 1, dm[i]))

    print("\n########## lines mentioning house / housing ##########")
    for i, ln in enumerate(dm):
        if re.search(r"house", ln, re.I):
            print("%5d| %s" % (i + 1, ln))

    print("\n########## tech research rule count ##########")
    res = [i for i, ln in enumerate(dm) if "can-research" in ln]
    print("(can-research ...) at lines:", res[:40], "... total", len(res))

    print("\n########## every constant referenced by the DM script ##########")
    text = "\r\n".join(dm)
    names = sorted(set(re.findall(r"\(([a-z][a-z0-9\-]+)\s", text)))
    cst = open(CONST, "rb").read().decode("latin-1")
    consts = set(re.findall(r"\(defconst\s+([a-z0-9\-]+)", cst))
    used = sorted(n for n in names if n in consts)
    print("constants defined in the constants file AND used by the DM script:")
    for n in used:
        print("   %-28s %d use(s)" % (n, len(re.findall(r"\(" + n + r"[\s\)]", text))))


if __name__ == "__main__":
    main()
