"""Full inventory of the game folder: files, sizes, mtimes, plus AI folder hex."""
import os
import time

ROOT = r"D:\新建文件夹 (10)\3DMGAME_Age_of_Empires_II_HD.CHS.Green\Age of Empires II HD"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), r"inventory_out.txt")
lines = []


def fmt(ts):
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(ts))


lines.append("ROOT EXISTS: %s" % os.path.isdir(ROOT))
for dirpath, dirnames, filenames in os.walk(ROOT):
    rel = os.path.relpath(dirpath, ROOT)
    depth = 0 if rel == "." else rel.count(os.sep) + 1
    if depth > 3:
        dirnames[:] = []
        continue
    lines.append("")
    lines.append("[DIR] %s  (%d files, %d subdirs)" % (rel, len(filenames), len(dirnames)))
    for d in sorted(dirnames):
        lines.append("    + %s" % d)
    for f in sorted(filenames):
        fp = os.path.join(dirpath, f)
        try:
            st = os.stat(fp)
            lines.append("    %-42s %9d  %s" % (f, st.st_size, fmt(st.st_mtime)))
        except OSError as e:
            lines.append("    %-42s  ERR %s" % (f, e))

# hex dump of AI\AI.txt
ai = os.path.join(ROOT, "AI", "AI.txt")
if os.path.isfile(ai):
    with open(ai, "rb") as fh:
        raw = fh.read()
    lines.append("")
    lines.append("AI.txt bytes (%d): %r" % (len(raw), raw[:400]))

with open(OUT, "w", encoding="utf-8") as fh:
    fh.write("\n".join(lines))
print("wrote", OUT, len(lines), "lines")
