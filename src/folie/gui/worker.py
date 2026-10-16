"""Génération en arrière-plan sans dépendance à wxPython."""

from dataclasses import dataclass
from pathlib import Path
from threading import Thread
from typing import Callable

from folie.core.generator import GenerationResult, ScanProgress, generate_html


@dataclass(frozen=True)
class GenerationOptions:
    source: Path
    output: Path
    exclude: tuple[str, ...] = ()
    exclude_hidden: bool = False
    title: str | None = None
    sort_entries: bool = True


def start_generation(
    options: GenerationOptions,
    on_progress: Callable[[ScanProgress], None],
    on_success: Callable[[GenerationResult], None],
    on_error: Callable[[str], None],
) -> Thread:
    """Les callbacks s'exécutent dans le thread de travail : la GUI les relaie."""
    def run() -> None:
        try:
            result = generate_html(
                options.source,
                options.output,
                exclude=options.exclude,
                exclude_hidden=options.exclude_hidden,
                title=options.title,
                sort_entries=options.sort_entries,
                progress_callback=on_progress,
            )
        except Exception as exc:
            on_error(str(exc))
        else:
            on_success(result)

    thread = Thread(target=run, name="folie-generation", daemon=False)
    thread.start()
    return thread
