import argparse
import os
import subprocess
from datetime import datetime
from email.mime.text import MIMEText
import smtplib
from pathlib import Path

import feedparser

# RSS feed configuration: section -> (url, limit)
FEEDS = {
    "World News": {"url": "https://feeds.bbci.co.uk/news/world/rss.xml", "limit": 5},
    "Australian News": {"url": "https://www.abc.net.au/news/feed/51120/rss.xml", "limit": 5},
    "Tucson News": {"url": "https://www.kold.com/arc/outboundfeeds/rss/category/news/?outputType=xml", "limit": 10},
    "Physics News": {"url": "https://phys.org/rss-feed/physics-news/", "limit": 5},
    "Science News": {"url": "https://www.sciencedaily.com/rss/top/science.xml", "limit": 5},
    "Biology News": {"url": "https://phys.org/rss-feed/biology-news/", "limit": 5},
    "AI News": {"url": "https://techcrunch.com/tag/artificial-intelligence/feed/", "limit": 5},
    "Technology News": {"url": "https://feeds.arstechnica.com/arstechnica/technology-lab", "limit": 5},
}


def fetch_feed(url: str, limit: int):
    """Return list of entries from an RSS feed."""
    parsed = feedparser.parse(url)
    entries = []
    for entry in parsed.entries[:limit]:
        title = entry.get("title", "No title")
        link = entry.get("link", "")
        published = entry.get("published", "")
        entries.append({"title": title, "link": link, "published": published})
    return entries


def build_report() -> str:
    date_str = datetime.now().strftime("%Y-%m-%d")
    lines = [f"# Daily News Report - {date_str}", ""]
    for section, cfg in FEEDS.items():
        lines.append(f"## {section}")
        items = fetch_feed(cfg["url"], cfg["limit"])
        if not items:
            lines.append("No news available.\n")
            continue
        for item in items:
            lines.append(f"- [{item['title']}]({item['link']}) - {item['published']}")
        lines.append("")
    return "\n".join(lines)


def save_report(content: str, output_dir: str) -> Path:
    date_str = datetime.now().strftime("%Y-%m-%d")
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    file_path = out_path / f"{date_str}.md"
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
    return file_path


def send_email(subject: str, content: str) -> None:
    """Send email using environment configuration."""
    smtp_server = os.environ.get("SMTP_SERVER")
    smtp_port = int(os.environ.get("SMTP_PORT", "587"))
    email_from = os.environ.get("EMAIL_FROM")
    email_to = os.environ.get("EMAIL_TO")
    password = os.environ.get("EMAIL_PASSWORD")
    if not all([smtp_server, email_from, email_to, password]):
        print("Email credentials not fully provided; skipping email.")
        return
    msg = MIMEText(content, "plain", "utf-8")
    msg["Subject"] = subject
    msg["From"] = email_from
    msg["To"] = email_to
    with smtplib.SMTP(smtp_server, smtp_port) as server:
        server.starttls()
        server.login(email_from, password)
        server.sendmail(email_from, [email_to], msg.as_string())


def git_commit(file_path: Path, message: str) -> None:
    subprocess.run(["git", "add", str(file_path)], check=True)
    subprocess.run(["git", "commit", "-m", message], check=True)


def main():
    parser = argparse.ArgumentParser(description="Fetch daily news and store as markdown.")
    parser.add_argument("--output-dir", default="news", help="Directory to store news files")
    parser.add_argument("--no-email", action="store_true", help="Do not send email")
    parser.add_argument("--no-commit", action="store_true", help="Do not commit to git")
    args = parser.parse_args()

    report = build_report()
    file_path = save_report(report, args.output_dir)

    if not args.no_email:
        send_email("Daily News Report", report)

    if not args.no_commit:
        commit_message = f"Add daily news report for {datetime.now().date()}"
        git_commit(file_path, commit_message)

    print(f"News report saved to {file_path}")


if __name__ == "__main__":
    main()
