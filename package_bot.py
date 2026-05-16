"""
Packages Montka into an AI Arena compatible zip.

Usage:
    python package_bot.py

Output: publish/Montka.zip
"""
import os
import glob
import zipfile
from os import path, walk

ROOT = path.dirname(path.abspath(__file__))
VENV_SITE = path.join(ROOT, "venv", "Lib", "site-packages")
VENV_SRC = path.join(ROOT, "venv", "src", "ares-sc2")
OUT_DIR = path.join(ROOT, "publish")
OUT_ZIP = path.join(OUT_DIR, "Montka.zip")
LINUX_WHEELS_DIR = path.join(OUT_DIR, "linux_wheels")

SKIP_DIRS = {"__pycache__", ".git", ".github", "tests", "docs", "build", "dist", "pickle_gameinfo"}
# Keep .so (Linux), skip Windows .pyd and source files
SKIP_EXTS = {".pyc", ".pyo", ".c", ".pyd", ".pyx"}


def add_dir(zf: zipfile.ZipFile, src_dir: str, arc_prefix: str):
    for dirpath, dirnames, filenames in walk(src_dir):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for filename in filenames:
            ext = path.splitext(filename)[1].lower()
            if ext in SKIP_EXTS:
                continue
            full = path.join(dirpath, filename)
            rel = path.relpath(full, src_dir)
            arc = path.join(arc_prefix, rel).replace("\\", "/")
            zf.write(full, arc)


def add_file(zf: zipfile.ZipFile, src: str, arc: str):
    zf.write(src, arc)


def bundle_cython_extensions(zf: zipfile.ZipFile):
    """Extract cython_extensions from all downloaded Linux wheels (cp311/312/313)."""
    wheels = glob.glob(path.join(LINUX_WHEELS_DIR, "cython_extensions_sc2-0.16.0-cp3*linux*.whl"))
    if not wheels:
        print("  ERROR: No cython_extensions Linux wheels found in publish/linux_wheels/")
        print("  Run this first:")
        for pyver in ["311", "312", "313"]:
            print(f"    venv\\Scripts\\pip.exe download cython-extensions-sc2==0.16.0 "
                  f"--platform manylinux2014_x86_64 --python-version {pyver} "
                  f"--only-binary=:all: --no-deps -d publish\\linux_wheels")
        return

    added = set()
    for wheel_path in sorted(wheels):
        print(f"  Bundling {path.basename(wheel_path)}")
        with zipfile.ZipFile(wheel_path) as whl:
            for entry in whl.namelist():
                if ".dist-info/" in entry or entry in added:
                    continue
                # skip Windows .pyd files inside the wheel (shouldn't be any, but safe)
                if entry.endswith(".pyd"):
                    continue
                added.add(entry)
                zf.writestr(entry, whl.read(entry))


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    if path.isfile(OUT_ZIP):
        os.remove(OUT_ZIP)

    with zipfile.ZipFile(OUT_ZIP, "w", zipfile.ZIP_DEFLATED) as zf:
        print("Adding run.py...")
        add_file(zf, path.join(ROOT, "run.py"), "run.py")

        print("Adding config.yml...")
        add_file(zf, path.join(ROOT, "config.yml"), "config.yml")

        print("Adding requirements.txt...")
        add_file(zf, path.join(ROOT, "requirements.txt"), "requirements.txt")

        print("Adding montka/...")
        add_dir(zf, path.join(ROOT, "montka"), "montka")

        print("Adding ares/ ...")
        add_dir(zf, path.join(VENV_SRC, "src", "ares"), "ares")

        print("Adding sc2_helper/ (includes Linux .so)...")
        add_dir(zf, path.join(VENV_SRC, "sc2_helper"), "sc2_helper")

        print("Adding sc2/ (burnysc2, pure Python)...")
        add_dir(zf, path.join(VENV_SITE, "sc2"), "sc2")

        print("Adding map_analyzer/ (pure Python)...")
        add_dir(zf, path.join(VENV_SITE, "map_analyzer"), "map_analyzer")

        print("Adding cython_extensions/ (Linux wheels)...")
        bundle_cython_extensions(zf)

    size_kb = os.path.getsize(OUT_ZIP) // 1024
    print(f"\nCreated {OUT_ZIP} ({size_kb} KB)")
    print("Top-level contents:")
    with zipfile.ZipFile(OUT_ZIP) as zf:
        tops = sorted({n.split("/")[0] for n in zf.namelist()})
        for t in tops:
            print(f"  {t}")


if __name__ == "__main__":
    main()
