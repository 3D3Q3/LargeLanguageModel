"""System tray application bootstrap for Genius."""
from __future__ import annotations

import logging
import threading
from pathlib import Path
from typing import Iterable, List, Optional

import pystray
from pystray import Menu, MenuItem

from .config import MenuItemConfig, TaskConfig, load_config
from .database import DatabaseManager
from .icon import load_icon
from .llm import LLMClient
from .memory import MemoryManager
from .notifications import NotificationManager
from .tasks import TaskContext, registry
from .voice import VoiceCommandProcessor

logger = logging.getLogger(__name__)


class GeniusApp:
    """Main entry point for the Genius tray experience."""

    def __init__(self, config_path: Optional[Path] = None) -> None:
        self.config = load_config(config_path)
        if "quit" not in self.config.tasks:
            self.config.tasks["quit"] = TaskConfig(name="quit", type="quit", description="Quit Genius")

        self.database = DatabaseManager(self.config.database.path)
        self.notification_manager = NotificationManager()
        self.llm_client = LLMClient(self.config.llm)
        self.voice_processor = VoiceCommandProcessor(self.config.voice)
        self.memory_manager = MemoryManager()
        self.memory_manager.start()

        self.context = TaskContext(
            config=self.config,
            database=self.database,
            notification_manager=self.notification_manager,
            llm_client=self.llm_client,
            voice_processor=self.voice_processor,
            invoke_task=self.execute_task,
        )

        self._icon: Optional[pystray.Icon] = None
        self._icon_thread: Optional[threading.Thread] = None
        self._stopping = False

    # ------------------------------------------------------------------
    # Menu construction
    # ------------------------------------------------------------------
    def _build_menu(self, items: Iterable[MenuItemConfig]) -> List[pystray.MenuItem]:
        menu_items: List[pystray.MenuItem] = []
        for item in items:
            if item.separator:
                menu_items.append(Menu.SEPARATOR)
                continue
            if item.submenu:
                submenu = Menu(*self._build_menu(item.submenu))
                menu_items.append(MenuItem(item.title or "", submenu=submenu))
                continue
            if not item.task:
                continue
            menu_items.append(MenuItem(item.title or item.task, self._build_callback(item.task)))
        return menu_items

    def _build_callback(self, task_name: str):
        def _callback(icon, item) -> None:  # pragma: no cover - GUI callback
            self.execute_task(task_name)

        return _callback

    # ------------------------------------------------------------------
    # Task execution routing
    # ------------------------------------------------------------------
    def execute_task(self, task_name: str) -> None:
        if task_name == "__quit__":
            self.quit()
            return
        task = self.config.tasks.get(task_name)
        if task is None:
            # Allow referencing built in quit task by name even if not configured explicitly
            if task_name == "quit":
                task = TaskConfig(name="quit", type="quit", description="Quit Genius")
            else:
                logger.warning("Unknown task requested: %s", task_name)
                self.notification_manager.show("Genius", f"Unknown task {task_name}")
                return
        try:
            self.context.invoke_task = self.execute_task
            registry.execute(task, self.context)
        except Exception as exc:
            logger.exception("Task %s failed", task_name)
            self.notification_manager.show("Genius error", str(exc))

    # ------------------------------------------------------------------
    # Icon management
    # ------------------------------------------------------------------
    def run(self) -> None:
        image = load_icon(self.config.icon)
        menu = Menu(*self._build_menu(self.config.menu))
        title = f"{self.config.application_name} - {self.config.author}"
        self._icon = pystray.Icon(self.config.application_name, image=image, title=title, menu=menu)
        logger.info("Starting Genius tray icon")
        try:
            self._icon.run()
        finally:
            self.quit()

    def run_detached(self) -> None:
        if self._icon is not None:
            raise RuntimeError("Icon already running")

        def _worker() -> None:
            self.run()

        self._icon_thread = threading.Thread(target=_worker, name="GeniusTray", daemon=True)
        self._icon_thread.start()

    def quit(self) -> None:
        if self._stopping:
            return
        self._stopping = True
        logger.info("Stopping Genius")
        if self.voice_processor:
            self.voice_processor.stop()
        self.memory_manager.stop()
        self.database.close()
        if self._icon is not None:
            try:
                self._icon.stop()
            except Exception:  # pragma: no cover - defensive
                pass
            self._icon.visible = False
            self._icon = None
        if self._icon_thread and self._icon_thread.is_alive():
            self._icon_thread.join(timeout=2)


def main(config_path: Optional[str] = None) -> None:
    logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(levelname)s %(name)s: %(message)s")
    app = GeniusApp(Path(config_path) if config_path else None)
    app.run()


if __name__ == "__main__":  # pragma: no cover
    main()
