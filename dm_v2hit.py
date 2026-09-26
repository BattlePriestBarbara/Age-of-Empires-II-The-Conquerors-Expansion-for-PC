"""dm_v2hit.py -- make sure the current payloads carry no marker text of an
earlier build.

Why this matters twice over:
  * dm_install2.py refuses to finish if a superseded block is still installed,
    so our own text must not contain the old marker (it did: a comment quoted
    the old start-up line verbatim, which made that check fire on the *new*
    file);
  * dm_patch2.strip_v1() cuts the script at the first old marker, so an old
    marker inside our own block would make a re-run cut the block in half.
"""
import hashlib
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from drs_lib import Drs

W = os.path.dirname(os.path.abspath(__file__))
GAME = os.environ.get("AOE2HD_DIR") or (r"D:\新建文件夹 (10)\3DMGAME_Age_of_Empires_II_HD.CHS.Green"
        r"\Age of Empires II HD")
OUT = os.path.join(W, "patch_out2")
PATCHED = os.path.join(W, "patched_drs2")
BACKUP = os.path.join(W, "backup_drs")

# b"HD DEATH-MATCH AI PATCH" is v1's header, b"AI FIX V2" v2's
STALE = (b"HD DEATH-MATCH AI PATCH", b"AI FIX V2")
CURRENT = (b"AI FIX V3", b"AI FIX BASE")

jobs = [("built payload x1", os.path.join(OUT, "x1_drs_anib_60002.bin"), None),
        ("built payload aok", os.path.join(OUT, "aok_drs_anib_60002.bin"), None),
        ("built payload x1 base", os.path.join(OUT, "x1_drs_anib_60001.bin"), None),
        ("built payload aok base", os.path.join(OUT, "aok_drs_anib_60001.bin"), None),
        ("repacked gamedata_x1.drs", os.path.join(PATCHED, "gamedata_x1.drs"), (b"anib", 60002)),
        ("repacked gamedata.drs", os.path.join(PATCHED, "gamedata.drs"), (b"anib", 60002)),
        ("LIVE  gamedata_x1.drs", os.path.join(GAME, "Data", "gamedata_x1.drs"), (b"anib", 60002)),
        ("LIVE  gamedata.drs", os.path.join(GAME, "Data", "gamedata.drs"), (b"anib", 60002))]

bad = 0
for label, path, key in jobs:
    if not os.path.exists(path):
        print("%-26s MISSING %s" % (label, path))
        continue
    data = Drs(path).payload(*key) if key else open(path, "rb").read()
    low = data.lower()
    hits = [m.decode() for m in STALE if low.count(m.lower())]
    have = [m.decode() for m in CURRENT if m.lower() in low]
    print("%-26s %7d B  md5 %s  stale=%-28s current=%s"
          % (label, len(data), hashlib.md5(data).hexdigest(),
             ",".join(hits) or "none", ",".join(have) or "none"))
    if label.startswith("LIVE"):
        continue
    if hits:
        bad += 1
        for m in STALE:
            i = low.find(m.lower())
            while i >= 0:
                print("     %r at offset %d: %r" % (m.decode(), i,
                                                    data[max(0, i - 60):i + 30]))
                i = low.find(m.lower(), i + 1)
print("\npayloads carrying a stale marker: %d" % bad)
