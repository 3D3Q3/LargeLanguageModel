"""GUI form helpers for Genius."""
from __future__ import annotations

import logging
import random
import secrets
import sys
import tkinter as tk
import uuid
from datetime import datetime
from tkinter import messagebox, ttk
from typing import Any, Dict

from .icon import icon_for_tk

if sys.platform == "win32":  # pragma: no cover - Windows-specific cosmetics
    import ctypes

    DWMWA_USE_IMMERSIVE_DARK_MODE = 20
    DWMWA_CAPTION_COLOR = 35
else:  # pragma: no cover - non Windows fallback
    ctypes = None  # type: ignore[assignment]


logger = logging.getLogger(__name__)


PALETTE = {
    "background": "#0f172a",
    "surface": "#17233b",
    "surface_alt": "#1f2d4a",
    "accent": "#6366f1",
    "accent_hover": "#818cf8",
    "text": "#e2e8f0",
    "muted": "#94a3b8",
}

_STYLE_INITIALIZED = False


class FormCancelled(Exception):
    """Raised when the user cancels a form."""


def _ensure_style(root: tk.Misc) -> ttk.Style:
    global _STYLE_INITIALIZED
    style = ttk.Style(root)
    if not _STYLE_INITIALIZED:
        try:
            style.theme_use("clam")
        except Exception:  # pragma: no cover - ttk theme availability
            pass
        style.configure("G.Background.TFrame", background=PALETTE["background"])
        style.configure("G.Surface.TFrame", background=PALETTE["surface"])
        style.configure("G.Header.TFrame", background=PALETTE["surface_alt"])
        style.configure("G.FormLabel.TLabel", background=PALETTE["surface"], foreground=PALETTE["text"], font=("Segoe UI", 10, "bold"))
        style.configure("G.Helper.TLabel", background=PALETTE["surface"], foreground=PALETTE["muted"], font=("Segoe UI", 9))
        style.configure("G.Header.TLabel", background=PALETTE["surface_alt"], foreground=PALETTE["text"], font=("Segoe UI", 11, "bold"))
        style.configure("G.TEntry", fieldbackground=PALETTE["surface_alt"], foreground=PALETTE["text"], borderwidth=0, relief="flat")
        style.configure("G.TCombobox", fieldbackground=PALETTE["surface_alt"], foreground=PALETTE["text"], background=PALETTE["surface_alt"])
        style.configure("G.Accent.TButton", background=PALETTE["accent"], foreground="white", focuscolor=PALETTE["accent"], font=("Segoe UI", 10, "bold"))
        style.map("G.Accent.TButton", background=[("active", PALETTE["accent_hover"])], foreground=[("disabled", PALETTE["muted"])])
        style.configure("G.Secondary.TButton", background=PALETTE["surface_alt"], foreground=PALETTE["text"], font=("Segoe UI", 10))
        style.map("G.Secondary.TButton", background=[("active", PALETTE["accent"]), ("disabled", PALETTE["surface_alt"])])
        style.configure("G.TSeparator", background=PALETTE["surface_alt"], foreground=PALETTE["surface_alt"])
        _STYLE_INITIALIZED = True
    return style


def _apply_windows_titlebar(window: tk.Tk) -> None:
    """Enable Windows 11 styled dark titlebars.

    Adapted from the KumaTray project by QueryLab (MIT License).
    """

    if ctypes is None:  # pragma: no cover - non Windows environments
        return
    try:
        hwnd = ctypes.windll.user32.GetParent(window.winfo_id())
        use_dark = ctypes.c_int(1)
        ctypes.windll.dwmapi.DwmSetWindowAttribute(
            hwnd,
            DWMWA_USE_IMMERSIVE_DARK_MODE,
            ctypes.byref(use_dark),
            ctypes.sizeof(use_dark),
        )

        r, g, b = (int(PALETTE["surface_alt"][i : i + 2], 16) for i in (1, 3, 5))
        color_ref = (b << 16) | (g << 8) | r
        accent_color = ctypes.c_int(color_ref)
        ctypes.windll.dwmapi.DwmSetWindowAttribute(
            hwnd,
            DWMWA_CAPTION_COLOR,
            ctypes.byref(accent_color),
            ctypes.sizeof(accent_color),
        )
    except Exception:  # pragma: no cover - defensive logging
        logger.debug("Unable to apply immersive dark titlebar", exc_info=True)


def _resolve_default(field: Dict[str, Any]) -> str:
    generator = (field.get("generate") or "").lower()
    if generator == "uuid":
        return str(uuid.uuid4())
    if generator == "token":
        return secrets.token_hex(3).upper()
    if generator == "timestamp":
        return datetime.now().strftime("%Y-%m-%d %H:%M")
    if generator == "build":
        return f"build-{datetime.now().strftime('%Y%m%d')}-{secrets.token_hex(2)}"
    if generator == "choice":
        options = field.get("options") or []
        if options:
            return random.choice(options)
    return field.get("default", "")


class FormWindow(tk.Tk):
    """A lightweight tkinter form that collects user input."""

    def __init__(self, title: str, form_config: Dict[str, Any]):
        super().__init__()
        self._form_config = form_config
        self._values: Dict[str, Any] = {}
        self._result_available = False

        self.title(title)
        self.geometry("480x10")  # height recalculates later
        self.resizable(False, False)
        self.configure(bg=PALETTE["background"])
        self.option_add("*Font", "Segoe UI 10")
        self.protocol("WM_DELETE_WINDOW", self._cancel)

        self._style = _ensure_style(self)
        self._icon_image = icon_for_tk(None, size=40)
        if self._icon_image:
            self.iconphoto(True, self._icon_image)

        self._build_layout()
        self.after(20, self._center_on_screen)
        self.after(40, lambda: self.focus_force())
        _apply_windows_titlebar(self)

    def _build_layout(self) -> None:
        container = ttk.Frame(self, padding=(22, 18, 22, 18), style="G.Surface.TFrame")
        container.grid(row=0, column=0, sticky="nsew")
        self.columnconfigure(0, weight=1)

        header = ttk.Frame(container, padding=(12, 10, 12, 16), style="G.Header.TFrame")
        header.grid(row=0, column=0, sticky="ew")
        header.columnconfigure(1, weight=1)

        if self._icon_image:
            ttk.Label(header, image=self._icon_image, style="G.Header.TLabel").grid(row=0, column=0, sticky="w")
        title_text = self._form_config.get("title", "Genius")
        ttk.Label(header, text=title_text, style="G.Header.TLabel").grid(row=0, column=1, sticky="w", padx=(12, 0))

        description = self._form_config.get("description")
        if description:
            ttk.Label(
                container,
                text=description,
                style="G.Helper.TLabel",
                wraplength=360,
            ).grid(row=1, column=0, sticky="w", pady=(12, 6))

        ttk.Separator(container, style="G.TSeparator").grid(row=2, column=0, sticky="ew", pady=(4, 12))

        form_frame = ttk.Frame(container, style="G.Surface.TFrame")
        form_frame.grid(row=3, column=0, sticky="nsew")
        form_frame.columnconfigure(1, weight=1)

        padding = {"padx": (8, 6), "pady": (4, 4)}
        fields = self._form_config.get("fields", [])
        row_index = 0
        for field in fields:
            label = ttk.Label(form_frame, text=field.get("label", field["name"]), style="G.FormLabel.TLabel")
            label.grid(row=row_index, column=0, sticky="w", **padding)

            field_type = field.get("type", "text")
            default_value = _resolve_default(field)
            if field_type == "choice":
                var = tk.StringVar(value=default_value)
                widget = ttk.Combobox(form_frame, textvariable=var, state="readonly", style="G.TCombobox")
                widget["values"] = field.get("options", [])
            elif field_type == "multiline":
                widget = tk.Text(form_frame, width=48, height=6, wrap="word")
                widget.insert("1.0", default_value)
                widget.configure(bg=PALETTE["surface_alt"], fg=PALETTE["text"], insertbackground=PALETTE["accent"], relief="flat", highlightthickness=1, highlightbackground=PALETTE["surface_alt"], highlightcolor=PALETTE["accent"])
            else:
                var = tk.StringVar(value=default_value)
                widget = ttk.Entry(form_frame, textvariable=var, style="G.TEntry")

            widget.grid(row=row_index, column=1, sticky="ew", **padding)
            form_frame.rowconfigure(row_index, weight=0)
            self._values[field["name"]] = widget

            helper = field.get("helper")
            if helper:
                row_index += 1
                ttk.Label(
                    form_frame,
                    text=helper,
                    style="G.Helper.TLabel",
                    wraplength=320,
                    anchor="w",
                    justify="left",
                ).grid(row=row_index, column=1, sticky="w", padx=(8, 6), pady=(0, 6))

            row_index += 1

        button_frame = ttk.Frame(container, padding=(0, 18, 0, 0), style="G.Surface.TFrame")
        button_frame.grid(row=4, column=0, sticky="ew")
        button_frame.columnconfigure(0, weight=1)

        action_row = ttk.Frame(button_frame, style="G.Surface.TFrame")
        action_row.grid(row=0, column=0, sticky="e")

        submit_button = ttk.Button(action_row, text=self._form_config.get("submit_label", "Submit"), style="G.Accent.TButton", command=self._submit)
        submit_button.grid(row=0, column=1, padx=(6, 0))

        cancel_button = ttk.Button(action_row, text=self._form_config.get("cancel_label", "Cancel"), style="G.Secondary.TButton", command=self._cancel)
        cancel_button.grid(row=0, column=0, padx=(0, 6))

        self.bind("<Return>", lambda event: self._submit())
        self.bind("<Escape>", lambda event: self._cancel())

    def _center_on_screen(self) -> None:
        self.update_idletasks()
        width = self.winfo_reqwidth()
        height = self.winfo_reqheight()
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width // 2) - (width // 2)
        y = (screen_height // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")

    def _collect_values(self) -> Dict[str, Any]:
        result: Dict[str, Any] = {}
        for name, widget in self._values.items():
            if isinstance(widget, tk.Text):
                result[name] = widget.get("1.0", tk.END).strip()
            elif isinstance(widget, ttk.Combobox):
                result[name] = widget.get()
            else:
                result[name] = widget.get()
        return result

    def _submit(self) -> None:
        self._submitted_values = self._collect_values()
        self._result_available = True
        self.destroy()

    def _cancel(self) -> None:
        self._submitted_values = {}
        self._result_available = False
        self.destroy()

    def show_modal(self) -> Dict[str, Any]:
        self.grab_set()
        self.mainloop()
        if not self._result_available:
            raise FormCancelled()
        return getattr(self, "_submitted_values", {})


def _build_message_root() -> tk.Tk:
    root = tk.Tk()
    root.withdraw()
    root.configure(bg=PALETTE["background"])
    root.attributes("-topmost", True)
    icon_image = icon_for_tk(None, size=32)
    if icon_image:
        root.iconphoto(True, icon_image)
    return root


def show_form(form_config: Dict[str, Any]) -> Dict[str, Any]:
    """Display a modal form and return the submitted values."""

    window = FormWindow(form_config.get("title", "Genius"), form_config)
    return window.show_modal()


def show_message(title: str, message: str) -> None:
    """Show a simple informational dialog."""

    root = _build_message_root()
    messagebox.showinfo(title, message, parent=root)
    root.destroy()


def ask_confirmation(title: str, message: str) -> bool:
    """Ask the user to confirm an action."""

    root = _build_message_root()
    result = messagebox.askyesno(title, message, parent=root)
    root.destroy()
    return result

