"""Point d'entrée du programme winfolie."""

import sys


def main() -> None:
    # Velopack attend une sortie rapide, sans GUI, pour ces étapes du cycle de vie.
    if len(sys.argv) > 1 and sys.argv[1] in {
        "--veloapp-install", "--veloapp-obsolete",
        "--veloapp-updated", "--veloapp-uninstall",
    }:
        return

    try:
        import wx
    except ModuleNotFoundError as exc:
        if exc.name != "wx":
            raise
        raise SystemExit(
            "wxPython est requis pour winfolie. Installez-le avec : uv sync --extra gui"
        ) from exc

    from folie.gui.main_window import MainWindow

    app = wx.App(False)
    app.SetAppName("WinFolie")
    window = MainWindow()
    window.Show()
    app.MainLoop()
