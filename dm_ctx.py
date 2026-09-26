"""dm_ctx.py -- dump the string neighbourhood around key AI-engine strings so we
can see the trigger / reporting path (AILog, AI Script Error, taunt commands).
"""
import os
import re

GAME = os.environ.get("AOE2HD_DIR") or (r"D:\新建文件夹 (10)\3DMGAME_Age_of_Empires_II_HD.CHS.Green"
        r"\Age of Empires II HD")
data = open(os.path.join(GAME, "AoK HD.exe"), "rb").read()
out = []


def strings(buf, minlen=4):
    cur = []
    start = 0
    for i, c in enumerate(buf):
        if 32 <= c < 127:
            if not cur:
                start = i
            cur.append(chr(c))
        else:
            if len(cur) >= minlen:
                yield start, "".join(cur)
            cur = []


for needle in (b"AILog LOGGING STARTED",
               b"AI Script Error",
               b"AILog\\%s.log",
               b"Logging to File %s",
               b"===Logging==="):
    idx = data.find(needle)
    out.append("\n### around %r  (file 0x%08x)" % (needle.decode(), idx))
    lo = max(0, idx - 700)
    hi = min(len(data), idx + 700)
    for off, s in strings(data[lo:hi], 3):
        out.append("   %08x  %s" % (lo + off, s[:140]))

out.append("\n=== taunt / chat command handling strings (taunt %d)")
for off, s in strings(data, 4):
    low = s.lower()
    if ("taunt" in low and ("%d" in s or "%i" in s)) or "logging" in low:
        out.append("   %08x  %s" % (off, s[:140]))

open("dm_ctx_out.txt", "w", encoding="utf-8").write("\n".join(out))
print("wrote dm_ctx_out.txt")
