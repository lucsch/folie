from __future__ import annotations

from pathlib import Path

from folie.generator import _human_size, generate_html


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


def test_existing_output_inside_source_is_not_listed(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    output = source / "index.html"
    output.write_text("ancienne version", encoding="utf-8")
    (source / "visible.txt").write_text("ok", encoding="utf-8")

    result = generate_html(source, output)

    assert result.file_count == 1
    assert "ancienne version" not in output.read_text(encoding="utf-8")


def test_human_sizes() -> None:
    assert _human_size(0) == "0 o"
    assert _human_size(1024) == "1 Ko"
    assert _human_size(1536) == "1,5 Ko"
