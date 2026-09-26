"""
One-shot pipeline: (re)build the patch, repack the DRS archives, verify, install.

Use this after editing the tuning constants in dm_patch.py:

    python dm_rebuild.py

Steps
  1. dm_patch.py     -> patch_out\\{aok,x1}_drs_anib_60002.bin  (+ copies the
                        patched script to patched_scripts\\ for inspection)
  2. dm_apply.py     -> patched_drs\\gamedata.drs, patched_drs\\gamedata_x1.drs
  3. dm_verify.py    -> paren/preprocessor balance of original vs patched
  4. dm_install.py   -> backup + install into the game + hash verification
"""
import os
import runpy
import sys

W = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, W)
MAKE_SCRIPTS = os.path.join(W, "patched_scripts")


def main():
    os.makedirs(MAKE_SCRIPTS, exist_ok=True)
    runpy.run_path(os.path.join(W, "dm_patch.py"), run_name="__main__")
    runpy.run_path(os.path.join(W, "dm_apply.py"), run_name="__main__")
    runpy.run_path(os.path.join(W, "dm_verify.py"), run_name="__main__")
    runpy.run_path(os.path.join(W, "dm_const_audit.py"), run_name="__main__")
    # keep readable copies of the patched scripts
    import shutil
    for src, dst in (
            (os.path.join(W, "patch_out", "x1_drs_anib_60002.bin"),
             os.path.join(MAKE_SCRIPTS, "petersen deathmatch (Conquerors).per")),
            (os.path.join(W, "patch_out", "aok_drs_anib_60002.bin"),
             os.path.join(MAKE_SCRIPTS, "petersen deathmatch (Age of Kings).per")),
            (os.path.join(W, "patch_out", "x1_drs_anib_60027.bin"),
             os.path.join(MAKE_SCRIPTS, "petersen constants (Conquerors).per")),
            (os.path.join(W, "patch_out", "aok_drs_anib_60010.bin"),
             os.path.join(MAKE_SCRIPTS, "petersen constants (Age of Kings).per"))):
        shutil.copy2(src, dst)
    runpy.run_path(os.path.join(W, "dm_install.py"), run_name="__main__")
    print("\npipeline finished - see dm_patch_report.txt / dm_repack_report.txt / "
          "dm_verify_out.txt / dm_const_audit_out.txt / dm_install_report.txt")


if __name__ == "__main__":
    main()
