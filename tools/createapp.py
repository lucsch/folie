"""Construit les exécutables Folie et WinFolie sur la plateforme courante."""

import argparse
import importlib.util
import subprocess
import sys
from pathlib import Path

from createversion import GitVersion

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("plateform", choices=("Windows", "Linux", "OSX"))
    parser.add_argument("--target", choices=("all", "folie", "winfolie"), default="all")
    args = parser.parse_args()
    actual_platform = {"win32": "Windows", "darwin": "OSX"}.get(sys.platform, "Linux")
    if args.plateform != actual_platform:
        parser.error("PyInstaller doit être exécuté sur la plateforme cible.")
    targets = ("folie", "winfolie") if args.target == "all" else (args.target,)
    if "winfolie" in targets and importlib.util.find_spec("wx") is None:
        parser.error("wxPython est requis : installez l'extra gui pour construire WinFolie.")
    GitVersion().write_to_file()
    try:
        for target in targets:
            subprocess.run(
                [sys.executable, "-m", "PyInstaller", "--clean", "--noconfirm",
                 "--distpath", str(PROJECT_ROOT / "dist"),
                 "--workpath", str(PROJECT_ROOT / "build"),
                 str(PROJECT_ROOT / "packaging" / f"{target}.spec")],
                cwd=PROJECT_ROOT, check=True,
            )
    except (OSError, subprocess.CalledProcessError) as exc:
        print(f"Échec de la construction : {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
