# LargeLanguageModel

Spot for ChatGPT to connect

## Genius Windows Automation Assistant

`genius/` contains a Windows 11 system tray companion named **Genius** by
**Don-Quixote De La Mancha 2025 3LL3 LLC**. Genius keeps frequently used
automation entry points a right-click away and provides a lightweight control
hub for links, scripts, pipelines, reminders, LLM assistance, and more.

### Highlights

- System tray menu driven by YAML configuration with nested sections.
- Launch PowerShell, CMD, Python, SSH, FTP, and custom data-pipeline routines.
- Open shortcuts, bookmarks, documentation, and rich forms that collect user
  input before triggering commands.
- Fluent-inspired modal forms with Windows 11 titlebar styling, accent
  colouring, and automatic random seed data for placeholders.
- Built-in SQLite logging for audits and reminder storage.
- Optional toast notifications for successes and reminders.
- Voice hotkey listener that can transcribe commands into task executions.
- Integrations for local Ollama models and OpenAI's Chat Completions API.
- Helper utilities for Windows start-up registration, resource management, and
  graceful shutdown.
- High fidelity tray icon with gradient glyph rendering and optional overrides
  via configuration.

### Installation

#### Quick installer build for Windows 11

The `installer/` directory contains an automated pipeline that bundles Genius
and its dependencies into a single Windows setup executable using PyInstaller
and Inno Setup.

1. On a Windows 11 workstation install:
   - [Python 3.11+](https://www.python.org/downloads/windows/)
   - [Inno Setup 6.2+](https://jrsoftware.org/isinfo.php) (adds `iscc.exe` to your `PATH`)
2. Open an elevated PowerShell prompt inside the repository and run:
   ```powershell
   Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
   .\installer\build_installer.ps1 -Version 1.0.0
   ```
   The script creates an isolated virtual environment, installs Genius
   requirements, renders the tray icon, compiles a standalone `Genius.exe`, and
   then calls Inno Setup to emit `installer\dist\installer\GeniusSetup-1.0.0.exe`.
   Use `-SkipInstaller` if you only need the portable PyInstaller build or
   `-ReuseGlobalPython` to avoid creating a virtual environment.
3. Run the generated installer. It copies Genius into `Program Files`, seeds a
   starter configuration at `%APPDATA%\Genius\genius_config.yaml`, and registers
   optional Start Menu/desktop/start-up shortcuts.

#### Manual Python installation

1. Install the core dependencies (from an elevated PowerShell prompt if
   installing system-wide):
   ```powershell
   pip install -r requirements.txt
   ```
2. (Optional) To enable speech commands install the additional packages:
   ```powershell
   pip install speechrecognition keyboard pyaudio
   ```
   > `pyaudio` can also be installed via [PyAudio wheel builds](https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio)
   > if the standard installation fails.
3. (Optional) For OpenAI access export an API key:
   ```powershell
   setx OPENAI_API_KEY "sk-..."
   ```

### Configuration

The app loads its configuration from `~/.genius/genius_config.yaml`. The first
launch automatically writes a starter template if the file does not exist,
populated with randomised identifiers so workflows run immediately. A more
feature-rich example lives at [`genius_config.yaml`](./genius_config.yaml).

Each task entry defines a `type` and optional `command`, `args`, `form`, and
`confirmation` message. Menu items refer to task names. For example:

```yaml
tasks:
  run_pipeline:
    type: run_pipeline
    command: "C:/Automation/pipeline.ps1"
    confirmation: "Execute the nightly pipeline now?"
    args:
      cwd: "C:/Automation"

menu:
  - title: "Data"
    submenu:
      - title: "Nightly Pipeline"
        task: "run_pipeline"
```

Supported task types include `open_url`, `open_file`, `run_shell`,
`run_powershell`, `run_pipeline`, `run_python`, `form_command`, `run_ssh`,
`run_ftp`, `show_info`, `voice_listener`, `llm_query`, and `quit`.

Forms can specify a `generate` helper to seed placeholder data automatically.
Available generators are `token`, `uuid`, `timestamp`, `build`, and `choice`
(randomly selects from the provided options). The top-level config accepts an
optional `icon` path to override the generated gradient glyph.

### Visual polish & interaction quality

- Form dialogs are themed with a dark fluent palette and fluent-inspired
  Windows 11 titlebars. Accent buttons highlight primary actions and helper
  text wraps neatly under fields.
- Multi-line inputs receive custom colours, and the default icon is rendered at
  high resolution with gradient shading, inner glow, and text glyph centering.
- Informational message boxes now include the Genius glyph and stay on top of
  busy desktops, making quick notifications easier to spot.

### Running Genius

Launch the tray application with:

```powershell
python -m genius --config genius_config.yaml  # optional custom path
```

The icon appears in the Windows notification area. Right-click to reveal the
configured actions. Selecting **Quit** stops the background services, voice
processor, and closes the SQLite connection quickly. A helper in
`genius.startup` can register a simple batch file in the Windows Start-up
folder so Genius starts automatically at logon:

```python
from genius import startup
startup.register_startup()
```

### Data and Notifications

Genius stores action history and reminders in `~/.genius/genius.db`. Toast
notifications (via `win10toast`) are used when available; otherwise events are
logged to the Python logger. The included `NotificationManager` and
`DatabaseManager` modules can be extended to support organization-specific
pipelines or messaging systems.

### Voice Automations

Voice automation is optional. When enabled, a global hotkey (default
`Ctrl+Alt+G`) activates speech capture. Utterances beginning with the configured
wake phrase map to task names defined under `voice_listener.args.commands`.

### LLM Access

The `llm_query` task type routes prompts to either a local Ollama model or the
OpenAI Chat Completions API. Configure providers in the `llm` section of the
YAML file. Responses appear in a simple dialog and are logged to the database
for traceability.

### Inspiration & acknowledgements

- The Windows titlebar customisation routine is adapted from the
  [QueryLab/KumaTray](https://github.com/querylab/kumatray) project (MIT
  License), which provided a solid reference for immersive dark mode tweaks on
  modern Windows builds.

## Daily News Aggregator

`news_fetcher.py` collects news from several RSS feeds and saves a daily report
in Markdown.

### Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. (Optional) Configure environment variables for email delivery:
   - `SMTP_SERVER`
   - `SMTP_PORT` (default: 587)
   - `EMAIL_FROM`
   - `EMAIL_TO`
   - `EMAIL_PASSWORD`

### Usage

Generate the report without emailing or committing:
```bash
python news_fetcher.py --no-email --no-commit
```
By default the script saves a file under `news/` named with today's date and
commits it to git. Remove `--no-email` or `--no-commit` to enable those
features.

### Scheduling

To fetch news daily at 3 PM using cron:
```cron
0 15 * * * /usr/bin/python /path/to/news_fetcher.py
```
Adjust the path and options as needed. This will generate the report, commit it
to the repository, and email a copy if configured.
