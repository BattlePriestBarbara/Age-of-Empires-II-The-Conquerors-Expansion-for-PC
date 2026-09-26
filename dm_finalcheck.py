"""End-to-end check of the installed patch + look for any other place the game could load AI from."""
import glob
import hashlib
import os

from drs_lib import Drs

W = os.path.dirname(os.path.abspath(__file__))
GAME = os.environ.get("AOE2HD_DIR") or r"D:\新建文件夹 (10)\3DMGAME_Age_of_Empires_II_HD.CHS.Green\Age of Empires II HD"
DATA = os.path.join(GAME, "Data")
out = []


def md5(p):
    return hashlib.md5(open(p, "rb").read()).hexdigest()


# 1) installed == patched_drs
for name in ("gamedata.drs", "gamedata_x1.drs"):
    a = os.path.join(DATA, name)
    b = os.path.join(W, "patched_drs", name)
    out.append("installed %-16s md5 %s" % (name, md5(a)))
    out.append("patched   %-16s md5 %s   identical=%s" % (name, md5(b), md5(a) == md5(b)))

# 2) tail of the freshly installed scripts (read straight out of the game's archives)
for name, key, n in (("gamedata_x1.drs", (b"anib", 60002), 42),
                     ("gamedata_x1.drs", (b"anib", 60027), 46),
                     ("gamedata.drs", (b"anib", 60010), 46)):
    d = Drs(os.path.join(DATA, name))
    raw = d.payload(*key)
    rows = raw.decode("latin-1").split("\n")
    out.append("")
    out.append("installed %s_%d (%s): %d bytes, %d lines" %
               (key[0].decode(), key[1], name, len(raw), len(rows)))
    out.append("--- last %d lines ---" % n)
    out.extend(r.rstrip("\r") for r in rows[-n:])

# 3) any other AI script source the game might read?
out.append("")
out.append("--- potential competing AI sources ---")
pats = [os.path.join(GAME, "AI", "**", "*"),
        os.path.join(GAME, "mods", "**", "*"),
        os.path.join(GAME, "Data", "**", "*")]
found = False
for p in pats:
    for f in glob.glob(p, recursive=True):
        if os.path.isfile(f):
            ext = os.path.splitext(f)[1].lower()
            if ext in (".per", ".ai", ".txt") or "ai" in os.path.basename(f).lower():
                out.append("  %s" % f)
                found = True
if not found:
    out.append("  (none)")
open(os.path.join(W, "dm_finalcheck_out.txt"), "w", encoding="utf-8").write("\n".join(out) + "\n")
print("\n".join(out))
