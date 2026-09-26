"""dm_direct.py -- (1) which preprocessor directive keywords does the AI
compiler accept?  (2) the nesting-depth limit; (3) how are .per/.ai files
resolved (DRS only, or loose file first)?
"""
import os
import re
import struct

GAME = os.environ.get("AOE2HD_DIR") or (r"D:\新建文件夹 (10)\3DMGAME_Age_of_Empires_II_HD.CHS.Green"
        r"\Age of Empires II HD")
data = open(os.path.join(GAME, "AoK HD.exe"), "rb").read()
out = []


def strings(buf, minlen=3):
    cur = []
    start = 0
    for i, c in enumerate(buf):
        if 32 <= c < 127:
            if not cur:
                start = i
            cur.append(chr(c))
        else:
            if len(cur) >= minlen:
                yield start, "".join(cur)
            cur = []


out.append("=== directive-looking strings in the exe")
seen = set()
for off, s in strings(data, 3):
    if "#" in s and re.search(r"#[a-zA-Z]", s):
        if s not in seen:
            seen.add(s)
            out.append("   %08x  %s" % (off, s[:160]))

out.append("\n=== strings with .per / .ai / anib / %s.per")
for off, s in strings(data, 3):
    low = s.lower()
    if re.search(r"\.(per|ai)\b", low) or "anib" in low or "ai_files" in low:
        out.append("   %08x  %r" % (off, s[:160]))

# ---- error-jump-table: locate the case for the ERR3003 message ----
out.append("\n=== AI error jump table @VA 0x00475284 (27 entries)")
base = 0x475284
tbl = struct.unpack_from("<27I", data, base - 0x400000)
msg_va = 0x00777e0c  # ERR3003 message string
for i, t in enumerate(tbl):
    mark = ""
    if t - 0x400000 >= 0 and t - 0x400000 < len(data):
        chunk = data[t - 0x400000:t - 0x400000 + 240]
        if b"ERR" in chunk:
            m = re.search(rb"ERR\d{4}[^\x00]*", chunk)
            mark = "  -> " + m.group().decode("latin-1")
            if struct.pack("<I", msg_va) in chunk:
                mark += "   <<< nesting-too-deep case"
    out.append("   [%2d] 0x%08x%s" % (i, t, mark))
open("dm_direct_out.txt", "w", encoding="utf-8").write("\n".join(out))
print("wrote dm_direct_out.txt")
