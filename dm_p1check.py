"""dm_p1check.py -- does gamedata_x1_p1.drs also carry the AI scripts?

AoE2 HD ships three data archives in <game>\\Data:

    gamedata.drs         (AoK)
    gamedata_x1.drs      (The Conquerors)
    gamedata_x1_p1.drs   (Conquerors patch 1 -- highest priority)

The v1 patch was installed into gamedata.drs / gamedata_x1.drs only.  If the
engine resolves anib_60002 / anib_60027 from gamedata_x1_p1.drs, the patch is
never loaded and the AI behaves exactly like the retail one (the reported
"still only gathers" symptom).

This script prints, for every archive, the entry ids and the md5 of the AI
scripts, so we can see whether _p1 duplicates them and whether the content is
identical to the backup.
"""
import hashlib
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from drs_lib import Drs  # noqa: E402

W = os.path.dirname(os.path.abspath(__file__))
GAME = os.environ.get("AOE2HD_DIR") or (r"D:\新建文件夹 (10)\3DMGAME_Age_of_Empires_II_HD.CHS.Green"
        r"\Age of Empires II HD\Data")
BACKUP = os.path.join(W, "backup_drs")
WANT = [(b"anib", 60001), (b"anib", 60002), (b"anib", 60010),
        (b"anib", 60026), (b"anib", 60027)]
ARCHIVES = ("gamedata.drs", "gamedata_x1.drs", "gamedata_x1_p1.drs")

out = []


def digests(path):
    if not os.path.exists(path):
        return None, {}
    d = Drs(path)
    got = {}
    for key in WANT:
        try:
            pl = d.payload(*key)
        except Exception:
            continue
        got[key] = (len(pl), hashlib.md5(pl).hexdigest())
    ids = sorted(fid for e, fid, s, m in d.entries() if e == b"anib")
    return ids, got


for name in ARCHIVES:
    live = os.path.join(GAME, name)
    out.append("=" * 78)
    out.append("=== %s" % name)
    if not os.path.exists(live):
        out.append("    MISSING: %s" % live)
        continue
    ids, got = digests(live)
    out.append("    %d bytes, anib ids present: %s" % (os.path.getsize(live), ids))
    for key in WANT:
        if key in got:
            out.append("    %s_%-5d  %7d bytes  md5 %s" % (key[0].decode(), key[1],
                                                           got[key][0], got[key][1]))
        else:
            out.append("    %s_%-5d  absent" % (key[0].decode(), key[1]))
    bak = os.path.join(BACKUP, name + ".orig")
    if os.path.exists(bak):
        _, bgot = digests(bak)
        for key in WANT:
            if key in got and key in bgot:
                same = "SAME as backup" if got[key] == bgot[key] else "differs from backup"
                out.append("    %s_%-5d  %s" % (key[0].decode(), key[1], same))

out.append("")
out.append("=== cross-archive comparison of the AI scripts (live copies)")
_, x1 = digests(os.path.join(GAME, "gamedata_x1.drs"))
_, p1 = digests(os.path.join(GAME, "gamedata_x1_p1.drs"))
_, aok = digests(os.path.join(GAME, "gamedata.drs"))
for key in WANT:
    row = []
    for label, src in (("aok", aok), ("x1", x1), ("x1p1", p1)):
        row.append("%s=%s" % (label, (src[key][1][:8] + "..") if key in src else "-"))
    out.append("    %s_%-5d  %s" % (key[0].decode(), key[1], "  ".join(row)))

txt = "\n".join(out)
open(os.path.join(W, "dm_p1check_out.txt"), "w", encoding="utf-8").write(txt + "\n")
print(txt)
