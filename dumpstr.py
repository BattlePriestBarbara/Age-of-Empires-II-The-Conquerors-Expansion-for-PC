"""Dump exe strings near interesting offsets -> UTF-8 file (avoids PowerShell UTF-16 redirect)."""
import os
EXE = r"D:\新建文件夹 (10)\3DMGAME_Age_of_Empires_II_HD.CHS.Green\Age of Empires II HD\AoK HD.exe"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), r"dumpstr_out.txt")

offs = [
    # AI folder / random folder references
    3613252, 3613408,
    3681576, 3681660,
    # deathmatch mentions
    3654582, 3681840, 3685941,
    # petersen name table
    3685320, 3685941, 3686068, 3686100, 3686200,
    # ai extension filter list
    3722505, 3725364, 3677600, 3677710,
]

with open(EXE, "rb") as f:
    data = f.read()

lines = []


def strings_in(a, b, minlen=4):
    chunk = data[a:b]
    out = []
    cur = b""
    start = 0
    for i, c in enumerate(chunk):
        if 32 <= c < 127:
            if not cur:
                start = a + i
            cur += bytes([c])
        else:
            if len(cur) >= minlen:
                out.append((start, cur.decode("latin-1")))
            cur = b""
    if len(cur) >= minlen:
        out.append((start, cur.decode("latin-1")))
    return out


for o in offs:
    a = max(0, o - 400)
    b = min(len(data), o + 700)
    lines.append("---- around 0x%06x (%d) : 0x%06x..0x%06x ----" % (o, o, a, b))
    for addr, t in strings_in(a, b, 3):
        lines.append("   0x%06x  %s" % (addr, t))
    lines.append("")

lines.append("== all 'anib' windows ==")
lo = data.lower()
i = 0
seen = 0
while seen < 40:
    i = lo.find(b"anib", i + 1)
    if i < 0:
        break
    lines.append("---- 0x%06x ----" % i)
    for addr, t in strings_in(max(0, i - 60), min(len(data), i + 60), 3):
        lines.append("   0x%06x  %s" % (addr, t))
    seen += 1

lines.append("")
lines.append("== all 'deathmatch' windows ==")
i = 0
seen = 0
while seen < 20:
    i = lo.find(b"deathmatch", i + 1)
    if i < 0:
        break
    lines.append("---- 0x%06x ----" % i)
    for addr, t in strings_in(max(0, i - 120), min(len(data), i + 120), 3):
        lines.append("   0x%06x  %s" % (addr, t))
    seen += 1

with open(OUT, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
print("wrote", OUT, len(lines))
