"""dm_timer3_check.py -- evidence: is timer 3 (t-production) free in Deathmatch?

The patch uses timer 3 (the constant `t-production` from `anib_60027`,
"petersen constants").  This script lists every extracted AI script that
mentions `t-production` (symbolic use) and every numeric use of timer 3
(`(enable-timer 3 ...)`, `(disable-timer 3 ...)`, `(timer-triggered 3)`),
so we can prove no Deathmatch-loaded script touches it.
"""
import glob
import os
import collections
import re

ROOTS = ["x1_drs", "aok_drs", "x1p1_drs"]
NUMERIC = re.compile(r"\((enable-timer|disable-timer|timer-triggered)\s+3\b")


def load(path):
    with open(path, "rb") as fh:
        return fh.read().decode("latin-1", errors="replace")


def main():
    symbolic = collections.Counter()
    numeric = collections.Counter()
    for root in ROOTS:
        for path in sorted(glob.glob(os.path.join(root, "*"))):
            if not os.path.isfile(path):
                continue
            text = load(path)
            n = len(re.findall(r"t-production", text))
            if n:
                symbolic[(root, os.path.basename(path))] = n
            for match in NUMERIC.finditer(text):
                numeric[(root, os.path.basename(path), match.group(1))] += 1
    print("symbolic uses of t-production (timer 3):")
    for key in sorted(symbolic):
        print("   %-12s %-22s %d" % (key[0], key[1], symbolic[key]))
    if not symbolic:
        print("   (none)")
    print("numeric uses of timer 3:")
    for key in sorted(numeric):
        print("   %-12s %-22s %-16s %d" % (key[0], key[1], key[2], numeric[key]))
    if not numeric:
        print("   (none)  <- no script anywhere uses timer 3 by number")
    dm = [(k, v) for k, v in list(symbolic.items()) + list(numeric.items())
          if os.path.basename(k[1]) == "anib_60002.bin"]
    print("timer 3 inside the Deathmatch script (anib_60002): %s" %
          ("USED by the original -> " + str(dm) if dm
           else "the original never touches it; only the appended patch rules do"))


if __name__ == "__main__":
    main()
