from __future__ import annotations

import queue
import threading
import tkinter as tk
from tkinter import messagebox
from tkinter import PhotoImage

import speech_recognition as sr

from jarvis.actions.router import CommandRouter
from jarvis.brain.llm import JarvisBrain
from jarvis.brain.memory import ConversationMemory
from jarvis.speech.listener import SpeechListener
from jarvis.speech.tts import SpeechSynthesizer
from jarvis.paths import asset_path
from jarvis.ui.screens import (
    CommandCenterScreen,
    ConversationScreen,
    HomeScreen,
    SettingsScreen,
)
from jarvis.ui.theme import Theme, THEMES
from jarvis.updater import check_for_update
from jarvis.utils.config import has_valid_openai_key, settings
from jarvis.utils.lucide_icons import all_nav_raster_pngs_exist, nav_icon_pair
from jarvis.utils.logger import setup_logger
from jarvis.utils.user_settings import default_ui_settings, load_ui_settings, save_ui_settings


class JarvisDesktopApp:
    def __init__(self) -> None:
        self.logger = setup_logger()
        self.memory = ConversationMemory(settings.user_data_dir / "memory.json")
        self.listener = SpeechListener()
        self.speaker = SpeechSynthesizer()
        self.brain = JarvisBrain(self.memory)
        self.router = CommandRouter()
        self.event_queue: queue.Queue[tuple[str, str]] = queue.Queue()
        self.running = True
        self.active_screen = "home"
        self.ui_settings = {**default_ui_settings(), **load_ui_settings()}
        self.voice_muted = not self.ui_settings.get("sound", True)
        th0 = THEMES.get(self.ui_settings.get("theme", "Neon") or "Neon", THEMES["Neon"])
        self._nav_theme: Theme = th0
        self._logo_image: object | None = None

        self.root = tk.Tk()
        self.root.title(f"{settings.app_name} {settings.version}")
        self.root.geometry("1024x700")
        self.root.minsize(920, 600)
        self.root.configure(bg=th0.bg)
        self.root.bind("<F8>", lambda _: self.toggle_listening())

        self.sidebar = tk.Frame(self.root, width=110, bg=th0.sidebar)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)
        self.content = tk.Frame(self.root, bg=th0.bg)
        self.content.pack(side="left", fill="both", expand=True)

        self._nav_use_raster: bool = False
        self._nav_icon_pairs: dict[str, tuple[object, object]] = {}
        self._nav: tk.Frame | None = None
        self._nav_hovered: str | None = None
        self._nav_canvases: dict[str, tk.Canvas] = {}
        self._nav_mdl_glyphs: dict[str, str] = {}
        self._nav_mdl_font: tuple = ("Segoe MDL2 Assets", 24)
        self._build_sidebar()
        self._build_screens()

        self.root.after(120, self._drain_queue)
        threading.Thread(target=self._loop, daemon=True).start()

    def _build_sidebar(self) -> None:
        th = self._nav_theme
        for w in self.sidebar.winfo_children():
            w.destroy()
        self.nav_buttons = {}
        self._nav_use_raster = False
        self._nav_icon_pairs = {}
        self._nav_canvases = {}
        self._nav_mdl_glyphs = {}
        self._nav = None
        self._nav_hovered = None
        self._logo_image = None

        top = tk.Frame(self.sidebar, bg=th.sidebar)
        top.pack(fill=tk.X, pady=(14, 10), padx=6)
        logo_path = asset_path("logo.png")
        if logo_path.is_file():
            self._logo_image = PhotoImage(file=str(logo_path))
            im = self._logo_image
            w = 88
            if isinstance(self._logo_image, PhotoImage) and im.width() > 0:  # type: ignore[union-attr]
                while im.width() > w:  # type: ignore[union-attr]
                    im = im.subsample(2, 2)  # type: ignore[assignment]
                    self._logo_image = im
        if self._logo_image is not None:
            self._logo_label = tk.Label(top, image=self._logo_image, bg=th.sidebar)  # type: ignore[union-attr]
        else:
            self._logo_label = tk.Label(
                top, text="AI", font=("Segoe UI", 20, "bold"), fg=th.hint, bg=th.sidebar
            )
        self._logo_label.pack()
        mdl: tuple[str, int] = ("Segoe MDL2 Assets", 24)
        self._nav_mdl_font = mdl
        mdl_items: list[tuple[str, str]] = [
            ("home", "\uE80F"),
            ("chat", "\uE8BD"),
            ("settings", "\uE713"),
            ("commands", "\uE945"),
        ]
        nav = tk.Frame(self.sidebar, bg=th.sidebar)
        # Nav directly under the logo, not vertically centered; spacer below fills the rest
        if all_nav_raster_pngs_exist():
            rasters: list[tuple[str, str]] = [
                ("home", "home"),
                ("chat", "chat"),
                ("settings", "settings"),
                ("commands", "zap"),
            ]
            candidate: dict[str, tuple[object, object]] = {}
            for key, file_base in rasters:
                d, a = nav_icon_pair(self.root, file_base)
                if d is None or a is None:
                    candidate = {}
                    break
                candidate[key] = (d, a)
            if len(candidate) == len(rasters):
                self._nav_icon_pairs = candidate
                self._nav_use_raster = True
                for key, _ in rasters:
                    row = tk.Frame(nav, bg=th.sidebar)
                    row.pack(fill=tk.X, pady=18, padx=0)
                    c = tk.Canvas(
                        row,
                        width=66,
                        height=66,
                        highlightthickness=0,
                        bd=0,
                        bg=th.sidebar,
                        cursor="hand2",
                    )
                    c.pack(anchor=tk.CENTER, pady=4, padx=4)
                    c.bind("<Button-1>", lambda _e, k=key: self.show_screen(k))
                    c.bind("<Enter>", lambda _e, k=key: self._on_nav_enter_canvas(_e, k))
                    c.bind("<Leave>", lambda _e, k=key: self._on_nav_leave_canvas(_e, k))
                    self.nav_buttons[key] = c
                    self._nav_canvases[key] = c
                self._nav = nav
                nav.pack(side=tk.TOP, fill=tk.X, pady=(4, 8), padx=0)
                tk.Frame(self.sidebar, bg=th.sidebar).pack(
                    side=tk.TOP, fill=tk.BOTH, expand=True
                )
                self._style_nav_inactive()
                self._highlight_active()
                return

        for key, ch in mdl_items:
            self._nav_mdl_glyphs[key] = ch
            row = tk.Frame(nav, bg=th.sidebar)
            row.pack(fill=tk.X, pady=18, padx=0)
            c = tk.Canvas(
                row,
                width=66,
                height=66,
                highlightthickness=0,
                bd=0,
                bg=th.sidebar,
                cursor="hand2",
            )
            c.pack(anchor=tk.CENTER, pady=4, padx=4)
            c.bind("<Button-1>", lambda _e, k=key: self.show_screen(k))
            c.bind("<Enter>", lambda _e, k=key: self._on_nav_enter_canvas(_e, k))
            c.bind("<Leave>", lambda _e, k=key: self._on_nav_leave_canvas(_e, k))
            self.nav_buttons[key] = c
            self._nav_canvases[key] = c
        self._nav = nav
        nav.pack(side=tk.TOP, fill=tk.X, pady=(4, 8), padx=0)
        tk.Frame(self.sidebar, bg=th.sidebar).pack(
            side=tk.TOP, fill=tk.BOTH, expand=True
        )
        self._style_nav_inactive()
        self._highlight_active()

    def _on_nav_enter_canvas(self, _e: object, key: str) -> None:
        if key == self.active_screen:
            return
        old = self._nav_hovered
        self._nav_hovered = key
        if old and old != key:
            self._draw_nav_item(old)
        self._draw_nav_item(key)

    def _on_nav_leave_canvas(self, _e: object, key: str) -> None:
        if self._nav_hovered == key:
            self._nav_hovered = None
        self._draw_nav_item(key)

    def _draw_nav_item(self, key: str) -> None:
        c = self._nav_canvases.get(key)
        if c is None:
            return
        t = self._nav_theme
        c.delete("all")
        c.configure(bg=t.sidebar, highlightthickness=0)
        if c.master and isinstance(c.master, tk.Frame):
            c.master.configure(bg=t.sidebar)
        w, h = int(c.cget("width")), int(c.cget("height"))
        cx, cy = w // 2, h // 2
        r = (min(w, h) - 2) // 2
        on = key == self.active_screen
        hovered = self._nav_hovered == key
        if on:
            c.create_oval(
                cx - r, cy - r, cx + r, cy + r, fill=t.nav_active, outline="", width=0
            )
        elif hovered:
            c.create_oval(
                cx - r, cy - r, cx + r, cy + r, fill=t.card_highlight, outline="", width=0
            )
        if self._nav_use_raster and key in self._nav_icon_pairs:
            d, a = self._nav_icon_pairs[key]
            im = a if on else d
            c._nav_icon_ref = im  # type: ignore[attr-defined]
            c.create_image(cx, cy, image=im)  # type: ignore[union-attr]
        else:
            ch = self._nav_mdl_glyphs.get(key, "")
            if on:
                fill = "#ffffff"
            elif hovered and not on:
                fill = t.text
            else:
                fill = "#c2cad8"
            c.create_text(
                cx,
                cy,
                text=ch,
                font=self._nav_mdl_font,
                fill=fill,  # type: ignore[assignment]
            )

    def _set_nav_look_for_key(self, key: str) -> None:
        self._draw_nav_item(key)

    def _style_nav_inactive(self) -> None:
        self._nav_hovered = None

    def _build_screens(self) -> None:
        theme = THEMES[self.ui_settings["theme"]]
        mic_options = ["Default"] + self.listener.list_microphones()
        voice_options = ["Default"] + self.speaker.list_voices()
        self.screens = {
            "home": HomeScreen(
                self.content,
                theme,
                self.toggle_voice_mute,
                self._run_manual_command,
            ),
            "chat": ConversationScreen(self.content, theme),
            "settings": SettingsScreen(
                self.content,
                theme,
                self._on_settings_save,
                self._check_updates,
                settings.version,
                mic_options,
                voice_options,
                self.ui_settings,
            ),
            "commands": CommandCenterScreen(self.content, theme, self._run_manual_command),
        }
        for frame in self.screens.values():
            frame.place(x=0, y=0, relwidth=1, relheight=1)
        # Ensure Home is visible first; show_screen no-ops when target is already active.
        self.screens["home"].lift()
        self.screens["home"].set_muted(self.voice_muted)
        self._apply_settings(self.ui_settings.copy(), persist=False)

    def _highlight_active(self) -> None:
        for key in self.nav_buttons:
            self._set_nav_look_for_key(key)

    def show_screen(self, name: str, animate: bool = True) -> None:
        if name not in self.screens or name == self.active_screen:
            return
        old = self.screens[self.active_screen]
        new = self.screens[name]
        self.active_screen = name
        self._highlight_active()
        if not animate or not self.ui_settings["animations"]:
            old.lower()
            new.lift()
            return
        width = self.content.winfo_width() or 900
        new.place_configure(x=width)
        new.lift()
        steps = 12
        step_px = max(width // steps, 1)

        def tick(i: int) -> None:
            if i >= steps:
                new.place_configure(x=0)
                old.lower()
                return
            new.place_configure(x=width - (i + 1) * step_px)
            old.place_configure(x=-(i + 1) * step_px // 2)
            self.root.after(24, lambda: tick(i + 1))

        tick(0)

    def _on_settings_save(self, payload: dict) -> None:
        self._apply_settings(payload, persist=True)
        save_ui_settings(dict(self.ui_settings))
        messagebox.showinfo("Settings", "Settings saved.")
        self.logger.info("User settings saved to profile.")

    def _apply_settings(self, payload: dict, *, persist: bool) -> None:
        self.ui_settings.update(payload)
        api_key = payload.get("openai_api_key", "")
        self.brain.set_api_key(api_key)
        self.listener.set_api_key(api_key)
        self._refresh_api_warning()
        self.speaker.set_volume(payload.get("volume", 1.0))
        self.voice_muted = not payload.get("sound", True)
        self.screens["home"].set_muted(self.voice_muted)
        selected_model = payload.get("model")
        if selected_model:
            self.brain.set_model(selected_model)
        wake_word = (payload.get("wake_word") or "jarvis").strip().lower()
        self.listener.set_wake_word(wake_word)
        mic_name = payload.get("mic", "Default")
        self.listener.set_device_by_name(mic_name)
        self.speaker.set_voice_by_name(payload.get("voice", "Default"))
        theme_name = payload.get("theme", "Neon")
        if theme_name in THEMES:
            theme = THEMES[theme_name]
            self._nav_theme = theme
            self.root.configure(bg=theme.bg)
            self.content.configure(bg=theme.bg)
            self.sidebar.configure(bg=theme.sidebar)
            for w in self.sidebar.winfo_children():
                try:
                    w.configure(bg=theme.sidebar)
                except tk.TclError:
                    pass
            if getattr(self, "_logo_label", None) is not None:
                self._logo_label.configure(bg=theme.sidebar)
            self._nav_hovered = None
            self._highlight_active()
            for screen in self.screens.values():
                screen.apply_theme(theme)

    def _check_updates(self) -> None:
        try:
            available, message = check_for_update(settings.version)
            messagebox.showinfo("Update", message if not available else f"Update available: {message}")
        except Exception as exc:
            messagebox.showerror("Update error", str(exc))

    def toggle_listening(self) -> None:
        self.running = not self.running
        state = "Listening (hotkey active)" if self.running else "Paused (press F8)"
        self._enqueue("state", state)
        if not self.running:
            self._enqueue("mic", "off")
            self._enqueue("mic_health", "paused")
        if self.running:
            threading.Thread(target=self._loop, daemon=True).start()

    def toggle_voice_mute(self) -> None:
        self.voice_muted = not self.voice_muted
        self.ui_settings["sound"] = not self.voice_muted
        self.screens["home"].set_muted(self.voice_muted)
        if self.voice_muted:
            self.speaker.interrupt()
            self._enqueue("state", "Muted")
        else:
            self._enqueue("state", "Listening")

    def _refresh_api_warning(self) -> None:
        if has_valid_openai_key(self.ui_settings.get("openai_api_key")):
            self._enqueue("api_hint", "0")
        else:
            self._enqueue("api_hint", "1")

    def _enqueue(self, key: str, value: str) -> None:
        self.event_queue.put((key, value))

    def _drain_queue(self) -> None:
        try:
            while True:
                key, value = self.event_queue.get_nowait()
                if key == "state":
                    self.screens["home"].set_state(value)
                elif key == "snippet":
                    self.screens["home"].set_snippet(value)
                elif key == "api_hint":
                    self.screens["home"].set_api_key_hint(value == "1")
                elif key == "chat_user":
                    self.screens["chat"].add_message("user", value, self.ui_settings["animations"])
                elif key == "chat_assistant":
                    self.screens["chat"].add_message("assistant", value, self.ui_settings["animations"])
                elif key == "mic":
                    self.screens["home"].set_mic_processing(value == "on")
                elif key == "mic_health":
                    self.screens["home"].set_mic_health(value)
        except queue.Empty:
            pass
        self.root.after(120, self._drain_queue)

    def _loop(self) -> None:
        try:
            self.listener.calibrate(0.8)
            self._enqueue("state", "Listening")
            self._enqueue("mic_health", "ok")
        except Exception as exc:
            self.logger.exception("Microphone calibration failed")
            self._enqueue("state", f"Mic error: {exc}")
            self._enqueue("mic_health", "err")
            return

        while self.running:
            try:
                self._enqueue("mic", "on")
                text = self.listener.listen_once()
                self._enqueue("mic", "off")
                if not text:
                    continue
                if not self.listener.matches_wake_word(text):
                    self._enqueue("state", f"Say '{self.listener.wake_word}' to activate")
                    continue
                cleaned = text.replace(self.listener.wake_word, "").strip(",. ").strip()
                if not cleaned:
                    continue
                self._run_manual_command(cleaned)
            except sr.WaitTimeoutError:
                self._enqueue("mic", "off")
                continue
            except Exception as exc:
                self.logger.exception("Voice loop error")
                self._enqueue("mic", "off")
                self._enqueue("state", f"Error: {exc}")

    def _run_manual_command(self, text: str) -> None:
        threading.Thread(target=self._process_text, args=(text,), daemon=True).start()

    def _process_text(self, text: str) -> None:
        self._enqueue("chat_user", text)
        self._enqueue("snippet", f"User: {text}")
        self._enqueue("state", "Thinking")
        try:
            action_result = self.router.route_many(text)
            if action_result is None:
                action_result = self.brain.reply(text)
            if self.ui_settings["response_style"] == "concise":
                action_result = action_result[:320]
            self._enqueue("chat_assistant", action_result)
            self._enqueue("snippet", f"Jarvis: {action_result}")
            if self.ui_settings["sound"]:
                self._enqueue("state", "Speaking")
                self.speaker.speak(action_result)
        except Exception as exc:
            self.logger.exception("Text processing failed")
            self._enqueue("chat_assistant", f"Error: {exc}")
        finally:
            self._enqueue("state", "Listening")

    def run(self) -> None:
        self.root.mainloop()
