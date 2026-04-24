from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from jarvis.ui.theme import Theme


class BaseScreen(tk.Frame):
    def __init__(self, parent: tk.Widget, theme: Theme) -> None:
        super().__init__(parent, bg=theme.bg)
        self.theme = theme

    def apply_theme(self, theme: Theme) -> None:
        self.theme = theme
        self.configure(bg=theme.bg)


class HomeScreen(BaseScreen):
    def __init__(self, parent: tk.Widget, theme: Theme) -> None:
        super().__init__(parent, theme)
        self.state_var = tk.StringVar(value="Listening")
        self.snippet_var = tk.StringVar(value="Try saying: Open Chrome")
        self._pulse_phase = 0

        card = tk.Frame(self, bg=theme.panel, bd=0, highlightthickness=1, highlightbackground=theme.accent_soft)
        card.pack(fill="both", expand=True, padx=20, pady=20)

        self.canvas = tk.Canvas(card, bg=theme.panel, highlightthickness=0, height=170)
        self.canvas.pack(fill="x", pady=20)
        self.p1 = self.canvas.create_oval(200, 35, 360, 155, fill=theme.accent_soft, outline="")
        self.p2 = self.canvas.create_oval(220, 55, 340, 135, fill=theme.accent, outline="")

        self.state_label = tk.Label(card, textvariable=self.state_var, fg=theme.text, bg=theme.panel, font=("Segoe UI", 18, "bold"))
        self.state_label.pack(pady=(0, 8))
        self.snippet_label = tk.Label(card, textvariable=self.snippet_var, fg=theme.text_dim, bg=theme.panel, font=("Segoe UI", 11), wraplength=700)
        self.snippet_label.pack(pady=(0, 12))
        self._animate_pulse()

    def _animate_pulse(self) -> None:
        self._pulse_phase = (self._pulse_phase + 1) % 30
        scale = 1 + (self._pulse_phase / 300.0 if self._pulse_phase <= 15 else (30 - self._pulse_phase) / 300.0)
        self.canvas.scale(self.p2, 280, 95, scale, scale)
        self.after(140, self._animate_pulse)

    def set_state(self, state: str) -> None:
        self.state_var.set(state)

    def set_snippet(self, text: str) -> None:
        self.snippet_var.set(text)


class ConversationScreen(BaseScreen):
    def __init__(self, parent: tk.Widget, theme: Theme) -> None:
        super().__init__(parent, theme)
        self.messages: list[tuple[str, str]] = []
        self.last_assistant_text = ""

        top = tk.Frame(self, bg=theme.bg)
        top.pack(fill="x", padx=20, pady=(16, 8))
        self.search_var = tk.StringVar()
        tk.Entry(top, textvariable=self.search_var).pack(side="left", fill="x", expand=True)
        tk.Button(top, text="Search", command=self.search).pack(side="left", padx=8)
        tk.Button(top, text="Copy last response", command=self.copy_last_response).pack(side="left")

        self.canvas = tk.Canvas(self, bg=theme.bg, highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.inner = tk.Frame(self.canvas, bg=theme.bg)
        self.inner.bind("<Configure>", lambda _: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.create_window((0, 0), window=self.inner, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.canvas.pack(side="left", fill="both", expand=True, padx=(20, 0), pady=(0, 20))
        self.scrollbar.pack(side="left", fill="y", padx=(6, 20), pady=(0, 20))

    def add_message(self, role: str, text: str, animated: bool = True) -> None:
        self.messages.append((role, text))
        if role == "assistant":
            self.last_assistant_text = text
        bubble_bg = self.theme.user_bubble if role == "user" else self.theme.jarvis_bubble
        anchor = "e" if role == "user" else "w"
        container = tk.Frame(self.inner, bg=self.theme.bg)
        container.pack(fill="x", padx=12, pady=6)
        bubble = tk.Label(
            container,
            text=text,
            bg=bubble_bg,
            fg=self.theme.text,
            justify="left",
            wraplength=620,
            padx=12,
            pady=8,
            font=("Segoe UI", 10),
        )
        bubble.pack(anchor=anchor)
        if animated:
            bubble.configure(fg=self.theme.text_dim)
            self.after(120, lambda: bubble.configure(fg=self.theme.text))
        self.after(80, lambda: self.canvas.yview_moveto(1.0))

    def search(self) -> None:
        q = self.search_var.get().strip().lower()
        if not q:
            return
        for role, text in reversed(self.messages):
            if q in text.lower():
                self.add_message("assistant", f"Search match ({role}): {text}", animated=False)
                return
        self.add_message("assistant", "No matching message found.", animated=False)

    def copy_last_response(self) -> None:
        if not self.last_assistant_text:
            return
        self.clipboard_clear()
        self.clipboard_append(self.last_assistant_text)


class SettingsScreen(BaseScreen):
    def __init__(self, parent: tk.Widget, theme: Theme, on_change: callable, on_check_updates: callable) -> None:
        super().__init__(parent, theme)
        self.on_change = on_change
        self.on_check_updates = on_check_updates

        card = tk.Frame(self, bg=theme.panel)
        card.pack(fill="both", expand=True, padx=20, pady=20)

        self.theme_var = tk.StringVar(value="Neon")
        self.anim_var = tk.BooleanVar(value=True)
        self.sound_var = tk.BooleanVar(value=True)
        self.style_var = tk.StringVar(value="concise")
        self.model_var = tk.StringVar(value="")
        self.mic_var = tk.StringVar(value="Default")
        self.voice_var = tk.StringVar(value="Default")
        self.volume_var = tk.DoubleVar(value=1.0)

        tk.Label(card, text="General", bg=theme.panel, fg=theme.text, font=("Segoe UI", 12, "bold")).pack(anchor="w", padx=16, pady=(16, 6))
        self._row(card, "Theme", tk.OptionMenu(card, self.theme_var, "Neon", "Dark", "Minimal", command=lambda _: self._emit()))
        self._row(card, "Animations", tk.Checkbutton(card, variable=self.anim_var, command=self._emit, bg=theme.panel, fg=theme.text, selectcolor=theme.panel_alt))
        self._row(card, "Sound", tk.Checkbutton(card, variable=self.sound_var, command=self._emit, bg=theme.panel, fg=theme.text, selectcolor=theme.panel_alt))

        tk.Label(card, text="AI Settings", bg=theme.panel, fg=theme.text, font=("Segoe UI", 12, "bold")).pack(anchor="w", padx=16, pady=(16, 6))
        self._row(card, "Model", tk.Entry(card, textvariable=self.model_var))
        self._row(card, "Response style", tk.OptionMenu(card, self.style_var, "concise", "detailed", command=lambda _: self._emit()))

        tk.Label(card, text="Audio", bg=theme.panel, fg=theme.text, font=("Segoe UI", 12, "bold")).pack(anchor="w", padx=16, pady=(16, 6))
        self._row(card, "Mic input", tk.Entry(card, textvariable=self.mic_var))
        self._row(card, "Voice", tk.Entry(card, textvariable=self.voice_var))
        volume = tk.Scale(card, variable=self.volume_var, from_=0.0, to=1.0, resolution=0.05, orient="horizontal", command=lambda _: self._emit(), bg=theme.panel, fg=theme.text, highlightthickness=0)
        self._row(card, "Volume", volume)

        tk.Label(card, text="Updates & Info", bg=theme.panel, fg=theme.text, font=("Segoe UI", 12, "bold")).pack(anchor="w", padx=16, pady=(16, 6))
        meta = tk.Frame(card, bg=theme.panel)
        meta.pack(fill="x", padx=16, pady=(0, 12))
        tk.Label(meta, text="Version: v0.1.0", bg=theme.panel, fg=theme.text_dim).pack(side="left")
        tk.Label(meta, text="Author: Manish", bg=theme.panel, fg=theme.text_dim).pack(side="left", padx=20)
        tk.Button(meta, text="Check for updates", command=self.on_check_updates).pack(side="right")

    def _row(self, parent: tk.Widget, label: str, widget: tk.Widget) -> None:
        row = tk.Frame(parent, bg=self.theme.panel)
        row.pack(fill="x", padx=16, pady=4)
        tk.Label(row, text=label, width=16, anchor="w", bg=self.theme.panel, fg=self.theme.text_dim).pack(side="left")
        widget.pack(side="left", fill="x", expand=True)

    def _emit(self) -> None:
        self.on_change(self.current_settings())

    def current_settings(self) -> dict:
        return {
            "theme": self.theme_var.get(),
            "animations": self.anim_var.get(),
            "sound": self.sound_var.get(),
            "response_style": self.style_var.get(),
            "model": self.model_var.get().strip(),
            "mic": self.mic_var.get().strip(),
            "voice": self.voice_var.get().strip(),
            "volume": self.volume_var.get(),
        }


class CommandCenterScreen(BaseScreen):
    def __init__(self, parent: tk.Widget, theme: Theme, on_command: callable) -> None:
        super().__init__(parent, theme)
        self.on_command = on_command
        grid = tk.Frame(self, bg=theme.bg)
        grid.pack(fill="both", expand=True, padx=20, pady=20)
        commands = [
            ("Open Chrome", "open chrome"),
            ("Open VS Code", "open vscode"),
            ("Check Weather", "weather in Mumbai"),
            ("News", "news"),
        ]
        for idx, (label, command) in enumerate(commands):
            btn = tk.Button(
                grid,
                text=label,
                command=lambda c=command: self.on_command(c),
                bg=theme.panel,
                fg=theme.text,
                activebackground=theme.accent_soft,
                relief="flat",
                padx=18,
                pady=18,
            )
            btn.grid(row=idx // 2, column=idx % 2, sticky="nsew", padx=10, pady=10)
            btn.bind("<Enter>", lambda e, b=btn: b.configure(bg=theme.accent_soft))
            btn.bind("<Leave>", lambda e, b=btn: b.configure(bg=theme.panel))
        grid.columnconfigure(0, weight=1)
        grid.columnconfigure(1, weight=1)
        grid.rowconfigure(0, weight=1)
        grid.rowconfigure(1, weight=1)
