"""Windows startup integration utilities."""
from __future__ import annotations

import logging
import os
import sys
from pathlib import Path
from typing import Optional


logger = logging.getLogger(__name__)


STARTUP_FILE = "Genius-startup.bat"


def _startup_directory() -> Path:
    appdata = os.environ.get("APPDATA")
    if not appdata:
        raise RuntimeError("APPDATA environment variable is not available")
    return Path(appdata) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"


def register_startup(python_executable: Optional[Path] = None) -> Path:
    """Register the application to run at logon."""

    if os.name != "nt":  # pragma: no cover - Windows specific
        raise RuntimeError("Startup registration only supported on Windows")

    startup_dir = _startup_directory()
    startup_dir.mkdir(parents=True, exist_ok=True)
    python_executable = Path(python_executable or sys.executable)
    command = f"@echo off\nstart \"\" \"{python_executable}\" -m genius\n"
    startup_file = startup_dir / STARTUP_FILE
    startup_file.write_text(command, encoding="utf-8")
    logger.info("Genius registered to start with Windows: %s", startup_file)
    return startup_file


def remove_startup() -> None:
    if os.name != "nt":  # pragma: no cover - Windows specific
        raise RuntimeError("Startup registration only supported on Windows")
    startup_file = _startup_directory() / STARTUP_FILE
    if startup_file.exists():
        startup_file.unlink()
        logger.info("Removed Genius startup registration")


def is_registered() -> bool:
    if os.name != "nt":  # pragma: no cover - Windows specific
        return False
    return (_startup_directory() / STARTUP_FILE).exists()
