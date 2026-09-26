"""Find int32 LE arrays containing ANIB resource ids (60001..60029 etc) in the exe."""
import os
import struct

EXE = r"D:\新建文件夹 (10)\3DMGAME_Age_of_Empires_II_HD.CHS.Green\Age of Empires II HD\AoK HD.exe"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), r"find_ids2_out.txt")

with open(EXE, "rb") as f:
    data = f.read()

lines = []


def i32(off):
    return struct.unpack_from("<i", data, off)[0]


# 1) every offset where i32 == 60027 (petersen constants) / 60026 (root) / 54000
for target in (60027, 60026, 60028, 60029, 60001, 54000, 54202):
    hits = []
    for off in range(0, len(data) - 4, 4):
        if i32(off) == target:
            hits.append(off)
    lines.append("== i32 == %d : %d aligned hits ==" % (target, len(hits)))
    for off in hits[:12]:
        vals = [i32(off + 4 * k) for k in range(-8, 12)]
        lines.append("   0x%06x  ... %s ..." % (off, " ".join(str(v) for v in vals)))
    lines.append("")

# 2) dump all ASCII strings in the AI-name table region
def strings_in(a, b, minlen=3):
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


lines.append("== strings 0x382c00..0x384200 ==")
for addr, t in strings_in(0x382C00, 0x384200, 4):
    lines.append("   0x%06x  %s" % (addr, t))

with open(OUT, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
print("wrote", OUT, len(lines))
