"""Icon utilities for the Genius tray application."""
from __future__ import annotations

from pathlib import Path
from typing import Iterable, List, Optional

from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps


PALETTE = {
    "outer": "#0f172a",
    "inner_start": "#4f46e5",
    "inner_end": "#06b6d4",
    "glyph": "#f8fafc",
    "glow": (99, 102, 241, 120),
}


def _create_gradient_disc(size: int) -> Image.Image:
    gradient = Image.linear_gradient("L").rotate(45, expand=True)
    gradient = gradient.resize((size * 2, size * 2), Image.LANCZOS)
    gradient = gradient.crop((size // 2, size // 2, size // 2 + size, size // 2 + size))
    colored = ImageOps.colorize(gradient, PALETTE["inner_start"], PALETTE["inner_end"]).convert("RGBA")

    mask = Image.new("L", (size, size), 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.ellipse((0, 0, size - 1, size - 1), fill=255)

    disc = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    disc.paste(colored, mask=mask)
    return disc


def _add_glyph(image: Image.Image, label: str) -> Image.Image:
    draw = ImageDraw.Draw(image)
    size = image.width
    try:
        font = ImageFont.truetype("segoeui.ttf", int(size * 0.48))
    except Exception:  # pragma: no cover - fallback when font unavailable
        font = ImageFont.load_default()
    text_width, text_height = draw.textsize(label, font=font)
    x = (size - text_width) / 2
    y = (size - text_height) / 2 - size * 0.02
    draw.text((x, y), label, fill=PALETTE["glyph"], font=font)
    return image


def build_icon(size: int = 128, label: str = "G") -> Image.Image:
    """Generate a modern circular icon with soft glow and glyph."""

    base = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    disc = _create_gradient_disc(size - 8)

    shadow = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    shadow_draw = ImageDraw.Draw(shadow)
    shadow_draw.ellipse((8, 8, size - 1, size - 1), fill=PALETTE["glow"])
    shadow = shadow.filter(ImageFilter.GaussianBlur(radius=6))

    base.alpha_composite(shadow)
    base.alpha_composite(disc, dest=(4, 4))

    draw = ImageDraw.Draw(base)
    draw.ellipse((6, 6, size - 7, size - 7), outline=(255, 255, 255, 40), width=2)

    return _add_glyph(base, label.upper())


def load_icon(path: Optional[Path], size: int = 128) -> Image.Image:
    """Load an icon from disk or build the default Genius glyph."""

    if path:
        candidate = Path(path).expanduser()
        if candidate.exists():
            with Image.open(candidate) as handle:
                icon = handle.convert("RGBA")
            if size:
                icon = icon.resize((size, size), Image.LANCZOS)
            return icon
    return build_icon(size=size)


def icon_variants(path: Optional[Path], sizes: Iterable[int]) -> List[Image.Image]:
    """Return resized icon variants suitable for Windows multi-resolution trays."""

    images: List[Image.Image] = []
    for icon_size in sizes:
        images.append(load_icon(path, size=icon_size))
    return images


def icon_for_tk(path: Optional[Path], size: int = 48):
    """Return a ``PhotoImage`` instance for tkinter windows."""

    try:
        from PIL import ImageTk
    except Exception:  # pragma: no cover - pillow without tkinter bindings
        return None

    image = load_icon(path, size=size)
    return ImageTk.PhotoImage(image)
