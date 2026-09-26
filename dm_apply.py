"""Apply the death-match AI patch to the game's DRS archives (writes patched copies)."""
import hashlib
import os
import shutil

from drs_lib import Drs, repack

W = os.path.dirname(os.path.abspath(__file__))
GAME = os.environ.get("AOE2HD_DIR") or r"D:\新建文件夹 (10)\3DMGAME_Age_of_Empires_II_HD.CHS.Green\Age of Empires II HD"
DATA = os.path.join(GAME, "Data")
PATCHED = os.path.join(W, "patched_drs")
BACKUP = os.path.join(W, "backup_drs")

TARGETS = [
    # (archive in <game>\Data, [(patched script in patch_out, (drs ext, id)), ...])
    ("gamedata.drs", [
        ("aok_drs_anib_60002.bin", (b"anib", 60002)),      # petersen deathmatch
        ("aok_drs_anib_60010.bin", (b"anib", 60010)),      # constants (fix 4)
    ]),
    ("gamedata_x1.drs", [
        ("x1_drs_anib_60002.bin", (b"anib", 60002)),       # petersen deathmatch
        ("x1_drs_anib_60027.bin", (b"anib", 60027)),       # constants (fix 4)
    ]),
]


def main():
    os.makedirs(PATCHED, exist_ok=True)
    os.makedirs(BACKUP, exist_ok=True)
    report = []
    for drs_name, items in TARGETS:
        # always repack from the pristine original (backup) so that the result is
        # deterministic and cannot accumulate a patch twice
        pristine = os.path.join(BACKUP, drs_name + ".orig")
        src = pristine if os.path.exists(pristine) else os.path.join(DATA, drs_name)
        dst = os.path.join(PATCHED, drs_name)
        repl = {}
        for patch_file, key in items:
            path = os.path.join(W, "patch_out", patch_file)
            repl[key] = open(path, "rb").read()
        report.append("=== %s" % drs_name)
        res = repack(src, dst, repl)
        report.append("  source    : %s  md5 %s  (%d bytes)" %
                      (src, hashlib.md5(open(src, 'rb').read()).hexdigest(), res["size_before"]))
        report.append("  dst     %s  (%d bytes)" % (dst, res["size_after"]))
        for patch_file, key in items:
            report.append("  payload   : %-24s -> %s_%d  (%d bytes)"
                          % (patch_file, key[0].decode(), key[1], len(repl[key])))
        report.append("  entries: %d total, %d byte-identical, %d changed"
                      % (res["n_entries"], res["unchanged"], len(res["changed"])))
        for before, after in res["changed"]:
            report.append("    CHANGED ext=%r id=%d  %d -> %d bytes  md5 %s -> %s" %
                          (before[0], before[1], before[2], after[2], before[3], after[3]))
        # sanity: the patched archive must still expose the patched scripts
        chk = Drs(dst)
        for key, payload in sorted(repl.items(), key=lambda kv: kv[0][1]):
            got = chk.payload(*key)
            assert got == payload, "round-trip mismatch for %s %r" % (drs_name, key)
            report.append("  round-trip ok: %s_%d in the patched archive == %d bytes, md5 %s"
                          % (key[0].decode(), key[1], len(got), hashlib.md5(got).hexdigest()))
    open(os.path.join(W, "dm_repack_report.txt"), "w", encoding="utf-8").write("\n".join(report) + "\n")
    print("\n".join(report))


def res_size(path):
    return os.path.getsize(path) if os.path.exists(path) else -1


if __name__ == "__main__":
    main()
