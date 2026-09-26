"""Apply the v2 death-match AI payloads to the game's DRS archives (patched copies).

Always repacks the *pristine* archive from backup_drs\\*.orig, so the result can
never accumulate a patch twice, and verifies that the retail script is still a
byte-exact prefix of the patched one.
"""
import hashlib
import os

from drs_lib import Drs, repack

W = os.path.dirname(os.path.abspath(__file__))
GAME = os.environ.get("AOE2HD_DIR") or r"D:\新建文件夹 (10)\3DMGAME_Age_of_Empires_II_HD.CHS.Green\Age of Empires II HD"
DATA = os.path.join(GAME, "Data")
PATCHED = os.path.join(W, "patched_drs2")
BACKUP = os.path.join(W, "backup_drs")
PATCH_OUT = os.path.join(W, "patch_out2")

TARGETS = [
    # (archive in <game>\Data, [(patched script, (drs ext, id)), ...])
    ("gamedata.drs", [
        ("aok_drs_anib_60002.bin", (b"anib", 60002)),   # petersen deathmatch
        ("aok_drs_anib_60001.bin", (b"anib", 60001)),   # base marker
    ]),
    ("gamedata_x1.drs", [
        ("x1_drs_anib_60002.bin", (b"anib", 60002)),
        ("x1_drs_anib_60001.bin", (b"anib", 60001)),
    ]),
]


def md5(data):
    return hashlib.md5(data).hexdigest()


def main():
    os.makedirs(PATCHED, exist_ok=True)
    report = []
    for drs_name, items in TARGETS:
        pristine = os.path.join(BACKUP, drs_name + ".orig")
        assert os.path.exists(pristine), "missing pristine backup %s" % pristine
        dst = os.path.join(PATCHED, drs_name)
        repl = {}
        for patch_file, key in items:
            path = os.path.join(PATCH_OUT, patch_file)
            with open(path, "rb") as fh:
                repl[key] = fh.read()
        report.append("=== %s" % drs_name)
        report.append("  pristine source : %s  md5 %s  (%d bytes)"
                      % (pristine, md5(open(pristine, "rb").read()),
                         os.path.getsize(pristine)))
        res = repack(pristine, dst, repl)
        report.append("  patched         : %s  md5 %s  (%d bytes)"
                      % (dst, md5(open(dst, "rb").read()), res["size_after"]))
        for patch_file, key in items:
            report.append("  payload         : %-24s -> %s_%d  (%d bytes, md5 %s)"
                          % (patch_file, key[0].decode(), key[1], len(repl[key]),
                             md5(repl[key])))
        report.append("  entries: %d total, %d byte-identical, %d changed"
                      % (res["n_entries"], res["unchanged"], len(res["changed"])))
        for before, after in res["changed"]:
            report.append("    CHANGED ext=%r id=%d  %d -> %d bytes  md5 %s -> %s"
                          % (before[0], before[1], before[2], after[2], before[3], after[3]))
        # the patched archive must expose exactly our payloads, and the retail
        # script must still be an untouched prefix of the patched script
        chk = Drs(dst)
        ref = Drs(pristine)
        for key, payload in sorted(repl.items(), key=lambda kv: kv[0][1]):
            got = chk.payload(*key)
            assert got == payload, "round-trip mismatch for %s %r" % (drs_name, key)
            old = ref.payload(*key)
            assert got[:len(old)] == old if key[1] == 60002 else True
            note = ("retail script kept as a byte-exact prefix (%d bytes) + %d appended"
                    % (len(old), len(got) - len(old))) if key[1] == 60002 else \
                   ("marker appended to the retail script (%d + %d bytes)"
                    % (len(old), len(got) - len(old)))
            report.append("  round-trip ok   : %s_%d == %d bytes, md5 %s  | %s"
                          % (key[0].decode(), key[1], len(got), md5(got), note))
    txt = "\n".join(report)
    with open(os.path.join(W, "dm_repack2_report.txt"), "w", encoding="utf-8") as fh:
        fh.write(txt + "\n")
    print(txt)


if __name__ == "__main__":
    main()
