"""Dump the table structure of an AoE2 DRS archive (read-only inspection)."""
import struct
import sys


def dump(path, show_head=64):
    data = open(path, "rb").read()
    out = []
    out.append("=" * 72)
    out.append("FILE: %s size: %d" % (path, len(data)))
    out.append("copyright : %r" % data[0:40])
    out.append("version   : %r" % data[40:44])
    out.append("ftype     : %r" % data[44:56])
    n_tables, first_off = struct.unpack_from("<ii", data, 56)
    out.append("n_tables  : %d  first_file_offset: %d" % (n_tables, first_off))
    pos = 64
    tables = []
    for _ in range(n_tables):
        ext = data[pos:pos + 4]
        off, n_files = struct.unpack_from("<ii", data, pos + 4)
        tables.append((ext, off, n_files))
        pos += 12
    for ext, off, n_files in tables:
        out.append("-" * 72)
        out.append("table ext=%r table_offset=%d n_files=%d" % (ext, off, n_files))
        for i in range(n_files):
            fid, foff, fsize = struct.unpack_from("<iii", data, off + 12 * i)
            head = data[foff:foff + show_head]
            head = head.replace(b"\r", b"|").replace(b"\n", b"|")
            head = "".join(chr(c) if 32 <= c < 127 else "~" for c in head)
            out.append("   id=%-6d off=%-9d size=%-8d head=%s"
                       % (fid, foff, fsize, head))
    text = "\n".join(out)
    with open("drs_report.txt", "a", encoding="utf-8") as fh:
        fh.write(text + "\n")
    print(text)


if __name__ == "__main__":
    for p in sys.argv[1:]:
        dump(p)
