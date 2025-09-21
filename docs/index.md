# LargeLanguageModel News Hub

Welcome! This project fetches daily headlines from a curated list of RSS feeds and now offers a
hands-free listening experience.

## Install dependencies

```bash
pip install -r requirements.txt
```

## Generate the daily report

Run the fetcher to download the latest headlines into the `news/` directory:

```bash
python news_fetcher.py --no-email --no-commit
```

Remove `--no-email` or `--no-commit` if you have configured SMTP credentials and want the script to
handle delivery and git history automatically.

## Listen to the news

Use the companion helper to flatten the newest Markdown report and read it out loud:

```bash
python news_reader.py
```

Key features:

- Launches `news_fetcher.py` (email and git commits are off by default for safety).
- Detects the freshest Markdown report in the `news/` folder.
- Converts Markdown to plain sentences while skipping code blocks.
- Uses the operating system's built-in speech engine through `pyttsx3`, so it works offline on
  Windows, macOS, and Linux.

Add the `--no-speech` flag to print the summary without audio, `--voice` to hint at a different
voice, or `--rate` to control narration speed. Any extra unknown options are forwarded directly to
`news_fetcher.py`.

## Text-to-speech rationale

We compared several approaches before settling on `pyttsx3`:

- **Cloud TTS APIs** deliver great quality but require credentials, ongoing internet access, and
  often add cost.
- **Browser speech synthesis** is friendly for web apps yet awkward to trigger from command line
  automation and unavailable on server-only machines.
- **Native OS speech engines** are bundled with most desktops. `pyttsx3` talks to those engines
  behind a single Python API, giving the broadest reach without extra services.

This makes the listening workflow simple to set up across the widest range of devices.
