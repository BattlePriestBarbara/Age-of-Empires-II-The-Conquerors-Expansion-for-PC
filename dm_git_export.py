"""dm_git_export.py -- build the git-ready snapshot of this workspace.

    python D:\\aoe2_work\\dm_git_export.py [target]        (default D:\\aoe2_aoefix)

It

  1. creates the target folder,
  2. copies every *.py / *.txt / *.md / *.cmd of the workspace root (tools,
     evidence logs, documents) plus LICENSE, and - for a locally runnable
     chain - the game data folders, which .gitignore keeps out of the
     repository,
  3. makes the copied scripts portable:
        W    = r"D:\\aoe2_work" -> W = os.path.dirname(os.path.abspath(__file__))
        GAME = <hard path>      -> GAME = os.environ.get("AOE2HD_DIR") or <hard path>
     (and inserts "import os" where it is missing),
  4. writes .gitignore and a draft of docs/FILE_MAP.md,
  5. prints a summary.  The source workspace is never modified.
"""
import os
import re
import shutil
import sys

SRC = r"D:\aoe2_work"
DST = sys.argv[1] if len(sys.argv) > 1 else r"D:\aoe2_aoefix"

COPY_EXT = (".py", ".txt", ".md", ".cmd")
# extension-less files that still belong into the repository
COPY_NAMES = ("LICENSE",)
# game data: copied so the chain runs here, excluded from git
DATA_DIRS = ("x1_drs", "aok_drs", "x1p1_drs", "backup_drs", "patched_drs",
             "patched_drs2", "patch_out", "patch_out2", "patched_scripts")
# documents that belong into docs/ instead of the root
MOVE_TO_DOCS = {"readme_v2_backup.md": "readme_v2_history.md"}

GITIGNORE = """\
# ---------------------------------------------------------------------------
# game data - NEVER upload this (Age of Empires II HD assets / *.drs archives)
# ---------------------------------------------------------------------------
x1_drs/
aok_drs/
x1p1_drs/
backup_drs/
patched_drs/
patched_drs2/
patch_out/
patch_out2/
patched_scripts/
*.drs
*.drs.orig
*.exe

# ---------------------------------------------------------------------------
# python / editor
# ---------------------------------------------------------------------------
__pycache__/
*.pyc
.vscode/
.idea/
"""


def patch_script(text):
    """make one copied script portable; returns (new text, list of changes)"""
    changes = []
    root = "os.path.dirname(os.path.abspath(__file__))"
    # 1. raw string paths: r"D:\aoe2_work\<sub>" -> join(root, r"<sub>")
    new, n = re.subn(r'r"D:\\aoe2_work\\([^"]*)"',
                     lambda m: 'os.path.join(%s, r"%s")' % (root, m.group(1)), text)
    if n:
        changes.append("%d absolute sub path(s) -> os.path.join(root, ...)" % n)
    # 2. the bare root itself (W, BASE, ...)
    new, n = re.subn(r'r"D:\\aoe2_work"', root, new)
    if n:
        changes.append("%d bare root -> script directory" % n)
    # 3. the same path inside docstrings / comments: leave a relative path
    new = new.replace("D:\\\\aoe2_work\\\\", "").replace("D:\\aoe2_work\\", "")
    new, n = re.subn(r"D:\\\\?aoe2_work", "the repository root", new)
    if n:
        changes.append("%d docstring/comment path(s) neutralised" % n)
    # 4. GAME = ...  (single line or parenthesised over two lines)
    new, n = re.subn(r"(?m)^GAME = ",
                     'GAME = os.environ.get("AOE2HD_DIR") or ', new)
    if n:
        changes.append("GAME -> $AOE2HD_DIR override (%d site)" % n)
    # 5. import os when the rewrite needs it
    if (root in new or 'os.environ.get("AOE2HD_DIR")' in new):
        if not re.search(r"(?m)^import os\b", new):
            m = re.match(r'\s*"""', new)
            end = new.find('"""', m.end()) if m else -1
            end = new.find("\n", end) + 1 if end >= 0 else 0
            new = new[:end] + "import os\n" + new[end:]
            changes.append("added 'import os'")
    return new, changes


def patch_cmd(text):
    """batch helper: call the tools relative to the .cmd file itself"""
    return text.replace('python "D:\\aoe2_work\\', 'python "%~dp0')


def main():
    if os.path.abspath(SRC) == os.path.abspath(DST):
        print("source and target are the same folder - nothing to do")
        return
    os.makedirs(DST, exist_ok=True)
    os.makedirs(os.path.join(DST, "docs"), exist_ok=True)
    log = []

    # ---- 1. tools / logs / documents ---------------------------------------
    n_code = n_log = 0
    patched = []
    for name in sorted(os.listdir(SRC)):
        path = os.path.join(SRC, name)
        if not os.path.isfile(path):
            continue
        ext = os.path.splitext(name)[1].lower()
        if ext not in COPY_EXT and name not in COPY_NAMES:
            continue
        if name in MOVE_TO_DOCS:
            shutil.copy2(path, os.path.join(DST, "docs", MOVE_TO_DOCS[name]))
            continue
        if ext == ".py":
            raw = open(path, "rb").read().decode("utf-8")
            if name == "dm_git_export.py":
                new, changes = raw, []      # the exporter itself stays verbatim
            else:
                new, changes = patch_script(raw)
            with open(os.path.join(DST, name), "wb") as fh:
                fh.write(new.encode("utf-8"))
            n_code += 1
            if changes:
                patched.append((name, ", ".join(changes)))
        elif ext == ".cmd":
            raw = open(path, "rb").read().decode("utf-8")
            new = patch_cmd(raw)
            with open(os.path.join(DST, name), "wb") as fh:
                fh.write(new.encode("utf-8"))
            n_log += 1
            if new != raw:
                patched.append((name, "tool path -> %~dp0"))
        else:
            shutil.copy2(path, os.path.join(DST, name))
            n_log += 1
    log.append("copied %d scripts (%d made portable), %d logs/documents"
               % (n_code, len(patched), n_log))

    # ---- 2. game data (local use only) -------------------------------------
    data_bytes = 0
    for d in DATA_DIRS:
        s = os.path.join(SRC, d)
        if not os.path.isdir(s):
            continue
        shutil.copytree(s, os.path.join(DST, d), dirs_exist_ok=True)
        for root, _dirs, files in os.walk(s):
            for f in files:
                data_bytes += os.path.getsize(os.path.join(root, f))
    log.append("copied %d game-data folders (%.1f MB) - git-ignored"
               % (len(DATA_DIRS), data_bytes / 1048576.0))

    # ---- 3. .gitignore -----------------------------------------------------
    with open(os.path.join(DST, ".gitignore"), "w", encoding="utf-8",
              newline="\n") as fh:
        fh.write(GITIGNORE)
    log.append("wrote .gitignore")

    # ---- 4. docs/FILE_MAP.md (from the module docstrings) ------------------
    rows = []
    for name in sorted(os.listdir(DST)):
        if not name.endswith(".py"):
            continue
        text = open(os.path.join(DST, name), encoding="utf-8").read()
        m = re.match(r'\s*"""(.*?)(?:\r?\n)??', text, re.S)
        first = ""
        if m:
            for line in m.group(1).split("\n"):
                line = line.strip()
                if line and not line.startswith('"""'):
                    first = line
                    break
        rows.append("| `%s` | %s |" % (name, first.replace("|", "/") or "(no docstring)"))
    logs = sorted(f for f in os.listdir(DST) if f.endswith((".txt", ".cmd", ".md")))
    with open(os.path.join(DST, "docs", "FILE_MAP.md"), "w", encoding="utf-8",
              newline="\n") as fh:
        fh.write("# 文件清单\n\n自动生成（`dm_git_export.py`，取自每个脚本的第一行文档字符串）。\n\n")
        fh.write("## 脚本（%d 个，位于仓库根目录）\n\n| 文件 | 用途（脚本自己的说明） |\n|---|---|\n"
                 % len(rows))
        fh.write("\n".join(rows) + "\n")
        fh.write("\n## 日志与报告（%d 个，位于仓库根目录）\n\n" % len(logs))
        for f in logs:
            fh.write("* `%s`  %d B\n" % (f, os.path.getsize(os.path.join(DST, f))))
    log.append("wrote docs/FILE_MAP.md (%d scripts, %d logs)" % (len(rows), len(logs)))

    # ---- 5. report ---------------------------------------------------------
    print("snapshot  ->  %s" % DST)
    for s in log:
        print("  * %s" % s)
    print("  * portable scripts: %d" % len(patched))
    for name, what in patched[:10]:
        print("      %-26s %s" % (name, what))
    if len(patched) > 10:
        print("      ... (%d more)" % (len(patched) - 10))


if __name__ == "__main__":
    main()

