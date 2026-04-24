from __future__ import annotations

import io

import speech_recognition as sr
from openai import OpenAI

from jarvis.utils.config import has_valid_openai_key, settings


class SpeechListener:
    def __init__(self) -> None:
        self.recognizer = sr.Recognizer()
        self.device_index: int | None = None
        self.mic = sr.Microphone(device_index=self.device_index)
        self.api_key = settings.openai_api_key or ""
        self.client = OpenAI(api_key=self.api_key) if has_valid_openai_key(self.api_key) else None
        self.wake_word_enabled = settings.wake_word_enabled
        self.wake_word = (settings.wake_word or "jarvis").strip().lower() or "jarvis"

    @staticmethod
    def list_microphones() -> list[str]:
        return sr.Microphone.list_microphone_names()

    def set_device_by_name(self, name: str) -> bool:
        clean = name.strip().lower()
        if not clean or clean == "default":
            self.device_index = None
            self.mic = sr.Microphone(device_index=None)
            return True
        for idx, item in enumerate(self.list_microphones()):
            if clean in item.lower():
                self.device_index = idx
                self.mic = sr.Microphone(device_index=idx)
                return True
        return False

    def set_wake_word(self, value: str) -> None:
        self.wake_word = value.strip().lower() or "jarvis"

    def set_api_key(self, api_key: str) -> None:
        self.api_key = (api_key or "").strip()
        self.client = OpenAI(api_key=self.api_key) if has_valid_openai_key(self.api_key) else None

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
        if not self.wake_word_enabled:
            return True
        return self.wake_word in text.lower()
