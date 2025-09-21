"""Utilities to keep the Genius application lightweight."""
from __future__ import annotations

import gc
import threading
from dataclasses import dataclass


@dataclass
class MemoryManager:
    """Periodically trigger garbage collection to maintain a small footprint."""

    interval_seconds: int = 120
    _thread: threading.Thread | None = None
    _stop_event: threading.Event | None = None

    def start(self) -> None:
        if self._thread is not None:
            return
        self._stop_event = threading.Event()
        self._thread = threading.Thread(target=self._run, name="GeniusMemory", daemon=True)
        self._thread.start()

    def _run(self) -> None:
        assert self._stop_event is not None
        while not self._stop_event.is_set():
            if self._stop_event.wait(self.interval_seconds):
                break
            gc.collect()

    def stop(self) -> None:
        if self._thread is None or self._stop_event is None:
            return
        self._stop_event.set()
        self._thread.join(timeout=2)
        self._thread = None
        self._stop_event = None
