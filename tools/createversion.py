"""Génère les informations Git partagées par Folie et WinFolie."""

import argparse
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUTPUT = PROJECT_ROOT / "src" / "folie" / "_build_version.py"


class GitVersion:
    def __init__(self) -> None:
        self.VERSION_MAJOR_MINOR = "1.0"
        self.m_commit_id = self._git("describe", "--always", "--dirty=+")
        self.m_commit_number = self._git("rev-list", "HEAD", "--count", fallback="0")
        self.m_branch_name = self._git("rev-parse", "--abbrev-ref", "HEAD")

    @staticmethod
    def _git(*args: str, fallback: str = "unknown") -> str:
        try:
            return subprocess.check_output(
                ["git", *args], cwd=PROJECT_ROOT, stderr=subprocess.DEVNULL, text=True,
            ).strip()
        except (OSError, subprocess.CalledProcessError):
            return fallback

    def write_to_file(self, filename: str | Path = DEFAULT_OUTPUT) -> None:
        path = Path(filename)
        if not path.is_absolute():
            path = PROJECT_ROOT / path
        path.parent.mkdir(parents=True, exist_ok=True)
        values = {
            "COMMIT_ID": self.m_commit_id,
            "COMMIT_NUMBER": self.m_commit_number,
            "BRANCH_NAME": self.m_branch_name,
            "VERSION_MAJOR_MINOR": self.VERSION_MAJOR_MINOR,
        }
        path.write_text(
            "# Généré par tools/createversion.py ; ne pas modifier.\n"
            + "".join(f"{key} = {value!r}\n" for key, value in values.items()),
            encoding="utf-8",
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("name", nargs="?", default=DEFAULT_OUTPUT, help="Fichier de sortie (relatif à la racine du projet).")
    GitVersion().write_to_file(parser.parse_args().name)
