"""Parcours d'un répertoire et génération d'une page HTML autonome."""

from __future__ import annotations

import fnmatch
import html
import os
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Iterable
from urllib.parse import quote


@dataclass(slots=True)
class FileItem:
    name: str
    path: Path
    size: int
    modified: datetime | None
    category: str
    label: str
    is_symlink: bool = False


@dataclass(slots=True)
class DirectoryItem:
    name: str
    path: Path
    directories: list["DirectoryItem"] = field(default_factory=list)
    files: list[FileItem] = field(default_factory=list)
    error: str | None = None

    @property
    def descendant_file_count(self) -> int:
        return len(self.files) + sum(
            child.descendant_file_count for child in self.directories
        )

    @property
    def descendant_size(self) -> int:
        return sum(item.size for item in self.files) + sum(
            child.descendant_size for child in self.directories
        )

    @property
    def descendant_directory_count(self) -> int:
        return len(self.directories) + sum(
            child.descendant_directory_count for child in self.directories
        )

    @property
    def error_count(self) -> int:
        return int(self.error is not None) + sum(
            child.error_count for child in self.directories
        )


@dataclass(frozen=True, slots=True)
class GenerationResult:
    output: Path
    file_count: int
    directory_count: int
    excluded_count: int
    error_count: int


_FILE_TYPES: dict[str, tuple[str, str]] = {
    ".doc": ("word", "W"),
    ".docx": ("word", "W"),
    ".odt": ("word", "W"),
    ".rtf": ("word", "W"),
    ".xls": ("excel", "X"),
    ".xlsx": ("excel", "X"),
    ".xlsm": ("excel", "X"),
    ".ods": ("excel", "X"),
    ".csv": ("excel", "X"),
    ".ppt": ("powerpoint", "P"),
    ".pptx": ("powerpoint", "P"),
    ".odp": ("powerpoint", "P"),
    ".pdf": ("pdf", "PDF"),
    ".jpg": ("image", "IMG"),
    ".jpeg": ("image", "IMG"),
    ".png": ("image", "IMG"),
    ".gif": ("image", "IMG"),
    ".webp": ("image", "IMG"),
    ".svg": ("image", "IMG"),
    ".tif": ("image", "IMG"),
    ".tiff": ("image", "IMG"),
    ".zip": ("archive", "ZIP"),
    ".7z": ("archive", "ZIP"),
    ".rar": ("archive", "ZIP"),
    ".tar": ("archive", "ZIP"),
    ".gz": ("archive", "ZIP"),
    ".txt": ("text", "TXT"),
    ".md": ("text", "TXT"),
    ".log": ("text", "TXT"),
    ".py": ("code", "</>"),
    ".js": ("code", "</>"),
    ".ts": ("code", "</>"),
    ".html": ("code", "</>"),
    ".css": ("code", "</>"),
    ".json": ("code", "</>"),
    ".xml": ("code", "</>"),
    ".mp3": ("audio", "♪"),
    ".wav": ("audio", "♪"),
    ".flac": ("audio", "♪"),
    ".mp4": ("video", "▶"),
    ".mov": ("video", "▶"),
    ".avi": ("video", "▶"),
    ".mkv": ("video", "▶"),
}


def _file_type(path: Path, is_symlink: bool) -> tuple[str, str]:
    if is_symlink:
        return "link", "↗"
    return _FILE_TYPES.get(path.suffix.lower(), ("generic", "FILE"))


def _matches_exclusion(relative: Path, patterns: tuple[str, ...]) -> bool:
    relative_text = relative.as_posix()
    name = relative.name
    for original_pattern in patterns:
        pattern = original_pattern.strip().replace("\\", "/")
        if pattern.startswith("./"):
            pattern = pattern[2:]
        pattern = pattern.rstrip("/")
        if not pattern:
            continue
        candidate = relative_text if "/" in pattern else name
        if fnmatch.fnmatchcase(candidate, pattern):
            return True
    return False


def _scan_directory(
    path: Path,
    root: Path,
    patterns: tuple[str, ...],
    exclude_hidden: bool,
    ignored_file: Path,
    excluded_counter: list[int],
) -> DirectoryItem:
    directory = DirectoryItem(name=path.name or str(path), path=path)
    try:
        with os.scandir(path) as scanner:
            entries = sorted(scanner, key=lambda item: item.name.casefold())
    except OSError as exc:
        directory.error = str(exc)
        return directory

    for entry in entries:
        entry_path = Path(entry.path)
        relative = entry_path.relative_to(root)
        try:
            is_symlink = entry.is_symlink()
            is_directory = entry.is_dir(follow_symlinks=False)
        except OSError:
            is_symlink = False
            is_directory = False

        if is_directory:
            if (exclude_hidden and entry.name.startswith(".")) or _matches_exclusion(
                relative, patterns
            ):
                excluded_counter[0] += 1
                continue
            directory.directories.append(
                _scan_directory(
                    entry_path,
                    root,
                    patterns,
                    exclude_hidden,
                    ignored_file,
                    excluded_counter,
                )
            )
            continue

        # Un ancien fichier de sortie placé dans l'arbre ne doit pas s'auto-indexer.
        try:
            if entry_path.resolve() == ignored_file:
                continue
        except OSError:
            pass

        try:
            stat = entry.stat(follow_symlinks=False)
            size = stat.st_size
            modified = datetime.fromtimestamp(stat.st_mtime).astimezone()
        except OSError:
            size = 0
            modified = None
        category, label = _file_type(entry_path, is_symlink)
        directory.files.append(
            FileItem(
                name=entry.name,
                path=entry_path.absolute(),
                size=size,
                modified=modified,
                category=category,
                label=label,
                is_symlink=is_symlink,
            )
        )
    return directory


def _human_size(size: int) -> str:
    value = float(size)
    units = ("o", "Ko", "Mo", "Go", "To", "Po")
    for unit in units:
        if abs(value) < 1024 or unit == units[-1]:
            if unit == "o":
                return f"{int(value)} {unit}"
            formatted = f"{value:.1f}".rstrip("0").rstrip(".").replace(".", ",")
            return f"{formatted} {unit}"
        value /= 1024
    return f"{size} o"


def _file_uri(path: Path) -> str:
    """Produit une URI file: en conservant correctement les caractères spéciaux."""
    try:
        return path.resolve().as_uri()
    except (OSError, ValueError):
        return "file://" + quote(str(path.absolute()))


def _render_file(item: FileItem) -> str:
    escaped_name = html.escape(item.name)
    escaped_path = html.escape(str(item.path))
    escaped_uri = html.escape(_file_uri(item.path), quote=True)
    if item.modified is None:
        modified_html = '<span class="muted">Indisponible</span>'
    else:
        machine_date = item.modified.isoformat(timespec="seconds")
        display_date = item.modified.strftime("%d.%m.%Y %H:%M:%S")
        modified_html = (
            f'<time datetime="{html.escape(machine_date, quote=True)}">'
            f"{html.escape(display_date)}</time>"
        )
    link_note = " — lien symbolique" if item.is_symlink else ""
    return f"""
<a class="tree-row file-row" href="{escaped_uri}" target="_blank" rel="noopener"
   title="Ouvrir {escaped_name}{link_note}">
  <span class="name-cell">
    <span class="file-icon type-{item.category}" aria-hidden="true"><span>{html.escape(item.label)}</span></span>
    <span class="file-name">{escaped_name}</span>
  </span>
  <span class="size-cell" title="{item.size} octets">{_human_size(item.size)}</span>
  <span class="date-cell">{modified_html}</span>
  <span class="path-cell" title="{escaped_path}">{escaped_path}</span>
  <span class="open-cell" aria-hidden="true">↗</span>
</a>"""


def _render_directory(item: DirectoryItem, depth: int = 0) -> str:
    count = item.descendant_file_count
    folder_word = "fichier" if count == 1 else "fichiers"
    open_attribute = " open" if depth == 0 else ""
    escaped_name = html.escape(item.name)
    escaped_path = html.escape(str(item.path))
    parts = [
        f'<details class="directory" data-depth="{depth}"{open_attribute}>',
        '<summary class="tree-row directory-row">',
        '<span class="name-cell">',
        '<span class="chevron" aria-hidden="true"></span>',
        '<span class="folder-icon" aria-hidden="true"></span>',
        f'<span class="folder-name">{escaped_name}</span>',
        f'<span class="count-badge">{count} {folder_word}</span>',
        "</span>",
        f'<span class="size-cell">{_human_size(item.descendant_size)}</span>',
        '<span class="date-cell muted">—</span>',
        f'<span class="path-cell" title="{escaped_path}">{escaped_path}</span>',
        '<span class="open-cell"></span>',
        "</summary>",
        '<div class="directory-children">',
    ]
    if item.error:
        parts.append(
            '<div class="error-row" role="alert">⚠ Impossible de lire ce dossier : '
            f"{html.escape(item.error)}</div>"
        )
    parts.extend(_render_directory(child, depth + 1) for child in item.directories)
    parts.extend(_render_file(file_item) for file_item in item.files)
    if not item.directories and not item.files and not item.error:
        parts.append('<div class="empty-row">Dossier vide</div>')
    parts.extend(("</div>", "</details>"))
    return "\n".join(parts)


def _render_page(root: DirectoryItem, title: str, excluded_count: int) -> str:
    generated_at = datetime.now().astimezone()
    file_count = root.descendant_file_count
    directory_count = root.descendant_directory_count
    tree_html = _render_directory(root)
    escaped_title = html.escape(title)
    escaped_root = html.escape(str(root.path))
    generated_text = generated_at.strftime("%d.%m.%Y à %H:%M:%S")
    return f"""<!doctype html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="color-scheme" content="light dark">
<title>{escaped_title} — Index des fichiers</title>
<style>
:root {{
  color-scheme: light;
  --bg: #f4f6fa; --panel: #fff; --text: #172033; --muted: #667085;
  --line: #e5e9f0; --accent: #315efb; --hover: #f0f5ff;
  --shadow: 0 12px 32px rgba(20, 35, 70, .08);
}}
@media (prefers-color-scheme: dark) {{
  :root {{ color-scheme: dark; --bg:#10131a; --panel:#181d27; --text:#f1f3f7;
    --muted:#9aa4b5; --line:#2a3240; --accent:#83a2ff; --hover:#202a3c;
    --shadow:0 12px 32px rgba(0,0,0,.25); }}
}}
* {{ box-sizing: border-box; }}
body {{ margin:0; background:var(--bg); color:var(--text); font:14px/1.45 system-ui,-apple-system,"Segoe UI",sans-serif; }}
.page {{ width:min(1500px, calc(100% - 32px)); margin:32px auto; }}
header {{ display:flex; align-items:flex-end; justify-content:space-between; gap:24px; margin-bottom:20px; }}
h1 {{ margin:0 0 5px; font-size:clamp(24px,3vw,38px); letter-spacing:-.035em; }}
.subtitle {{ color:var(--muted); overflow-wrap:anywhere; }}
.stats {{ display:flex; gap:8px; flex-wrap:wrap; justify-content:flex-end; }}
.stat {{ padding:8px 12px; background:var(--panel); border:1px solid var(--line); border-radius:10px; white-space:nowrap; }}
.toolbar {{ display:flex; gap:9px; margin-bottom:12px; }}
.search-wrap {{ position:relative; flex:1; }}
.search-wrap::before {{ content:"⌕"; position:absolute; left:13px; top:7px; color:var(--muted); font-size:20px; }}
input,button {{ font:inherit; color:inherit; background:var(--panel); border:1px solid var(--line); border-radius:9px; }}
input {{ width:100%; padding:10px 12px 10px 39px; outline:none; }}
input:focus {{ border-color:var(--accent); box-shadow:0 0 0 3px color-mix(in srgb,var(--accent) 17%,transparent); }}
button {{ padding:9px 13px; cursor:pointer; }} button:hover {{ background:var(--hover); }}
.tree-card {{ background:var(--panel); border:1px solid var(--line); border-radius:14px; box-shadow:var(--shadow); overflow:hidden; }}
.columns,.tree-row {{ display:grid; grid-template-columns:minmax(270px,1.2fr) 100px 170px minmax(260px,1fr) 28px; gap:12px; align-items:center; }}
.columns {{ padding:10px 16px; background:color-mix(in srgb,var(--panel) 88%,var(--bg)); color:var(--muted); font-size:12px; font-weight:650; text-transform:uppercase; letter-spacing:.04em; border-bottom:1px solid var(--line); }}
.tree-row {{ min-height:48px; padding:7px 16px; border-bottom:1px solid var(--line); }}
.directory-row {{ cursor:pointer; list-style:none; font-weight:650; user-select:none; }}
.directory-row::-webkit-details-marker {{ display:none; }}
.directory-row:hover,.file-row:hover {{ background:var(--hover); }}
.file-row {{ color:inherit; text-decoration:none; }}
.directory-children {{ padding-left:22px; }}
.directory-children > * {{ border-left:1px solid var(--line); }}
.name-cell {{ display:flex; min-width:0; align-items:center; gap:10px; }}
.file-name,.folder-name {{ overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }}
.chevron {{ width:8px; height:8px; border-right:2px solid var(--muted); border-bottom:2px solid var(--muted); transform:rotate(-45deg); transition:transform .15s ease; flex:none; }}
details[open] > summary .chevron {{ transform:rotate(45deg); }}
.folder-icon {{ width:22px; height:15px; border-radius:3px; background:#e8aa2c; position:relative; flex:none; box-shadow:inset 0 -2px 0 rgba(0,0,0,.1); }}
.folder-icon::before {{ content:""; position:absolute; width:10px; height:4px; top:-3px; left:2px; border-radius:2px 2px 0 0; background:#e8aa2c; }}
.file-icon {{ width:25px; height:31px; border-radius:3px; display:grid; place-items:end center; padding-bottom:4px; color:white; background:#7d8797; font-size:7px; font-weight:800; position:relative; flex:none; box-shadow:inset 0 -2px 0 rgba(0,0,0,.12); }}
.file-icon::after {{ content:""; position:absolute; right:0; top:0; border-style:solid; border-width:0 8px 8px 0; border-color:transparent var(--panel) transparent transparent; opacity:.75; }}
.type-word{{background:#2b579a}} .type-excel{{background:#217346}} .type-powerpoint{{background:#d24726}} .type-pdf{{background:#d93831}} .type-image{{background:#8b5cf6}} .type-archive{{background:#b7791f}} .type-code{{background:#475569}} .type-text{{background:#64748b}} .type-audio{{background:#db2777}} .type-video{{background:#0891b2}} .type-link{{background:#6366f1}}
.count-badge {{ margin-left:auto; color:var(--muted); font-size:12px; font-weight:500; }}
.size-cell,.date-cell {{ white-space:nowrap; font-variant-numeric:tabular-nums; }}
.path-cell {{ overflow:hidden; text-overflow:ellipsis; white-space:nowrap; color:var(--muted); font-family:ui-monospace,"SFMono-Regular",Consolas,monospace; font-size:12px; }}
.open-cell {{ color:var(--accent); font-size:17px; text-align:center; }} .muted,.empty-row {{ color:var(--muted); }}
.empty-row,.error-row {{ padding:12px 18px 12px 52px; border-bottom:1px solid var(--line); font-style:italic; }} .error-row{{color:#d04444}}
.search-hidden {{ display:none !important; }}
footer {{ color:var(--muted); margin:14px 3px; font-size:12px; }}
@media (max-width:900px) {{
  .columns,.tree-row {{ grid-template-columns:minmax(220px,1fr) 90px 155px 28px; }}
  .path-cell,.columns .path-heading {{ display:none; }} header{{align-items:flex-start;flex-direction:column}} .stats{{justify-content:flex-start}}
}}
@media (max-width:620px) {{
  .page{{width:100%;margin:0}} header,.toolbar,footer{{margin-left:12px;margin-right:12px}} header{{padding-top:20px}}
  .tree-card{{border-radius:0;border-left:0;border-right:0}} .toolbar{{flex-wrap:wrap}} .search-wrap{{flex-basis:100%}}
  .columns,.tree-row{{grid-template-columns:minmax(150px,1fr) 78px 24px;gap:7px;padding-left:10px;padding-right:10px}}
  .date-cell,.columns .date-heading{{display:none}} .directory-children{{padding-left:10px}} .count-badge{{display:none}}
}}
</style>
</head>
<body>
<main class="page">
  <header>
    <div><h1>{escaped_title}</h1><div class="subtitle">{escaped_root}</div></div>
    <div class="stats" aria-label="Résumé">
      <span class="stat"><strong id="visible-count">{file_count}</strong> fichier(s)</span>
      <span class="stat"><strong>{directory_count}</strong> sous-dossier(s)</span>
      <span class="stat"><strong>{_human_size(root.descendant_size)}</strong></span>
    </div>
  </header>
  <div class="toolbar">
    <label class="search-wrap"><span hidden>Rechercher</span><input id="search" type="search" placeholder="Rechercher un nom, un chemin…" autocomplete="off"></label>
    <button type="button" id="expand">Tout déplier</button>
    <button type="button" id="collapse">Tout replier</button>
  </div>
  <section class="tree-card" aria-label="Arborescence des fichiers">
    <div class="columns" aria-hidden="true"><span>Nom</span><span>Taille</span><span class="date-heading">Dernière modification</span><span class="path-heading">Chemin complet</span><span></span></div>
    {tree_html}
  </section>
  <footer>Inventaire généré le {generated_text}. {excluded_count} dossier(s) exclu(s). Les fichiers s’ouvrent selon les réglages de votre navigateur et de votre système.</footer>
</main>
<script>
(() => {{
  const directories = [...document.querySelectorAll('details.directory')];
  const files = [...document.querySelectorAll('.file-row')];
  const search = document.getElementById('search');
  const visibleCount = document.getElementById('visible-count');
  const normalize = value => value.normalize('NFD').replace(/[\\u0300-\\u036f]/g, '').toLocaleLowerCase();

  document.getElementById('expand').addEventListener('click', () => directories.forEach(item => item.open = true));
  document.getElementById('collapse').addEventListener('click', () => directories.forEach((item, index) => item.open = index === 0));

  search.addEventListener('input', () => {{
    const query = normalize(search.value.trim());
    let shown = 0;
    files.forEach(file => {{
      const matches = !query || normalize(file.textContent).includes(query);
      file.classList.toggle('search-hidden', !matches);
      if (matches) shown += 1;
    }});
    [...directories].reverse().forEach((directory, reverseIndex) => {{
      const summary = directory.querySelector(':scope > summary');
      const ownMatch = query && normalize(summary.textContent).includes(query);
      const childMatch = !!directory.querySelector(':scope > .directory-children > .file-row:not(.search-hidden), :scope > .directory-children > details.directory:not(.search-hidden)');
      const isRoot = reverseIndex === directories.length - 1;
      const visible = !query || ownMatch || childMatch || isRoot;
      directory.classList.toggle('search-hidden', !visible);
      if (query && visible) directory.open = true;
    }});
    visibleCount.textContent = shown;
  }});
}})();
</script>
</body>
</html>
"""


def generate_html(
    source: str | Path,
    output: str | Path = "index_fichiers.html",
    *,
    exclude: Iterable[str] = (),
    exclude_hidden: bool = False,
    title: str | None = None,
) -> GenerationResult:
    """Génère un index HTML autonome à partir de ``source``.

    Les motifs sans séparateur correspondent au nom d'un dossier à n'importe quel
    niveau. Ceux contenant ``/`` correspondent à son chemin relatif à ``source``.
    Les liens symboliques ne sont jamais suivis, ce qui évite les parcours cycliques.
    """
    source_path = Path(source).expanduser().resolve()
    if not source_path.exists():
        raise ValueError(f"le répertoire n'existe pas : {source_path}")
    if not source_path.is_dir():
        raise ValueError(f"ce chemin n'est pas un répertoire : {source_path}")

    output_path = Path(output).expanduser().resolve()
    if output_path.exists() and output_path.is_dir():
        raise ValueError(f"la sortie désigne un répertoire : {output_path}")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    excluded_counter = [0]
    root = _scan_directory(
        source_path,
        source_path,
        tuple(exclude),
        exclude_hidden,
        output_path,
        excluded_counter,
    )
    page_title = title or source_path.name or str(source_path)
    rendered = _render_page(root, page_title, excluded_counter[0])
    output_path.write_text(rendered, encoding="utf-8")

    return GenerationResult(
        output=output_path,
        file_count=root.descendant_file_count,
        directory_count=root.descendant_directory_count,
        excluded_count=excluded_counter[0],
        error_count=root.error_count,
    )
