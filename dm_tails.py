"""Small focused dumps -> files (terminal echo is unreliable in this env)."""
import os

W = os.path.dirname(os.path.abspath(__file__))


def load(idx, d="x1_drs"):
    p = os.path.join(W, d, "anib_%d.bin" % idx)
    raw = open(p, "rb").read()
    try:
        return raw, raw.decode("utf-8")
    except UnicodeDecodeError:
        return raw, raw.decode("latin-1")


def section(idx, a, b, title, fh):
    raw, txt = load(idx)
    rows = txt.split("\n")
    fh.write("### anib_%d %s (len=%d bytes, %d lines) %s\n" % (idx, "", len(raw), len(rows), title))
    for i in range(max(0, a - 1), min(b, len(rows))):
        fh.write("%5d| %s\n" % (i + 1, rows[i].rstrip("\r")))
    fh.write("\n")


with open(os.path.join(W, "dm_tails_out.txt"), "w", encoding="utf-8") as f:
    raw, txt = load(60002)
    rows = txt.split("\n")
    n = len(rows)
    f.write("60002 total lines=%d  total bytes=%d\n\n" % (n, len(raw)))
    f.write("=== 60002 last 45 lines ===\n")
    for i in range(n - 45, n):
        f.write("%5d| %s\n" % (i + 1, rows[i].rstrip("\r")))
    f.write("\n=== 60002 last 6 preprocessor lines ===\n")
    for i, r in enumerate(rows):
        if r.startswith("#"):
            f.write("%5d| %s\n" % (i + 1, r.rstrip()))
    f.write("\n=== 60002 first 40 lines ===\n")
    for i in range(0, min(40, n)):
        f.write("%5d| %s\n" % (i + 1, rows[i].rstrip("\r")))

    f.write("\n\n=== 60007 (supplement) preprocessor + DEATH-MATCH context ===\n")
    raw7, txt7 = load(60007)
    r7 = txt7.split("\n")
    f.write("60007 total lines=%d bytes=%d\n" % (len(r7), len(raw7)))
    for i, r in enumerate(r7):
        if r.startswith("#"):
            f.write("%5d| %s\n" % (i + 1, r.rstrip()))
    f.write("\n=== 60007 last 30 lines ===\n")
    for i in range(max(0, len(r7) - 30), len(r7)):
        f.write("%5d| %s\n" % (i + 1, r7[i].rstrip("\r")))

    f.write("\n\n=== 60027 (constants) unit-max / deathmatch-unit-max blocks ===\n")
    raw27, txt27 = load(60027)
    r27 = txt27.split("\n")
    f.write("60027 total lines=%d bytes=%d\n" % (len(r27), len(raw27)))
    for i, r in enumerate(r27):
        s = r.strip()
        if s.startswith("#") or "unit-max" in s or "POPULATION" in s.upper():
            f.write("%5d| %s\n" % (i + 1, r.rstrip("\r")))
    f.write("\n=== 60027 first 20 and last 10 lines ===\n")
    for i in range(0, min(20, len(r27))):
        f.write("%5d| %s\n" % (i + 1, r27[i].rstrip("\r")))
    for i in range(max(0, len(r27) - 10), len(r27)):
        f.write("%5d| %s\n" % (i + 1, r27[i].rstrip("\r")))

print("wrote dm_tails_out.txt")
