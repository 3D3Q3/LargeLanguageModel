"""Optional speech automation for Genius."""
from __future__ import annotations

import logging
import threading
from dataclasses import dataclass, field
from typing import Callable, Dict, Optional

from .config import VoiceConfig

try:  # pragma: no cover - optional dependency
    import speech_recognition as sr
except ImportError:  # pragma: no cover - optional dependency
    sr = None  # type: ignore

try:  # pragma: no cover - optional dependency
    import keyboard  # type: ignore
except ImportError:  # pragma: no cover - optional dependency
    keyboard = None  # type: ignore


logger = logging.getLogger(__name__)


@dataclass
class VoiceCommandProcessor:
    """Listen for a hotkey and use speech to trigger automation tasks."""

    config: VoiceConfig
    commands: Dict[str, Callable[[], None]] = field(default_factory=dict)
    on_transcription: Optional[Callable[[str], None]] = None

    _thread: threading.Thread | None = None
    _stop_event: threading.Event | None = None

    def start(self) -> None:
        if not self.config.enabled:
            logger.info("Voice automation disabled in configuration")
            return
        if sr is None or keyboard is None:
            logger.warning(
                "Voice automation requested but dependencies are missing. Install "
                "speech_recognition, keyboard, and PyAudio on Windows."
            )
            return
        if self._thread is not None:
            return
        self._stop_event = threading.Event()
        self._thread = threading.Thread(target=self._run, name="GeniusVoice", daemon=True)
        self._thread.start()
        logger.info("Voice command processor started")

    def stop(self) -> None:
        if self._stop_event is None or self._thread is None:
            return
        self._stop_event.set()
        if keyboard is not None:
            try:
                keyboard.press_and_release("esc")
            except Exception:  # pragma: no cover - best effort cleanup
                pass
        self._thread.join(timeout=2)
        self._thread = None
        self._stop_event = None
        logger.info("Voice command processor stopped")

    def set_commands(self, mapping: Dict[str, Callable[[], None]]) -> None:
        self.commands = mapping

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _run(self) -> None:  # pragma: no cover - interactive loop
        assert self._stop_event is not None
        recognizer = sr.Recognizer()
        microphone = sr.Microphone()
        hotkey = self.config.hotkey or "ctrl+alt+g"
        wake_phrase = (self.config.wake_phrase or "").lower().strip()

        while not self._stop_event.is_set():
            try:
                keyboard.wait(hotkey)
            except Exception as exc:
                logger.error("Keyboard listener error: %s", exc)
                break
            if self._stop_event.is_set():
                break
            text = self._capture_speech(recognizer, microphone)
            if not text:
                continue
            logger.debug("Transcribed voice command: %s", text)
            if self.on_transcription is not None:
                self.on_transcription(text)
            processed = text.lower().strip()
            if wake_phrase and processed.startswith(wake_phrase):
                processed = processed[len(wake_phrase) :].strip()
            self._dispatch(processed)

    def _capture_speech(self, recognizer: "sr.Recognizer", microphone: "sr.Microphone") -> str:
        try:
            with microphone as source:
                recognizer.adjust_for_ambient_noise(source, duration=0.3)
                audio = recognizer.listen(source, timeout=5)
            return recognizer.recognize_google(audio)
        except Exception as exc:
            logger.error("Failed to transcribe speech: %s", exc)
            return ""

    def _dispatch(self, transcript: str) -> None:
        if not transcript:
            return
        for trigger, callback in self.commands.items():
            if transcript.startswith(trigger.lower()):
                try:
                    callback()
                except Exception as exc:  # pragma: no cover - defensive
                    logger.exception("Voice command handler failed: %s", exc)
                return
        logger.info("No voice command registered for: %s", transcript)
