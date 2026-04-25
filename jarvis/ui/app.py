from __future__ import annotations

import queue
import re
import threading
import time
import tkinter as tk
from tkinter import messagebox
from tkinter import PhotoImage

import speech_recognition as sr
try:
    import ttkbootstrap as tb
except Exception:  # pragma: no cover - optional UI dependency fallback
    tb = None  # type: ignore[assignment]

from jarvis.actions import developer
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
        self.active_screen = "home"
        self.ui_settings = {**default_ui_settings(), **load_ui_settings()}
        self.running = bool(self.ui_settings.get("mic_enabled", True))
        self._listener_thread: threading.Thread | None = None
        self._tts_active = False
        self._assistant_busy = False
        self._last_tts_text = ""
        self._last_tts_end_monotonic = 0.0
        self._post_tts_cooldown_sec = 1.0
        self._pending_git_command: str | None = None
        self._pending_git_repo: str | None = None
        self.voice_muted = not self.ui_settings.get("sound", True)
        th0 = THEMES.get(self.ui_settings.get("theme", "Neon") or "Neon", THEMES["Neon"])
        self._nav_theme: Theme = th0
        self._logo_image: object | None = None

        if tb is not None:
            self.root = tb.Window(themename="darkly")
        else:
            self.root = tk.Tk()
        self.root.title(f"{settings.app_name} {settings.version}")
        self.root.geometry("1024x700")
        self.root.minsize(920, 600)
        self.root.configure(bg=th0.bg)
        self.root.bind("<F8>", lambda _: self.toggle_listening())
        self._apply_modern_theme(self.ui_settings.get("theme", "Neon"))

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
        if self.running:
            self._ensure_listener_thread()
        else:
            self._enqueue("state", "Mic Off")
            self._enqueue("mic", "off")
            self._enqueue("mic_health", "paused")

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
                self.toggle_listening,
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
        self.screens["home"].set_listening_enabled(self.running)
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
        self.listener.set_noise_cancellation_level(payload.get("noise_cancellation_level", 5))
        self.voice_muted = not payload.get("sound", True)
        selected_model = payload.get("model")
        if selected_model:
            self.brain.set_model(selected_model)
        self.set_listening(bool(payload.get("mic_enabled", self.running)))
        mic_name = payload.get("mic", "Default")
        self.listener.set_device_by_name(mic_name)
        self.speaker.set_voice_by_name(payload.get("voice", "Default"))
        theme_name = payload.get("theme", "Neon")
        if theme_name in THEMES:
            theme = THEMES[theme_name]
            self._nav_theme = theme
            self._apply_modern_theme(theme_name)
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

    def _apply_modern_theme(self, theme_name: str) -> None:
        if tb is None:
            return
        theme_map = {
            "Neon": "darkly",
            "Dark": "superhero",
            "Minimal": "flatly",
        }
        bootstrap_theme = theme_map.get(theme_name, "darkly")
        try:
            style = tb.Style()
            if style.theme.name != bootstrap_theme:
                style.theme_use(bootstrap_theme)
        except Exception:
            # Keep the app usable even if bootstrap theme switch fails at runtime.
            return

    def _check_updates(self) -> None:
        try:
            available, message = check_for_update(settings.version)
            messagebox.showinfo("Update", message if not available else f"Update available: {message}")
        except Exception as exc:
            messagebox.showerror("Update error", str(exc))

    def _ensure_listener_thread(self) -> None:
        if self._listener_thread is not None and self._listener_thread.is_alive():
            return
        self._listener_thread = threading.Thread(target=self._loop, daemon=True)
        self._listener_thread.start()

    def set_listening(self, enabled: bool) -> None:
        self.running = enabled
        self.ui_settings["mic_enabled"] = enabled
        state = "Listening..." if enabled else "Mic Off"
        self._enqueue("state", state)
        self.screens["home"].set_listening_enabled(enabled)
        if not enabled:
            self._enqueue("mic", "off")
            self._enqueue("mic_health", "paused")
            self.speaker.interrupt()
        else:
            self._enqueue("mic_health", "ok")
            self._ensure_listener_thread()

    def toggle_listening(self) -> None:
        self.set_listening(not self.running)

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
        if self.running:
            self._enqueue("state", "Listening...")
        self._enqueue("mic_health", "ok")

        while self.running:
            try:
                if self._assistant_busy or self._tts_active:
                    self._enqueue("mic", "off")
                    time.sleep(0.08)
                    continue
                self._enqueue("mic", "on")
                text = self.listener.listen_once()
                self._enqueue("mic", "off")
                if not text:
                    continue
                if self._should_ignore_recognized_text(text):
                    self._enqueue("snippet", "Ignored echo/noise input")
                    continue
                # Always surface speech-to-text on Home as soon as it is recognized.
                self._enqueue("snippet", f"Heard: {text}")
                self._run_manual_command(text.strip())
            except sr.WaitTimeoutError:
                self._enqueue("mic", "off")
                continue
            except Exception as exc:
                self.logger.exception("Voice loop error")
                self._enqueue("mic", "off")
                self._enqueue("state", f"Error: {exc}")

    def _run_manual_command(self, text: str) -> None:
        # Pause listening while the assistant is processing/speaking to avoid feedback loops.
        self._assistant_busy = True
        threading.Thread(target=self._process_text, args=(text,), daemon=True).start()

    @staticmethod
    def _normalize_text_for_compare(text: str) -> str:
        s = (text or "").lower()
        s = re.sub(r"https?://", "", s)
        s = re.sub(r"www\.", "", s)
        s = re.sub(r"[^a-z0-9\s]", " ", s)
        return " ".join(s.split())

    def _should_ignore_recognized_text(self, heard_text: str) -> bool:
        now = time.monotonic()
        # Audio tail suppression right after TTS stops.
        if now - self._last_tts_end_monotonic < self._post_tts_cooldown_sec:
            return True
        heard_norm = self._normalize_text_for_compare(heard_text)
        tts_norm = self._normalize_text_for_compare(self._last_tts_text)
        if not heard_norm or not tts_norm:
            return False
        heard_tokens = heard_norm.split()
        tts_tokens = set(tts_norm.split())
        if not heard_tokens:
            return False
        overlap = sum(1 for tok in heard_tokens if tok in tts_tokens) / len(heard_tokens)
        return overlap >= 0.7

    @staticmethod
    def _is_yes_text(text: str) -> bool:
        s = (text or "").strip().lower()
        return s in {"yes", "yeah", "yep", "confirm", "ok", "okay", "do it", "proceed"}

    @staticmethod
    def _is_no_text(text: str) -> bool:
        s = (text or "").strip().lower()
        return s in {"no", "nope", "cancel", "stop", "dont", "don't", "not now"}

    @staticmethod
    def _extract_git_request_command(text: str) -> str | None:
        t = (text or "").strip()
        tl = t.lower()
        if tl.startswith("git commit and push"):
            return t
        if tl.startswith("commit and push"):
            return t
        if tl.startswith("git commit"):
            return t
        if "git status" in tl:
            return "git status"
        if "git pull" in tl:
            return "git pull"
        if "git push" in tl:
            return "git push"
        return None

    def _begin_git_approval(self, git_command: str) -> str:
        repo = developer.resolve_git_repo_path()
        if not repo:
            self._pending_git_command = None
            self._pending_git_repo = None
            return "I could not find a git repository. Tell me the project folder path first."
        self._pending_git_command = git_command.strip()
        self._pending_git_repo = repo
        return (
            f"Git action requested.\nRepo: {repo}\n"
            f"Command: {self._pending_git_command}\n"
            "Should I execute this? Say yes or no."
        )

    def _process_text(self, text: str) -> None:
        self._enqueue("chat_user", text)
        self._enqueue("snippet", f"User: {text}")
        self._enqueue("state", "Thinking")
        try:
            action_result: str | None = None
            if self._pending_git_command:
                if self._is_yes_text(text):
                    cmd = self._pending_git_command
                    repo = self._pending_git_repo or "unknown"
                    self._pending_git_command = None
                    self._pending_git_repo = None
                    executed = self.router.route_many(cmd) or "Git command was not executed."
                    action_result = f"Executing in repo: {repo}\n{executed}"
                elif self._is_no_text(text):
                    self._pending_git_command = None
                    self._pending_git_repo = None
                    action_result = "Okay, I cancelled that git command."
                else:
                    action_result = "Please say yes to execute the pending git command, or no to cancel."
            else:
                git_request = self._extract_git_request_command(text)
                if git_request:
                    action_result = self._begin_git_approval(git_request)
                else:
                    action_result = self.router.route_many(text)
            if action_result is None:
                llm_reply = self.brain.reply(text)
                ai_cmd = self.brain.extract_command(llm_reply)
                if ai_cmd:
                    ai_git = self._extract_git_request_command(ai_cmd)
                    if ai_git:
                        action_result = self._begin_git_approval(ai_git)
                    else:
                        routed = self.router.route_many(ai_cmd)
                        if routed:
                            action_result = routed
                        else:
                            action_result = (
                                f"I planned this action but could not execute it yet: {ai_cmd}. "
                                "Try saying it in a different way."
                            )
                else:
                    action_result = llm_reply
            if self.ui_settings["response_style"] == "concise":
                action_result = action_result[:320]
            self._enqueue("chat_assistant", action_result)
            self._enqueue("snippet", f"Jarvis: {action_result}")
            if self.ui_settings["sound"]:
                self._enqueue("state", "Speaking")
                self._tts_active = True
                self._last_tts_text = action_result
                self.speaker.speak(action_result)
        except Exception as exc:
            self.logger.exception("Text processing failed")
            self._enqueue("chat_assistant", f"Error: {exc}")
        finally:
            self._tts_active = False
            self._last_tts_end_monotonic = time.monotonic()
            self._assistant_busy = False
            self._enqueue("state", "Listening..." if self.running else "Mic Off")

    def run(self) -> None:
        self.root.mainloop()
