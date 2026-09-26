"""dm_kw.py -- find the AI preprocessor's directive keyword table in the exe
(with and without the leading '#') and any #if-depth limit constant.
"""
import os
import re

GAME = os.environ.get("AOE2HD_DIR") or (r"D:\新建文件夹 (10)\3DMGAME_Age_of_Empires_II_HD.CHS.Green"
        r"\Age of Empires II HD")
data = open(os.path.join(GAME, "AoK HD.exe"), "rb").read()
out = []

CANDS = ["load-if-defined", "load-if-not-defined", "end-if", "else", "elif",
         "ifdef", "ifndef", "undef", "include", "define", "defconst",
         "if", "endif", "load-if", "load"]
out.append("=== candidate directive keywords as null-terminated strings")
for w in CANDS:
    for form in (w, "#" + w):
        needle = form.encode() + b"\x00"
        hits = [m.start() for m in re.finditer(re.escape(needle), data)]
        if not hits:
            continue
        out.append("   %-22r %d hit(s)" % (form, len(hits)))
        for h in hits[:8]:
            lo, hi = max(0, h - 160), min(len(data), h + 200)
            region = data[lo:hi]
            txt = region.replace(b"\x00", b"\n")
            out.append("      @%08x:" % h)
            for line in txt.split(b"\n"):
                s = "".join(chr(c) if 32 <= c < 127 else "." for c in line)
                if s.strip():
                    out.append("         %s" % s[:150])

out.append("\n=== ERR3xxx neighbours (preprocessor error strings) as raw region")
idx = data.find(b"ERR3001")
lo, hi = max(0, idx - 300), min(len(data), idx + 700)
out.append("   region 0x%08x - 0x%08x" % (lo, hi))
cur = []
for c in data[lo:hi]:
    if 32 <= c < 127:
        cur.append(chr(c))
    else:
        if len(cur) >= 3:
            out.append("      %s" % "".join(cur)[:150])
        cur = []

open("dm_kw_out.txt", "w", encoding="utf-8").write("\n".join(out))
print("wrote dm_kw_out.txt")
