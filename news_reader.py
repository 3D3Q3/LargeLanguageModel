#!/usr/bin/env python3
"""Run the news fetcher, flatten the latest report, and read it aloud."""

from __future__ import annotations

import argparse
import re
import shlex
import subprocess
import sys
import time
from pathlib import Path
from typing import Iterable, Sequence, Set


def run_fetcher(
    *,
    fetcher_path: Path,
    python_executable: str,
    allow_email: bool,
    allow_commit: bool,
    extra_args: Sequence[str],
) -> None:
    """Invoke ``news_fetcher.py`` with sane defaults."""

    cmd = [python_executable, str(fetcher_path)]
    if not allow_email:
        cmd.append("--no-email")
    if not allow_commit:
        cmd.append("--no-commit")
    cmd.extend(extra_args)

    pretty = " ".join(shlex.quote(part) for part in cmd)
    print(f"Running news_fetcher.py via: {pretty}")
    subprocess.run(cmd, check=True)


def _list_reports(output_dir: Path) -> Sequence[Path]:
    return sorted(output_dir.glob("*.md"), key=lambda p: p.stat().st_mtime)


def find_latest_report(
    output_dir: Path,
    existing_reports: Set[Path],
    *,
    wait_seconds: float = 5.0,
) -> Path:
    """Return the newly created report or the freshest report available."""

    deadline = time.time() + wait_seconds
    last_seen: Sequence[Path] = []
    output_dir.mkdir(parents=True, exist_ok=True)

    while time.time() <= deadline:
        reports = _list_reports(output_dir)
        if reports:
            last_seen = reports
            new_reports = [p for p in reports if p.resolve() not in existing_reports]
            if new_reports:
                latest = max(new_reports, key=lambda p: p.stat().st_mtime)
                print(f"Found newly generated report: {latest}")
                return latest
        time.sleep(0.2)

    if last_seen:
        latest = max(last_seen, key=lambda p: p.stat().st_mtime)
        print(
            "No brand new report detected; falling back to the freshest existing file "
            f"({latest})."
        )
        return latest

    raise FileNotFoundError(
        f"No Markdown reports were found in {output_dir}. Did the fetcher run correctly?"
    )


HEADING_PATTERN = re.compile(r"^#{1,6}\s*")
LINK_PATTERN = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
INLINE_CODE_PATTERN = re.compile(r"`([^`]*)`")


def markdown_to_speech_text(markdown: str) -> str:
    """Strip Markdown syntax and code blocks to make narration friendlier."""

    lines: list[str] = []
    in_code_block = False

    for raw_line in markdown.splitlines():
        stripped = raw_line.strip()
        if stripped.startswith("```"):
            in_code_block = not in_code_block
            continue
        if in_code_block:
            continue

        if not stripped:
            lines.append("")
            continue

        if stripped.startswith("#"):
            heading_text = HEADING_PATTERN.sub("", stripped).strip()
            if raw_line.startswith("##"):
                lines.append(f"{heading_text}:")
            else:
                lines.append(heading_text)
            continue

        working = raw_line.strip()
        if working.startswith(("- ", "* ", "+ ")):
            working = working[2:]

        working = LINK_PATTERN.sub(r"\1", working)
        working = INLINE_CODE_PATTERN.sub(r"\1", working)
        working = working.replace("**", "")
        working = working.replace("__", "")
        working = working.replace("\u2013", "-")
        working = working.replace("\u2014", "-")
        working = re.sub(r"\s+", " ", working).strip()
        if working:
            lines.append(working)

    compact: list[str] = []
    last_blank = False
    for line in lines:
        if not line:
            if not last_blank:
                compact.append("")
            last_blank = True
        else:
            compact.append(line)
            last_blank = False

    return "\n".join(compact).strip()


def speak_text(text: str, *, voice: str | None = None, rate: int | None = None) -> bool:
    try:
        import pyttsx3
    except ImportError:
        print(
            "pyttsx3 is not installed. Install it with 'pip install pyttsx3' to enable speech."
        )
        return False

    try:
        engine = pyttsx3.init()
    except Exception as exc:  # pragma: no cover - defensive
        print(f"Unable to initialise text-to-speech engine: {exc}")
        return False

    if rate is not None:
        engine.setProperty("rate", rate)

    if voice:
        voice_lower = voice.lower()
        selected = None
        for candidate in engine.getProperty("voices"):
            if voice_lower in candidate.name.lower() or voice_lower in candidate.id.lower():
                selected = candidate.id
                break
        if selected:
            engine.setProperty("voice", selected)
        else:
            print(f"Requested voice '{voice}' was not found. Using the default voice instead.")

    paragraphs = [segment.strip() for segment in text.split("\n\n") if segment.strip()]
    for chunk in paragraphs:
        engine.say(chunk)
    try:
        engine.runAndWait()
    except Exception as exc:  # pragma: no cover - defensive
        print(f"The speech engine failed while speaking: {exc}")
        return False

    return True


def load_existing_reports(paths: Iterable[Path]) -> Set[Path]:
    return {p.resolve() for p in paths}


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Fetch the latest news report, flatten it for narration, and optionally read it aloud."
        ),
    )
    parser.add_argument(
        "--fetcher-path",
        default="news_fetcher.py",
        help="Path to the news_fetcher.py script (default: news_fetcher.py).",
    )
    parser.add_argument(
        "--output-dir",
        default="news",
        help="Directory where the news reports are stored (default: news).",
    )
    parser.add_argument(
        "--python",
        dest="python_executable",
        default=sys.executable,
        help="Python interpreter used to run news_fetcher.py (default: current interpreter).",
    )
    parser.add_argument(
        "--allow-email",
        action="store_true",
        help="Allow the fetcher to send email (disabled by default).",
    )
    parser.add_argument(
        "--allow-commit",
        action="store_true",
        help="Allow the fetcher to commit to git (disabled by default).",
    )
    parser.add_argument(
        "--no-speech",
        action="store_true",
        help="Skip the text-to-speech step and only print the flattened report.",
    )
    parser.add_argument(
        "--voice",
        help="Optional voice hint passed to pyttsx3 (substring match).",
    )
    parser.add_argument(
        "--rate",
        type=int,
        help="Optional speech rate to use when speaking (words per minute).",
    )

    args, extra_fetcher_args = parser.parse_known_args(argv)

    fetcher_path = Path(args.fetcher_path)
    output_dir = Path(args.output_dir)

    existing_reports = load_existing_reports(output_dir.glob("*.md")) if output_dir.exists() else set()

    try:
        run_fetcher(
            fetcher_path=fetcher_path,
            python_executable=args.python_executable,
            allow_email=args.allow_email,
            allow_commit=args.allow_commit,
            extra_args=extra_fetcher_args,
        )
    except subprocess.CalledProcessError as exc:
        print(f"news_fetcher.py exited with a non-zero status: {exc.returncode}")
        return exc.returncode

    try:
        report_path = find_latest_report(output_dir, existing_reports)
    except FileNotFoundError as exc:
        print(exc)
        return 1

    print(f"Preparing report from {report_path}")
    report_text = report_path.read_text(encoding="utf-8")
    flattened = markdown_to_speech_text(report_text)

    if not flattened:
        print("The report appears to be empty after formatting.")
        return 0

    print("\n===== Daily News Summary =====\n")
    print(flattened)
    print("\n==============================\n")

    if args.no_speech:
        return 0

    success = speak_text(flattened, voice=args.voice, rate=args.rate)
    if success:
        print("Finished reading the report aloud.")
        return 0

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
