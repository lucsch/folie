from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from folie.cli import app


runner = CliRunner()


def test_cli_generates_index_and_accepts_repeated_exclusions(tmp_path: Path) -> None:
    source = tmp_path / "documents"
    source.mkdir()
    (source / "rapport.pdf").write_bytes(b"pdf")
    excluded = source / "cache"
    excluded.mkdir()
    (excluded / "temporaire.txt").write_text("temp", encoding="utf-8")
    output = tmp_path / "inventaire.html"

    result = runner.invoke(
        app,
        [
            str(source),
            "--output",
            str(output),
            "--exclude",
            "cache",
            "--exclude",
            "archives*",
            "--title",
            "Documents partagés",
        ],
    )

    assert result.exit_code == 0, result.output
    assert "1 fichier(s)" in result.output
    assert "1 dossier(s) exclu(s)" in result.output
    assert output.exists()
    page = output.read_text(encoding="utf-8")
    assert "Documents partagés" in page
    assert "rapport.pdf" in page
    assert "temporaire.txt" not in page


def test_cli_rejects_a_file_as_source(tmp_path: Path) -> None:
    source_file = tmp_path / "document.txt"
    source_file.write_text("contenu", encoding="utf-8")

    result = runner.invoke(app, [str(source_file)])

    assert result.exit_code == 2
    assert "directory" in result.output.lower()
