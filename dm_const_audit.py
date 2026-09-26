"""dm_const_audit.py -- which constants of the DM AI exist only for the 8 classic
population caps (25..200), and how often does the death-match script use them?

At a lobby population limit of 500 the engine defines NONE of the symbols
POPULATION-CAP-25 ... POPULATION-CAP-200 (see dm_exe_ai.py), so every constant
that is defined only inside such a block stays undefined and every rule that
mentions it is invalid -> the Deathmatch AI more or less stops working.
"""
import os
import re
import sys

W = os.path.dirname(os.path.abspath(__file__))
PAIRS = [
    ("Age of Kings (gamedata.drs)",
     os.path.join(W, "aok_drs", "anib_60002.bin"),
     os.path.join(W, "aok_drs", "anib_60010.bin")),
    ("Conquerors (gamedata_x1.drs)",
     os.path.join(W, "x1_drs", "anib_60002.bin"),
     os.path.join(W, "x1_drs", "anib_60027.bin")),
]
DEFCONST = re.compile(r"^\(defconst\s+([A-Za-z0-9\-_]+)\s+(.+?)\)\s*$")


def read(path):
    return open(path, "rb").read().decode("latin-1").replace("\r\n", "\n")


def scan_constants(data, cap_low=25, cap_high=200):
    """Return (in_caps, other): symbol -> (value, line) for the pop-cap ladder."""
    in_caps, other = {}, {}
    depth = 0
    cap_depth = None
    for i, line in enumerate(data.split("\n"), 1):
        s = line.strip()
        if s.startswith("#load-if-defined") or s.startswith("#load-if-not-defined"):
            depth += 1
            if cap_depth is None and re.search(r"POPULATION-CAP-\d+", s):
                cap_depth = depth
        elif s.startswith("#end-if"):
            depth -= 1
            if cap_depth is not None and depth < cap_depth:
                cap_depth = None
        else:
            m = DEFCONST.match(s)
            if m:
                if cap_depth is not None:
                    in_caps[m.group(1)] = (m.group(2), i)
                else:
                    other[m.group(1)] = (m.group(2), i)
    return in_caps, other


def main():
    for label, dm_path, const_path in PAIRS:
        dm = read(dm_path)
        const = read(const_path)
        in_caps, other = scan_constants(const)
        print("=" * 78)
        print("%s\n  DM script : %s (%d bytes, %d lines)" % (label, dm_path, len(dm), dm.count("\n") + 1))
        print("  constants : %s (%d lines)" % (const_path, const.count("\n") + 1))
        cap_symbols = sorted(set(re.findall(r"POPULATION-CAP-(\d+)", const)), key=int)
        print("  pop-cap blocks in this constants file: %s" % cap_symbols)
        risky = []
        for name in sorted(in_caps):
            if name in other:
                continue                     # also defined outside -> always available
            uses = len(re.findall(r"(?<![A-Za-z0-9\-_])%s(?![A-Za-z0-9\-_])" % re.escape(name), dm))
            if uses:
                risky.append((name, in_caps[name][0], in_caps[name][1], uses))
        print("  constants used by the DM script that exist ONLY for cap 25..200:")
        if not risky:
            print("    (none)")
        for name, val, line, uses in risky:
            print("    %-24s last def (cap 200 block, line %4d) = %-6s used %d time(s)"
                  % (name, line, val, uses))
        missing = [n for n, _, _, _ in risky if n not in in_caps]
        assert not missing, missing
        print("  -> these %d symbols must be defined by the fallback block" % len(risky))
    print()
    print("scan written to dm_const_audit_out.txt")


if __name__ == "__main__":
    sys.stdout = open(os.path.join(W, "dm_const_audit_out.txt"), "w", encoding="utf-8")
    main()
    sys.stdout.flush()
    sys.stdout = sys.__stdout__
    print(open(os.path.join(W, "dm_const_audit_out.txt"), encoding="utf-8").read())
