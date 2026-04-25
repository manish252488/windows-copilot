from __future__ import annotations

import math
import tkinter as tk
from typing import Any
try:
    from ttkbootstrap import ttk
except Exception:  # pragma: no cover - optional UI dependency fallback
    from tkinter import ttk

from PIL import Image, ImageDraw, ImageTk

from jarvis.ui.rounded_button import (
    install_rounded_panel_outline,
    install_rounded_primary_button,
    refresh_rounded_button,
)
from jarvis.ui.theme import Theme
from jarvis.utils.lucide_icons import mic_hero_photo


def _hex_to_rgb(s: str) -> tuple[int, int, int]:
    h = s.lstrip("#")
    if len(h) != 6:
        return 0, 0, 0
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def _lerp_color_hex(ha: str, hb: str, t: float) -> str:
    t = min(1, max(0, t))
    a = _hex_to_rgb(ha)
    b_ = _hex_to_rgb(hb)
    r = int(a[0] + (b_[0] - a[0]) * t)
    g = int(a[1] + (b_[1] - a[1]) * t)
    b = int(a[2] + (b_[2] - a[2]) * t)
    return f"#{r:02x}{g:02x}{b:02x}"


# Default inner padding for all `tk.Button` widgets (left/right, top/bottom)
BUTTON_PADX = 10
BUTTON_PADY = 8

# Command center quick-action tiles: compact cards with ~20px corner radius (web-style)
QUICK_TILE_W = 148
QUICK_TILE_H = 82
QUICK_TILE_CORNER = 20


def _quick_tile_pil(
    w: int,
    h: int,
    fill_hex: str,
    border_hex: str,
    corner: int = QUICK_TILE_CORNER,
) -> Any:
    r = min(max(0, corner), w // 2 - 1, h // 2 - 1)
    fr, fg, fb = _hex_to_rgb(fill_hex)
    o_r, o_g, o_b = _hex_to_rgb(border_hex)
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    dr = ImageDraw.Draw(img)
    dr.rounded_rectangle(
        (0, 0, w - 1, h - 1),
        radius=r,
        fill=(fr, fg, fb, 255),
        outline=(o_r, o_g, o_b, 255),
        width=1,
    )
    return img


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
        padx=BUTTON_PADX,
        pady=BUTTON_PADY,
    )


def style_primary_button(
    button: tk.Button,
    theme: Theme,
    *,
    compact: bool = True,
    padx: int | None = None,
    pady: int | None = None,
    font_size: int | None = None,
) -> None:
    px = padx if padx is not None else BUTTON_PADX
    py = pady if pady is not None else BUTTON_PADY
    fs = font_size if font_size is not None else (10 if compact else 11)
    button.configure(
        relief="flat",
        bd=0,
        cursor="hand2",
        bg=theme.accent_blue,
        fg="#ffffff",
        activebackground=theme.accent,
        activeforeground="#ffffff",
        font=("Segoe UI Semibold", fs),
        highlightthickness=0,
        padx=px,
        pady=py,
    )


def style_primary_hover(_button: tk.Button, _theme: Theme) -> None:
    """Replaced by install_rounded_primary_button (PIL, ≥15px radius)."""


def style_chat_copy_button(button: tk.Button, theme: Theme) -> None:
    """Secondary pill; same default padding as other buttons (see BUTTON_PADX / BUTTON_PADY)."""
    button.configure(
        relief=tk.FLAT,
        bd=0,
        cursor="hand2",
        bg=theme.panel,
        fg=theme.text,
        font=("Segoe UI Semibold", 9),
        highlightthickness=0,
        padx=BUTTON_PADX,
        pady=BUTTON_PADY,
        activebackground=theme.card_highlight,
        activeforeground=theme.text,
    )


def add_button_hover(
    _button: tk.Button, _theme: Theme, base_bg: str | None = None, hover_bg: str | None = None
) -> None:
    """Replaced by install_rounded_panel_outline; hover is drawn in rounded_button."""


def build_input_shell(parent: tk.Widget, theme: Theme) -> tuple[tk.Frame, tk.Frame]:
    shell = tk.Frame(
        parent,
        bg=theme.panel_alt,
        bd=0,
        highlightthickness=0,
        padx=0,
        pady=0,
    )
    inner = tk.Frame(shell, bg=theme.panel_alt, bd=0)
    inner.pack(fill="both", expand=True)
    return shell, inner


def style_seamless_entry(entry: tk.Entry, theme: Theme, *, bg: str) -> None:
    entry.configure(
        bg=bg,
        fg=theme.text,
        insertbackground=theme.text,
        relief=tk.FLAT,
        bd=0,
        borderwidth=0,
        highlightthickness=0,
        highlightbackground=bg,
        highlightcolor=bg,
        selectborderwidth=0,
        selectbackground=theme.accent_soft,
        selectforeground=theme.text,
    )


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
    SEND_BTN_SIZE = (142, 44)
    SEND_BTN_CORNER = 35
    SNIPPET_MAX_LINES = 4
    SNIPPET_CHARS_PER_LINE = 56
    SNIPPET_ANIM_MS = 110

    def __init__(
        self,
        parent: tk.Widget,
        theme: Theme,
        on_toggle_mic: object,
        on_submit_text: object,
    ) -> None:
        super().__init__(parent, theme)
        t = theme
        self._home_input_ph = HOME_INPUT_PH
        self.state_var = tk.StringVar(value="Say 'jarvis' to activate")
        self.snippet_var = tk.StringVar(value="Try saying: Open Chrome")
        self.input_var = tk.StringVar()
        self._on_toggle_mic = on_toggle_mic
        self._api_hint_visible = False
        self._mic_active = False
        # "ok" | "err" | "paused" — starts paused until speech thread finishes calibration
        self._mic_health: str = "paused"
        self._mic_glow_phase: float = 0.0
        self._mic_glow_after: str | None = None
        self._hero_glow_id: int | None = None

        self._input_pill_h = 56
        self._input_win_id: int | None = None
        self._input_pill_ph: object | None = None
        self._input_focus = False
        self._send_pressed = False
        self._send_hover_t = 0.0
        self._send_hover_after: str | None = None
        self._snippet_lines: list[str] = []
        self._snippet_queue: list[str] = []
        self._snippet_anim_after: str | None = None

        self._input_block = tk.Frame(self, bg=t.bg)
        self._input_block.pack(side="bottom", fill="x", padx=28, pady=24)
        self._input_canvas = tk.Canvas(
            self._input_block,
            height=self._input_pill_h,
            highlightthickness=0,
            bd=0,
            bg=t.bg,
        )
        self._input_canvas.pack(fill=tk.X, expand=True)
        self._input_inner = tk.Frame(
            self._input_canvas, bg=t.panel, bd=0, highlightthickness=0
        )
        self._input_icon = tk.Label(
            self._input_inner,
            text="\u263A",
            font=("Segoe UI Symbol", 11),
            fg=t.text_dim,
            bg=t.panel,
        )
        self._input_icon.pack(side="left", padx=(14, 8), pady=0)
        self.text_input = tk.Entry(
            self._input_inner, textvariable=self.input_var, font=("Segoe UI", 12)
        )
        style_seamless_entry(self.text_input, t, bg=t.panel)
        self.text_input.pack(side="left", fill="both", expand=True, padx=(0, 8), pady=6, ipady=2)
        self.text_input.bind(
            "<Return>", lambda _e: self._submit_on_enter(on_submit_text)  # type: ignore
        )
        self.text_input.bind("<FocusIn>", self._on_input_focus_in)
        self.text_input.bind("<FocusOut>", self._on_input_focus_out)
        self._send_btn = tk.Button(
            self._input_inner,
            text="Send  \u27A4",
            command=lambda: self._submit_text(on_submit_text),  # type: ignore
        )
        self._style_send_button_base()
        self._send_btn.pack(side="right", padx=(0, 6), pady=6, fill=tk.Y)
        self._send_btn.bind("<Enter>", self._on_send_enter)
        self._send_btn.bind("<Leave>", self._on_send_leave)
        self._send_btn.bind("<ButtonPress-1>", self._on_send_press)
        self._send_btn.bind("<ButtonRelease-1>", self._on_send_release)
        self._refresh_send_button_style()
        attach_placeholder(self.text_input, self.input_var, HOME_INPUT_PH, t)
        self._input_canvas.bind("<Configure>", self._on_home_input_configure)
        self.after_idle(self._redraw_home_input_pill)

        self._center = tk.Frame(self, bg=t.bg)
        self._center.pack(side="top", fill="both", expand=True, pady=(12, 0), padx=8)
        self._top_spacer = tk.Frame(self._center, bg=t.bg)
        self._top_spacer.pack(fill=tk.BOTH, expand=True)
        self._stack = tk.Frame(self._center, bg=t.bg)
        self._stack.pack(fill=tk.X)
        self._bottom_spacer = tk.Frame(self._center, bg=t.bg)
        self._bottom_spacer.pack(fill=tk.BOTH, expand=True)

        self._mic_status = tk.Frame(self._stack, bg=t.bg)
        self._mic_status.pack(pady=(28, 14))
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
            self._stack, width=300, height=270, highlightthickness=0, bg=t.bg, cursor="hand2"
        )
        self.hero_canvas.pack(pady=(0, 16))
        self.hero_canvas.bind("<Button-1>", self._on_hero_click)
        self._mic_hero_ph = mic_hero_photo(self, 80)
        self._hero_mic: int | None = None
        self._draw_hero()

        self.state_label = tk.Label(
            self._stack,
            textvariable=self.state_var,
            font=("Segoe UI Semibold", 27),
            fg=t.text,
            bg=t.bg,
        )
        self.state_label.pack(pady=(0, 10))

        self.api_key_hint_var = tk.StringVar(
            value="Set your API key in Settings → AI Settings to enable Jarvis responses."
        )
        self.api_key_hint_label = tk.Label(
            self._stack,
            textvariable=self.api_key_hint_var,
            font=("Segoe UI", 11),
            wraplength=520,
            justify=tk.CENTER,
        )
        self._style_api_key_hint(t)

        self.snippet_label = tk.Label(
            self._stack,
            textvariable=self.snippet_var,
            font=("Segoe UI", 11),
            wraplength=520,
            justify=tk.CENTER,
            height=self.SNIPPET_MAX_LINES,
            anchor="n",
        )
        self.snippet_label.pack(pady=(0, 22))
        self.snippet_label.configure(
            fg=_lerp_color_hex(t.text_dim, t.bg, 0.18),
            bg=t.bg,
        )

        self.after(0, self._install_rounded_home_buttons)
        self.set_snippet("Try saying: Open Chrome")

    def _install_rounded_home_buttons(self) -> None:
        t = self.theme
        install_rounded_primary_button(self._send_btn, t)
        self._apply_send_button_rounding()
        refresh_rounded_button(self._send_btn, t)

    def _style_send_button_base(self) -> None:
        self._send_btn.configure(
            relief="flat",
            bd=0,
            highlightthickness=0,
            padx=40,
            pady=20,
            font=("Segoe UI Semibold", 11),
            width=100,
            height=8,
        )

    def _apply_send_button_rounding(self) -> None:
        self._send_btn._round_size_lock = self.SEND_BTN_SIZE  # type: ignore[attr-defined]
        self._send_btn._round_corner_override = self.SEND_BTN_CORNER  # type: ignore[attr-defined]

    def _on_home_input_configure(self, _e: object) -> None:
        self._redraw_home_input_pill()

    def _on_input_focus_in(self, _e: object) -> None:
        self._input_focus = True
        self._redraw_home_input_pill()

    def _on_input_focus_out(self, _e: object) -> None:
        self._input_focus = False
        self._redraw_home_input_pill()

    def _on_send_enter(self, _e: object) -> None:
        self._animate_send_hover(1.0)

    def _on_send_leave(self, _e: object) -> None:
        self._send_pressed = False
        self._animate_send_hover(0.0)

    def _on_send_press(self, _e: object) -> None:
        self._send_pressed = True
        self._refresh_send_button_style()

    def _on_send_release(self, _e: object) -> None:
        self._send_pressed = False
        self._refresh_send_button_style()

    def _on_hero_click(self, _e: object) -> None:
        self._on_toggle_mic()  # type: ignore[misc, operator]

    def _animate_send_hover(self, target: float) -> None:
        if self._send_hover_after is not None:
            try:
                self.after_cancel(self._send_hover_after)  # type: ignore[arg-type]
            except (tk.TclError, ValueError):
                pass
            self._send_hover_after = None

        def tick() -> None:
            cur = self._send_hover_t
            if abs(cur - target) < 0.03:
                self._send_hover_t = target
                self._refresh_send_button_style()
                return
            self._send_hover_t = cur + (target - cur) * 0.35
            self._refresh_send_button_style()
            self._send_hover_after = self.after(16, tick)

        tick()

    def _refresh_send_button_style(self) -> None:
        t = self.theme
        self._style_send_button_base()
        self._apply_send_button_rounding()
        base = t.accent_blue
        hover = _lerp_color_hex(t.accent_blue, t.accent, 0.22)
        active = _lerp_color_hex(t.accent_blue, "#000000", 0.22)
        col = _lerp_color_hex(base, hover, self._send_hover_t)
        if self._send_pressed:
            col = active
        self._send_btn.configure(
            bg=col,
            fg="#ffffff",
            activebackground=col,
            activeforeground="#ffffff",
            relief="flat",
            bd=0,
            highlightthickness=0,
        )
        refresh_rounded_button(self._send_btn, t)

    def _redraw_home_input_pill(self) -> None:
        c = self._input_canvas
        t = self.theme
        c.update_idletasks()
        w = c.winfo_width()
        h = self._input_pill_h
        if w < 4:
            self.after(32, self._redraw_home_input_pill)
            return
        r = min(h // 2, 25)
        pr, pg, pb = _hex_to_rgb(t.panel)
        img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        dr = ImageDraw.Draw(img)
        # Single unified surface so input background matches container exactly.
        dr.rounded_rectangle(
            (0, 0, w - 1, h - 1),
            radius=r,
            fill=(pr, pg, pb, 255),
            outline=(0, 0, 0, 0),
            width=0,
        )
        if self._input_focus:
            g_r, g_g, g_b = _hex_to_rgb(t.accent_blue)
            dr.rounded_rectangle(
                (0, 0, w - 1, h - 1),
                radius=r,
                fill=(0, 0, 0, 0),
                outline=(g_r, g_g, g_b, 120),
                width=1,
            )
        self._input_pill_ph = ImageTk.PhotoImage(img, master=self)  # type: ignore[assignment]
        c.delete("pill")
        c.create_image(0, 0, image=self._input_pill_ph, anchor=tk.NW, tags=("pill",))
        c.configure(bg=t.bg, height=h)
        ix, iy = 8, 8
        i_w, i_h = w - 2 * ix, h - 2 * iy
        if i_w < 20 or i_h < 8:
            return
        if self._input_win_id is None:
            self._input_win_id = c.create_window(
                ix, iy, window=self._input_inner, anchor=tk.NW, width=i_w, height=i_h
            )
        else:
            c.coords(self._input_win_id, ix, iy)  # type: ignore[call-overload]
            c.itemconfig(self._input_win_id, width=i_w, height=i_h)  # type: ignore[call-overload]

    def _draw_hero(self) -> None:
        t = self.theme
        c = self.hero_canvas
        if self._mic_glow_after is not None:
            try:
                self.after_cancel(self._mic_glow_after)  # type: ignore[union-attr, arg-type]
            except (tk.TclError, ValueError):
                pass
            self._mic_glow_after = None
        self._hero_glow_id = None
        c.delete("all")
        c.configure(bg=t.bg, height=270, width=300)
        w, h = 300, 270
        cx, cy = w // 2, h // 2
        r_out, r_in = 102, 74
        # Outermost: animated health halo (drawn first = behind the rest)
        g0 = r_out + 8
        self._hero_glow_id = c.create_oval(
            cx - g0, cy - g0, cx + g0, cy + g0, fill="", outline=t.accent_soft, width=1
        )
        # Smooth multi-ring gradient for premium futuristic look.
        grad_steps = 5
        for i in range(grad_steps):
            p = i / max(grad_steps - 1, 1)
            rr = r_out - i * 2
            col = _lerp_color_hex(t.accent_soft, t.accent, 0.2 + 0.75 * p)
            c.create_oval(
                cx - rr,
                cy - rr,
                cx + rr,
                cy + rr,
                fill="",
                outline=col,
                width=max(1, 5 - i),
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
        self._apply_hero_glow()
        if self._mic_health == "ok":
            self._start_mic_glow_polling()

    def _start_mic_glow_polling(self) -> None:
        if self._mic_glow_after is not None:
            return
        if self._hero_glow_id is None:
            return
        self._mic_glow_after = self.after(50, self._on_mic_glow_tick)

    def _on_mic_glow_tick(self) -> None:
        self._mic_glow_after = None
        try:
            if not self.winfo_exists():
                return
        except tk.TclError:
            return
        if self._hero_glow_id is None:
            return
        self._apply_hero_glow()
        health = self._mic_health
        dphase: float
        if health == "ok":
            dphase = 0.3 if self._mic_active else 0.08
        else:
            dphase = 0.0
        if dphase > 0:
            self._mic_glow_phase = (self._mic_glow_phase + dphase) % (2 * math.pi)
        if health == "ok":
            self._mic_glow_after = self.after(50, self._on_mic_glow_tick)

    def _apply_hero_glow(self) -> None:
        if self._hero_glow_id is None:
            return
        t = self.theme
        c = self.hero_canvas
        w, h = 300, 270
        cx, cy = w // 2, h // 2
        r_out = 102
        p = 0.5 + 0.5 * math.sin(self._mic_glow_phase)
        hlt = self._mic_health
        try:
            if hlt == "err":
                r_h = r_out + 10
                c.coords(self._hero_glow_id, cx - r_h, cy - r_h, cx + r_h, cy + r_h)
                c.itemconfig(
                    self._hero_glow_id, outline="#c24a4a", width=3, fill=""
                )  # type: ignore[call-overload, union-attr]
            elif hlt == "paused":
                r_h = r_out + 6
                c.coords(self._hero_glow_id, cx - r_h, cy - r_h, cx + r_h, cy + r_h)
                c.itemconfig(  # type: ignore[call-overload, union-attr]
                    self._hero_glow_id, outline=t.text_dim, width=1, fill=""
                )
            elif hlt == "ok" and self._mic_active:
                # Open mic / capturing: bright fast pulse
                r_radius = r_out + 4 + 10 * p
                w_line = max(2, int(2 + 5 * p))
                o = _lerp_color_hex(t.accent_soft, t.accent, 0.25 + 0.55 * p)
                c.coords(  # type: ignore[call-overload, union-attr]
                    self._hero_glow_id, cx - r_radius, cy - r_radius, cx + r_radius, cy + r_radius
                )
                c.itemconfig(  # type: ignore[call-overload, union-attr]
                    self._hero_glow_id, outline=o, width=w_line, fill=""
                )
            else:
                # hlt == "ok" and not capturing: slow breathing
                p2 = p
                r_radius = r_out + 3 + 4 * p2
                w_line = max(1, int(1 + 2 * p2))
                o = _lerp_color_hex(t.accent_soft, t.accent, 0.08 + 0.2 * p2)
                c.coords(  # type: ignore[call-overload, union-attr]
                    self._hero_glow_id, cx - r_radius, cy - r_radius, cx + r_radius, cy + r_radius
                )
                c.itemconfig(  # type: ignore[call-overload, union-attr]
                    self._hero_glow_id, outline=o, width=w_line, fill=""
                )
        except tk.TclError:
            return

    def set_mic_health(self, health: str) -> None:
        h = (health or "").lower().strip()
        if h in ("ok", "err", "paused"):
            self._mic_health = h
        if h in ("err", "paused"):
            if self._mic_glow_after is not None:
                try:
                    self.after_cancel(self._mic_glow_after)  # type: ignore[union-attr, arg-type]
                except (tk.TclError, ValueError):
                    pass
                self._mic_glow_after = None
        self._apply_hero_glow()
        if h == "ok":
            self._start_mic_glow_polling()

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
        s = state.strip()
        if s in ("Listening", "Listening (hotkey active)"):
            s = "Say 'jarvis' to activate"
        self.state_var.set(s)

    def set_snippet(self, text: str) -> None:
        clean = (text or "").strip()
        if not clean:
            return
        self._snippet_queue.extend(self._chunk_snippet_text(clean))
        self._run_snippet_animation()

    def _chunk_snippet_text(self, text: str) -> list[str]:
        words = text.split()
        if not words:
            return []
        chunks: list[str] = []
        cur = ""
        limit = self.SNIPPET_CHARS_PER_LINE
        for word in words:
            candidate = word if not cur else f"{cur} {word}"
            if len(candidate) <= limit:
                cur = candidate
            else:
                if cur:
                    chunks.append(cur)
                if len(word) <= limit:
                    cur = word
                else:
                    chunks.append(word[:limit])
                    cur = word[limit:]
        if cur:
            chunks.append(cur)
        return chunks

    def _run_snippet_animation(self) -> None:
        if self._snippet_anim_after is not None:
            return

        def tick() -> None:
            if not self._snippet_queue:
                self._snippet_anim_after = None
                return
            nxt = self._snippet_queue.pop(0)
            self._snippet_lines.append(nxt)
            self._snippet_lines = self._snippet_lines[-self.SNIPPET_MAX_LINES :]
            self.snippet_var.set("\n".join(self._snippet_lines))
            self._snippet_anim_after = self.after(self.SNIPPET_ANIM_MS, tick)

        tick()

    def set_listening_enabled(self, enabled: bool) -> None:
        t = self.theme
        if enabled:
            self._mic_status_lbl.configure(text="Mic On (tap icon to turn off)", fg=t.text_dim)
        else:
            self._mic_status_lbl.configure(text="Mic Off (tap icon to turn on)", fg=t.text_dim)

    def set_mic_processing(self, active: bool) -> None:
        self._mic_active = active
        t = self.theme
        if active:
            self._mic_dot_cv.itemconfig(self._status_dot_oval, fill=t.accent)
            self._mic_status_lbl.configure(text="Mic processing", fg=t.text_dim)
        else:
            self._mic_dot_cv.itemconfig(self._status_dot_oval, fill=t.text_dim)
            self._mic_status_lbl.configure(text="Mic idle", fg=t.text_dim)
        self._apply_hero_glow()
        if self._mic_health == "ok" and self._mic_glow_after is None and self._hero_glow_id is not None:
            self._start_mic_glow_polling()

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
        self._top_spacer.configure(bg=t.bg)
        self._stack.configure(bg=t.bg)
        self._bottom_spacer.configure(bg=t.bg)
        self._input_block.configure(bg=t.bg)
        self._input_inner.configure(bg=t.panel, highlightthickness=0)
        self._input_icon.configure(bg=t.panel, fg=t.text_dim)
        self._input_canvas.configure(bg=t.bg, height=self._input_pill_h)
        style_seamless_entry(self.text_input, t, bg=t.panel)
        self.text_input.configure(disabledbackground=t.panel)
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
        self.snippet_label.configure(
            fg=_lerp_color_hex(t.text_dim, t.bg, 0.18),
            bg=t.bg,
        )
        self._refresh_send_button_style()
        self._redraw_home_input_pill()


# --- Chat ---------------------------------------------------------------------

CHAT_SEARCH_PH = "Search conversations..."
CHAT_PILL_H = 46
# One vertical column: outer margin + same inner gutter as message bubbles
CHAT_OUTER_X = 16
CHAT_BUBBLE_INSET = 20
CHAT_LEFT_ALIGN = CHAT_OUTER_X + CHAT_BUBBLE_INSET


class ConversationScreen(BaseScreen):
    def __init__(self, parent: tk.Widget, theme: Theme) -> None:
        super().__init__(parent, theme)
        t = self.theme
        self.messages: list[tuple[str, str]] = []
        self.last_assistant_text = ""
        self._search_ph = CHAT_SEARCH_PH

        self.top = tk.Frame(self, bg=t.bg)
        self.top.pack(fill=tk.X, padx=(CHAT_LEFT_ALIGN, CHAT_OUTER_X), pady=(18, 12))
        self.search_var = tk.StringVar()
        self._chat_pill_h = CHAT_PILL_H
        self._ph_win_id: int | None = None
        self._ph_pill_ph: object | None = None
        self._ph_canvas = tk.Canvas(
            self.top,
            height=self._chat_pill_h,
            highlightthickness=0,
            bd=0,
            bg=t.bg,
        )
        self._ph_canvas.grid(row=0, column=0, sticky="nsew", padx=(0, 14), pady=2)
        self._ph_inner = tk.Frame(
            self._ph_canvas, bg=t.panel, bd=0, highlightthickness=0
        )
        self._search_icon_label = tk.Label(
            self._ph_inner,
            text="\uE721",
            font=("Segoe MDL2 Assets", 12),
            fg=t.text_dim,
            bg=t.panel,
        )
        self._search_icon_label.pack(side=tk.LEFT, padx=(12, 6), pady=0)
        self.search_entry = tk.Entry(
            self._ph_inner,
            textvariable=self.search_var,
            font=("Segoe UI", 11),
        )
        style_seamless_entry(self.search_entry, t, bg=t.panel)
        self.search_entry.pack(
            side=tk.LEFT, fill=tk.BOTH, expand=True, ipady=3, padx=(0, 10), pady=0
        )
        self._ph_canvas.bind("<Configure>", self._on_chat_pill_configure)
        self.after_idle(self._redraw_chat_search_pill)
        attach_placeholder(self.search_entry, self.search_var, CHAT_SEARCH_PH, t)
        self._search_btn = tk.Button(self.top, text="Search", command=self.search)
        style_primary_button(self._search_btn, t, compact=True, font_size=9, padx=14, pady=6)
        self._search_btn.grid(row=0, column=1, padx=(0, 10), pady=1, sticky="ns")
        self._copy_btn = tk.Button(
            self.top, text="Copy last response", command=self.copy_last_response
        )
        style_chat_copy_button(self._copy_btn, t)
        self._copy_btn.configure(padx=14, pady=6, font=("Segoe UI Semibold", 9))
        self._copy_btn.grid(row=0, column=2, padx=0, pady=1, sticky="ns")
        self.top.rowconfigure(0, minsize=CHAT_PILL_H)
        self.top.columnconfigure(0, weight=1)
        self.top.columnconfigure(1, weight=0)
        self.top.columnconfigure(2, weight=0)
        self.after(0, self._install_rounded_chat_buttons)
        self.top.bind("<Configure>", self._on_topbar_configure, add="+")

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

        self.scrollbar.pack(
            side=tk.RIGHT, fill=tk.Y, padx=(0, CHAT_OUTER_X - 4), pady=(0, 8)
        )
        self.canvas.pack(
            side=tk.LEFT,
            fill=tk.BOTH,
            expand=True,
            padx=(CHAT_LEFT_ALIGN, 0),
            pady=(0, 12),
        )

    def _on_c_canvas(self, e: tk.Event) -> None:
        self.canvas.itemconfig(self._win, width=e.width)

    def _on_chat_pill_configure(self, _e: object) -> None:
        self._redraw_chat_search_pill()

    def _redraw_chat_search_pill(self) -> None:
        c = self._ph_canvas
        t = self.theme
        c.update_idletasks()
        w = c.winfo_width()
        h = self._chat_pill_h
        if w < 4:
            self.after(32, self._redraw_chat_search_pill)
            return
        r = min(h // 2, 22)
        pr, pg, pb = _hex_to_rgb(t.panel)
        o_r, o_g, o_b = _hex_to_rgb(t.input_border)
        img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        dr = ImageDraw.Draw(img)
        dr.rounded_rectangle(
            (0, 0, w - 1, h - 1),
            radius=r,
            fill=(pr, pg, pb, 255),
            outline=(o_r, o_g, o_b, 0),
            width=0,
        )
        self._ph_pill_ph = ImageTk.PhotoImage(img, master=self)  # type: ignore[assignment]
        c.delete("pill")
        c.create_image(0, 0, image=self._ph_pill_ph, anchor=tk.NW, tags=("pill",))
        c.configure(bg=t.bg, height=h)
        ix, iy = r - 1, 0
        i_w, i_h = w - 2 * ix, h - 2 * iy
        if i_w < 20 or i_h < 6:
            return
        if self._ph_win_id is None:
            self._ph_win_id = c.create_window(
                ix, iy, window=self._ph_inner, anchor=tk.NW, width=i_w, height=i_h
            )
        else:
            c.coords(self._ph_win_id, ix, iy)  # type: ignore[call-overload]
            c.itemconfig(self._ph_win_id, width=i_w, height=i_h)  # type: ignore[call-overload]

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
        cont.pack(fill=tk.X, padx=0, pady=6)
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

    def _install_rounded_chat_buttons(self) -> None:
        t = self.theme
        install_rounded_primary_button(self._search_btn, t)
        install_rounded_panel_outline(self._copy_btn, t, border="line")
        self._sync_chat_topbar_button_heights()

    def _on_topbar_configure(self, _e: object) -> None:
        self._sync_chat_topbar_button_heights()

    def _sync_chat_topbar_button_heights(self) -> None:
        target_h = max(34, self._chat_pill_h - 8)
        for btn in (self._search_btn, self._copy_btn):
            try:
                btn.update_idletasks()
                req_w = max(76, int(btn.winfo_reqwidth()))
                btn._round_size_lock = (req_w, target_h)  # type: ignore[attr-defined]
                btn._round_event_wh = (req_w, target_h)  # type: ignore[attr-defined]
            except tk.TclError:
                continue
        refresh_rounded_button(self._search_btn, self.theme)
        refresh_rounded_button(self._copy_btn, self.theme)

    def copy_last_response(self) -> None:
        if not self.last_assistant_text:
            return
        self.clipboard_clear()
        self.clipboard_append(self.last_assistant_text)

    def apply_theme(self, theme: Theme) -> None:
        super().apply_theme(theme)
        t = self.theme
        self.top.configure(bg=t.bg)
        self._ph_canvas.configure(bg=t.bg, height=self._chat_pill_h)
        self._ph_inner.configure(bg=t.panel, highlightthickness=0)
        self._search_icon_label.configure(bg=t.panel, fg=t.text_dim)
        style_seamless_entry(self.search_entry, t, bg=t.panel)
        if is_placeholder_value(self.search_var, self._search_ph):
            self.search_entry.configure(fg=t.text_dim)
        style_primary_button(self._search_btn, t, compact=True, font_size=9, padx=14, pady=6)
        style_chat_copy_button(self._copy_btn, t)
        self._copy_btn.configure(padx=14, pady=6, font=("Segoe UI Semibold", 9))
        refresh_rounded_button(self._search_btn, t)
        refresh_rounded_button(self._copy_btn, t)
        self._sync_chat_topbar_button_heights()
        self._redraw_chat_search_pill()
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
        self._text_entries: list[tk.Entry] = []
        self._comboboxes: list[ttk.Combobox] = []
        self._scales: list[tk.Scale] = []
        self._cbox_style_name: str = ""
        self._card: tk.Frame | None = None
        self._settings_left: tk.Frame | None = None
        self._settings_right: tk.Frame | None = None
        self._settings_v_all: tk.Frame | None = None
        self._settings_info: tk.Frame | None = None
        self._settings_save_row: tk.Frame | None = None
        self._settings_canvas: tk.Canvas | None = None
        self._settings_scrollbar: ttk.Scrollbar | None = None
        self._settings_inner: tk.Frame | None = None

        init = initial
        th = init.get("theme", "Neon")
        if th not in ("Neon", "Dark", "Minimal"):
            th = "Neon"
        self.theme_var = tk.StringVar(value=th)
        self.mic_enabled_var = tk.BooleanVar(value=bool(init.get("mic_enabled", True)))
        self.anim_var = tk.BooleanVar(value=init.get("animations", True))
        self.sound_var = tk.BooleanVar(value=init.get("sound", True))
        self.style_var = tk.StringVar(value=init.get("response_style", "concise"))
        self.model_var = tk.StringVar(value=init.get("model", "gpt-4.1-mini"))
        self.api_key_var = tk.StringVar(value=init.get("openai_api_key", "") or "")
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
        ncl = int(init.get("noise_cancellation_level", 5) or 5)
        ncl = max(1, min(10, ncl))
        self.noise_cancel_var = tk.IntVar(value=ncl)
        self._noise_cancel_pct = tk.StringVar(value=f"{ncl}/10")
        self._v_label: tk.Label | None = None
        self._nc_label: tk.Label | None = None

        self._settings_canvas = tk.Canvas(self, bg=t.bg, bd=0, highlightthickness=0)
        self._settings_scrollbar = ttk.Scrollbar(
            self, orient=tk.VERTICAL, command=self._settings_canvas.yview
        )
        self._settings_scrollbar.configure(style="Settings.Vertical.TScrollbar")
        self._settings_canvas.configure(yscrollcommand=self._settings_scrollbar.set)
        self._settings_scrollbar.pack(side=tk.RIGHT, fill=tk.Y, padx=(0, 8), pady=10)
        self._settings_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(10, 0), pady=10)
        self._settings_inner = tk.Frame(self._settings_canvas, bg=t.bg, bd=0, highlightthickness=0)
        self._settings_canvas.create_window((0, 0), window=self._settings_inner, anchor=tk.NW)
        self._settings_inner.bind("<Configure>", self._on_settings_frame_configure)
        self._settings_canvas.bind("<Configure>", self._on_settings_canvas_configure)
        self._settings_canvas.bind_all("<MouseWheel>", self._on_settings_mousewheel, add="+")

        self._card = tk.Frame(self._settings_inner, bg=t.bg, bd=0, highlightthickness=0)
        self._card.pack(fill=tk.BOTH, expand=True, padx=18, pady=18)
        card = self._card
        card.columnconfigure(0, weight=1)
        card.columnconfigure(1, weight=1)

        left = tk.Frame(
            card,
            bg=t.panel,
            bd=0,
            highlightthickness=1,
            highlightbackground=t.border,
            padx=18,
            pady=16,
        )
        right = tk.Frame(
            card,
            bg=t.panel,
            bd=0,
            highlightthickness=1,
            highlightbackground=t.border,
            padx=18,
            pady=16,
        )
        self._settings_left = left
        self._settings_right = right
        left.grid(row=0, column=0, sticky=tk.NSEW, padx=(0, 12), pady=(0, 24))
        right.grid(row=0, column=1, sticky=tk.NSEW, padx=(12, 0), pady=(0, 24))
        left.columnconfigure(1, weight=1)
        right.columnconfigure(1, weight=1)

        self._section_title(left, "General", 0, icon="\u2699")
        self._grid_row(
            left,
            1,
            "Theme",
            self._styled_combobox(left, self.theme_var, ["Neon", "Dark", "Minimal"]),
        )
        self._grid_row(left, 2, "Mic", self._styled_check(left, self.mic_enabled_var))
        self._grid_row(left, 3, "Animations", self._styled_check(left, self.anim_var))
        self._grid_row(left, 4, "Sound", self._styled_check(left, self.sound_var))
        self._section_title(left, "AI Settings", 5, pady=(28, 8), icon="\U0001F916")
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
            show="*",
            font=("Segoe UI", 11),
        )
        style_seamless_entry(api_entry, t, bg=t.panel_alt)
        self._text_entries.append(api_entry)
        api_entry.pack(fill=tk.X, expand=True, padx=8, pady=8, ipady=2)
        self._grid_row(left, 7, "OpenAI API key", api_shell)
        self._grid_row(
            left,
            8,
            "Response style",
            self._styled_combobox(left, self.style_var, ["concise", "detailed"]),
        )

        self._section_title(right, "Audio", 0, icon="\U0001F50A")
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
        nc_all = tk.Frame(right, bg=t.panel)
        nc_bar = tk.Frame(nc_all, bg=t.panel)
        nc_bar.pack(fill=tk.X, pady=(0, 2))
        self._nc_label = tk.Label(
            nc_bar,
            textvariable=self._noise_cancel_pct,
            font=("Segoe UI", 10),
            bg=t.panel,
            fg=t.accent_blue,
        )
        self._nc_label.pack(side=tk.RIGHT)
        noise_scale = tk.Scale(
            nc_all,
            variable=self.noise_cancel_var,
            from_=1,
            to=10,
            resolution=1,
            orient=tk.HORIZONTAL,
            command=self._on_noise_cancel,
            bg=t.panel,
            fg=t.text,
            troughcolor=t.panel_alt,
            activebackground=t.accent_blue,
            highlightthickness=0,
            length=200,
            font=("Segoe UI", 10),
        )
        self._scales.append(noise_scale)
        noise_scale.pack(fill=tk.X, expand=True, pady=(0, 2))
        self._grid_row(right, 3, "Noise cancel", nc_all)
        v_all = tk.Frame(right, bg=t.panel)
        self._settings_v_all = v_all
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
            troughcolor=t.panel_alt,
            activebackground=t.accent_blue,
            highlightthickness=0,
            length=200,
            font=("Segoe UI", 10),
        )
        self._scales.append(vol)
        vol.pack(fill=tk.X, expand=True, pady=(0, 2))
        self._grid_row(right, 4, "Volume", v_all)

        self._section_title(right, "Updates & Info", 5, pady=(28, 8), icon="\u2139")
        info = tk.Frame(right, bg=t.panel_alt, bd=0, highlightthickness=1, highlightbackground=t.border)
        self._settings_info = info
        info.grid(row=6, column=0, columnspan=2, sticky=tk.EW, pady=(2, 0))
        tk.Label(info, text=f"Version: v{version}", bg=t.panel_alt, fg=t.text_dim, font=("Segoe UI", 10)).pack(anchor=tk.W, padx=12, pady=(10, 2))
        tk.Label(info, text="Author: Manish", bg=t.panel_alt, fg=t.text_dim, font=("Segoe UI", 10)).pack(anchor=tk.W, padx=12, pady=(0, 10))
        self._u_btn = tk.Button(info, text="Check for updates", command=self.on_check_updates)  # type: ignore[assignment, attr-defined]
        style_primary_button(self._u_btn, t, compact=True, font_size=9)
        self._u_btn.pack(anchor=tk.E, padx=12, pady=(0, 10))  # type: ignore[union-attr]

        save_row = tk.Frame(card, bg=t.panel, bd=0, highlightthickness=1, highlightbackground=t.border, padx=14, pady=10)
        self._settings_save_row = save_row
        save_row.grid(row=1, column=0, columnspan=2, sticky=tk.EW, padx=0, pady=(0, 0))
        tk.Label(
            save_row,
            text="Click Save to store settings on this device.",
            bg=t.panel,
            fg=t.text_dim,
            font=("Segoe UI", 10),
        ).pack(side=tk.LEFT, pady=4, padx=(0, 12))
        self._s_btn = tk.Button(  # type: ignore[assignment, attr-defined]
            save_row, text="Save", command=lambda: self.on_save(self.current_settings())
        )
        style_primary_button(self._s_btn, t, compact=True, font_size=9)
        self._s_btn.pack(side=tk.RIGHT, pady=1)  # type: ignore[union-attr]

        self._ensure_cbox_style()
        self.after(0, self._install_rounded_settings_primary_buttons)

    def _on_volume(self, _v: str) -> None:
        self._vol_pct.set(f"{int(float(self.volume_var.get()) * 100)}%")

    def _on_noise_cancel(self, _v: str) -> None:
        self._noise_cancel_pct.set(f"{int(self.noise_cancel_var.get())}/10")

    def _on_settings_frame_configure(self, _e: object) -> None:
        if self._settings_canvas is None:
            return
        self._settings_canvas.configure(scrollregion=self._settings_canvas.bbox("all"))

    def _on_settings_canvas_configure(self, e: object) -> None:
        if self._settings_canvas is None or self._settings_inner is None:
            return
        try:
            w = int(e.width)  # type: ignore[attr-defined]
        except (AttributeError, ValueError):
            return
        win_ids = self._settings_canvas.find_all()
        if win_ids:
            self._settings_canvas.itemconfig(win_ids[0], width=w)

    def _on_settings_mousewheel(self, e: object) -> None:
        if self._settings_canvas is None:
            return
        try:
            if not self.winfo_ismapped():
                return
            delta = int(e.delta)  # type: ignore[attr-defined]
        except (tk.TclError, AttributeError, ValueError):
            return
        step = -1 if delta > 0 else 1
        self._settings_canvas.yview_scroll(step, "units")

    def _settings_sync_label_bg(self, parent: tk.Widget, t: Theme) -> None:
        bg = str(parent.cget("bg")) if hasattr(parent, "cget") else t.bg
        for c in parent.winfo_children():
            wclass = c.winfo_class()
            if wclass == "Label" and isinstance(c, tk.Label):
                try:
                    c.configure(bg=bg)
                    fn = c.cget("font")
                    size = 0
                    if isinstance(fn, tuple) and len(fn) > 1:
                        try:
                            size = int(fn[1])
                        except (TypeError, ValueError):
                            size = 0
                    elif isinstance(fn, str) and "Semibold" in fn:
                        size = 14
                    c.configure(fg=t.text if size >= 12 else t.text_dim)
                except tk.TclError:
                    pass
            elif wclass == "Frame" and isinstance(c, tk.Frame):
                try:
                    # Preserve tinted input/info cards while harmonizing generic containers.
                    if str(c.cget("bg")) in (t.bg, t.panel):
                        c.configure(bg=bg)
                except tk.TclError:
                    pass
                self._settings_sync_label_bg(c, t)

    def _install_rounded_settings_primary_buttons(self) -> None:
        t = self.theme
        install_rounded_primary_button(self._u_btn, t)  # type: ignore[union-attr, arg-type]
        install_rounded_primary_button(self._s_btn, t)  # type: ignore[union-attr, arg-type]

    def _section_title(
        self,
        parent: tk.Widget,
        title: str,
        row: int,
        pady: tuple[int, int] = (0, 6),
        icon: str = "",
    ) -> None:
        text = f"{icon}  {title}" if icon else title
        tk.Label(
            parent,
            text=text,
            bg=self.theme.panel,
            fg=self.theme.text,
            font=("Segoe UI Semibold", 16),
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
            font=("Segoe UI Semibold", 10),
        ).grid(row=row, column=0, sticky=tk.NW, pady=10, padx=(0, 10))
        widget.grid(row=row, column=1, sticky=tk.EW, pady=10, ipady=2)

    def _make_shell(self, parent: tk.Widget) -> tuple[tk.Frame, tk.Frame]:
        t = self.theme
        shell = tk.Frame(parent, bg=t.border, bd=0, highlightthickness=0, padx=1, pady=1)
        inner = tk.Frame(shell, bg=t.panel_alt, bd=0, highlightthickness=0)
        inner.pack(fill="both", expand=True)
        self._shell_tuples.append((shell, inner))
        return shell, inner

    def _ensure_cbox_style(self) -> None:
        if not self._cbox_style_name:
            self._cbox_style_name = f"Jarvis.{id(self)}.TCombobox"
        t = self.theme
        s = ttk.Style()
        s.configure(
            self._cbox_style_name,
            fieldbackground=t.panel_alt,
            background=t.panel_alt,
            foreground=t.text,
            bordercolor=t.panel_alt,
            darkcolor=t.panel_alt,
            lightcolor=t.panel_alt,
            arrowcolor=t.text,
            borderwidth=0,
            padding=10,
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

    def _styled_check(self, parent: tk.Widget, variable: tk.BooleanVar) -> tk.Widget:
        try:
            return ttk.Checkbutton(parent, variable=variable, cursor="hand2", bootstyle="round-toggle")
        except Exception:
            return tk.Checkbutton(
                parent,
                variable=variable,
                bg=self.theme.panel,
                activebackground=self.theme.panel,
                fg=self.theme.text,
                selectcolor=self.theme.text_dim,
                highlightthickness=0,
                activeforeground=self.theme.text,
                cursor="hand2",
            )

    def apply_theme(self, theme: Theme) -> None:
        super().apply_theme(theme)
        t = self.theme
        if self._settings_canvas is not None:
            self._settings_canvas.configure(bg=t.bg)
        st = ttk.Style()
        st.configure(
            "Settings.Vertical.TScrollbar",
            troughcolor=t.bg,
            background=t.accent_soft,
            bordercolor=t.bg,
            arrowcolor=t.text_dim,
            darkcolor=t.accent_blue,
            lightcolor=t.accent_soft,
            width=8,
        )
        st.map("Settings.Vertical.TScrollbar", background=[("active", t.accent)])
        settings_left = getattr(self, "_settings_left", None)
        settings_right = getattr(self, "_settings_right", None)
        settings_v_all = getattr(self, "_settings_v_all", None)
        settings_info = getattr(self, "_settings_info", None)
        settings_save_row = getattr(self, "_settings_save_row", None)
        if self._card is not None:
            self._card.configure(bg=t.bg, highlightthickness=0)
        if settings_left is not None:
            settings_left.configure(bg=t.panel, highlightthickness=1, highlightbackground=t.border)
        if settings_right is not None:
            settings_right.configure(bg=t.panel, highlightthickness=1, highlightbackground=t.border)
        if settings_v_all is not None:
            settings_v_all.configure(bg=t.panel)
        if settings_info is not None:
            settings_info.configure(bg=t.panel_alt, highlightthickness=1, highlightbackground=t.border)
        if settings_save_row is not None:
            settings_save_row.configure(bg=t.panel, highlightthickness=1, highlightbackground=t.border)
        for sh, inner in self._shell_tuples:
            sh.configure(bg=t.border)
            inner.configure(bg=t.panel_alt)
        for entry in self._text_entries:
            style_seamless_entry(entry, t, bg=t.panel_alt)
        for scale in self._scales:
            try:
                scale.configure(
                    bg=t.panel,
                    fg=t.text,
                    troughcolor=t.panel_alt,
                    activebackground=t.accent_blue,
                )
            except tk.TclError:
                pass
        if self._v_label is not None:
            self._v_label.configure(fg=t.accent_blue, bg=t.panel)
        if self._nc_label is not None:
            self._nc_label.configure(fg=t.accent_blue, bg=t.panel)
        for p in (settings_left, settings_right, settings_info, settings_save_row):
            if p is not None:
                self._settings_sync_label_bg(p, t)
        self._ensure_cbox_style()
        for cbox in self._comboboxes:
            cbox.update_idletasks()
        style_primary_button(  # type: ignore[union-attr, arg-type]
            self._u_btn, t, compact=True, font_size=9
        )
        style_primary_button(  # type: ignore[union-attr, arg-type]
            self._s_btn, t, compact=True, font_size=9
        )
        refresh_rounded_button(self._u_btn, t)  # type: ignore[union-attr, arg-type]
        refresh_rounded_button(self._s_btn, t)  # type: ignore[union-attr, arg-type]

    def current_settings(self) -> dict:
        return {
            "theme": self.theme_var.get(),
            "openai_api_key": self.api_key_var.get().strip(),
            "mic_enabled": self.mic_enabled_var.get(),
            "animations": self.anim_var.get(),
            "sound": self.sound_var.get(),
            "response_style": self.style_var.get(),
            "model": self.model_var.get().strip(),
            "mic": self.mic_var.get().strip(),
            "noise_cancellation_level": int(self.noise_cancel_var.get()),
            "voice": self.voice_var.get().strip(),
            "volume": self.volume_var.get(),
        }


# --- Command center: compact rounded quick-action tiles ------------------------


class CommandCenterScreen(BaseScreen):
    def __init__(self, parent: tk.Widget, theme: Theme, on_command: object) -> None:
        super().__init__(parent, theme)
        self._on_cmd = on_command
        t = self.theme
        w, h = QUICK_TILE_W, QUICK_TILE_H
        self._quick_specs: list[
            tuple[tk.Canvas, str, str, str, str, tuple[str, int]]
        ] = []

        self._wrap = tk.Frame(self, bg=t.bg)
        self._wrap.pack(fill=tk.BOTH, expand=True, padx=24, pady=20)
        self._hdr = tk.Label(
            self._wrap,
            text="Quick Actions",
            font=("Segoe UI Semibold", 18),
            bg=t.bg,
            fg=t.text,
            anchor=tk.W,
        )
        self._hdr.pack(fill=tk.X, pady=(0, 10))
        self._center_area = tk.Frame(self._wrap, bg=t.bg)
        self._center_area.pack(fill=tk.BOTH, expand=True)
        self._grid = tk.Frame(self._center_area, bg=t.bg)
        self._grid.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

        tiles: list[tuple[str, str, str]] = [
            ("Open Chrome", "open chrome", "#2d1f4a"),
            ("Open VS Code", "open vscode", "#153040"),
            ("Check Weather", "weather in Mumbai", "#1a2d55"),
            ("News", "news", "#3a1a35"),
        ]
        icons: list[str] = ["\uE774", "\uE943", "\uE753", "\U0001f4f0"]
        for idx, (label, cmd, fill_hex) in enumerate(tiles):
            ico = icons[idx]
            ico_font: tuple[str, int] = (
                ("Segoe UI", 18) if idx == 3 else ("Segoe MDL2 Assets", 26)
            )
            c = tk.Canvas(
                self._grid,
                width=w,
                height=h,
                highlightthickness=0,
                bd=0,
                bg=t.bg,
                cursor="hand2",
            )
            c.grid(row=idx // 2, column=idx % 2, padx=6, pady=6)
            self._quick_specs.append((c, label, cmd, fill_hex, ico, ico_font))
            self._draw_one_quick_tile(c, t, fill_hex, label, ico, ico_font, cmd)

    def _draw_one_quick_tile(
        self,
        c: tk.Canvas,
        t: Theme,
        fill_hex: str,
        label: str,
        icon: str,
        ico_font: tuple[str, int],
        cmd: str,
    ) -> None:
        w, h = QUICK_TILE_W, QUICK_TILE_H
        c.delete("all")
        c.configure(width=w, height=h, bg=t.bg, highlightthickness=0, cursor="hand2")
        im = _quick_tile_pil(w, h, fill_hex, t.border, QUICK_TILE_CORNER)
        ph = ImageTk.PhotoImage(im, master=c)  # type: ignore[assignment]
        c._tile_ph = ph  # type: ignore[attr-defined]  # keep ref; GC-safe
        c.create_image(0, 0, image=ph, anchor=tk.NW, tags=("bg",))
        cx, cy = w // 2, h // 2
        c.create_text(
            cx,
            cy - 12,
            text=icon,
            font=ico_font,  # type: ignore[assignment, arg-type]
            fill="#e6edff",
            tags=("content",),
        )
        c.create_text(
            cx,
            cy + 18,
            text=label,
            font=("Segoe UI Semibold", 9),
            fill="#ffffff",
            tags=("content",),
        )
        c.bind("<Button-1>", lambda _e, a=cmd: self._on_cmd(a))  # type: ignore[union-attr]

    def apply_theme(self, theme: Theme) -> None:
        super().apply_theme(theme)
        t = self.theme
        self._wrap.configure(bg=t.bg)
        self._center_area.configure(bg=t.bg)
        self._grid.configure(bg=t.bg)
        self._hdr.configure(bg=t.bg, fg=t.text)
        for c, label, _cmd, fill_hex, ico, ico_font in self._quick_specs:
            self._draw_one_quick_tile(c, t, fill_hex, label, ico, ico_font, _cmd)
