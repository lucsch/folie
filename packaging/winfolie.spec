# Configuration PyInstaller ; lancer avec tools/createapp.py.
from pathlib import Path
import sys

root = Path(SPECPATH).parent
analysis = Analysis(
    [str(root / "src" / "folie" / "gui/__main__.py")],
    pathex=[str(root / "src")],
    binaries=[], datas=[], hiddenimports=[],
    hookspath=[], hooksconfig={}, runtime_hooks=[],
    excludes=[], noarchive=False,
)
pyz = PYZ(analysis.pure)
exe = EXE(
    pyz, analysis.scripts, [], exclude_binaries=True,
    name="winfolie", debug=False, strip=False, upx=True, console=False,
)
collection = COLLECT(
    exe, analysis.binaries, analysis.datas, strip=False, upx=True, name="winfolie",
)
if sys.platform == "darwin":
    app = BUNDLE(collection, name="WinFolie.app", bundle_identifier="org.folie.winfolie")
