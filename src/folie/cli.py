"""Interface en ligne de commande de Folie, construite avec Typer."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.markup import escape
from rich.progress import Progress, SpinnerColumn, TextColumn, TimeElapsedColumn

from folie.version import COMMIT_NUMBER, VERSION_MAJOR_MINOR

from .generator import ScanProgress, generate_html


app = typer.Typer(
    name="folie",
    help=(
        "Génère une page HTML autonome et navigable décrivant le contenu "
        "d'un répertoire."
    ),
    no_args_is_help=True,
    pretty_exceptions_show_locals=False,
)


@app.command()
def generate(
    repertoire: Annotated[
        Path,
        typer.Argument(
            help="Répertoire à inventorier.",
            exists=True,
            file_okay=False,
            dir_okay=True,
            readable=True,
            resolve_path=True,
        ),
    ],
    output: Annotated[
        Path,
        typer.Option(
            "--output",
            "-o",
            help="Fichier HTML à créer.",
            show_default=True,
        ),
    ] = Path("index_fichiers.html"),
    exclude: Annotated[
        list[str] | None,
        typer.Option(
            "--exclude",
            "-x",
            metavar="MOTIF",
            help=(
                "Exclut les sous-répertoires correspondants. Les jokers * et ? "
                "sont acceptés ; l'option peut être répétée."
            ),
        ),
    ] = None,
    exclude_hidden: Annotated[
        bool,
        typer.Option(
            "--exclude-hidden",
            help="Exclut tous les sous-répertoires cachés.",
        ),
    ] = False,
    title: Annotated[
        str | None,
        typer.Option(
            "--title",
            help="Titre personnalisé de la page.",
        ),
    ] = None,
    show_progress: Annotated[
        bool,
        typer.Option(
            "--progress/--no-progress",
            help="Affiche ou masque la progression du parcours.",
        ),
    ] = True,
    sort_entries: Annotated[
        bool,
        typer.Option(
            "--sort/--no-sort",
            help="Trie les entrées ; --no-sort accélère les très gros dossiers.",
        ),
    ] = True,
) -> None:
    """Crée l'index HTML du RÉPERTOIRE indiqué."""
    progress_console = Console(stderr=True)
    progress = Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        TextColumn("• {task.fields[stats]}"),
        TextColumn("• [dim]{task.fields[current]}[/dim]"),
        TimeElapsedColumn(),
        console=progress_console,
        transient=False,
        disable=not show_progress,
        refresh_per_second=10,
    )

    def update_progress(status: ScanProgress) -> None:
        descriptions = {
            "scan": "Parcours en cours",
            "write": "Écriture du HTML",
            "done": "Terminé",
        }
        current = str(status.current_path)
        if len(current) > 80:
            current = f"…{current[-79:]}"
        files_count = f"{status.files_scanned:,}".replace(",", " ")
        directories_count = f"{status.directories_scanned:,}".replace(",", " ")
        stats = f"{files_count} fichiers, {directories_count} dossiers vus"
        progress.update(
            progress_task,
            description=descriptions[status.phase],
            stats=stats,
            current=escape(current),
        )
        if status.phase == "done":
            progress.update(progress_task, total=1, completed=1)

    try:
        with progress:
            progress_task = progress.add_task(
                "Initialisation",
                total=None,
                stats="0 fichier, 0 dossier vu",
                current=escape(str(repertoire)),
            )
            result = generate_html(
                repertoire,
                output,
                exclude=exclude or (),
                exclude_hidden=exclude_hidden,
                title=title,
                progress_callback=update_progress,
                sort_entries=sort_entries,
            )
    except (OSError, ValueError) as exc:
        typer.echo(f"Erreur : {exc}", err=True)
        raise typer.Exit(code=2) from exc

    typer.echo(
        f"Folie version : {VERSION_MAJOR_MINOR}.{COMMIT_NUMBER}\n"
        f"Index créé : {result.output}\n"
        f"{result.file_count} fichier(s), {result.directory_count} dossier(s), "
        f"{result.excluded_count} dossier(s) exclu(s)."
    )
    if result.error_count:
        typer.echo(
            f"Attention : {result.error_count} élément(s) n'ont pas pu être lus.",
            err=True,
        )


def main() -> None:
    """Point d'entrée utilisé par ``python -m folie`` et le script installé."""
    app()
