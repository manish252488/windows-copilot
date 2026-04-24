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

    def interrupt(self) -> None:
        with self._lock:
            self.engine.stop()
            self._speaking = False
