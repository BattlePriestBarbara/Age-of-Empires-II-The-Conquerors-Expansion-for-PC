"""
Install the v3 patched death-match AI archives into the game.

Safe procedure (same as dm_install.py):
  1. keep the pristine backup in backup_drs (created by v1, md5 shown)
  2. copy the patched archives from patched_drs2 into <game>\\Data
  3. verify: md5 of the installed files, the patch markers, the retail script as
     a byte-exact prefix, and that *only* the expected entries changed
"""
import hashlib
import os
import shutil
import time

from drs_lib import Drs

W = os.path.dirname(os.path.abspath(__file__))
GAME = os.environ.get("AOE2HD_DIR") or r"D:\新建文件夹 (10)\3DMGAME_Age_of_Empires_II_HD.CHS.Green\Age of Empires II HD"
DATA = os.path.join(GAME, "Data")
PATCHED = os.path.join(W, "patched_drs2")
BACKUP = os.path.join(W, "backup_drs")
V1_MARKER = b"HD DEATH-MATCH AI PATCH"
FILES = ("gamedata.drs", "gamedata_x1.drs")
# exactly these entries may differ from the pristine backup
EXPECTED_DIFFS = {
    "gamedata.drs": {(b"anib", 60002), (b"anib", 60001)},
    "gamedata_x1.drs": {(b"anib", 60002), (b"anib", 60001)},
}
# (ext, id) -> text that must be present after patching
MARKERS = {(b"anib", 60002): b"AI FIX V3", (b"anib", 60001): b"AI FIX BASE"}
# text of a superseded build that must *not* be left in the installed archive
STALE = {(b"anib", 60002): (b"AI FIX V2", b"HD DEATH-MATCH AI PATCH")}


def md5(path):
    with open(path, "rb") as fh:
        return hashlib.md5(fh.read()).hexdigest()


def main():
    log = []
    for name in FILES:
        game_file = os.path.join(DATA, name)
        bak = os.path.join(BACKUP, name + ".orig")
        patched = os.path.join(PATCHED, name)
        assert os.path.exists(bak), "missing pristine backup %s" % bak
        assert os.path.exists(patched), "run dm_patch2.py + dm_apply2.py first"

        log.append("=== %s" % name)
        log.append("  live before : md5 %s  (%d bytes)"
                   % (md5(game_file), os.path.getsize(game_file)))
        log.append("  backup      : %s  md5 %s" % (bak, md5(bak)))
        b = Drs(bak)
        for key in sorted(EXPECTED_DIFFS[name]):
            payload = b.payload(*key)
            assert V1_MARKER not in payload, \
                "the backup is not pristine (%r carries a v1 block)" % (key,)
            log.append("  backup %s_%d : %d bytes, md5 %s, no patch"
                       % (key[0].decode(), key[1], len(payload), hashlib.md5(payload).hexdigest()))
        if os.path.exists(game_file):
            live = Drs(game_file)
            log.append("  live anib_60002 currently carries the v1 block: %s"
                       % (V1_MARKER in live.payload(b"anib", 60002)))

        shutil.copy2(patched, game_file)
        log.append("  installed   : md5 %s  (%d bytes)" % (md5(game_file), os.path.getsize(game_file)))

        d = Drs(game_file)
        for key in sorted(EXPECTED_DIFFS[name]):
            marker = MARKERS[key]
            payload = d.payload(*key)
            assert marker.lower() in payload.lower(), "patch marker missing for %r" % (key,)
            for old in STALE.get(key, ()):
                assert old.lower() not in payload.lower(), \
                    "the superseded block %r is still installed in %r" % (old, key)
            target = d.payload(b"anib", 60002) if key[1] == 60002 else None
            note = "marker present, no superseded block"
            if target is not None:
                old = Drs(bak).payload(*key)
                assert target[:len(old)] == old, "the retail script is not the prefix of the patch!"
                note = ("marker present, retail script intact as a %d byte prefix "
                        "(+%d bytes appended)" % (len(old), len(target) - len(old)))
            log.append("  installed %s_%d : %d bytes, %s"
                       % (key[0].decode(), key[1], len(payload), note))
        ob = Drs(bak)
        orig_map = {(e, fid): (size, dig) for e, fid, size, dig in ob.entries()}
        new_map = {(e, fid): (size, dig) for e, fid, size, dig in d.entries()}
        assert set(orig_map) == set(new_map), "entry set changed!"
        diffs = sorted(k for k in orig_map if orig_map[k] != new_map[k])
        log.append("  installed archive: %d entries, %d differ from the backup: %s"
                   % (len(new_map), len(diffs), diffs))
        assert set(diffs) == EXPECTED_DIFFS[name], \
            "unexpected changed entries: %s (expected %s)" % (set(diffs), EXPECTED_DIFFS[name])

    log.append("")
    log.append("done at %s" % time.strftime("%Y-%m-%d %H:%M:%S"))
    txt = "\n".join(log)
    with open(os.path.join(W, "dm_install2_report.txt"), "w", encoding="utf-8") as fh:
        fh.write(txt + "\n")
    print(txt)


if __name__ == "__main__":
    main()
