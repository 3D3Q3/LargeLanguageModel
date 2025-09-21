"""Notification helpers for Windows 11."""
from __future__ import annotations

import logging
from typing import Optional

try:
    from win10toast import ToastNotifier
except ImportError:  # pragma: no cover - optional dependency on Windows
    ToastNotifier = None  # type: ignore


class NotificationManager:
    """Provide desktop notifications with graceful degradation."""

    def __init__(self) -> None:
        self._toast: Optional[ToastNotifier] = None
        if ToastNotifier is not None:
            try:
                self._toast = ToastNotifier()
            except Exception as exc:  # pragma: no cover - defensive
                logging.getLogger(__name__).warning(
                    "Unable to initialize toast notifications: %s", exc
                )

    def show(self, title: str, message: str, duration: int = 5) -> None:
        if self._toast is not None:
            try:
                self._toast.show_toast(title, message, duration=duration, threaded=True)
                return
            except Exception as exc:  # pragma: no cover - defensive
                logging.getLogger(__name__).error(
                    "Failed to display toast notification: %s", exc
                )
        logging.getLogger(__name__).info("Notification: %s - %s", title, message)
