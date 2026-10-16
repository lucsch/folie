"""Point d'entrée du programme winfolie."""


def main() -> None:
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
