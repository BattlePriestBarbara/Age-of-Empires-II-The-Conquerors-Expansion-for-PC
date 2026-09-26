"""Parse the static AI-name -> DRS-id table found in .text around 0x143980."""
import os
import struct

EXE = r"D:\新建文件夹 (10)\3DMGAME_Age_of_Empires_II_HD.CHS.Green\Age of Empires II HD\AoK HD.exe"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), r"ai_table_out.txt")
with open(EXE, "rb") as f:
    data = f.read()

lines = []


def cstr(off, n=64):
    e = data.index(b"\0", off)
    return data[off:min(e, off + n)].decode("latin-1")


# dump raw hex of the region
for base, length in ((0x143920, 0x120), (0x143960, 0x120), (0x143bc0, 0x60)):
    lines.append("== hex 0x%x .. 0x%x ==" % (base, base + length))
    for o in range(base, base + length, 16):
        chunk = data[o:o + 16]
        lines.append("  %06x  %s  %s" % (o, " ".join("%02x" % b for b in chunk),
                                         "".join(chr(c) if 32 <= c < 127 else "." for c in chunk)))
    lines.append("")

# try to detect records: u32 pointer into .rdata string pool + u16 id in 60000..60200
lines.append("== candidate records ==")
cands = []
for off in range(0x143000, 0x144100):
    ptr = struct.unpack_from("<I", data, off)[0]
    if not (0x00783000 <= ptr <= 0x00785000):
        continue
    s = cstr(ptr - 0x400000 + 0x34e000 - 0x34e000 + (0x34e000 - 0x34e000) + (ptr - 0x400000)) if False else None
    try:
        # VA->file offset: .rdata VA 0x34e000 -> file 0x34e000
        s = cstr(ptr - 0x400000)
    except ValueError:
        continue
    if not s.endswith(".per"):
        continue
    tail = data[off + 4:off + 16]
    cands.append((off, ptr, s, tail.hex()))
for off, ptr, s, tail in cands:
    lines.append("  0x%06x  ptr=0x%06x  %-32s tail=%s" % (off, ptr, s, tail))

lines.append("")
lines.append("== strides ==")
offs = [c[0] for c in cands]
lines.append(str([hex(o) for o in offs]))
diffs = [offs[i + 1] - offs[i] for i in range(len(offs) - 1)]
lines.append("diffs: %s" % diffs)

lines.append("")
lines.append("== interpreted: name -> i16 at +5, i16 at +6..8 ==")
for off, ptr, s, tail in cands:
    v5 = struct.unpack_from("<h", data, off + 5)[0]
    v4 = struct.unpack_from("<H", data, off + 4)[0]
    lines.append("  %-34s  u16@+4=%-7d i16@+5=%-7d" % (s, v4, v5))

with open(OUT, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
print("wrote", OUT, len(lines), "lines")
