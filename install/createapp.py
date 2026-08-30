"""Build the Folie executables with PyInstaller."""

import argparse
import importlib.util
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

PROJECT_ROOT = Path(__file__).resolve().parent.parent
BIN_DIR = PROJECT_ROOT / "bin"
SOURCE_DIR = PROJECT_ROOT / "src"
ACTIVE_PLATEFORM = ("Windows", "Linux", "OSX")


def _load_git_version():
    createversion_path = SOURCE_DIR / "folie" / "createversion.py"
    spec = importlib.util.spec_from_file_location(
        "folie_createversion", createversion_path
    )
    if spec is None or spec.loader is None:
        raise ImportError(f"Unable to load {createversion_path}")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.GitVersion


GitVersion = _load_git_version()


@dataclass(frozen=True)
class BuildTarget:
    name: Literal["folie"]
    entrypoint: Path
    windowed: bool
    hidden_imports: tuple[str, ...] = ()


class CreateApp:
    def __init__(self, plateform: str = "OSX") -> None:
        if plateform not in ACTIVE_PLATEFORM:
            raise ValueError(f"plateform must be one of {ACTIVE_PLATEFORM!r}.")

        self.basepath = PROJECT_ROOT
        self.binpath = BIN_DIR
        self.plateform = plateform
        self.iconfile = self.basepath / "art" / self._get_icon()
        self.m_commit_number = ""

    def _get_icon(self) -> str:
        """Return the Kryptos icon name for the selected platform."""
        if self.plateform == "Windows":
            return "kryptos.ico"
        if self.plateform == "Linux":
            return "kryptos.png"
        return "kryptos.icns"

    def update_version(self) -> bool:
        git_version = GitVersion()
        git_version.write_to_file(str(SOURCE_DIR / "folie" / "version.py"))
        self.m_commit_number = git_version.m_commit_number
        return True

    def create_exe(self, target: str = "all") -> bool:
        """Build ``kryptos``, ``kryptonite``, or both executables."""
        targets = self._get_targets(target)
        self.binpath.mkdir(parents=True, exist_ok=True)

        try:
            for build_target in targets:
                spec_path = self._create_spec(build_target)
                if self.plateform == "OSX" and build_target.name == "folie":
                    self._add_macos_bundle_metadata(spec_path)
                self._build_spec(spec_path)
        except (OSError, subprocess.CalledProcessError) as error:
            print(f"Build failed: {error}", file=sys.stderr)
            return False

        return True

    def _get_targets(self, target: str) -> tuple[BuildTarget, ...]:
        available_targets = {
            "folie": BuildTarget(
                name="folie",
                entrypoint=SOURCE_DIR / "folie" / "__main__.py",
                windowed=False,
            )
        }
        if target == "all":
            return tuple(available_targets.values())
        try:
            return (available_targets[target],)
        except KeyError:
            raise ValueError(
                "target must be one of 'all', 'folie'"
            ) from None

    def _create_spec(self, target: BuildTarget) -> Path:
        executable_name = self._executable_name(target)
        spec_path = self.binpath / f"{executable_name}.spec"
        mode = "--onedir" if self.plateform in {"Windows", "OSX"} else "--onefile"
        command = [
            sys.executable,
            "-m",
            "PyInstaller.utils.cliutils.makespec",
            mode,
            "--windowed" if target.windowed else "--console",
            "--specpath",
            str(self.binpath),
            "--name",
            executable_name,
            "--paths",
            str(self.basepath),
            "--paths",
            str(SOURCE_DIR),
        ]
        for hidden_import in target.hidden_imports:
            command.extend(("--hidden-import", hidden_import))
        if target.windowed and self.iconfile.exists():
            command.extend(("--icon", str(self.iconfile)))
        command.append(str(target.entrypoint))

        self._run(command)
        if not spec_path.is_file():
            raise OSError(f"Spec file not found after generation: {spec_path}")
        return spec_path

    def _build_spec(self, spec_path: Path) -> None:
        self._run(
            [
                sys.executable,
                "-m",
                "PyInstaller",
                "--clean",
                "--noconfirm",
                "--distpath",
                str(self.binpath / "dist"),
                "--workpath",
                str(self.binpath / "build"),
                str(spec_path),
            ]
        )

    def _executable_name(self, target: BuildTarget) -> str:
        suffix = f"_{self.m_commit_number}" if self.m_commit_number else ""
        return f"{target.name}{suffix}"

    def _add_macos_bundle_metadata(self, spec_path: Path) -> None:
        """Add application metadata to the generated macOS bundle."""
        contents = spec_path.read_text(encoding="utf-8")
        marker = "    bundle_identifier=None,\n)"
        if marker not in contents:
            return

        replacement = (
            "    bundle_identifier=None,\n"
            "    info_plist={\n"
            f"        'CFBundleShortVersionString': '1.0.{self.m_commit_number}',\n"
            "        'NSHumanReadableCopyright': '(c) 2026, Lucien SCHREIBER',\n"
            "        'NSHighResolutionCapable': True,\n"
            "        'NSRequiresAquaSystemAppearance': False,\n"
            "    },\n"
            ")"
        )
        spec_path.write_text(contents.replace(marker, replacement), encoding="utf-8")

    def _run(self, command: list[str]) -> None:
        print("Running:", subprocess.list2cmdline(command))
        subprocess.run(command, cwd=self.basepath, check=True)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build the Folie executables."
    )
    parser.add_argument(
        "plateform",
        choices=ACTIVE_PLATEFORM,
        help="target operating system",
    )
    parser.add_argument(
        "--target",
        choices=("all", "folie"),
        default="all",
        help="executable to build (default: all)",
    )
    args = parser.parse_args()

    app = CreateApp(plateform=args.plateform)
    app.update_version()
    return 0 if app.create_exe(target=args.target) else 1


if __name__ == "__main__":
    raise SystemExit(main())
