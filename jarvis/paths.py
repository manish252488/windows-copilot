from __future__ import annotations

from pathlib import Path

JARVIS_PACKAGE = Path(__file__).resolve().parent


def asset_path(*parts: str) -> Path:
    return JARVIS_PACKAGE.joinpath("assets", *parts)
