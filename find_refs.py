"""Find PE section layout, then locate pointers/references to the AI-name string pool."""
import os
import struct

EXE = r"D:\新建文件夹 (10)\3DMGAME_Age_of_Empires_II_HD.CHS.Green\Age of Empires II HD\AoK HD.exe"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), r"find_refs_out.txt")
lines = []

with open(EXE, "rb") as f:
    data = f.read()
lines.append("exe size %d" % len(data))

pe = data.find(b"PE\0\0")
lines.append("PE sig at 0x%x" % pe)
nsec, tstamp = struct.unpack_from("<HH", data, pe + 6)
opt_size = struct.unpack_from("<H", data, pe + 20)[0]
lines.append("sections=%d opt_hdr_size=%d" % (nsec, opt_size))
magic = struct.unpack_from("<H", data, pe + 24)[0]
lines.append("optional magic=0x%x (%s)" % (magic, "PE32" if magic == 0x10b else "PE32+"))
image_base = struct.unpack_from("<I", data, pe + 24 + 28)[0]
lines.append("image base = 0x%x" % image_base)
sec_off = pe + 24 + opt_size
secs = []
for i in range(nsec):
    o = sec_off + i * 40
    name = data[o:o + 8].rstrip(b"\0").decode("latin-1")
    vsize, va, rawsize, rawptr = struct.unpack_from("<IIII", data, o + 8)
    secs.append((name, va, vsize, rawptr, rawsize))
    lines.append("  %-8s VA=0x%08x vsize=0x%06x raw=0x%08x rawsize=0x%06x" % (name, va, vsize, rawptr, rawsize))


def off2va(off):
    for name, va, vsize, rawptr, rawsize in secs:
        if rawptr <= off < rawptr + rawsize:
            return image_base + va + (off - rawptr), name
    return None, None


def va2off(va):
    for name, sva, vsize, rawptr, rawsize in secs:
        if sva <= va - image_base < sva + max(vsize, rawsize):
            return rawptr + (va - image_base - sva)
    return None


# string pool offsets of interest
targets = [0x383bd0, 0x383e2c, 0x383e44, 0x383c08, 0x383d64]
lines.append("")
for t in targets:
    va, sec = off2va(t)
    lines.append("offset 0x%x -> VA 0x%x (%s): %r" % (t, va or 0, sec, data[t:t + 32].split(b"\0")[0]))

lines.append("")
lines.append("== references (4-byte LE pointer to 'petersen deathmatch.per' VA and neighbours) ==")
for t in targets:
    va, sec = off2va(t)
    if va is None:
        continue
    pat = struct.pack("<I", va)
    idx = data.find(pat)
    hits = []
    while idx != -1:
        hits.append(idx)
        idx = data.find(pat, idx + 1)
    lines.append("VA 0x%08x referenced at %d places: %s" % (va, len(hits), [hex(h) for h in hits[:20]]))
    for h in hits[:6]:
        lo = max(0, h - 64)
        hi = h + 128
        chunk = data[lo:hi]
        lines.append("   @0x%x sec=%s" % (h, off2va(h)[1]))
        # show as ints and ascii
        ints = struct.unpack_from("<%di" % ((hi - lo) // 4), data, lo)
        lines.append("      ints: " + " ".join(str(x) for x in ints))
        lines.append("      asc : " + "".join(chr(c) if 32 <= c < 127 else "." for c in chunk))

lines.append("")
lines.append("== 2-byte LE occurrences of 60001..60031 ==")
for val in range(60001, 60032):
    pat = struct.pack("<H", val)
    idx = data.find(pat)
    hits = []
    while idx != -1 and len(hits) < 12:
        hits.append(idx)
        idx = data.find(pat, idx + 1)
    if hits:
        lines.append("  %d: %s" % (val, [hex(h) for h in hits]))

with open(OUT, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
print("wrote", OUT, len(lines), "lines")
