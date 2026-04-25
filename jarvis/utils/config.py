from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


ROOT_DIR = Path(__file__).resolve().parents[2]
load_dotenv(ROOT_DIR / ".env")
DEFAULT_DATA_DIR = Path(os.getenv("APPDATA", str(ROOT_DIR))) / "Jarvis"


@dataclass(frozen=True)
class Settings:
    app_name: str = "Jarvis"
    version: str = "0.1.0"
    debug: bool = os.getenv("JARVIS_DEBUG", "0") == "1"
    openai_api_key: str | None = os.getenv("OPENAI_API_KEY")
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
    openai_tts_model: str = os.getenv("OPENAI_TTS_MODEL", "gpt-4o-mini-tts")
    openai_tts_voice: str = os.getenv("OPENAI_TTS_VOICE", "alloy")
    stt_locale: str = os.getenv("STT_LOCALE", "en-IN")
    whisper_language: str = os.getenv("WHISPER_LANGUAGE", "en")
    stt_timeout_seconds: int = int(os.getenv("STT_TIMEOUT_SECONDS", "6"))
    stt_phrase_time_limit_seconds: int = int(os.getenv("STT_PHRASE_TIME_LIMIT_SECONDS", "20"))
    stt_pause_threshold_seconds: float = float(os.getenv("STT_PAUSE_THRESHOLD_SECONDS", "2.0"))
    stt_openai_prompt: str = os.getenv(
        "STT_OPENAI_PROMPT",
        "Indian English accent. Keep words exact. Preserve product names and commands.",
    )
    weather_api_key: str | None = os.getenv("WEATHER_API_KEY")
    weather_default_city: str = os.getenv("WEATHER_DEFAULT_CITY", "")
    weather_country_code: str = os.getenv("WEATHER_COUNTRY_CODE", "IN")
    news_api_key: str | None = os.getenv("NEWS_API_KEY")
    user_data_dir: Path = Path(os.getenv("JARVIS_DATA_DIR", DEFAULT_DATA_DIR))
    default_shell_path: str = os.getenv("JARVIS_SHELL", "powershell")
    update_manifest_url: str | None = os.getenv("UPDATE_MANIFEST_URL")


settings = Settings()


def has_valid_openai_key(key: str | None = None) -> bool:
    """If `key` is omitted, uses `settings.openai_api_key` (from .env)."""
    k = (key if key is not None else settings.openai_api_key) or ""
    k = k.strip()
    if not k:
        return False
    placeholders = {
        "your_openai_api_key_here",
        "sk-your-key",
        "YOUR_OPENAI_KEY",
    }
    return k not in placeholders
