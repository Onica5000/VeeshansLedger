"""Build a single-file EQLSkyTracker.exe with PyInstaller.

    python build/build_exe.py
"""
import os
import shutil
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIST = os.path.join(ROOT, "dist")
WORK = os.path.join(ROOT, "build", "_work")

MIN_PYINSTALLER = (6, 22)


def _check_pyinstaller():
    """Python 3.14 uses Tcl/Tk 9.0; PyInstaller < 6.22 mis-bundles it and the exe
    dies at launch with a missing `_tcl_data` directory."""
    try:
        import PyInstaller
    except ImportError:
        sys.exit("PyInstaller is not installed.  pip install 'pyinstaller>=6.22'")
    ver = tuple(int(x) for x in PyInstaller.__version__.split(".")[:2])
    if ver < MIN_PYINSTALLER:
        sys.exit(
            "PyInstaller %s is too old for Python 3.14 Tcl/Tk 9. "
            "The built exe would fail with a missing _tcl_data directory. "
            "Upgrade:  pip install --upgrade pyinstaller>=6.22"
            % PyInstaller.__version__)
    print("PyInstaller %s OK" % PyInstaller.__version__)


def main():
    _check_pyinstaller()
    exe_out = os.path.join(DIST, "EQLSkyTracker.exe")
    if os.path.exists(exe_out):
        try:
            os.remove(exe_out)          # a running instance locks it
        except OSError:
            sys.exit("Cannot replace %s - close any running EQLSkyTracker first." % exe_out)
    sep = ";" if os.name == "nt" else ":"
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm", "--clean", "--onefile", "--windowed",
        "--name", "EQLSkyTracker",
        "--distpath", DIST,
        "--workpath", WORK,
        "--specpath", WORK,
        "--paths", os.path.join(ROOT, "src"),
        "--add-data", "%s%s%s" % (os.path.join(ROOT, "data", "sky.json"), sep, "data"),
        "--hidden-import", "reportlab.graphics.barcode.code128",
        os.path.join(ROOT, "src", "main.py"),
    ]
    print(" ".join(cmd))
    rc = subprocess.call(cmd)
    if rc == 0:
        exe = os.path.join(DIST, "EQLSkyTracker.exe")
        if os.path.exists(exe):
            print("\nBuilt: %s  (%.1f MB)" % (exe, os.path.getsize(exe) / 1048576.0))
    return rc

if __name__ == "__main__":
    sys.exit(main())
