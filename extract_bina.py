"""Extract all 'bina' (text) entries of AoE2 DRS files to a folder for analysis."""
import os
import struct
import sys


def extract(path, outdir):
    data = open(path, "rb").read()
    n_tables, _ = struct.unpack_from("<ii", data, 56)
    pos = 64
    os.makedirs(outdir, exist_ok=True)
    for _ in range(n_tables):
        ext = data[pos:pos + 4]
        off, n_files = struct.unpack_from("<ii", data, pos + 4)
        pos += 12
        name = ext.decode("latin-1").strip().replace(" ", "_")
        for i in range(n_files):
            fid, foff, fsize = struct.unpack_from("<iii", data, off + 12 * i)
            blob = data[foff:foff + fsize]
            fn = os.path.join(outdir, "%s_%d.bin" % (name, fid))
            with open(fn, "wb") as fh:
                fh.write(blob)
            print("wrote %-28s %8d bytes" % (fn, fsize))


if __name__ == "__main__":
    extract(sys.argv[1], sys.argv[2])
