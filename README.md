# LargeLanguageModel

Spot for ChatGPT to connect

## Daily News Aggregator

`news_fetcher.py` collects news from several RSS feeds and saves a daily report in Markdown.

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

### Scheduling

To fetch news daily at 3 PM using cron:
```cron
0 15 * * * /usr/bin/python /path/to/news_fetcher.py
```
Adjust the path and options as needed. This will generate the report, commit it to the repository, and email a copy if configured.
