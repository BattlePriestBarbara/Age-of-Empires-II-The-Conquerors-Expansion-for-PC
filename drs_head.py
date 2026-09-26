"""Hex dump the first bytes of each gamedata DRS to pin down the header layout."""
import os
import struct

GAME = os.environ.get("AOE2HD_DIR") or r"D:\新建文件夹 (10)\3DMGAME_Age_of_Empires_II_HD.CHS.Green\Age of Empires II HD\Data"
out = []
for f in ("gamedata.drs", "gamedata_x1.drs", "gamedata_x1_p1.drs"):
    p = os.path.join(GAME, f)
    data = open(p, "rb").read()
    out.append("=" * 78)
    out.append("%s size=%d" % (f, len(data)))
    for base in (0, 64, 128):
        chunk = data[base:base + 64]
        hexs = " ".join("%02x" % c for c in chunk)
        txt = "".join(chr(c) if 32 <= c < 127 else "." for c in chunk)
        out.append("  @%-5d hex=%s" % (base, hexs))
        out.append("  @%-5d asc=%s" % (base, txt))
    out.append("  ints at 56,60  : %s" % (struct.unpack_from("<ii", data, 56),))
    out.append("  ints at 60,64  : %s" % (struct.unpack_from("<ii", data, 60),))
    out.append("  ints at 56,64  : %s" % (struct.unpack_from("<ii", data, 56),))
open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "drs_head_out.txt"), "w", encoding="utf-8").write("\n".join(out))
print("\n".join(out))
