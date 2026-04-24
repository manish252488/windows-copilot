from __future__ import annotations

import io

import speech_recognition as sr
from openai import OpenAI

from jarvis.utils.config import has_valid_openai_key, settings


class SpeechListener:
    def __init__(self) -> None:
        self.recognizer = sr.Recognizer()
        self.mic = sr.Microphone()
        self.client = OpenAI() if has_valid_openai_key() else None

    def calibrate(self, seconds: float = 1.0) -> None:
        with self.mic as source:
            self.recognizer.adjust_for_ambient_noise(source, duration=seconds)

    def listen_once(self, timeout: int = 4, phrase_time_limit: int = 10) -> str | None:
        with self.mic as source:
            audio = self.recognizer.listen(
                source, timeout=timeout, phrase_time_limit=phrase_time_limit
            )
        return self._transcribe(audio)

    def _transcribe(self, audio: sr.AudioData) -> str:
        if self.client:
            wav_buffer = io.BytesIO(audio.get_wav_data())
            wav_buffer.name = "speech.wav"
            result = self.client.audio.transcriptions.create(
                model="whisper-1",
                file=wav_buffer,
                language=settings.whisper_language,
            )
            return result.text.strip()
        return self.recognizer.recognize_google(audio, language=settings.stt_locale).strip()

    def matches_wake_word(self, text: str) -> bool:
        if not settings.wake_word_enabled:
            return True
        return settings.wake_word in text.lower()
