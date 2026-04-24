"""
Tk has no real border-radius; we draw rounded rectangles (PIL) and use as Button image
with text composited, matching a ~15px+ web-style radius when space allows.
"""

from __future__ import annotations

import tkinter as tk
from typing import Any, Literal

from PIL import Image, ImageDraw, ImageTk

from jarvis.ui.theme import Theme

# Min corner radius in px (matches typical website UI); capped down on small controls.
BUTTON_CORNER_RADIUS = 15


def _hex(s: str) -> tuple[int, int, int]:
    h = s.lstrip("#")
    if len(h) != 6:
        return 0, 0, 0
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def _radius_for(w: int, h: int) -> int:
    m = min(w, h) // 2 - 1
    return min(BUTTON_CORNER_RADIUS, max(0, m))


def _parent_bg(button: tk.Button, theme: Theme) -> str:
    try:
        return str(button.master.cget("bg"))
    except tk.TclError:
        return theme.bg


# Sane upper bounds: oversized PhotoImage + <Configure> storms can freeze the Tk main loop
_ROUND_MAX_W = 300
_ROUND_MAX_H = 72


def _measure_button(
    button: tk.Button, *, from_wh: tuple[int, int] | None = None
) -> tuple[int, int]:
    if from_wh is not None:
        w, h = from_wh[0], from_wh[1]
    else:
        button.update_idletasks()
        w, h = button.winfo_width() or 0, button.winfo_height() or 0
        if w < 2 or h < 2:
            w = w or (button.winfo_reqwidth() or 0)
            h = h or (button.winfo_reqheight() or 0)
    w = int(min(max(w, 2), _ROUND_MAX_W))
    h = int(min(max(h, 2), _ROUND_MAX_H))
    return w, h


def _build_rounded_solid_pil(
    w: int,
    h: int,
    r: int,
    fill_hex: str,
    border_hex: str | None = None,
    border_w: int = 0,
) -> Any:
    fr, fg, fb = _hex(fill_hex)
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    dr = ImageDraw.Draw(img)
    if border_w > 0 and border_hex is not None:
        or_, og, ob = _hex(border_hex)
        dr.rounded_rectangle(
            (0, 0, w - 1, h - 1),
            radius=r,
            fill=(fr, fg, fb, 255),
            outline=(or_, og, ob, 255),
            width=border_w,
        )
    else:
        dr.rounded_rectangle(
            (0, 0, w - 1, h - 1),
            radius=r,
            fill=(fr, fg, fb, 255),
        )
    return img


def _round_draw(
    button: tk.Button, _from_wh: tuple[int, int] | None = None
) -> None:
    if not getattr(button, "_round_init", False):
        return
    t: Theme = button._round_theme  # type: ignore[assignment, attr-defined]
    k = str(getattr(button, "_round_kind", "primary"))
    w, h = _measure_button(button, from_wh=_from_wh)
    # Fixed size after lock: do not let the pill grow on later <Configure> / measure
    lock = getattr(button, "_round_size_lock", None)  # type: ignore[assignment, attr-defined]
    if lock is not None:
        w, h = int(lock[0]), int(lock[1])
    r = _radius_for(w, h)
    pbg = _parent_bg(button, t)
    hov = bool(getattr(button, "_round_hovered", False))

    if k == "primary":
        fill = t.accent if hov else t.accent_blue
        im = _build_rounded_solid_pil(w, h, r, fill, None, 0)
    else:
        sk = str(getattr(button, "_round_border_key", "line"))
        border = t.text_dim if sk == "dim" else t.border
        fill = t.card_highlight if hov else t.panel
        im = _build_rounded_solid_pil(w, h, r, fill, border, 1)

    ph = ImageTk.PhotoImage(im, master=button)  # type: ignore[assignment, misc]
    button._round_photo = ph  # type: ignore[attr-defined]
    button._round_applied_wh = (w, h)  # type: ignore[attr-defined]
    try:
        button.config(
            image=ph,  # type: ignore[call-overload]
            compound=tk.CENTER,
            highlightthickness=0,
            bd=0,
            bg=pbg,
            activebackground=pbg,
        )
    except tk.TclError:
        return


def refresh_rounded_button(button: tk.Button, theme: Theme) -> None:
    if not getattr(button, "_round_init", False):
        return
    button._round_theme = theme  # type: ignore[attr-defined]
    lock = getattr(button, "_round_size_lock", None)  # type: ignore[assignment, arg-type]
    wh = (
        lock
        or getattr(button, "_round_event_wh", None)  # type: ignore[union-attr, arg-type]
        or getattr(button, "_round_applied_wh", None)  # type: ignore[union-attr, arg-type]
    )
    _round_draw(button, wh)  # type: ignore[union-attr, arg-type]


def _wire_rounded_interaction(button: tk.Button) -> None:
    def _wh_for_draw() -> tuple[int, int] | None:  # prefer fixed lock
        loc = getattr(button, "_round_size_lock", None)  # type: ignore[attr-defined, union-attr, arg-type]
        if loc is not None:
            return (int(loc[0]), int(loc[1]))  # type: ignore[union-attr, arg-type]
        return getattr(button, "_round_event_wh", None) or getattr(
            button, "_round_applied_wh", None
        )

    def draw_at(wh: tuple[int, int] | None = None) -> None:
        if wh is None:
            wh = _wh_for_draw()
        _round_draw(button, wh)

    def on_enter(_e: object) -> None:
        try:
            if str(button.cget("state")) == "disabled":
                return
        except tk.TclError:
            return
        button._round_hovered = True  # type: ignore[attr-defined]
        draw_at(_wh_for_draw())

    def on_leave(_e: object) -> None:
        button._round_hovered = False  # type: ignore[attr-defined]
        draw_at(_wh_for_draw())

    def on_cfg(e: object) -> None:  # noqa: ANN001
        if getattr(button, "_round_size_lock", None) is not None:
            return
        try:
            w, h = int(e.width), int(e.height)  # type: ignore[union-attr, arg-type]
        except (AttributeError, ValueError, tk.TclError):
            return
        if w < 2 or h < 2:
            return
        prev = getattr(button, "_round_event_wh", None)  # type: ignore[assignment, attr-defined]
        if (
            prev is not None
            and abs(w - int(prev[0])) <= 1
            and abs(h - int(prev[1])) <= 1
        ):
            return
        button._round_event_wh = (w, h)  # type: ignore[attr-defined]

        def do() -> None:  # debounce: collapse <Configure> storms (prevents "not responding")
            if not getattr(button, "_round_init", False):
                return
            button._round_cfg_id = None  # type: ignore[attr-defined]
            w2, h2 = getattr(button, "_round_event_wh", (w, h))  # type: ignore[union-attr, arg-type]
            _round_draw(button, (int(w2), int(h2)))

        cid = getattr(button, "_round_cfg_id", None)  # type: ignore[union-attr]
        if cid is not None:
            try:
                button.after_cancel(cid)  # type: ignore[union-attr, arg-type]
            except (tk.TclError, ValueError):
                pass
        button._round_cfg_id = button.winfo_toplevel().after(40, do)  # type: ignore[attr-defined]

    button._round_hovered = False  # type: ignore[attr-defined]
    button._round_event_wh = None  # type: ignore[attr-defined]

    def _freeze_size(_attempt: int = 0) -> None:
        if not getattr(button, "_round_init", False):
            return
        if getattr(button, "_round_size_lock", None) is not None:
            return
        button.update_idletasks()
        w = int(button.winfo_reqwidth() or 0) or int(button.winfo_width() or 0)
        h = int(button.winfo_reqheight() or 0) or int(button.winfo_height() or 0)
        w = int(min(max(w, 2), _ROUND_MAX_W))
        h = int(min(max(h, 2), _ROUND_MAX_H))
        if (w < 6 or h < 4) and _attempt < 4:
            button.winfo_toplevel().after(48, lambda: _freeze_size(_attempt + 1))
            return
        if w < 2 or h < 2:
            return
        button._round_size_lock = (w, h)  # type: ignore[attr-defined]
        cfg_id = getattr(button, "_round_cfg_id", None)  # type: ignore[union-attr, arg-type]
        if cfg_id is not None:
            try:
                button.after_cancel(cfg_id)  # type: ignore[union-attr, arg-type]
            except (tk.TclError, ValueError):
                pass
            button._round_cfg_id = None  # type: ignore[attr-defined]
        _round_draw(button, (w, h))

    button.bind("<Enter>", on_enter, add="+")
    button.bind("<Leave>", on_leave, add="+")
    button.bind("<Configure>", on_cfg, add="+")
    draw_at()
    button.winfo_toplevel().after_idle(_freeze_size)


def install_rounded_primary_button(button: tk.Button, theme: Theme) -> None:
    if getattr(button, "_round_init", False):
        button._round_kind = "primary"  # type: ignore[attr-defined]
        button._round_theme = theme  # type: ignore[attr-defined]
        _round_draw(button)
        return
    button._round_kind = "primary"  # type: ignore[attr-defined]
    button._round_init = True  # type: ignore[attr-defined]
    button._round_theme = theme  # type: ignore[attr-defined]
    _wire_rounded_interaction(button)


def install_rounded_panel_outline(
    button: tk.Button, theme: Theme, *, border: Literal["dim", "line"] = "line"
) -> None:
    if getattr(button, "_round_init", False):
        button._round_kind = "panel_outline"  # type: ignore[attr-defined]
        button._round_theme = theme  # type: ignore[attr-defined]
        button._round_border_key = "dim" if border == "dim" else "line"  # type: ignore[attr-defined]
        _round_draw(button)
        return
    button._round_kind = "panel_outline"  # type: ignore[attr-defined]
    button._round_border_key = "dim" if border == "dim" else "line"  # type: ignore[attr-defined]
    button._round_init = True  # type: ignore[attr-defined]
    button._round_theme = theme  # type: ignore[attr-defined]
    _wire_rounded_interaction(button)
