# job-board-ranker

A small Python tool that reads companies' **official public job-board APIs** (Greenhouse, Lever and Ashby),
keeps only internship-type roles, and ranks them with plain rules and a stated reason for every point.

I built the first version for my own internship search (the full personal version reads 58 company boards
every morning). This repository is a clean, standalone extract: rules only, no model calls, no personal data.

## What it does

- Fetches each company's published JSON feed. No login, scraping or browser automation.
- Normalizes the three platforms into one `Posting` shape (title, location, remote, URL, date).
- Drops senior and non-internship titles, then scores topics (AI, data, Python, research...), remote roles
  and places you prefer. Every score comes with its reasons.
- Stores what it has seen in SQLite so each run shows only new postings.
- A board that disappears is logged and skipped; it never stops the run.

## Run it

```bash
pip install -r requirements.txt
python -m job_board_ranker boards.example.json --place "Los Angeles" --place "Irvine"
```

`boards.json` is a list of `{"source": "greenhouse|lever|ashby", "token": "<the company's board id>", "company": "Name"}`.
Use `--all` to show everything instead of only new postings.

## Test it

```bash
pip install -r requirements-dev.txt
python -m pytest
```

The tests are offline: the HTTP getter is injected, so no test touches the network.

## Limits (honest)

- Ranking is keyword rules, not understanding of the job. It is a first filter for a human, not a verdict.
- Greenhouse list responses omit descriptions, so topic matching on Greenhouse relies on the title unless you
  call `fetch_description` for shortlisted jobs.
- Board ids change; check a company's own careers page if a board stops answering.

## License

MIT
