from __future__ import annotations

from html.parser import HTMLParser
from pathlib import Path

import pytest

from folie.generator import ScanProgress, _human_size, generate_html


def test_directory_copy_paths_preserve_original_characters(tmp_path: Path) -> None:
    source = tmp_path / "Mes documents"
    nested = source / "Été & bilan '100%20'"
    nested.mkdir(parents=True)
    output = tmp_path / "inventaire.html"
    generate_html(source, output)
    paths: list[str] = []

    class CopyButtonParser(HTMLParser):
        def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
            attributes = dict(attrs)
            if tag == "button" and "data-path" in attributes:
                paths.append(attributes["data-path"])

    CopyButtonParser().feed(output.read_text(encoding="utf-8"))

    assert paths == [str(source.resolve()), str(nested.resolve())]


def test_generate_autonomous_html_with_metadata_and_escaped_names(tmp_path: Path) -> None:
    source = tmp_path / "Mes documents"
    source.mkdir()
    word_file = source / "rapport & bilan.docx"
    word_file.write_bytes(b"contenu")
    nested = source / "Photos"
    nested.mkdir()
    (nested / "image été.jpg").write_bytes(b"1234")
    output = tmp_path / "inventaire.html"

    result = generate_html(source, output, title="Mon inventaire")
    page = output.read_text(encoding="utf-8")

    assert result.file_count == 2
    assert result.directory_count == 1
    assert "Mon inventaire" in page
    assert "rapport &amp; bilan.docx" in page
    assert word_file.resolve().as_uri().replace("&", "&amp;") in page
    assert str(word_file.resolve()).replace("&", "&amp;") in page
    assert 'class="file-icon type-word"' in page
    assert 'class="file-icon type-image"' in page
    assert "<script>" in page
    assert "http://" not in page and "https://" not in page
    assert "Aucun dossier exclu." in page


def test_excludes_directories_by_name_path_glob_and_hidden_flag(tmp_path: Path) -> None:
    source = tmp_path / "source"
    for relative in (
        "keep/ok.txt",
        "node_modules/package.js",
        "archive/2024/old.pdf",
        "archive/latest/current.pdf",
        ".private/secret.txt",
    ):
        path = source / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(relative, encoding="utf-8")

    result = generate_html(
        source,
        tmp_path / "out.html",
        exclude=["node_modules", "archive/20*"],
        exclude_hidden=True,
    )
    page = result.output.read_text(encoding="utf-8")

    assert result.file_count == 2
    assert result.excluded_count == 3
    assert "ok.txt" in page
    assert "current.pdf" in page
    assert "package.js" not in page
    assert "old.pdf" not in page
    assert "secret.txt" not in page
    assert "Dossiers exclus (3)" in page
    for relative in (".private", "archive/2024", "node_modules"):
        assert f"<li><code>{Path(relative)}</code></li>" in page


def test_excluded_directory_names_are_escaped(tmp_path: Path) -> None:
    source = tmp_path / "source"
    (source / "Été & archives").mkdir(parents=True)
    result = generate_html(source, tmp_path / "out.html", exclude=["Été & archives"])
    page = result.output.read_text(encoding="utf-8")

    assert result.excluded_count == 1
    assert "<li><code>Été &amp; archives</code></li>" in page


def test_existing_output_inside_source_is_not_listed(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    output = source / "index.html"
    output.write_text("ancienne version", encoding="utf-8")
    (source / "visible.txt").write_text("ok", encoding="utf-8")

    result = generate_html(source, output)

    assert result.file_count == 1
    assert "ancienne version" not in output.read_text(encoding="utf-8")


@pytest.mark.parametrize(
    ("size", "expected"),
    [
        pytest.param(0, "0 o", id="zero-byte"),
        pytest.param(1024, "1 Ko", id="one-kibibyte"),
        pytest.param(1536, "1,5 Ko", id="decimal-kibibytes"),
    ],
)
def test_human_sizes(size: int, expected: str) -> None:
    assert _human_size(size) == expected


def test_missing_source_is_rejected(tmp_path: Path) -> None:
    missing_source = tmp_path / "inexistant"

    with pytest.raises(ValueError, match="n'existe pas"):
        generate_html(missing_source, tmp_path / "out.html")


def test_reports_scan_and_write_progress(tmp_path: Path) -> None:
    source = tmp_path / "source"
    nested = source / "documents"
    nested.mkdir(parents=True)
    (source / "premier.txt").write_text("1", encoding="utf-8")
    (nested / "second.pdf").write_text("22", encoding="utf-8")
    events: list[ScanProgress] = []

    generate_html(
        source,
        tmp_path / "out.html",
        progress_callback=events.append,
        progress_interval=1,
        sort_entries=False,
    )

    assert events[0].phase == "scan"
    assert {event.phase for event in events} == {"scan", "write", "done"}
    assert events[-1].files_scanned == 2
    assert events[-1].directories_scanned == 1
    assert events[-1].bytes_scanned == 3
