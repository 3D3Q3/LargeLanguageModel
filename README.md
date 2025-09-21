# LargeLanguageModel

Spot for ChatGPT to connect

## Daily News Aggregator

`news_fetcher.py` collects news from several RSS feeds and saves a daily report in Markdown.

### Listen to the report

Run `news_reader.py` to fetch the latest headlines and hear them read aloud. The helper script

1. runs `news_fetcher.py` (email and git commits are disabled by default),
2. finds the freshest Markdown report in the `news/` folder,
3. converts the Markdown into listener-friendly text, and
4. uses the operating system's speech engine (via [`pyttsx3`](https://pyttsx3.readthedocs.io/en/latest/)) to narrate the report.

#### Text-to-speech research notes

We compared three approaches to narration:

* **Cloud APIs** (e.g., Azure, AWS, Google): excellent voices but require API keys, working
  internet connections, and often incur cost, making automation harder for most setups.
* **Browser speech synthesis**: convenient on the web, yet difficult to trigger from a Python
  script and unavailable on headless or server environments.
* **Local/native speech engines**: present on all major desktop operating systems. The
  `pyttsx3` package offers a single Python interface that delegates to SAPI5 (Windows), NSSpeech
  Synthesizer (macOS), and eSpeak/ESpeak NG (Linux), so it works offline on the widest range of
  devices without additional services.

Given those trade-offs, `pyttsx3` was selected for its offline operation, permissive license, and
support for multiple platforms with a single dependency.

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
By default the script saves a file under `news/` named with today's date and commits it to git. Remove `--no-email` or `--no-commit` to enable those features.

Listen to the newest report (speak it aloud by default):
```bash
python news_reader.py
```
Pass `--no-speech` if you only want the flattened text in the terminal. Use `--voice` or `--rate`
to adjust the narrator, and forward any extra flags to `news_fetcher.py` after the script's own
options.

### Scheduling

To fetch news daily at 3 PM using cron:
```cron
0 15 * * * /usr/bin/python /path/to/news_fetcher.py
```
Adjust the path and options as needed. This will generate the report, commit it to the repository, and email a copy if configured.
