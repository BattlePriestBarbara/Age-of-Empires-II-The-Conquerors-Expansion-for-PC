"""dm_ailog.py -- (1) does the engine write an AI log/error file, and is one
already on this machine?  (2) which error-report format strings exist?
"""
import os
import re
import sys

GAME = os.environ.get("AOE2HD_DIR") or (r"D:\新建文件夹 (10)\3DMGAME_Age_of_Empires_II_HD.CHS.Green"
        r"\Age of Empires II HD")
data = open(os.path.join(GAME, "AoK HD.exe"), "rb").read()
out = []


def strings(buf, minlen=4):
    cur = []
    for c in buf:
        if 32 <= c < 127:
            cur.append(chr(c))
        else:
            if len(cur) >= minlen:
                yield "".join(cur)
            cur = []


out.append("=== filename-ish strings in the exe (.txt/.log/.ailog/.prs)")
for s in sorted(set(strings(data))):
    low = s.lower()
    if low.endswith((".txt", ".log", ".ailog", ".aix")) or "ailog" in low:
        out.append("   %r" % s[:120])

out.append("\n=== strings containing 'line' + number format or AI error report")
for s in sorted(set(strings(data, 5))):
    low = s.lower()
    if ("line %" in low or "ai error" in low or "ai script" in low
            or "ailog" in low or "logging" in low):
        out.append("   %r" % s[:150])

out.append("\n=== existing AI/log files on disk")
cands = [GAME, os.path.join(GAME, "Data"), os.path.join(GAME, "SaveGame"),
         os.path.join(os.path.expanduser("~"), "Games"),
         os.path.join(os.path.expanduser("~"), "Games", "Age of Empires II HD"),
         os.path.join(os.path.expanduser("~"), "Documents",
                      "Age of Empires II HD"),
         os.path.dirname(os.path.abspath(__file__))]
for c in cands:
    if not os.path.isdir(c):
        out.append("   %-70s <missing>" % c)
        continue
    names = []
    for root, dirs, files in os.walk(c):
        if root.count(os.sep) - c.count(os.sep) > 2:
            dirs[:] = []
            continue
        for f in files:
            low = f.lower()
            if low.endswith((".log", ".txt")) or "log" in low or "ai" in low[:3]:
                names.append(os.path.join(root, f))
    for n in names[:60]:
        try:
            size = os.path.getsize(n)
        except OSError:
            size = -1
        out.append("   %-78s %8d B" % (n, size))
    if not names:
        out.append("   %-70s (no log/txt files)" % c)

open("dm_ailog_out.txt", "w", encoding="utf-8").write("\n".join(out))
print("wrote dm_ailog_out.txt")
