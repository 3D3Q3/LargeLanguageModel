"""Configuration models and loader for the Genius tray application."""
from __future__ import annotations

import random
import secrets
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml


CONFIG_FILE_NAME = "genius_config.yaml"
DEFAULT_CONFIG_PATH = Path.home() / ".genius" / CONFIG_FILE_NAME


@dataclass
class TaskConfig:
    """Configuration for a single task that can be invoked from the menu."""

    name: str
    type: str
    description: str | None = None
    command: Optional[str] = None
    args: Dict[str, Any] = field(default_factory=dict)
    form: Optional[Dict[str, Any]] = None
    confirmation: Optional[str] = None


@dataclass
class MenuItemConfig:
    """Represents an item in the taskbar menu."""

    title: str | None = None
    task: Optional[str] = None
    submenu: List["MenuItemConfig"] = field(default_factory=list)
    separator: bool = False


@dataclass
class VoiceConfig:
    """Voice automation configuration."""

    enabled: bool = False
    hotkey: str = "ctrl+alt+g"
    wake_phrase: Optional[str] = None
    profile: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DatabaseConfig:
    """Database configuration."""

    path: Path = Path.home() / ".genius" / "genius.db"


@dataclass
class LLMConfig:
    """Configuration for connecting to local and remote language models."""

    enable_ollama: bool = False
    ollama_url: str = "http://localhost:11434"
    enable_openai: bool = False
    openai_model: str = "gpt-4o-mini"
    openai_api_key_env: str = "OPENAI_API_KEY"


@dataclass
class Config:
    """Root configuration model for the Genius app."""

    author: str
    application_name: str
    tasks: Dict[str, TaskConfig]
    menu: List[MenuItemConfig]
    icon: Optional[Path] = None
    voice: VoiceConfig = field(default_factory=VoiceConfig)
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    llm: LLMConfig = field(default_factory=LLMConfig)


class ConfigError(RuntimeError):
    """Raised when the configuration file is invalid."""


def _coerce_menu(data: List[Dict[str, Any]]) -> List[MenuItemConfig]:
    menu_items: List[MenuItemConfig] = []
    for entry in data:
        if entry.get("separator"):
            menu_items.append(MenuItemConfig(separator=True))
            continue
        submenu = entry.get("submenu") or []
        menu_items.append(
            MenuItemConfig(
                title=entry.get("title"),
                task=entry.get("task"),
                submenu=_coerce_menu(submenu) if submenu else [],
                separator=False,
            )
        )
    return menu_items


def _coerce_tasks(data: Dict[str, Dict[str, Any]]) -> Dict[str, TaskConfig]:
    tasks: Dict[str, TaskConfig] = {}
    for name, value in data.items():
        tasks[name] = TaskConfig(
            name=name,
            type=value["type"],
            description=value.get("description"),
            command=value.get("command"),
            args=value.get("args", {}),
            form=value.get("form"),
            confirmation=value.get("confirmation"),
        )
    return tasks


def load_config(config_path: Optional[Path] = None) -> Config:
    """Load configuration from disk or provide defaults.

    Parameters
    ----------
    config_path:
        Optional explicit path to a configuration file. When not provided the
        function will look for the application specific configuration in the
        user's profile directory. When no configuration exists a default one is
        generated and stored.
    """

    resolved_path = config_path
    if resolved_path is None:
        resolved_path = DEFAULT_CONFIG_PATH
    resolved_path = Path(resolved_path)

    if not resolved_path.exists():
        resolved_path.parent.mkdir(parents=True, exist_ok=True)
        resolved_path.write_text(_default_config_text())

    with resolved_path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)

    if not data:
        raise ConfigError("Configuration file is empty or malformed")

    tasks = _coerce_tasks(data.get("tasks", {}))
    if not tasks:
        raise ConfigError("No tasks configured")

    menu_data = data.get("menu")
    if not isinstance(menu_data, list):
        raise ConfigError("Menu must be a list")

    icon_value = data.get("icon")
    icon_path = Path(icon_value).expanduser() if icon_value else None

    return Config(
        author=data.get("author", "Unknown"),
        application_name=data.get("application_name", "Genius"),
        tasks=tasks,
        menu=_coerce_menu(menu_data),
        icon=icon_path,
        voice=VoiceConfig(**(data.get("voice") or {})),
        database=DatabaseConfig(**(data.get("database") or {})),
        llm=LLMConfig(**(data.get("llm") or {})),
    )


def _default_config_text() -> str:
    """Provide the default configuration shipped with the repository."""

    pipeline_id = f"run-{secrets.token_hex(2).upper()}"
    azure_primary = f"SUB-{secrets.token_hex(4).upper()}"
    azure_secondary = f"SUB-{secrets.token_hex(3).upper()}"
    slot_name = f"slot-{random.randint(10, 99)}"
    ftp_password = secrets.token_urlsafe(6)
    reminder_id = secrets.token_hex(4).upper()
    ssh_host = f"automation-{random.randint(100, 999)}.cloud.example.com"
    generated_on = datetime.now().strftime("%Y-%m-%d %H:%M")

    return f"""
# Genius default configuration
# Generated automatically if no configuration exists.
author: "Don-Quixote De La Mancha 2025 3LL3 LLC"
application_name: "Genius"
# icon: "C:/Path/To/custom.ico"  # Optional custom tray icon

tasks:
  open_docs:
    type: open_url
    description: "Read the product documentation"
    command: "https://example.com/docs"

  launch_shell:
    type: run_shell
    description: "Open a customized shell prompt"
    command: "powershell.exe"

  run_pipeline:
    type: run_pipeline
    description: "Execute the daily data pipeline"
    command: "C:/Automation/run_pipeline.ps1 -RunId {pipeline_id}"
    confirmation: "Run the daily data pipeline now?"
    args:
      cwd: "C:/Automation"

  ssh_cloud:
    type: run_ssh
    description: "Connect to the cloud automation host"
    args:
      hostname: "{ssh_host}"
      username: "admin"
      command: "./deploy_latest.sh --run {pipeline_id}"

  ftp_publish:
    type: run_ftp
    description: "Publish the latest website bundle"
    args:
      host: "ftp.example.com"
      username: "web"
      password: "{ftp_password}"
      actions:
        - type: upload
          local: "C:/Automation/site.zip"
          remote: "public_html/site.zip"

  voice_capture:
    type: voice_listener
    description: "Enable the hotkey voice automation listener"

  ollama_query:
    type: llm_query
    description: "Ask the local Ollama model a question"
    args:
      provider: "ollama"
      prompt: "Summarize today's reminders"

  open_notes:
    type: open_file
    description: "View the reminders and notes"
    command: "C:/Automation/notes.md"

  azure_release:
    type: form_command
    description: "Promote a build to Azure App Service"
    command: "powershell.exe -File C:/Automation/release.ps1 -Subscription {{subscription}} -Slot {{slot}} -Build {{build_tag}} -Notes \"{{release_notes}}\""
    form:
      title: "Azure Release"
      description: "Sample data has been generated automatically. Adjust values before submission."
      submit_label: "Deploy"
      fields:
        - name: subscription
          label: "Subscription"
          type: choice
          options: ["{azure_primary}", "{azure_secondary}"]
          generate: "choice"
        - name: slot
          label: "Deployment slot"
          default: "{slot_name}"
          helper: "Choose the staging slot to warm before swapping to production."
        - name: build_tag
          label: "Build tag"
          generate: "build"
        - name: release_notes
          label: "Release notes"
          type: multiline
          default: "Deployment drafted on {generated_on}."

  remind_myself:
    type: show_info
    description: "Display a generated reminder stub"
    args:
      message: "Reminder {reminder_id}: Check telemetry dashboards after deployments."

  quit:
    type: quit
    description: "Quit the Genius assistant"

menu:
  - title: "Launch Shell"
    task: "launch_shell"
  - title: "Daily Data Pipeline"
    task: "run_pipeline"
  - separator: true
  - title: "Resources"
    submenu:
      - title: "Documentation"
        task: "open_docs"
      - title: "Notes"
        task: "open_notes"
      - title: "Reminder"
        task: "remind_myself"
  - title: "Cloud"
    submenu:
      - title: "Automation Host"
        task: "ssh_cloud"
      - title: "FTP Publish"
        task: "ftp_publish"
      - title: "Azure Release"
        task: "azure_release"
  - title: "Voice Automations"
    task: "voice_capture"
  - title: "Ask Ollama"
    task: "ollama_query"
  - separator: true
  - title: "Quit"
    task: "quit"

  voice:
    enabled: false
    hotkey: "ctrl+alt+g"
    wake_phrase: "hey genius"
    profile: {{}}

llm:
  enable_ollama: true
  ollama_url: "http://localhost:11434"
  enable_openai: false
  openai_model: "gpt-4o-mini"
  openai_api_key_env: "OPENAI_API_KEY"
"""
