"""Generate a multi-resolution Windows icon for the Genius installer."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Iterable, Sequence

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from genius.icon import build_icon

DEFAULT_SIZES: Sequence[int] = (256, 128, 64, 48, 32, 24, 16)


def create_icon_frames(label: str, sizes: Iterable[int]):
    """Return Pillow images for each requested size using the Genius glyph."""

    for size in sizes:
        yield build_icon(size=size, label=label)


def write_ico(output: Path, label: str, sizes: Sequence[int]) -> Path:
    output.parent.mkdir(parents=True, exist_ok=True)
    frames = list(create_icon_frames(label, sizes))
    base = frames[0]
    base.save(output, format="ICO", sizes=[(size, size) for size in sizes])
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate the Genius icon bundle")
    parser.add_argument("--output", type=Path, required=True, help="Destination .ico file")
    parser.add_argument("--label", default="G", help="Optional glyph label to render")
    parser.add_argument(
        "--sizes",
        type=int,
        nargs="*",
        default=list(DEFAULT_SIZES),
        help="Icon sizes to embed (largest first)",
    )
    args = parser.parse_args()

    write_ico(args.output, args.label, args.sizes)


if __name__ == "__main__":  # pragma: no cover
    main()
