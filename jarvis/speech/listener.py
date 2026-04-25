from __future__ import annotations

import io

import speech_recognition as sr
from openai import OpenAI

from jarvis.utils.config import has_valid_openai_key, settings


class SpeechListener:
    def __init__(self) -> None:
        self.recognizer = sr.Recognizer()
        # End phrase when speaker pauses for ~2s after speaking.
        self.recognizer.pause_threshold = settings.stt_pause_threshold_seconds
        self.recognizer.dynamic_energy_threshold = True
        self.device_index: int | None = None
        self.mic = sr.Microphone(device_index=self.device_index)
        self.api_key = settings.openai_api_key or ""
        self.client = OpenAI(api_key=self.api_key) if has_valid_openai_key(self.api_key) else None
        self.noise_cancellation_level = 5
        self.set_noise_cancellation_level(self.noise_cancellation_level)

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

    def set_api_key(self, api_key: str) -> None:
        self.api_key = (api_key or "").strip()
        self.client = OpenAI(api_key=self.api_key) if has_valid_openai_key(self.api_key) else None

    def set_noise_cancellation_level(self, level: int | float) -> None:
        # 1 = minimal filtering (more sensitive), 10 = aggressive filtering.
        lv = int(max(1, min(10, int(level))))
        self.noise_cancellation_level = lv
        base_threshold = 120
        step = 95
        self.recognizer.energy_threshold = base_threshold + (lv - 1) * step
        self.recognizer.dynamic_energy_adjustment_damping = max(0.03, 0.18 - lv * 0.012)
        self.recognizer.dynamic_energy_adjustment_ratio = 1.5 + (lv * 0.2)

    def calibrate(self, seconds: float = 1.0) -> None:
        with self.mic as source:
            self.recognizer.adjust_for_ambient_noise(source, duration=seconds)

    def listen_once(self, timeout: int | None = None, phrase_time_limit: int | None = None) -> str | None:
        timeout = timeout if timeout is not None else settings.stt_timeout_seconds
        phrase_time_limit = (
            phrase_time_limit
            if phrase_time_limit is not None
            else settings.stt_phrase_time_limit_seconds
        )
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
                temperature=0,
                prompt=settings.stt_openai_prompt,
            )
            return result.text.strip()
        return self.recognizer.recognize_google(audio, language=settings.stt_locale).strip()

