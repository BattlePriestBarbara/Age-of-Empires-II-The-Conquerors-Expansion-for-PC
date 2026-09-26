"""Probe the real DRS header/table layout of the game's gamedata*.drs so we can repack safely."""
import hashlib
import os
import struct
import sys

GAME = os.environ.get("AOE2HD_DIR") or r"D:\新建文件夹 (10)\3DMGAME_Age_of_Empires_II_HD.CHS.Green\Age of Empires II HD\Data"


def probe(path):
    data = open(path, "rb").read()
    out = []
    out.append("=" * 78)
    out.append("FILE %s  size=%d  md5=%s" % (os.path.basename(path), len(data),
                                             hashlib.md5(data).hexdigest()))
    out.append("copyright = %r" % data[0:40])
    out.append("version   = %r" % data[40:44])
    out.append("ftype     = %r" % data[44:56])
    n_tables, tbl_off = struct.unpack_from("<ii", data, 56)
    out.append("n_tables=%d  table_list_offset=%d" % (n_tables, tbl_off))
    pos = tbl_off
    for _ in range(n_tables):
        ext = data[pos:pos + 4]
        off, n = struct.unpack_from("<ii", data, pos + 4)
        entries = []
        for i in range(n):
            fid, foff, fsize = struct.unpack_from("<iii", data, off + 12 * i)
            entries.append((fid, foff, fsize))
        out.append("  table %-4r info_off=%-9d n_files=%-5d first_ids=%s" %
                   (ext, off, n, [e[0] for e in entries[:6]]))
        if ext in (b"anib",):
            for fid, foff, fsize in entries:
                if fid in (60001, 60002, 60026, 60027):
                    abs_try = data[foff:foff + 16]
                    rel_try = data[off + foff:off + foff + 16]
                    out.append("     id=%d off=%-9d size=%-8d abs=%-20r rel=%-20r" %
                               (fid, foff, fsize, abs_try, rel_try))
        pos += 12
    return "\n".join(out)


if __name__ == "__main__":
    txt = []
    for f in ("gamedata.drs", "gamedata_x1.drs", "gamedata_x1_p1.drs"):
        p = os.path.join(GAME, f)
        if os.path.exists(p):
            txt.append(probe(p))
    open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "drs_probe_out.txt"), "w", encoding="utf-8").write("\n".join(txt))
    print("ok")
