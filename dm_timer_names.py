"""Which timer names exist (exe) and who uses them (AI scripts)?"""
import os
import re

W = os.path.dirname(os.path.abspath(__file__))
GAME = os.environ.get("AOE2HD_DIR") or r"D:\新建文件夹 (10)\3DMGAME_Age_of_Empires_II_HD.CHS.Green\Age of Empires II HD"
out = []

# 1) timer names present in the AI scripts, per file, per dir
usage = {}
for d in ("aok_drs", "x1_drs", "x1p1_drs"):
    p = os.path.join(W, d)
    if not os.path.isdir(p):
        continue
    for f in sorted(os.listdir(p)):
        t = open(os.path.join(p, f), "rb").read().decode("latin-1")
        names = sorted(set(re.findall(r"(?<![\w-])t-[a-z0-9-]+", t)))
        if names:
            usage["%s/%s" % (d, f)] = names
out.append("=== timer names used, per AI script ===")
for k in sorted(usage):
    out.append("  %-28s %s" % (k, " ".join(usage[k])))

allt = sorted({n for v in usage.values() for n in v})
out.append("")
out.append("=== union of timer names used by scripts: %d ===" % len(allt))
out.append("  " + " ".join(allt))

# 2) exe string scan for t- timer names
exe = os.path.join(GAME, "AoK HD.exe")
data = open(exe, "rb").read()
out.append("")
out.append("=== 't-...' strings in exe (len>=4) ===")
seen = set()
for m in re.finditer(rb"t-[a-z0-9][a-z0-9-]{2,}", data):
    s = m.start()
    # require NUL-terminated and preceded by NUL (proper string start)
    if data[s - 1] != 0 or data[m.end()] != 0:
        continue
    v = m.group().decode()
    if v not in seen:
        seen.add(v)
for v in sorted(seen):
    out.append("  " + v)
out.append("")
out.append("total exe timer-name strings: %d" % len(seen))

open(os.path.join(W, "dm_timer_names_out.txt"), "w", encoding="utf-8").write("\n".join(out))
print("wrote dm_timer_names_out.txt", len(out), "lines")
