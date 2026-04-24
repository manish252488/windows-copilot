from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Theme:
    """Visual tokens for the Figma-style dark UI."""

    bg: str
    panel: str
    panel_alt: str
    text: str
    text_dim: str
    accent: str
    accent_soft: str
    user_bubble: str
    jarvis_bubble: str
    sidebar: str
    border: str
    accent_blue: str
    input_border: str
    hint: str
    nav_active: str
    card_highlight: str


THEMES: dict[str, Theme] = {
    "Neon": Theme(
        bg="#0b0f1a",
        panel="#151c2c",
        panel_alt="#1a2236",
        text="#ffffff",
        text_dim="#9ba4bf",
        accent="#a040ff",
        accent_soft="#2a3558",
        user_bubble="#2a3a7a",
        jarvis_bubble="#1e2a55",
        sidebar="#050a12",
        border="#2a3350",
        accent_blue="#1a91ff",
        input_border="#2e3a5c",
        hint="#c9b0ff",
        nav_active="#1a91ff",
        card_highlight="#1e2a40",
    ),
    "Dark": Theme(
        bg="#0d1117",
        panel="#161b22",
        panel_alt="#21262d",
        text="#f0f3f6",
        text_dim="#8b949e",
        accent="#7d4dff",
        accent_soft="#30363d",
        user_bubble="#2d4a6f",
        jarvis_bubble="#1f3d52",
        sidebar="#010409",
        border="#30363d",
        accent_blue="#1f6feb",
        input_border="#3d444d",
        hint="#d1b3ff",
        nav_active="#1f6feb",
        card_highlight="#21262d",
    ),
    "Minimal": Theme(
        bg="#f4f7ff",
        panel="#ffffff",
        panel_alt="#e9eefb",
        text="#1a2233",
        text_dim="#58657d",
        accent="#5b7cfa",
        accent_soft="#d3dcff",
        user_bubble="#dbe7ff",
        jarvis_bubble="#e6ebf8",
        sidebar="#eef1f8",
        border="#c8d4f0",
        accent_blue="#2563eb",
        input_border="#c2cce8",
        hint="#6b4e9e",
        nav_active="#2563eb",
        card_highlight="#e8edfb",
    ),
}
