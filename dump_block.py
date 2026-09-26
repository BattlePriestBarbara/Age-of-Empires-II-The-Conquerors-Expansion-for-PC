"""dump the appended tails of the built payloads for visual inspection"""
import os

W = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(W, "patch_out2")
JOBS = [
    ("x1_drs_anib_60002.bin", 54203, "dm_block_dump_out.txt"),
    ("x1_drs_anib_60001.bin", 29337, "base_block_dump_out.txt"),
]

for src, cut, dst in JOBS:
    raw = open(os.path.join(OUT, src), "rb").read()
    with open(os.path.join(W, dst), "w", encoding="utf-8", newline="") as fh:
        fh.write(raw[cut:].decode("latin-1"))
    print("%-22s %d bytes total, appended tail %d bytes -> %s" % (src, len(raw), len(raw) - cut, dst))
