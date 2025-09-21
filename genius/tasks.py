"""Task execution layer for the Genius application."""
from __future__ import annotations

import json
import logging
import os
import subprocess
import sys
import webbrowser
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, Optional

from .config import Config, TaskConfig
from .database import DatabaseManager
from .forms import FormCancelled, ask_confirmation, show_form, show_message
from .llm import LLMClient
from .notifications import NotificationManager
from .voice import VoiceCommandProcessor

try:  # pragma: no cover - optional dependency
    import paramiko  # type: ignore
except ImportError:  # pragma: no cover - optional dependency
    paramiko = None  # type: ignore

from ftplib import FTP

logger = logging.getLogger(__name__)


@dataclass
class TaskContext:
    config: Config
    database: DatabaseManager
    notification_manager: NotificationManager
    llm_client: LLMClient
    voice_processor: Optional[VoiceCommandProcessor] = None
    invoke_task: Optional[Callable[[str], None]] = None


class TaskRegistry:
    def __init__(self) -> None:
        self._handlers: Dict[str, Callable[[TaskConfig, TaskContext], None]] = {}

    def register(self, task_type: str) -> Callable[[Callable[[TaskConfig, TaskContext], None]], Callable[[TaskConfig, TaskContext], None]]:
        def decorator(func: Callable[[TaskConfig, TaskContext], None]) -> Callable[[TaskConfig, TaskContext], None]:
            self._handlers[task_type] = func
            return func

        return decorator

    def execute(self, task: TaskConfig, context: TaskContext) -> None:
        handler = self._handlers.get(task.type)
        if handler is None:
            raise RuntimeError(f"No handler registered for task type {task.type}")
        handler(task, context)


registry = TaskRegistry()


# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------

def _log_action(context: TaskContext, task: TaskConfig, payload: Optional[Dict[str, Any]] = None) -> None:
    try:
        serialized = json.dumps(payload) if payload else None
        context.database.log_action(task.name, serialized)
    except Exception:  # pragma: no cover - defensive logging
        logger.exception("Unable to persist audit log entry")


def _run_subprocess(command: str, cwd: Optional[str] = None) -> None:
    creationflags = 0
    if os.name == "nt":
        creationflags = subprocess.CREATE_NEW_CONSOLE  # type: ignore[attr-defined]
    subprocess.Popen(command, cwd=cwd, shell=True, creationflags=creationflags)  # noqa: S603,S607


def _format_command(task: TaskConfig, values: Optional[Dict[str, Any]] = None) -> str:
    command = task.command or task.args.get("command")
    if not command:
        raise RuntimeError(f"Task {task.name} is missing a command")
    if values:
        try:
            command = command.format(**values)
        except KeyError as exc:
            raise RuntimeError(f"Missing placeholder {exc} for task {task.name}") from exc
    return command


def _confirm_if_needed(task: TaskConfig) -> bool:
    if task.confirmation:
        return ask_confirmation("Genius", task.confirmation)
    return True


def _notify(context: TaskContext, title: str, message: str) -> None:
    context.notification_manager.show(title, message)


# ---------------------------------------------------------------------------
# Task handlers
# ---------------------------------------------------------------------------


@registry.register("open_url")
def _handle_open_url(task: TaskConfig, context: TaskContext) -> None:
    command = _format_command(task)
    webbrowser.open(command)
    _log_action(context, task, {"url": command})
    _notify(context, "Genius", f"Opening {command}")


@registry.register("open_file")
def _handle_open_file(task: TaskConfig, context: TaskContext) -> None:
    target = _format_command(task)
    path = Path(target)
    try:
        if os.name == "nt":
            os.startfile(target)  # type: ignore[attr-defined]
        else:  # pragma: no cover - Windows specific
            if path.is_dir():
                subprocess.Popen(["xdg-open", target])  # noqa: S603,S607
            else:
                subprocess.Popen(["xdg-open", str(path)])  # noqa: S603,S607
    except Exception as exc:
        logger.exception("Failed to open file: %s", exc)
        raise
    _log_action(context, task, {"path": target})


@registry.register("run_shell")
def _handle_run_shell(task: TaskConfig, context: TaskContext) -> None:
    if not _confirm_if_needed(task):
        return
    command = _format_command(task)
    _run_subprocess(command)
    _log_action(context, task, {"command": command})
    _notify(context, "Genius", f"Running {command}")


@registry.register("run_powershell")
def _handle_run_powershell(task: TaskConfig, context: TaskContext) -> None:
    if not _confirm_if_needed(task):
        return
    script = _format_command(task)
    command = f"powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File \"{script}\""
    _run_subprocess(command)
    _log_action(context, task, {"script": script})
    _notify(context, "Genius", f"Running PowerShell script {script}")


@registry.register("run_pipeline")
def _handle_run_pipeline(task: TaskConfig, context: TaskContext) -> None:
    if not _confirm_if_needed(task):
        return
    command = _format_command(task)
    working_dir = task.args.get("cwd")
    _run_subprocess(command, cwd=working_dir)
    _log_action(context, task, {"command": command, "cwd": working_dir})
    _notify(context, "Genius", "Pipeline execution triggered")


@registry.register("run_python")
def _handle_run_python(task: TaskConfig, context: TaskContext) -> None:
    if not _confirm_if_needed(task):
        return
    script_path = _format_command(task)
    subprocess.Popen([sys.executable, script_path])  # noqa: S603,S607
    _log_action(context, task, {"script": script_path})


@registry.register("form_command")
def _handle_form_command(task: TaskConfig, context: TaskContext) -> None:
    if not task.form:
        raise RuntimeError(f"Task {task.name} defines no form configuration")
    try:
        values = show_form(task.form)
    except FormCancelled:
        logger.info("Form cancelled for task %s", task.name)
        return
    command = _format_command(task, values)
    _run_subprocess(command)
    _log_action(context, task, {"command": command, "values": values})
    _notify(context, "Genius", f"Executing {task.name}")


@registry.register("show_info")
def _handle_show_info(task: TaskConfig, context: TaskContext) -> None:
    message = task.args.get("message") or task.description or task.command or ""
    show_message(task.name, message)
    _log_action(context, task, {"message": message})


@registry.register("run_ssh")
def _handle_run_ssh(task: TaskConfig, context: TaskContext) -> None:
    if paramiko is None:
        raise RuntimeError("paramiko is required for SSH tasks")
    args = task.args
    hostname = args.get("hostname")
    username = args.get("username")
    password = args.get("password")
    key_file = args.get("key_file")
    command = args.get("command") or task.command
    if not hostname or not username or not command:
        raise RuntimeError("SSH task requires hostname, username, and command")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname=hostname, username=username, password=password, key_filename=key_file)
    stdin, stdout, stderr = client.exec_command(command)
    output = stdout.read().decode("utf-8")
    error = stderr.read().decode("utf-8")
    client.close()
    payload = {"hostname": hostname, "command": command, "output": output, "error": error}
    _log_action(context, task, payload)
    if error:
        _notify(context, "Genius", f"SSH command completed with errors for {hostname}")
    else:
        _notify(context, "Genius", f"SSH command completed for {hostname}")


@registry.register("run_ftp")
def _handle_run_ftp(task: TaskConfig, context: TaskContext) -> None:
    args = task.args
    host = args.get("host")
    username = args.get("username")
    password = args.get("password")
    actions = args.get("actions", [])
    if not host or not username or not password:
        raise RuntimeError("FTP task requires host, username, and password")
    ftp = FTP(host)
    ftp.login(user=username, passwd=password)
    for action in actions:
        kind = action.get("type")
        if kind == "upload":
            local_path = Path(action["local"])
            remote_path = action.get("remote", local_path.name)
            with local_path.open("rb") as handle:
                ftp.storbinary(f"STOR {remote_path}", handle)
        elif kind == "download":
            remote_path = action["remote"]
            local_path = Path(action.get("local", remote_path))
            with local_path.open("wb") as handle:
                ftp.retrbinary(f"RETR {remote_path}", handle.write)
    ftp.quit()
    _log_action(context, task, {"host": host, "actions": actions})
    _notify(context, "Genius", f"FTP actions completed for {host}")


@registry.register("voice_listener")
def _handle_voice_listener(task: TaskConfig, context: TaskContext) -> None:
    processor = context.voice_processor
    if processor is None:
        raise RuntimeError("Voice automation is not configured")
    mapping: Dict[str, Callable[[], None]] = {}
    for entry in task.args.get("commands", []):
        phrase = entry.get("phrase")
        target_task = entry.get("task")
        if not phrase or not target_task:
            continue
        if context.invoke_task is None:
            continue
        def _callback(target: str = target_task) -> None:
            assert context.invoke_task is not None
            context.invoke_task(target)

        mapping[phrase.lower()] = _callback
    processor.set_commands(mapping)
    processor.start()
    _log_action(context, task, {"commands": list(mapping.keys())})
    _notify(context, "Genius", "Voice listener armed")


@registry.register("llm_query")
def _handle_llm_query(task: TaskConfig, context: TaskContext) -> None:
    provider = task.args.get("provider", "ollama")
    prompt = task.args.get("prompt") or task.command
    if not prompt:
        raise RuntimeError("LLM query task requires a prompt")
    response = context.llm_client.query(provider, prompt, **task.args)
    show_message(f"LLM response ({provider})", response)
    _log_action(context, task, {"provider": provider, "prompt": prompt, "response": response})


@registry.register("quit")
def _handle_quit(task: TaskConfig, context: TaskContext) -> None:
    if context.invoke_task is None:
        raise RuntimeError("Quit task requires application callback")
    context.invoke_task("__quit__")
