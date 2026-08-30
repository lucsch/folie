"""Folie, un générateur d'index HTML pour répertoires locaux."""

from .generator import GenerationResult, ScanProgress, generate_html

__all__ = ["GenerationResult", "ScanProgress", "generate_html"]
__version__ = "0.1.0"
