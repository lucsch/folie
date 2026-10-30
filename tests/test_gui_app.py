import subprocess
import sys
from pathlib import Path

import pytest


@pytest.mark.parametrize("hook", [
    "--veloapp-install", "--veloapp-obsolete",
    "--veloapp-updated", "--veloapp-uninstall",
])
def test_velopack_hooks_exit_without_loading_gui(hook: str) -> None:
    # A fresh process must exit successfully even when GUI imports are unavailable.
    source = Path(__file__).resolve().parents[1] / "src"
    script = f"""
import sys
sys.path.insert(0, {str(source)!r})
sys.modules['wx'] = None
sys.modules['folie.gui.main_window'] = None
from folie.gui.app import main
sys.argv = ['winfolie.exe', {hook!r}, '1.0.42']
main()
"""
    result = subprocess.run(
        [sys.executable, "-c", script], capture_output=True, text=True, timeout=10,
    )
    assert result.returncode == 0, result.stderr
