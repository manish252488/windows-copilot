from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from jarvis.ui.theme import Theme
from jarvis.utils.lucide_icons import mic_hero_photo


def style_button(button: tk.Button, theme: Theme, *, compact: bool = False) -> None:
    button.configure(
        relief="flat",
        bd=0,
        cursor="hand2",
        bg=theme.panel_alt,
        fg=theme.text,
        activebackground=theme.card_highlight,
        activeforeground=theme.text,
        highlightthickness=1,
        highlightbackground=theme.border,
        highlightcolor=theme.accent,
        font=("Segoe UI Semibold", 10 if compact else 11),
        padx=12 if compact else 16,
        pady=7 if compact else 10,
    )


def style_primary_button(button: tk.Button, theme: Theme, *, compact: bool = True) -> None:
    button.configure(
        relief="flat",
        bd=0,
        cursor="hand2",
        bg=theme.accent_blue,
        fg="#ffffff",
        activebackground=theme.accent,
        activeforeground="#ffffff",
        font=("Segoe UI Semibold", 10 if compact else 11),
        highlightthickness=0,
        padx=16 if compact else 20,
        pady=8 if compact else 10,
    )


def style_primary_hover(button: tk.Button, theme: Theme) -> None:
    h = theme.accent

    def _in(_e: object) -> None:
        try:
            if str(button.cget("bg")) == h:
                return
        except tk.TclError:
            return
        button.configure(bg=h)

    def _out(_e: object) -> None:
        try:
            if str(button.cget("state")) == "disabled":
                return
        except tk.TclError:
            return
        button.configure(bg=theme.accent_blue)

    button.bind("<Enter>", _in)
    button.bind("<Leave>", _out)


def style_outline_mute(button: tk.Button, theme: Theme) -> None:
    button.configure(
        relief="flat",
        bd=0,
        cursor="hand2",
        bg=theme.panel,
        fg=theme.text,
        activebackground=theme.card_highlight,
        activeforeground=theme.text,
        font=("Segoe UI", 10),
        highlightthickness=1,
        highlightbackground=theme.text_dim,
        highlightcolor=theme.text,
        padx=24,
        pady=8,
    )


def add_button_hover(
    button: tk.Button, theme: Theme, base_bg: str | None = None, hover_bg: str | None = None
) -> None:
    normal = base_bg or str(button.cget("bg"))
    hov = hover_bg or theme.card_highlight
    button.bind("<Enter>", lambda _e: button.configure(bg=hov))
    button.bind("<Leave>", lambda _e: button.configure(bg=normal))


def build_input_shell(parent: tk.Widget, theme: Theme) -> tuple[tk.Frame, tk.Frame]:
    shell = tk.Frame(
        parent,
        bg=theme.border,
        bd=0,
        highlightthickness=0,
        padx=1,
        pady=1,
    )
    inner = tk.Frame(shell, bg=theme.panel_alt, bd=0)
    inner.pack(fill="both", expand=True)
    return shell, inner


def attach_placeholder(
    entry: tk.Entry,
    var: tk.StringVar,
    placeholder: str,
    theme: Theme,
) -> None:
    if not var.get().strip():
        var.set(placeholder)
        entry.configure(fg=theme.text_dim)

    def on_in(_: object) -> None:
        if var.get() == placeholder:
            var.set("")
            entry.configure(fg=theme.text)

    def on_out(_: object) -> None:
        v = var.get().strip()
        if not v:
            var.set(placeholder)
            entry.configure(fg=theme.text_dim)

    entry.bind("<FocusIn>", on_in, add="+")
    entry.bind("<FocusOut>", on_out, add="+")


def is_placeholder_value(var: tk.StringVar, placeholder: str) -> bool:
    return (var.get() or "").strip() == (placeholder or "").strip()


class BaseScreen(tk.Frame):
    def __init__(self, parent: tk.Widget, theme: Theme) -> None:
        super().__init__(parent, bg=theme.bg)
        self.theme = theme

    def apply_theme(self, theme: Theme) -> None:
        self.theme = theme
        self.configure(bg=theme.bg)


# --- Home: listening, gradient ring, bottom pill input (Figma) -----------------

HOME_INPUT_PH = "Type your message..."

# MDL2 microphone; fallback to emoji if font missing
_MIC_FONT = ("Segoe MDL2 Assets", 56)


class HomeScreen(BaseScreen):
    def __init__(
        self,
        parent: tk.Widget,
        theme: Theme,
        on_toggle_mute: object,
        on_submit_text: object,
    ) -> None:
        super().__init__(parent, theme)
        t = theme
        self._home_input_ph = HOME_INPUT_PH
        self.state_var = tk.StringVar(value="Listening")
        self.snippet_var = tk.StringVar(value="Try saying: Open Chrome")
        self.mute_btn_var = tk.StringVar(value="Mute Voice")
        self.input_var = tk.StringVar()
        self._api_hint_visible = False
        self._mic_active = False

        self._input_block = tk.Frame(self, bg=t.bg)
        self._input_block.pack(side="bottom", fill="x", padx=28, pady=24)
        shell, inner = build_input_shell(self._input_block, t)
        shell.pack(fill="x", expand=True)
        inner.configure(bg=t.panel)
        self._input_shell, self._input_inner = shell, inner
        self._input_inner.config(highlightthickness=1, highlightbackground=t.input_border)
        self.text_input = tk.Entry(
            inner,
            textvariable=self.input_var,
            bg=t.panel,
            fg=t.text,
            insertbackground=t.text,
            relief="flat",
            bd=0,
            font=("Segoe UI", 12),
        )
        self.text_input.pack(side="left", fill="x", expand=True, padx=(20, 8), pady=12, ipady=4)
        self.text_input.bind(
            "<Return>", lambda _e: self._submit_on_enter(on_submit_text)  # type: ignore
        )
        self._send_btn = tk.Button(inner, text="Send", command=lambda: self._submit_text(on_submit_text))  # type: ignore
        style_primary_button(self._send_btn, t)
        style_primary_hover(self._send_btn, t)
        self._send_btn.pack(side="right", padx=(4, 16), pady=6)
        attach_placeholder(self.text_input, self.input_var, HOME_INPUT_PH, t)

        self._center = tk.Frame(self, bg=t.bg)
        self._center.pack(side="top", fill="both", expand=True, pady=(8, 0), padx=8)

        self._mic_status = tk.Frame(self._center, bg=t.bg)
        self._mic_status.pack(pady=(0, 8))
        self._mic_dot_cv = tk.Canvas(
            self._mic_status, width=12, height=12, highlightthickness=0, bg=t.bg
        )
        self._mic_dot_cv.pack(side="left", padx=(0, 8))
        self._status_dot_oval = self._mic_dot_cv.create_oval(0, 0, 10, 10, fill=t.text_dim, outline="")
        self._mic_status_lbl = tk.Label(
            self._mic_status,
            text="Mic idle",
            font=("Segoe UI", 10),
            fg=t.text_dim,
            bg=t.bg,
        )
        self._mic_status_lbl.pack(side="left")

        self.hero_canvas = tk.Canvas(
            self._center, width=300, height=270, highlightthickness=0, bg=t.bg
        )
        self.hero_canvas.pack(pady=(0, 8))
        self._mic_hero_ph = mic_hero_photo(self, 80)
        self._hero_mic: int | None = None
        self._draw_hero()

        self.state_label = tk.Label(
            self._center,
            textvariable=self.state_var,
            font=("Segoe UI Semibold", 26),
            fg=t.text,
            bg=t.bg,
        )
        self.state_label.pack(pady=(0, 4))

        self.api_key_hint_var = tk.StringVar(
            value="Set your API key in Settings → AI Settings to enable Jarvis responses."
        )
        self.api_key_hint_label = tk.Label(
            self._center,
            textvariable=self.api_key_hint_var,
            font=("Segoe UI", 11),
            wraplength=520,
            justify=tk.CENTER,
        )
        self._style_api_key_hint(t)

        self.snippet_label = tk.Label(
            self._center,
            textvariable=self.snippet_var,
            font=("Segoe UI", 10),
            wraplength=520,
            justify=tk.CENTER,
        )
        self.snippet_label.pack(pady=(0, 16))
        self.snippet_label.configure(fg=t.text_dim, bg=t.bg)

        self._mute_btn = tk.Button(self._center, textvariable=self.mute_btn_var, command=on_toggle_mute)  # type: ignore
        style_outline_mute(self._mute_btn, t)
        add_button_hover(
            self._mute_btn, t, base_bg=t.panel, hover_bg=t.card_highlight
        )
        self._mute_btn.pack(pady=(0, 4))

    def _draw_hero(self) -> None:
        t = self.theme
        c = self.hero_canvas
        c.delete("all")
        c.configure(bg=t.bg, height=270, width=300)
        w, h = 300, 270
        cx, cy = w // 2, h // 2
        r_out, r_in = 102, 74
        c.create_oval(
            cx - r_out - 4,
            cy - r_out - 4,
            cx + r_out + 4,
            cy + r_out + 4,
            fill="",
            outline=t.accent_soft,
            width=1,
        )
        c.create_oval(
            cx - r_out,
            cy - r_out,
            cx + r_out,
            cy + r_out,
            fill="",
            outline=t.accent,
            width=14,
        )
        c.create_oval(
            cx - r_in, cy - r_in, cx + r_in, cy + r_in, fill=t.bg, outline=""
        )
        c.create_oval(
            cx - r_in + 1,
            cy - r_in + 1,
            cx + r_in - 1,
            cy + r_in - 1,
            fill=t.panel,
            outline="",
        )
        if self._mic_hero_ph is not None:
            self._hero_mic = c.create_image(cx, cy, image=self._mic_hero_ph, anchor=tk.CENTER)
        else:
            try:
                self._hero_mic = c.create_text(
                    cx, cy, text="\uE720", font=_MIC_FONT, fill="#ffffff", anchor=tk.CENTER
                )
            except tk.TclError:
                self._hero_mic = c.create_text(
                    cx, cy, text="Mic", font=("Segoe UI", 20), fill="#ffffff", anchor=tk.CENTER
                )

    def _submit_on_enter(self, on_submit: object) -> None:
        if is_placeholder_value(self.input_var, self._home_input_ph):
            return
        self._submit_text(on_submit)  # type: ignore

    def _submit_text(self, on_submit: object) -> None:
        ph = self._home_input_ph
        raw = self.input_var.get()
        if raw.strip() == ph or not raw.strip():
            return
        text = raw.strip()
        on_submit(text)  # type: ignore
        self.text_input.delete(0, tk.END)
        self.input_var.set(ph)
        self.text_input.configure(fg=self.theme.text_dim)

    def set_state(self, state: str) -> None:
        self.state_var.set(state)

    def set_snippet(self, text: str) -> None:
        self.snippet_var.set(text)

    def set_muted(self, muted: bool) -> None:
        self.mute_btn_var.set("Unmute Voice" if muted else "Mute Voice")

    def set_mic_processing(self, active: bool) -> None:
        self._mic_active = active
        t = self.theme
        if active:
            self._mic_dot_cv.itemconfig(self._status_dot_oval, fill=t.accent)
            self._mic_status_lbl.configure(text="Mic processing", fg=t.text_dim)
        else:
            self._mic_dot_cv.itemconfig(self._status_dot_oval, fill=t.text_dim)
            self._mic_status_lbl.configure(text="Mic idle", fg=t.text_dim)

    def _style_api_key_hint(self, theme: Theme) -> None:
        self.api_key_hint_label.configure(bg=theme.bg, fg=theme.hint, wraplength=520, justify=tk.CENTER)

    def set_api_key_hint(self, show: bool, text: str | None = None) -> None:
        if text is not None:
            self.api_key_hint_var.set(text)
        if show and not self._api_hint_visible:
            self.api_key_hint_label.pack(pady=(0, 6), before=self.snippet_label)
            self._api_hint_visible = True
        elif not show and self._api_hint_visible:
            self.api_key_hint_label.pack_forget()
            self._api_hint_visible = False

    def apply_theme(self, theme: Theme) -> None:
        super().apply_theme(theme)
        t = self.theme
        self._center.configure(bg=t.bg)
        self._input_block.configure(bg=t.bg)
        self._input_shell.configure(bg=t.border)
        self._input_inner.configure(bg=t.panel, highlightthickness=1, highlightbackground=t.input_border)
        self.text_input.configure(
            bg=t.panel, fg=t.text, insertbackground=t.text, disabledbackground=t.panel
        )
        if not is_placeholder_value(self.input_var, self._home_input_ph):
            self.text_input.configure(fg=t.text)
        else:
            self.text_input.configure(fg=t.text_dim)
        self._mic_status.configure(bg=t.bg)
        self._mic_dot_cv.configure(bg=t.bg)
        if self._mic_active:
            self._mic_dot_cv.itemconfig(self._status_dot_oval, fill=t.accent)
        else:
            self._mic_dot_cv.itemconfig(self._status_dot_oval, fill=t.text_dim)
        self._mic_status_lbl.configure(bg=t.bg, fg=t.text_dim)
        self._draw_hero()
        self.state_label.configure(fg=t.text, bg=t.bg)
        self._style_api_key_hint(t)
        self.snippet_label.configure(fg=t.text_dim, bg=t.bg)
        style_primary_button(self._send_btn, t, compact=True)
        style_primary_hover(self._send_btn, t)
        style_outline_mute(self._mute_btn, t)
        add_button_hover(self._mute_btn, t, base_bg=t.panel, hover_bg=t.card_highlight)


# --- Chat ---------------------------------------------------------------------

CHAT_SEARCH_PH = "Search conversations..."


class ConversationScreen(BaseScreen):
    def __init__(self, parent: tk.Widget, theme: Theme) -> None:
        super().__init__(parent, theme)
        t = self.theme
        self.messages: list[tuple[str, str]] = []
        self.last_assistant_text = ""
        self._search_ph = CHAT_SEARCH_PH

        self.top = tk.Frame(self, bg=t.bg)
        self.top.pack(fill=tk.X, padx=24, pady=(20, 12))
        self.search_var = tk.StringVar()
        self._ph_shell, self._ph_inner = build_input_shell(self.top, t)
        self._ph_inner.config(highlightthickness=1, highlightbackground=t.input_border, bg=t.panel)
        self._ph_shell.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        self.search_entry = tk.Entry(
            self._ph_inner,
            textvariable=self.search_var,
            bg=t.panel,
            fg=t.text,
            insertbackground=t.text,
            relief=tk.FLAT,
            bd=0,
            font=("Segoe UI", 11),
        )
        self.search_entry.pack(
            side=tk.LEFT, fill=tk.X, expand=True, ipady=10, padx=(20, 12), pady=2
        )
        attach_placeholder(self.search_entry, self.search_var, CHAT_SEARCH_PH, t)
        self._search_btn = tk.Button(
            self.top, text="Search", command=self.search, font=("Segoe UI Semibold", 10)
        )
        style_primary_button(self._search_btn, t, compact=True)
        style_primary_hover(self._search_btn, t)
        self._search_btn.pack(side=tk.LEFT, padx=4, ipady=2)
        self._copy_btn = tk.Button(
            self.top, text="Copy last response", command=self.copy_last_response, font=("Segoe UI", 10)
        )
        self._copy_btn.configure(
            relief=tk.FLAT,
            bd=0,
            highlightthickness=1,
            highlightbackground=t.border,
            cursor="hand2",
            padx=10,
            pady=6,
            bg=t.panel,
            fg=t.text,
        )
        add_button_hover(
            self._copy_btn, t, base_bg=t.panel, hover_bg=t.card_highlight
        )
        self._copy_btn.pack(side=tk.LEFT, padx=4)

        self._empty = tk.Label(
            self,
            text="Start a conversation with Jarvis",
            font=("Segoe UI", 12),
            fg=t.text_dim,
            bg=t.bg,
        )
        self._empty.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

        self.canvas = tk.Canvas(self, bg=t.bg, highlightthickness=0, bd=0)
        st = ttk.Style()
        st.theme_use("clam")
        st.configure(
            "Vertical.TScrollbar",
            troughcolor=t.bg,
            background=t.accent_soft,
            bordercolor=t.bg,
            arrowcolor=t.text_dim,
            darkcolor=t.accent_blue,
            lightcolor=t.accent_soft,
            width=8,
        )
        st.map("Vertical.TScrollbar", background=[("active", t.accent)])
        self.scrollbar = ttk.Scrollbar(
            self,
            orient=tk.VERTICAL,
            command=self.canvas.yview,
            style="Vertical.TScrollbar",
        )
        self.inner = tk.Frame(self.canvas, bg=t.bg)
        self.inner.bind(
            "<Configure>", lambda _e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        self._win = self.canvas.create_window((0, 0), window=self.inner, anchor=tk.NW)
        self.canvas.bind("<Configure>", self._on_c_canvas)

        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y, padx=(0, 12), pady=(0, 8))
        self.canvas.pack(
            side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(16, 0), pady=(0, 12)
        )

    def _on_c_canvas(self, e: tk.Event) -> None:
        self.canvas.itemconfig(self._win, width=e.width)

    def add_message(self, role: str, text: str, animated: bool = True) -> None:
        self.messages.append((role, text))
        if role == "assistant":
            self.last_assistant_text = text
        t = self.theme
        if len(self.messages) == 1:
            self._empty.place_forget()
        bg_b = t.user_bubble if role == "user" else t.jarvis_bubble
        anc = "e" if role == "user" else "w"
        cont = tk.Frame(self.inner, bg=t.bg)
        cont.pack(fill=tk.X, padx=20, pady=6)
        b = tk.Label(
            cont,
            text=text,
            bg=bg_b,
            fg=t.text,
            wraplength=560,
            font=("Segoe UI", 10),
            justify=tk.LEFT,
            padx=12,
            pady=8,
        )
        b.pack(anchor=anc)
        if animated:
            b.configure(fg=t.text_dim)
            self.after(120, lambda: b.configure(fg=t.text))
        self.after(30, lambda: self.canvas.yview_moveto(1.0))

    def search(self) -> None:
        if is_placeholder_value(self.search_var, self._search_ph):
            return
        q = self.search_var.get().strip().lower()
        if not q or q == self._search_ph.lower():
            return
        for role, text in reversed(self.messages):
            if q in text.lower():
                self.add_message(
                    "assistant", f"Search match ({role}): {text}", animated=False
                )
                return
        self.add_message("assistant", "No matching message found.", animated=False)

    def copy_last_response(self) -> None:
        if not self.last_assistant_text:
            return
        self.clipboard_clear()
        self.clipboard_append(self.last_assistant_text)

    def apply_theme(self, theme: Theme) -> None:
        super().apply_theme(theme)
        t = self.theme
        self.top.configure(bg=t.bg)
        self._ph_shell.configure(bg=t.border)
        self._ph_inner.configure(
            bg=t.panel, highlightthickness=1, highlightbackground=t.input_border
        )
        self.search_entry.configure(bg=t.panel, fg=t.text, insertbackground=t.text)
        if is_placeholder_value(self.search_var, self._search_ph):
            self.search_entry.configure(fg=t.text_dim)
        style_primary_button(self._search_btn, t, compact=True)
        style_primary_hover(self._search_btn, t)
        self._copy_btn.configure(
            bg=t.panel, fg=t.text, highlightbackground=t.border, activebackground=t.card_highlight
        )
        self._empty.configure(fg=t.text_dim, bg=t.bg)
        self.canvas.configure(bg=t.bg)
        self.inner.configure(bg=t.bg)
        st = ttk.Style()
        st.configure(
            "Vertical.TScrollbar",
            troughcolor=t.bg,
            background=t.accent_soft,
            bordercolor=t.bg,
            darkcolor=t.accent_blue,
            lightcolor=t.accent_soft,
        )


# --- Settings: two columns in one card (Figma palette) ------------------------


class SettingsScreen(BaseScreen):
    def __init__(
        self,
        parent: tk.Widget,
        theme: Theme,
        on_save: object,
        on_check_updates: object,
        version: str,
        mic_options: list[str],
        voice_options: list[str],
        initial: dict,
    ) -> None:
        super().__init__(parent, theme)
        t = self.theme
        self.on_save = on_save
        self.on_check_updates = on_check_updates
        self._shell_tuples: list[tuple[tk.Frame, tk.Frame]] = []
        self._comboboxes: list[ttk.Combobox] = []
        self._scales: list[tk.Scale] = []
        self._cbox_style_name: str = ""
        self._card: tk.Frame | None = None

        init = initial
        th = init.get("theme", "Neon")
        if th not in ("Neon", "Dark", "Minimal"):
            th = "Neon"
        self.theme_var = tk.StringVar(value=th)
        self.anim_var = tk.BooleanVar(value=init.get("animations", True))
        self.sound_var = tk.BooleanVar(value=init.get("sound", True))
        self.style_var = tk.StringVar(value=init.get("response_style", "concise"))
        self.model_var = tk.StringVar(value=init.get("model", "gpt-4.1-mini"))
        self.api_key_var = tk.StringVar(value=init.get("openai_api_key", "") or "")
        self.wake_word_var = tk.StringVar(value=(init.get("wake_word") or "jarvis") or "jarvis")
        mic0 = init.get("mic", "Default") or "Default"
        if mic0 not in (mic_options or ["Default"]):
            mic0 = mic_options[0] if mic_options else "Default"
        self.mic_var = tk.StringVar(value=mic0)
        v0 = init.get("voice", "Default") or "Default"
        if v0 not in (voice_options or ["Default"]):
            v0 = voice_options[0] if voice_options else "Default"
        self.voice_var = tk.StringVar(value=v0)
        vvol = float(init.get("volume", 1.0) or 1.0)
        self.volume_var = tk.DoubleVar(value=vvol)
        self._vol_pct = tk.StringVar(value=f"{int(vvol * 100)}%")
        self._v_label: tk.Label | None = None

        self._card = tk.Frame(
            self,
            bg=t.panel,
            bd=0,
            highlightthickness=1,
            highlightbackground=t.border,
        )
        self._card.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        card = self._card
        card.columnconfigure(0, weight=1)
        card.columnconfigure(1, weight=1)

        left = tk.Frame(card, bg=t.panel)
        right = tk.Frame(card, bg=t.panel)
        left.grid(row=0, column=0, sticky=tk.NSEW, padx=(16, 10), pady=16)
        right.grid(row=0, column=1, sticky=tk.NSEW, padx=(10, 16), pady=16)
        left.columnconfigure(1, weight=1)
        right.columnconfigure(1, weight=1)

        self._section_title(left, "General", 0)
        self._grid_row(
            left,
            1,
            "Theme",
            self._styled_combobox(left, self.theme_var, ["Neon", "Dark", "Minimal"]),
        )
        wake_shell, wake_inner = self._make_shell(left)
        wake_word_entry = tk.Entry(
            wake_inner,
            textvariable=self.wake_word_var,
            bg=t.panel_alt,
            fg=t.text,
            insertbackground=t.text,
            relief=tk.FLAT,
            bd=0,
            font=("Segoe UI", 11),
        )
        wake_word_entry.pack(fill=tk.X, expand=True, padx=8, pady=8, ipady=2)
        self._grid_row(left, 2, "Wake word", wake_shell)
        self._grid_row(left, 3, "Animations", self._styled_check(left, self.anim_var))
        self._grid_row(left, 4, "Sound", self._styled_check(left, self.sound_var))
        self._section_title(left, "AI Settings", 5, pady=(20, 6))
        self._grid_row(
            left,
            6,
            "Model",
            self._styled_combobox(
                left, self.model_var, ["gpt-4.1-mini", "gpt-4.1", "gpt-4o-mini"]
            ),
        )
        api_shell, api_inner = self._make_shell(left)
        api_entry = tk.Entry(
            api_inner,
            textvariable=self.api_key_var,
            bg=t.panel_alt,
            fg=t.text,
            insertbackground=t.text,
            show="*",
            font=("Segoe UI", 11),
        )
        api_entry.pack(fill=tk.X, expand=True, padx=8, pady=8, ipady=2)
        self._grid_row(left, 7, "OpenAI API key", api_shell)
        self._grid_row(
            left,
            8,
            "Response style",
            self._styled_combobox(left, self.style_var, ["concise", "detailed"]),
        )

        self._section_title(right, "Audio", 0)
        self._grid_row(
            right,
            1,
            "Mic input",
            self._styled_combobox(right, self.mic_var, (mic_options or ["Default"])),
        )
        self._grid_row(
            right,
            2,
            "Voice",
            self._styled_combobox(right, self.voice_var, (voice_options or ["Default"])),
        )
        v_all = tk.Frame(right, bg=t.panel)
        tbar = tk.Frame(v_all, bg=t.panel)
        tbar.pack(fill=tk.X, pady=(0, 2))
        self._v_label = tk.Label(
            tbar,
            textvariable=self._vol_pct,
            font=("Segoe UI", 10),
            bg=t.panel,
            fg=t.accent_blue,
        )
        self._v_label.pack(side=tk.RIGHT)
        vol = tk.Scale(
            v_all,
            variable=self.volume_var,
            from_=0.0,
            to=1.0,
            resolution=0.05,
            orient=tk.HORIZONTAL,
            command=self._on_volume,
            bg=t.panel,
            fg=t.text,
            troughcolor=t.bg,
            activebackground=t.accent_blue,
            highlightthickness=0,
            length=200,
            font=("Segoe UI", 10),
        )
        self._scales.append(vol)
        vol.pack(fill=tk.X, expand=True, pady=(0, 2))
        self._grid_row(right, 3, "Volume", v_all)

        self._section_title(right, "Updates & Info", 4, pady=(20, 6))
        info = tk.Frame(right, bg=t.panel_alt, highlightthickness=1, highlightbackground=t.border)
        info.grid(row=5, column=0, columnspan=2, sticky=tk.EW, pady=(2, 0))
        tk.Label(info, text=f"Version: v{version}", bg=t.panel_alt, fg=t.text_dim, font=("Segoe UI", 10)).pack(anchor=tk.W, padx=10, pady=(8, 2))
        tk.Label(info, text="Author: Manish", bg=t.panel_alt, fg=t.text_dim, font=("Segoe UI", 10)).pack(anchor=tk.W, padx=10, pady=(0, 8))
        u_btn = tk.Button(info, text="Check for updates", command=self.on_check_updates)  # type: ignore[assignment]
        style_primary_button(u_btn, t, compact=True)
        style_primary_hover(u_btn, t)
        u_btn.pack(anchor=tk.E, padx=10, pady=(0, 10))

        save_row = tk.Frame(card, bg=t.panel)
        save_row.grid(row=1, column=0, columnspan=2, sticky=tk.EW, padx=20, pady=(0, 20))
        tk.Label(
            save_row,
            text="Click Save to store settings on this device.",
            bg=t.panel,
            fg=t.text_dim,
            font=("Segoe UI", 10),
        ).pack(side=tk.LEFT, pady=4, padx=(0, 12))
        s_btn = tk.Button(save_row, text="Save", command=lambda: self.on_save(self.current_settings()))  # type: ignore[assignment]
        style_primary_button(s_btn, t, compact=True)
        style_primary_hover(s_btn, t)
        s_btn.pack(side=tk.RIGHT, pady=2)

        self._ensure_cbox_style()

    def _on_volume(self, _v: str) -> None:
        self._vol_pct.set(f"{int(float(self.volume_var.get()) * 100)}%")

    def _section_title(
        self, parent: tk.Widget, title: str, row: int, pady: tuple[int, int] = (0, 6)
    ) -> None:
        tk.Label(
            parent,
            text=title,
            bg=self.theme.panel,
            fg=self.theme.text,
            font=("Segoe UI Semibold", 14),
        ).grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=pady)

    def _grid_row(
        self,
        parent: tk.Widget,
        row: int,
        label: str,
        widget: tk.Widget,
    ) -> None:
        tk.Label(
            parent,
            text=label,
            bg=self.theme.panel,
            fg=self.theme.text_dim,
            width=12,
            font=("Segoe UI", 10),
        ).grid(row=row, column=0, sticky=tk.NW, pady=6, padx=(0, 6))
        widget.grid(row=row, column=1, sticky=tk.EW, pady=6, ipady=2)

    def _make_shell(self, parent: tk.Widget) -> tuple[tk.Frame, tk.Frame]:
        shell, inner = build_input_shell(parent, self.theme)
        self._shell_tuples.append((shell, inner))
        return shell, inner

    def _ensure_cbox_style(self) -> None:
        if not self._cbox_style_name:
            self._cbox_style_name = f"Jarvis.{id(self)}.TCombobox"
        t = self.theme
        s = ttk.Style()
        s.theme_use("clam")
        s.configure(
            self._cbox_style_name,
            fieldbackground=t.panel_alt,
            background=t.panel_alt,
            foreground=t.text,
            bordercolor=t.border,
            darkcolor=t.panel_alt,
            lightcolor=t.panel_alt,
            arrowcolor=t.text,
            borderwidth=0,
            padding=8,
            font=("Segoe UI", 11),
        )
        s.map(
            self._cbox_style_name,
            fieldbackground=[("readonly", t.panel_alt)],
            selectbackground=[("readonly", t.panel_alt)],
            selectforeground=[("readonly", t.text)],
            arrowcolor=[("active", t.accent_blue)],
        )

    def _styled_combobox(
        self, parent: tk.Widget, variable: tk.StringVar, options: list[str] | tuple[str, ...]
    ) -> tk.Widget:
        if not self._cbox_style_name:
            self._cbox_style_name = f"Jarvis.{id(self)}.TCombobox"
        self._ensure_cbox_style()
        shell, inner = self._make_shell(parent)
        olist = list(options)
        widget = ttk.Combobox(
            inner,
            textvariable=variable,
            values=olist,
            state="readonly",
            style=self._cbox_style_name,
            font=("Segoe UI", 11),
        )
        widget.pack(fill=tk.X, expand=True, padx=4, pady=4)
        self._comboboxes.append(widget)
        if variable.get() not in olist and olist:
            variable.set(olist[0])
        return shell

    def _styled_check(self, parent: tk.Widget, variable: tk.BooleanVar) -> tk.Checkbutton:
        return tk.Checkbutton(
            parent,
            variable=variable,
            bg=self.theme.panel,
            activebackground=self.theme.panel,
            fg=self.theme.text,
            selectcolor=self.theme.panel_alt,
            highlightthickness=0,
            activeforeground=self.theme.text,
            cursor="hand2",
        )

    def apply_theme(self, theme: Theme) -> None:
        super().apply_theme(theme)
        t = self.theme
        if self._card is not None:
            self._card.configure(bg=t.panel, highlightbackground=t.border)
        for sh, inner in self._shell_tuples:
            sh.configure(bg=t.border)
            inner.configure(bg=t.panel_alt)
        for scale in self._scales:
            try:
                scale.configure(
                    bg=t.panel,
                    fg=t.text,
                    troughcolor=t.bg,
                    activebackground=t.accent_blue,
                )
            except tk.TclError:
                pass
        if self._v_label is not None:
            self._v_label.configure(fg=t.accent_blue, bg=t.panel)
        self._ensure_cbox_style()
        for cbox in self._comboboxes:
            cbox.update_idletasks()

    def current_settings(self) -> dict:
        return {
            "theme": self.theme_var.get(),
            "openai_api_key": self.api_key_var.get().strip(),
            "wake_word": self.wake_word_var.get().strip() or "jarvis",
            "animations": self.anim_var.get(),
            "sound": self.sound_var.get(),
            "response_style": self.style_var.get(),
            "model": self.model_var.get().strip(),
            "mic": self.mic_var.get().strip(),
            "voice": self.voice_var.get().strip(),
            "volume": self.volume_var.get(),
        }


# --- Command center: gradient-style tiles + title -----------------------------


class CommandCenterScreen(BaseScreen):
    def __init__(self, parent: tk.Widget, theme: Theme, on_command: object) -> None:
        super().__init__(parent, theme)
        self._on_cmd = on_command
        t = self.theme
        self._tile_frames: list[tk.Frame] = []

        self._wrap = tk.Frame(self, bg=t.bg)
        self._wrap.pack(fill=tk.BOTH, expand=True, padx=24, pady=20)
        self._grid = tk.Frame(self._wrap, bg=t.bg)
        for c in (0, 1):
            self._grid.columnconfigure(c, weight=1)
        for r in (0, 1):
            self._grid.rowconfigure(r, weight=1)

        self._hdr = tk.Label(
            self._wrap,
            text="Quick Actions",
            font=("Segoe UI Semibold", 22),
            bg=t.bg,
            fg=t.text,
            anchor=tk.W,
        )
        self._hdr.pack(fill=tk.X, pady=(0, 12))
        self._grid.pack(fill=tk.BOTH, expand=True)

        tiles: list[tuple[str, str, str]] = [
            ("Open Chrome", "open chrome", "#2d1f4a"),
            ("Open VS Code", "open vscode", "#153040"),
            ("Check Weather", "weather in Mumbai", "#1a2d55"),
            ("News", "news", "#3a1a35"),
        ]
        icons: list[str] = ["\uE774", "\uE943", "\uE753", "\U0001f4f0"]
        f_md = ("Segoe MDL2 Assets", 40)
        for idx, (label, cmd, bg1) in enumerate(tiles):
            ico = icons[idx]
            c = tk.Frame(
                self._grid,
                bg=bg1,
                highlightthickness=1,
                highlightbackground=t.border,
            )
            c.grid(row=idx // 2, column=idx % 2, sticky=tk.NSEW, padx=10, pady=10, ipady=12, ipadx=4)
            self._tile_frames.append(c)
            try:
                ico_l = tk.Label(c, text=ico, font=f_md, bg=bg1, fg="#e6edff", cursor="hand2")
            except tk.TclError:
                ico_l = tk.Label(
                    c, text="\u25cf", font=("Segoe UI", 32), bg=bg1, fg="#e6edff", cursor="hand2"
                )
            ico_l.pack(pady=(12, 4))
            tk.Label(
                c, text=label, font=("Segoe UI Semibold", 12), bg=bg1, fg="#ffffff", cursor="hand2"
            ).pack(pady=(0, 12))

            c.bind("<Button-1>", lambda _e, cmd=cmd: self._on_cmd(cmd))  # type: ignore[union-attr]
            for w in c.winfo_children():
                w.bind(
                    "<Button-1>", lambda _e, cmd=cmd: self._on_cmd(cmd)  # type: ignore[union-attr]
                )

    def apply_theme(self, theme: Theme) -> None:
        super().apply_theme(theme)
        t = self.theme
        self._wrap.configure(bg=t.bg)
        self._grid.configure(bg=t.bg)
        self._hdr.configure(bg=t.bg, fg=t.text)
        for fr in self._tile_frames:
            fr.configure(highlightbackground=t.border)
