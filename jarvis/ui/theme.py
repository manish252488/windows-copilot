from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Theme:
    bg: str
    panel: str
    panel_alt: str
    text: str
    text_dim: str
    accent: str
    accent_soft: str
    user_bubble: str
    jarvis_bubble: str


THEMES: dict[str, Theme] = {
    "Neon": Theme(
        bg="#08111f",
        panel="#10213f",
        panel_alt="#0d1a31",
        text="#e7f0ff",
        text_dim="#9db0d7",
        accent="#2de2e6",
        accent_soft="#1d6f8a",
        user_bubble="#214f88",
        jarvis_bubble="#184a5b",
    ),
    "Dark": Theme(
        bg="#121417",
        panel="#1d232a",
        panel_alt="#171c22",
        text="#e6e8eb",
        text_dim="#a8afb8",
        accent="#4d8dff",
        accent_soft="#304f87",
        user_bubble="#2f5ca3",
        jarvis_bubble="#2f4458",
    ),
    "Minimal": Theme(
        bg="#f5f7fb",
        panel="#ffffff",
        panel_alt="#eef2f8",
        text="#1b2430",
        text_dim="#5a6778",
        accent="#3b82f6",
        accent_soft="#d6e5ff",
        user_bubble="#dbeafe",
        jarvis_bubble="#e2e8f0",
    ),
}
