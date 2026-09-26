"""Scan the exe for tables of small integers in the 60000-range (DRS id tables for the AI files)."""
import struct
import sys

EXE = ("D:\\\u65b0\u5efa\u6587\u4ef6\u5939 (10)\\3DMGAME_Age_of_Empires_II_HD.CHS.Green"
       "\\Age of Empires II HD\\AoK HD.exe")


def scan(lo=59900, hi=60100, min_len=4):
    data = open(EXE, "rb").read()
    hits = []
    i = 0
    n = len(data) - 4
    while i < n:
        v = struct.unpack_from("<i", data, i)[0]
        if lo <= v <= hi:
            vals = []
            j = i
            while j < n:
                w = struct.unpack_from("<i", data, j)[0]
                if not (lo <= w <= hi):
                    break
                vals.append(w)
                j += 4
            if len(vals) >= min_len:
                hits.append((i, vals))
                i = j
                continue
        i += 1
    print("== int32 runs in [%d,%d] (len>=%d): %d" % (lo, hi, min_len, len(hits)))
    for off, vals in hits[:60]:
        print("   @%d  n=%d  %s" % (off, len(vals), vals))
    return hits


if __name__ == "__main__":
    scan(int(sys.argv[1]) if len(sys.argv) > 1 else 59900,
         int(sys.argv[2]) if len(sys.argv) > 2 else 60100,
         int(sys.argv[3]) if len(sys.argv) > 3 else 4)
