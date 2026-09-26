"""dm_nest.py -- locate every site that raises AI error code 19
(= ERR3003 Preprocessor nesting too deep) and dump the comparison that guards
it, to read the nesting limit straight out of the disassembly.
"""
import os
import re
import struct

GAME = os.environ.get("AOE2HD_DIR") or (r"D:\新建文件夹 (10)\3DMGAME_Age_of_Empires_II_HD.CHS.Green"
        r"\Age of Empires II HD")
data = open(os.path.join(GAME, "AoK HD.exe"), "rb").read()
out = []

TEXT = (0x1000, 0x34d000)   # raw range of .text
ERR_FIELD = 0x8e0           # [ctx + 0x8e0] = AI error code
codes = {}
n = len(data)
i = TEXT[0]
while i < TEXT[0] + TEXT[1] - 8:
    if data[i] == 0xc7:
        m = data[i + 1]
        mod, reg, rm = m >> 6, (m >> 3) & 7, m & 7
        disp = None
        p = i + 2
        if mod == 2 and rm != 4:
            disp = struct.unpack_from("<i", data, p)[0]
            p += 4
        elif mod == 2 and rm == 4:
            sib = data[p]
            p += 1
            if (sib & 7) == 5:
                disp = struct.unpack_from("<i", data, p)[0]
                p += 4
            else:
                disp = struct.unpack_from("<i", data, p)[0]
                p += 4
        elif mod == 1:
            disp = struct.unpack_from("<b", data, p)[0]
            p += 1
        if disp == ERR_FIELD and reg == 0:
            imm = struct.unpack_from("<I", data, p)[0]
            codes.setdefault(imm, []).append(i)
    i += 1

out.append("=== mov dword [reg+0x%x], IMM  -> raise whose AI error code" % ERR_FIELD)
for imm in sorted(codes):
    out.append("   code %2d raised at: %s"
               % (imm, ", ".join("0x%08x" % (c - TEXT[0] + 0x401000)
                                 for c in codes[imm][:12])))

out.append("\n=== context of the code-19 (nesting too deep) raise site(s)")
for c in codes.get(19, []):
    va = c - TEXT[0] + 0x401000
    lo = max(0, c - 160)
    hi = min(n, c + 64)
    out.append("   --- raise at VA 0x%08x" % va)
    for k in range(lo, hi, 16):
        chunk = data[k:k + 16]
        # crude mnemonics for the common immediates we look for
        out.append("      %08x  %s" % (k, " ".join("%02x" % b for b in chunk)))
    # look backwards for a cmp reg, imm8 (83 f8..ff / 3d)
    back = data[max(0, c - 400):c]
    for m in re.finditer(rb"\x83[\xf8-\xff](.)", back):
        out.append("        cmp reg, 0x%02x  (bytes at 0x%08x)"
                   % (m.group(1)[0], max(0, c - 400) + m.start()))
    for m in re.finditer(rb"\x3d(.{4})", back):
        out.append("        cmp eax, 0x%x"
                   % struct.unpack("<I", m.group(1))[0])

open("dm_nest_out.txt", "w", encoding="utf-8").write("\n".join(out))
print("wrote dm_nest_out.txt")
