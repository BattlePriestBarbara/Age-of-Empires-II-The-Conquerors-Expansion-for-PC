"""
Restore the ORIGINAL (unpatched) AI archives into the game.

    python dm_restore.py

Uses the pristine copies in backup_drs and verifies the result.
"""
import hashlib
import os
import shutil

from drs_lib import Drs

W = os.path.dirname(os.path.abspath(__file__))
GAME = os.environ.get("AOE2HD_DIR") or r"D:\新建文件夹 (10)\3DMGAME_Age_of_Empires_II_HD.CHS.Green\Age of Empires II HD"
DATA = os.path.join(GAME, "Data")
BACKUP = os.path.join(W, "backup_drs")
MARKER = b"HD DEATH-MATCH AI PATCH"
CONST_MARKER = b"catch-all for unknown population limits"
EXPECTED = {
    "gamedata.drs": "be574545e247b85a196109836a1f9d44",
    "gamedata_x1.drs": "f41c418333e624b7a1077ad166f9dcb0",
}
# (drs ext, id) -> marker that must be gone after restoring
MARKERS = {(b"anib", 60002): MARKER, (b"anib", 60010): CONST_MARKER,
           (b"anib", 60027): CONST_MARKER}


def md5(p):
    return hashlib.md5(open(p, "rb").read()).hexdigest()


def main():
    log = []
    for name, want in EXPECTED.items():
        bak = os.path.join(BACKUP, name + ".orig")
        dst = os.path.join(DATA, name)
        assert os.path.exists(bak), "missing backup: %s" % bak
        got = md5(bak)
        assert got == want, "backup %s has md5 %s, expected %s" % (bak, got, want)
        shutil.copy2(bak, dst)
        assert md5(dst) == want, "restore failed for %s" % dst
        d = Drs(dst)
        for key, marker in MARKERS.items():
            assert marker not in d.payload(*key), "%r still patched in %s" % (key, name)
        log.append("%s restored: md5 %s (original), anib_60002 = %d bytes, everything unpatched" %
                   (name, md5(dst), len(d.payload(b"anib", 60002))))
    txt = "\n".join(log)
    open(os.path.join(W, "dm_restore_report.txt"), "w", encoding="utf-8").write(txt + "\n")
    print(txt)


if __name__ == "__main__":
    main()
