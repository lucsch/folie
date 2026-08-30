"""Interface en ligne de commande de Folie, construite avec Typer."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from .generator import generate_html


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
) -> None:
    """Crée l'index HTML du RÉPERTOIRE indiqué."""
    try:
        result = generate_html(
            repertoire,
            output,
            exclude=exclude or (),
            exclude_hidden=exclude_hidden,
            title=title,
        )
    except (OSError, ValueError) as exc:
        typer.echo(f"Erreur : {exc}", err=True)
        raise typer.Exit(code=2) from exc

    typer.echo(
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
