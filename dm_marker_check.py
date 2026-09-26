"""dm_marker_check.py -- state of the live game archives vs backup / patched copies.

    python dm_marker_check.py

Prints, for every DRS entry the patch touches, the size/md5/marker state of
   * the pristine backup (backup_drs\\*.orig),
   * the freshly repacked copy (patched_drs\\),
   * the file currently installed in the game (Data\\).
"""
import hashlib
import os

from drs_lib import Drs

W = os.path.dirname(os.path.abspath(__file__))
GAME = os.environ.get("AOE2HD_DIR") or r"D:\新建文件夹 (10)\3DMGAME_Age_of_Empires_II_HD.CHS.Green\Age of Empires II HD"
DATA = os.path.join(GAME, "Data")
# key -> markers to look for; the first one is the current build, the extra ones
# are the superseded blocks (their presence means a stale file is in place)
MARKERS = {
    (b"anib", 60002): (b"AI FIX V3", b"AI FIX V2", b"HD DEATH-MATCH AI PATCH"),
    (b"anib", 60001): (b"AI FIX BASE", b"catch-all for unknown population limits"),
}
FILES = ("gamedata.drs", "gamedata_x1.drs")
COPIED = os.path.join(W, "patched_drs2")
BACKUP = os.path.join(W, "backup_drs")


def md5(path):
    return hashlib.md5(open(path, "rb").read()).hexdigest()


def main():
    for name in FILES:
        live = os.path.join(DATA, name)
        patched = os.path.join(COPIED, name)
        bak = os.path.join(BACKUP, name + ".orig")
        print("=" * 76)
        for label, path in (("backup ", bak), ("patched", patched), ("live   ", live)):
            if os.path.exists(path):
                print("  %s  %9d bytes  md5 %s  %s" % (label, os.path.getsize(path), md5(path), path))
        if not os.path.exists(bak):
            continue
        ob, oc, ol = Drs(bak), Drs(patched), Drs(live)
        for key, markers in sorted(MARKERS.items()):
            try:
                pb = ob.payload(*key)
            except KeyError:
                continue
            pc = oc.payload(*key)
            pl = ol.payload(*key)

            def hit(payload):
                low = payload.lower()
                found = ",".join(m.decode() for m in markers if m.lower() in low)
                return found or "no marker"

            print("  %s_%-6d backup %6d B  patched %6d B(%s)  live %6d B(%s)  patched==live: %s"
                  % (key[0].decode(), key[1], len(pb), len(pc), hit(pc),
                     len(pl), hit(pl), pc == pl))
        diffs = [k for k in ((e, i) for e, i, _, _ in ob.entries())
                 if ob.payload(*k) != ol.payload(*k)]
        print("  entries differing between backup and live: %s" % diffs)


if __name__ == "__main__":
    main()
