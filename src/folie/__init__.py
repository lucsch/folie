"""Folie, un générateur d'index HTML pour répertoires locaux."""

from folie.core.generator import GenerationResult, ScanProgress, generate_html

__all__ = ["GenerationResult", "ScanProgress", "generate_html"]
from .version import COMMIT_NUMBER, VERSION_MAJOR_MINOR

__version__ = f"{VERSION_MAJOR_MINOR}.{COMMIT_NUMBER}"
