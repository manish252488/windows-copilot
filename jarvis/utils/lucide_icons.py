"""Load Lucide-style raster icons (PNG from SVG) and recolor for Tkinter."""
from __future__ import annotations

import tkinter as tk
from pathlib import Path
from typing import Any

from jarvis.paths import asset_path

# Matches sidebar inactive / active (app.py)
NAV_COLOR_INACTIVE = "#c2cad8"
NAV_COLOR_ACTIVE = "#ffffff"
MIC_COLOR = "#ffffff"


def _has_pillow() -> bool:
    try:
        import PIL.Image  # noqa: F401
        return True
    except ImportError:
        return False


def icon_png_path(name: str) -> Path:
    return asset_path("icons", f"{name}.png")


def all_nav_raster_pngs_exist() -> bool:
    for name in ("home", "chat", "settings", "zap"):
        if not icon_png_path(name).is_file():
            return False
    return True


def _tint_rgba(im: Any, hex_color: str) -> Any:
    r = int(hex_color[1:3], 16)
    g = int(hex_color[3:5], 16)
    b = int(hex_color[5:7], 16)
    im = im.convert("RGBA")
    px = im.load()
    w, h = im.size
    for yy in range(h):
        for xx in range(w):
            a = px[xx, yy][3]
            if a:
                px[xx, yy] = (r, g, b, a)
    return im


def photo_tinted(path: Path, hex_color: str, master: tk.Misc, size: int | None = None) -> Any:
    if not _has_pillow():
        return None
    if not path.is_file():
        return None
    from PIL import Image, ImageTk

    im = Image.open(path).convert("RGBA")
    if size is not None and im.size != (size, size):
        im = im.resize((size, size), Image.Resampling.LANCZOS)
    im = _tint_rgba(im, hex_color)
    return ImageTk.PhotoImage(im, master=master)


def nav_icon_pair(
    master: tk.Misc,
    base_name: str,
    size: int = 28,
) -> tuple[Any, Any]:
    p = icon_png_path(base_name)
    dim = photo_tinted(p, NAV_COLOR_INACTIVE, master, size)
    act = photo_tinted(p, NAV_COLOR_ACTIVE, master, size)
    return (dim, act)


def mic_hero_photo(master: tk.Misc, size: int = 80) -> Any:
    p = icon_png_path("mic")
    return photo_tinted(p, MIC_COLOR, master, size)
