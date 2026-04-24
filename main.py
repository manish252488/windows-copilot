from __future__ import annotations

import queue
import threading
import tkinter as tk
from tkinter import messagebox

import speech_recognition as sr

from jarvis.actions.router import CommandRouter
from jarvis.brain.llm import JarvisBrain
from jarvis.brain.memory import ConversationMemory
from jarvis.speech.listener import SpeechListener
from jarvis.speech.tts import SpeechSynthesizer
from jarvis.updater import check_for_update
from jarvis.utils.config import settings
from jarvis.utils.logger import setup_logger


class JarvisApp:
    def __init__(self) -> None:
        self.logger = setup_logger()
        self.memory = ConversationMemory(settings.user_data_dir / "memory.json")
        self.listener = SpeechListener()
        self.speaker = SpeechSynthesizer()
        self.brain = JarvisBrain(self.memory)
        self.router = CommandRouter()
        self.running = False
        self.event_queue: queue.Queue[tuple[str, str]] = queue.Queue()

        self.root = tk.Tk()
        self.root.title(f"{settings.app_name} {settings.version}")
        self.root.geometry("520x300")
        self.root.attributes("-topmost", True)

        self.state_var = tk.StringVar(value="Idle")
        self.last_command_var = tk.StringVar(value="Last command: -")
        self.response_var = tk.StringVar(value="Response: -")
        self.manual_text_var = tk.StringVar(value="")

        self._build_ui()
        self.root.after(150, self._drain_queue)

    def _build_ui(self) -> None:
        tk.Label(self.root, textvariable=self.state_var, font=("Segoe UI", 14, "bold")).pack(
            pady=8
        )
        tk.Label(self.root, textvariable=self.last_command_var, wraplength=480).pack(pady=6)
        tk.Label(self.root, textvariable=self.response_var, wraplength=480).pack(pady=6)

        btns = tk.Frame(self.root)
        btns.pack(pady=12)

        tk.Button(btns, text="Start", command=self.start).grid(row=0, column=0, padx=8)
        tk.Button(btns, text="Stop", command=self.stop).grid(row=0, column=1, padx=8)
        tk.Button(btns, text="Interrupt Speech", command=self.speaker.interrupt).grid(
            row=0, column=2, padx=8
        )
        tk.Button(btns, text="Check Updates", command=self._check_updates).grid(
            row=0, column=3, padx=8
        )

        manual = tk.Frame(self.root)
        manual.pack(pady=6, fill="x", padx=10)
        tk.Entry(manual, textvariable=self.manual_text_var).pack(side="left", fill="x", expand=True)
        tk.Button(manual, text="Send Text Command", command=self._send_manual_command).pack(
            side="left", padx=8
        )

    def _send_manual_command(self) -> None:
        text = self.manual_text_var.get().strip()
        if not text:
            return
        threading.Thread(target=self._process_text, args=(text,), daemon=True).start()
        self.manual_text_var.set("")

    def _check_updates(self) -> None:
        try:
            available, message = check_for_update(settings.version)
            if available:
                messagebox.showinfo("Update", message)
            else:
                messagebox.showinfo("Update", message)
        except Exception as exc:
            messagebox.showerror("Update error", str(exc))

    def start(self) -> None:
        if self.running:
            return
        self.running = True
        self.state_var.set("Calibrating microphone...")
        threading.Thread(target=self._loop, daemon=True).start()

    def stop(self) -> None:
        self.running = False
        self.state_var.set("Stopped")

    def _enqueue(self, key: str, value: str) -> None:
        self.event_queue.put((key, value))

    def _drain_queue(self) -> None:
        try:
            while True:
                key, value = self.event_queue.get_nowait()
                if key == "state":
                    self.state_var.set(value)
                elif key == "last":
                    self.last_command_var.set(value)
                elif key == "response":
                    self.response_var.set(value)
        except queue.Empty:
            pass
        self.root.after(150, self._drain_queue)

    def _loop(self) -> None:
        try:
            self.listener.calibrate(1.0)
            self._enqueue("state", "Listening...")
        except Exception as exc:
            self.logger.exception("Microphone calibration failed")
            self._enqueue("state", f"Mic error: {exc}")
            self.running = False
            return

        while self.running:
            try:
                text = self.listener.listen_once()
                if not text:
                    continue
                self._enqueue("last", f"Last command: {text}")
                if not self.listener.matches_wake_word(text):
                    self._enqueue(
                        "state",
                        f"Wake word not heard. Say '{settings.wake_word}' first.",
                    )
                    continue
                cleaned = text.replace(settings.wake_word, "").strip(",. ").strip()
                if not cleaned:
                    continue
                self._process_text(cleaned)
            except sr.WaitTimeoutError:
                continue
            except sr.UnknownValueError:
                self._enqueue("state", "Could not understand audio. Try again.")
            except sr.RequestError as exc:
                self._enqueue("response", f"Response: Speech API error - {exc}")
                self._enqueue("state", "Listening...")
            except Exception as exc:
                self.logger.exception("Loop error")
                self._enqueue("response", f"Response: Error - {exc}")
                self._enqueue("state", "Listening...")

    def _process_text(self, text: str) -> None:
        if self.speaker.speaking:
            self.speaker.interrupt()
        self._enqueue("state", "Processing...")
        try:
            action_result = self.router.route_many(text)
            if action_result is None:
                action_result = self.brain.reply(text)
            self._enqueue("response", f"Response: {action_result}")
            self._enqueue("state", "Speaking...")
            self.speaker.speak(action_result)
        except Exception as exc:
            self.logger.exception("Text processing failed")
            self._enqueue("response", f"Response: Error - {exc}")
        finally:
            self._enqueue("state", "Listening..." if self.running else "Idle")

    def run(self) -> None:
        self.root.mainloop()


if __name__ == "__main__":
    JarvisApp().run()
