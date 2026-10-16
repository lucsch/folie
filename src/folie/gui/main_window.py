"""Fenêtre principale de WinFolie."""

from pathlib import Path
import time

import wx

from folie.core.generator import GenerationResult, ScanProgress
from folie.gui.worker import GenerationOptions, start_generation
from folie.version import COMMIT_NUMBER, VERSION_MAJOR_MINOR


class MainWindow(wx.Frame):
    def __init__(self) -> None:
        super().__init__(None, title=f"WinFolie {VERSION_MAJOR_MINOR}.{COMMIT_NUMBER}", size=(760, 650))
        self.SetMinSize((620, 580))
        self._busy = False
        self._result: GenerationResult | None = None
        panel = wx.Panel(self)
        layout = wx.BoxSizer(wx.VERTICAL)
        self.source = wx.DirPickerCtrl(
            panel, message="Répertoire à inventorier",
            style=wx.DIRP_USE_TEXTCTRL | wx.DIRP_DIR_MUST_EXIST,
        )
        self.output = wx.FilePickerCtrl(
            panel, path=str(Path.cwd() / "index_fichiers.html"),
            message="Enregistrer l’inventaire", wildcard="Fichiers HTML (*.html)|*.html",
            style=wx.FLP_SAVE | wx.FLP_USE_TEXTCTRL,
        )
        self.title = wx.TextCtrl(panel)
        self.exclusions = wx.TextCtrl(panel, style=wx.TE_MULTILINE, size=(-1, 90))
        for label, control in (
            ("Répertoire à inventorier", self.source),
            ("Fichier HTML de sortie", self.output),
            ("Titre de la page (facultatif)", self.title),
            ("Dossiers à exclure — un motif par ligne (* et ? acceptés)", self.exclusions),
        ):
            layout.Add(wx.StaticText(panel, label=label), 0, wx.LEFT | wx.RIGHT | wx.TOP, 12)
            layout.Add(control, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, 12)
        self.hidden = wx.CheckBox(panel, label="Exclure les dossiers cachés")
        self.sort = wx.CheckBox(panel, label="Trier les fichiers et les dossiers")
        self.sort.SetValue(True)
        self.show_progress = wx.CheckBox(panel, label="Afficher la progression")
        self.show_progress.SetValue(True)
        for control in (self.hidden, self.sort, self.show_progress):
            layout.Add(control, 0, wx.LEFT | wx.RIGHT | wx.TOP, 12)
        actions = wx.BoxSizer(wx.HORIZONTAL)
        self.generate = wx.Button(panel, label="Générer l’inventaire")
        self.open_result = wx.Button(panel, label="Ouvrir l’inventaire")
        self.open_result.Disable()
        actions.Add(self.generate, 0, wx.RIGHT, 8)
        actions.Add(self.open_result)
        layout.Add(actions, 0, wx.ALL, 12)
        self.gauge = wx.Gauge(panel, range=100)
        layout.Add(self.gauge, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 12)
        self.status = wx.TextCtrl(panel, value="Prêt.", style=wx.TE_MULTILINE | wx.TE_READONLY)
        layout.Add(self.status, 1, wx.EXPAND | wx.ALL, 12)
        panel.SetSizer(layout)
        self._inputs = (self.source, self.output, self.title, self.exclusions,
                        self.hidden, self.sort, self.show_progress, self.generate)
        self.generate.Bind(wx.EVT_BUTTON, self._on_generate)
        self.open_result.Bind(wx.EVT_BUTTON, self._on_open)
        self.Bind(wx.EVT_CLOSE, self._on_close)
        self.Centre()

    def _set_busy(self, busy: bool) -> None:
        self._busy = busy
        for control in self._inputs:
            control.Enable(not busy)
        self.open_result.Enable(not busy and self._result is not None)

    def _on_generate(self, event: wx.CommandEvent) -> None:
        if not self.source.GetPath().strip() or not self.output.GetPath().strip():
            wx.MessageBox("Choisissez un répertoire et un fichier de sortie.", "WinFolie", wx.OK | wx.ICON_WARNING, self)
            return
        source = Path(self.source.GetPath()).expanduser().resolve()
        output = Path(self.output.GetPath()).expanduser().resolve()
        if not source.is_dir() or output.is_dir():
            wx.MessageBox("Le répertoire source ou le fichier de sortie est invalide.", "WinFolie", wx.OK | wx.ICON_WARNING, self)
            return
        if output.exists() and wx.MessageBox(
            f"Remplacer le fichier existant ?\n{output}", "WinFolie",
            wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION, self,
        ) != wx.YES:
            return
        options = GenerationOptions(
            source=source, output=output,
            exclude=tuple(line.strip() for line in self.exclusions.GetValue().splitlines() if line.strip()),
            exclude_hidden=self.hidden.GetValue(),
            title=self.title.GetValue().strip() or None,
            sort_entries=self.sort.GetValue(),
        )
        self._result = None
        self._set_busy(True)
        self.gauge.SetValue(0)
        self.status.SetValue("Génération en cours…")
        show_progress = self.show_progress.GetValue()
        last_update = 0.0

        def report(progress: ScanProgress) -> None:
            nonlocal last_update
            now = time.monotonic()
            if show_progress and (progress.phase != "scan" or now - last_update >= 0.1):
                last_update = now
                wx.CallAfter(self._on_progress, progress)

        start_generation(
            options, report,
            lambda result: wx.CallAfter(self._on_success, result),
            lambda error: wx.CallAfter(self._on_error, error),
        )

    def _on_progress(self, progress: ScanProgress) -> None:
        if not self or not self._busy:
            return
        self.gauge.Pulse()
        phase = {"scan": "Parcours", "write": "Écriture HTML", "done": "Finalisation"}[progress.phase]
        self.status.SetValue(
            f"{phase} : {progress.files_scanned} fichier(s), "
            f"{progress.directories_scanned} dossier(s) vus\n{progress.current_path}"
        )

    def _on_success(self, result: GenerationResult) -> None:
        if not self:
            return
        self._result = result
        self._set_busy(False)
        self.gauge.SetValue(100)
        self.status.SetValue(
            f"Index créé : {result.output}\n{result.file_count} fichier(s), "
            f"{result.directory_count} dossier(s), {result.excluded_count} dossier(s) exclu(s)."
            + (f"\nAttention : {result.error_count} élément(s) n’ont pas pu être lus." if result.error_count else "")
        )

    def _on_error(self, error: str) -> None:
        if not self:
            return
        self._set_busy(False)
        self.gauge.SetValue(0)
        self.status.SetValue(f"Erreur : {error}")
        wx.MessageBox(error, "Échec de la génération", wx.OK | wx.ICON_ERROR, self)

    def _on_open(self, event: wx.CommandEvent) -> None:
        if self._result:
            wx.LaunchDefaultBrowser(self._result.output.as_uri())

    def _on_close(self, event: wx.CloseEvent) -> None:
        if self._busy and event.CanVeto():
            wx.MessageBox("Veuillez attendre la fin de la génération avant de fermer.", "WinFolie", wx.OK | wx.ICON_INFORMATION, self)
            event.Veto()
        else:
            event.Skip()
