"""Collect facts needed to author a DM AI patch: rule counts, unit names, timers."""
import os
import re
import sys

FOLDER = sys.argv[1] if len(sys.argv) > 1 else "x1_drs"
OUT = open("plan_dm_out.txt", "w", encoding="utf-8")


def w(*args):
    print(*args, file=OUT)


def text(name):
    return open(os.path.join(FOLDER, name), "rb").read().decode("latin-1")


files = sorted(os.listdir(FOLDER))
total_rules = 0
w("== files: %d ==" % len(files))
for name in files:
    t = text(name)
    n = len(re.findall(r"\(defrule", t, re.I))
    total_rules += n
    w("   %-20s rules=%-6d bytes=%d" % (name, n, len(t)))
w("   TOTAL defrule count = %d" % total_rules)

pats = {
    "train": r"\(train\s+([a-z0-9-]+)",
    "can-train": r"\(can-train\s+([a-z0-9-]+)",
    "unit-type-count-total": r"unit-type-count-total\s+([a-z0-9-]+)",
    "build": r"\(build\s+([a-z0-9-]+)",
    "research": r"\(research\s+([a-z0-9-]+)",
    "can-research": r"\(can-research\s+([a-z0-9-]+)",
    "attack": r"\((attack-now|attack-groups|defend-soldiers)[^\)]*\)",
    "enable-timer": r"\(enable-timer\s+([a-z0-9-]+)\s+([0-9]+)\)",
    "timer-triggered": r"\(timer-triggered\s+([a-z0-9-]+)\)",
    "defconst-t": r"\(defconst\s+(t-[a-z0-9-]+)\s+([0-9-]+)\)",
    "goal-set": r"\(set-goal\s+([a-z0-9-]+)",
}
for label, pat in pats.items():
    counts = {}
    for name in files:
        for m in re.finditer(pat, text(name), re.I):
            key = m.group(0).lower() if label == "attack" else m.group(1).lower()
            if label == "enable-timer":
                key = "%s=%s" % (m.group(1).lower(), m.group(2))
            if label == "defconst-t":
                key = "%s=%s" % (m.group(1).lower(), m.group(2))
            counts[key] = counts.get(key, 0) + 1
    items = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
    w("")
    w("== %s : %d unique ==" % (label, len(items)))
    for k, c in items:
        w("   %-34s %d" % (k, c))
OUT.close()
print("written plan_dm_out.txt")
