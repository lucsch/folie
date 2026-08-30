"""Interface en ligne de commande de Folie."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Sequence

from .generator import generate_html


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="folie",
        description=(
            "Génère une page HTML autonome et navigable décrivant le contenu "
            "d'un répertoire."
        ),
    )
    parser.add_argument("repertoire", type=Path, help="répertoire à inventorier")
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=Path("index_fichiers.html"),
        help="fichier HTML à créer (défaut : index_fichiers.html)",
    )
    parser.add_argument(
        "-x",
        "--exclude",
        action="append",
        default=[],
        metavar="MOTIF",
        help=(
            "exclut les sous-répertoires correspondants (nom ou chemin relatif, "
            "jokers * et ? acceptés). Répéter l'option si nécessaire"
        ),
    )
    parser.add_argument(
        "--exclude-hidden",
        action="store_true",
        help="exclut tous les sous-répertoires cachés (nom commençant par un point)",
    )
    parser.add_argument(
        "--title",
        help="titre personnalisé de la page (défaut : nom du répertoire)",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    try:
        result = generate_html(
            args.repertoire,
            args.output,
            exclude=args.exclude,
            exclude_hidden=args.exclude_hidden,
            title=args.title,
        )
    except (OSError, ValueError) as exc:
        print(f"Erreur : {exc}", file=sys.stderr)
        raise SystemExit(2) from exc

    print(
        f"Index créé : {result.output}\n"
        f"{result.file_count} fichier(s), {result.directory_count} dossier(s), "
        f"{result.excluded_count} dossier(s) exclu(s)."
    )
    if result.error_count:
        print(
            f"Attention : {result.error_count} élément(s) n'ont pas pu être lus.",
            file=sys.stderr,
        )

