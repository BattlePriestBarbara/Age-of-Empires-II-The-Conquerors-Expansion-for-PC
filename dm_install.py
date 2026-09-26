"""
Install the patched death-match AI archives into the game.

Safe procedure:
  1. copy the current gamedata*.drs into backup_drs (once, md5 recorded)
  2. copy the patched archives from patched_drs into <game>\\Data
  3. verify: md5 of installed files, and re-parse the installed archive to prove
     that anib_60002 carries the patch while every other entry is untouched
"""
import hashlib
import os
import shutil
import time

from drs_lib import Drs

W = os.path.dirname(os.path.abspath(__file__))
GAME = os.environ.get("AOE2HD_DIR") or r"D:\新建文件夹 (10)\3DMGAME_Age_of_Empires_II_HD.CHS.Green\Age of Empires II HD"
DATA = os.path.join(GAME, "Data")
PATCHED = os.path.join(W, "patched_drs")
BACKUP = os.path.join(W, "backup_drs")
MARKER = b"HD DEATH-MATCH AI PATCH"
CONST_MARKER = b"catch-all for unknown population limits"
FILES = ("gamedata.drs", "gamedata_x1.drs")
# exactly these entries are allowed to differ from the pristine backup
EXPECTED_DIFFS = {
    "gamedata.drs": {(b"anib", 60002), (b"anib", 60010)},
    "gamedata_x1.drs": {(b"anib", 60002), (b"anib", 60027)},
}
# (ext, id) -> marker that must be present in that entry after patching
MARKERS = {(b"anib", 60002): MARKER, (b"anib", 60010): CONST_MARKER,
           (b"anib", 60027): CONST_MARKER}


def md5(path):
    return hashlib.md5(open(path, "rb").read()).hexdigest()


def main():
    os.makedirs(BACKUP, exist_ok=True)
    log = []
    for name in FILES:
        game_file = os.path.join(DATA, name)
        bak = os.path.join(BACKUP, name + ".orig")
        patched = os.path.join(PATCHED, name)

        orig_md5 = md5(game_file)
        log.append("=== %s" % name)
        log.append("  live file : %s  md5 %s" % (game_file, orig_md5))
        if not os.path.exists(bak):
            shutil.copy2(game_file, bak)
            log.append("  backup    : %s  md5 %s  (created)" % (bak, md5(bak)))
        else:
            log.append("  backup    : %s  md5 %s  (kept)" % (bak, md5(bak)))
        # the backup must be a pristine (unpatched) archive
        b = Drs(bak)
        for key, marker in MARKERS.items():
            assert marker not in b.payload(*key), \
                "the backup already contains the patch (%r) - restore the original first" % key
        live = Drs(game_file)
        for key in sorted(EXPECTED_DIFFS[name]):
            marker = MARKERS[key]
            payload = live.payload(*key)
            log.append("  live %s_%d : %d bytes, script md5 %s, patch present: %s" %
                       (key[0].decode(), key[1], len(payload),
                        hashlib.md5(payload).hexdigest(), marker in payload))
        log.append("  live archive md5 %s" % orig_md5)
        shutil.copy2(patched, game_file)
        log.append("  installed : %s  md5 %s" % (game_file, md5(game_file)))

        d = Drs(game_file)
        for key in sorted(EXPECTED_DIFFS[name]):
            marker = MARKERS[key]
            payload = d.payload(*key)
            assert marker in payload, "patch marker missing for %r in the installed archive!" % (key,)
            log.append("  patch marker found in the installed %s_%d (%d bytes)"
                       % (key[0].decode(), key[1], len(payload)))
        ob = Drs(bak)
        orig_map = {(e, fid): (size, dig) for e, fid, size, dig in ob.entries()}
        new_map = {(e, fid): (size, dig) for e, fid, size, dig in d.entries()}
        assert set(orig_map) == set(new_map), "entry set changed!"
        diffs = [(k, orig_map[k], new_map[k]) for k in sorted(orig_map) if orig_map[k] != new_map[k]]
        log.append("  installed archive: %d entries, %d differ from the backup: %s" %
                   (len(new_map), len(diffs), diffs))
        got = {k for k, _, _ in diffs}
        assert got == EXPECTED_DIFFS[name], \
            "unexpected set of changed entries: %s (expected %s)" % (got, EXPECTED_DIFFS[name])

    stamp = time.strftime("%Y-%m-%d %H:%M:%S")
    log.append("")
    log.append("done at %s" % stamp)
    txt = "\n".join(log)
    open(os.path.join(W, "dm_install_report.txt"), "w", encoding="utf-8").write(txt + "\n")
    print(txt)


if __name__ == "__main__":
    main()
