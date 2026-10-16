from pathlib import Path
from threading import current_thread

from folie.gui.worker import GenerationOptions, start_generation


def test_worker_generates_with_options_and_reports_progress(tmp_path: Path) -> None:
    source = tmp_path / "documents"
    (source / "cache").mkdir(parents=True)
    (source / ".hidden").mkdir()
    (source / "rapport.txt").write_text("rapport")
    (source / "cache" / "ignored.txt").write_text("ignoré")
    output = tmp_path / "out.html"
    results, errors, progress, callback_threads = [], [], [], []

    def on_progress(status):
        progress.append(status)
        callback_threads.append(current_thread())

    thread = start_generation(
        GenerationOptions(source, output, ("cache",), True, "Mon titre", False),
        on_progress, results.append, errors.append,
    )
    thread.join(timeout=10)

    assert not thread.is_alive()
    assert not errors
    assert results[0].file_count == 1
    assert results[0].excluded_count == 2
    assert "Mon titre" in output.read_text()
    assert progress[-1].phase == "done"
    assert all(item is thread for item in callback_threads)


def test_worker_reports_failure_without_success(tmp_path: Path) -> None:
    results, errors = [], []
    thread = start_generation(
        GenerationOptions(tmp_path / "missing", tmp_path / "out.html"),
        lambda status: None, results.append, errors.append,
    )
    thread.join(timeout=10)

    assert not thread.is_alive()
    assert not results
    assert len(errors) == 1
    assert "n'existe pas" in errors[0]
