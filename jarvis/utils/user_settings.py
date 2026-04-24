from __future__ import annotations

import json
from pathlib import Path

from jarvis.utils import config


def _path() -> Path:
    config.settings.user_data_dir.mkdir(parents=True, exist_ok=True)
    return config.settings.user_data_dir / "ui_settings.json"


def default_ui_settings() -> dict:
    from jarvis.utils import config

    s = config.settings
    return {
        "theme": "Neon",
        "openai_api_key": "",
        "wake_word": (s.wake_word or "jarvis").strip().lower() or "jarvis",
        "animations": True,
        "sound": True,
        "response_style": "concise",
        "model": s.openai_model,
        "mic": "Default",
        "voice": "Default",
        "volume": 1.0,
    }


def load_ui_settings() -> dict:
    path = _path()
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            return data
    except (OSError, json.JSONDecodeError, TypeError):
        pass
    return {}


def save_ui_settings(data: dict) -> None:
    path = _path()
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
