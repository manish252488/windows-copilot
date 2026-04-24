"""
One-off / dev: rasterize Lucide-style SVGs in jarvis/assets/icons to white-on-transparent PNGs.
Requires: pip install cairosvg pillow
Run from repo root: python scripts/render_svg_icons.py
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

try:
    import cairosvg
except ImportError as e:
    print("Install cairosvg: pip install cairosvg", file=sys.stderr)
    raise SystemExit(1) from e

ROOT = Path(__file__).resolve().parents[1]
ICONS = ROOT / "jarvis" / "assets" / "icons"
NAV = 22
MIC = 80


def render(name: str, out_name: str, size: int) -> None:
    p = ICONS / name
    if not p.is_file():
        print("skip (missing):", p)
        return
    s = p.read_text(encoding="utf-8")
    s = s.replace("currentColor", "#ffffff")
    s = s.replace("stroke:currentColor", "stroke:#ffffff")
    out = io.BytesIO()
    cairosvg.svg2png(
        bytestring=s.encode("utf-8"),
        write_to=out,
        output_width=size,
        output_height=size,
    )
    out_path = ICONS / out_name
    out_path.write_bytes(out.getvalue())
    print("wrote", out_path, len(out.getvalue()), "bytes")


def main() -> int:
    icons = [
        ("home.svg", "home.png", NAV),
        ("message-square.svg", "chat.png", NAV),
        ("settings.svg", "settings.png", NAV),
        ("zap.svg", "zap.png", NAV),
        ("mic.svg", "mic.png", MIC),
    ]
    for src, dst, sz in icons:
        render(src, dst, sz)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
