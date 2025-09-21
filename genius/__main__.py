"""Entry point for running Genius as a module."""
from __future__ import annotations

import argparse
from pathlib import Path

from .tray import main


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Launch the Genius automation assistant")
    parser.add_argument("--config", type=Path, help="Optional path to a configuration file", default=None)
    return parser.parse_args()


def run() -> None:
    args = parse_args()
    main(str(args.config) if args.config else None)


if __name__ == "__main__":  # pragma: no cover
    run()
