from __future__ import annotations

import threading

import pyttsx3


class SpeechSynthesizer:
    def __init__(self, rate: int = 185) -> None:
        self.engine = pyttsx3.init()
        self.engine.setProperty("rate", rate)
        self._lock = threading.Lock()
        self._speaking = False

    @property
    def speaking(self) -> bool:
        return self._speaking

    def speak(self, text: str) -> None:
        with self._lock:
            self._speaking = True
            self.engine.say(text)
            self.engine.runAndWait()
            self._speaking = False

    def set_volume(self, value: float) -> None:
        with self._lock:
            self.engine.setProperty("volume", max(0.0, min(value, 1.0)))

    def list_voices(self) -> list[str]:
        voices = self.engine.getProperty("voices")
        return [getattr(v, "name", "unknown") for v in voices]

    def set_voice_by_name(self, name: str) -> bool:
        clean = name.strip().lower()
        if not clean or clean == "default":
            return True
        for voice in self.engine.getProperty("voices"):
            if clean in getattr(voice, "name", "").lower():
                self.engine.setProperty("voice", voice.id)
                return True
        return False

    def interrupt(self) -> None:
        with self._lock:
            self.engine.stop()
            self._speaking = False
