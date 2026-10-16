# Configuration PyInstaller ; lancer avec tools/createapp.py.
from pathlib import Path
import sys

root = Path(SPECPATH).parent
analysis = Analysis(
    [str(root / "src" / "folie" / "__main__.py")],
    pathex=[str(root / "src")],
    binaries=[], datas=[], hiddenimports=[],
    hookspath=[], hooksconfig={}, runtime_hooks=[],
    excludes=['wx'], noarchive=False,
)
pyz = PYZ(analysis.pure)
exe = EXE(
    pyz, analysis.scripts, [], exclude_binaries=True,
    name="folie", debug=False, strip=False, upx=True, console=True,
)
collection = COLLECT(
    exe, analysis.binaries, analysis.datas, strip=False, upx=True, name="folie",
)
