# JobRadar

**A self-updating job discovery dashboard for software engineers.**

JobRadar continuously fetches job listings from multiple sources, deduplicates them, stores them in a local database, and surfaces them through a clean web UI with filtering and pagination — all from a single deployable service.

---

## Problem

Finding engineering jobs requires checking multiple job boards, applying inconsistent keyword searches across each one, and manually filtering out noise. There is no single place to see relevant roles across curated sources in one view.

JobRadar solves this by running a background agent that fetches, normalises, and stores jobs from multiple sources on a configurable schedule, then exposing them through a searchable dashboard.

---

## Key Features

- Multi-source job ingestion (Remotive, Greenhouse, Indeed, We Work Remotely)
- Background agent that runs on a configurable interval with no external scheduler needed
- Keyword, source, job type, and posting-date filters in the UI
- Deduplication by job URL — no repeated listings across runs
- Single deployable service — web app and background agent run in the same process
- Fully configurable via environment variables

---

## Architecture Overview

```
┌─────────────────────────────────────────────────┐
│                  Web Process                     │
│                                                  │
│  ┌─────────────┐        ┌──────────────────────┐ │
│  │  Flask App  │        │   Agent Thread       │ │
│  │  (app.py)   │        │   (agent.py)         │ │
│  │             │        │                      │ │
│  │  GET /      │        │  every N minutes:    │ │
│  │  GET /jobs  │        │  sources → filter    │ │
│  │  GET /health│        │         → SQLite     │ │
│  └──────┬──────┘        └──────────┬───────────┘ │
│         │                          │              │
│         └──────────┬───────────────┘              │
│                    │                              │
│             ┌──────▼──────┐                       │
│             │  SQLite DB  │                       │
│             │  (jobs.db)  │                       │
│             └─────────────┘                       │
└─────────────────────────────────────────────────┘
```

The Flask web server and the background agent share a single process and a single SQLite file. No message queue, no separate worker service, no external database required.

---

## System Design

### Single-process architecture

On startup, `app.py` initialises the database schema, then launches `agent.start_worker()` in a Python daemon thread. The thread runs the fetch cycle, sleeps, and repeats indefinitely. When the web process exits, the thread exits with it automatically.

This design avoids the complexity of a separate worker service and works within SQLite's single-file model. The trade-off is that job fetching and web serving share the same process resources.

### Deduplication

Every job URL is stored with a `UNIQUE` constraint in SQLite. `save_job()` uses `INSERT` and catches `IntegrityError` silently — no explicit duplicate check needed. This means the agent can run repeatedly without creating duplicate rows.

### Normalised schema

All source adapters return jobs in the same dict shape:

```python
{
    "title":     str,
    "company":   str,
    "location":  str | None,
    "url":       str,          # unique key
    "job_type":  str | None,   # "full_time" | "part_time" | "contract" | None
    "posted_at": str | None,   # "YYYY-MM-DD"
}
```

This lets the agent, database layer, and UI remain source-agnostic.

---

## Source Adapters

| Source | Status | Method |
|---|---|---|
| **Remotive** | Active | Public REST API, no auth |
| **Greenhouse** | Active | Public JSON API per company board |
| **Indeed** | Registered | `python-jobspy` scraper |
| **We Work Remotely** | Registered | RSS feed via `feedparser` |
| **Glassdoor** | Stub | Placeholder, returns `[]` |

**Remotive** (`sources/remotive.py`) — queries `remotive.com/api/remote-jobs` with a keyword parameter. Returns jobs across all categories.

**Greenhouse** (`sources/greenhouse.py`) — queries the public Greenhouse board API for each company in a curated list of 25 tech companies. Uses a per-company result cap so no single company dominates. Companies that don't use Greenhouse 404 silently and are skipped. The company list is configurable via `GREENHOUSE_COMPANIES`.

**Indeed** (`sources/indeed.py`) — uses `python-jobspy` to scrape Indeed. Fetches only jobs posted in the last 72 hours. May be blocked in some regions or network environments.

**We Work Remotely** (`sources/weworkremotely.py`) — parses the WWR public RSS feed. Suitable for remote-only roles.

**Glassdoor** (`sources/glassdoor.py`) — stub returning an empty list. Exists in the registry so it can be enabled without changing application code once implemented.

### Adding a new source

1. Create `sources/mysource.py` with a `fetch_jobs(keyword, max_results)` function that returns a list of normalised job dicts.
2. Add it to the `SOURCES` dict in `sources/__init__.py`.
3. Add its name to `ENABLED_SOURCES` in your environment.

---

## Project Structure

```
jobradar/
├── app.py              # Flask web app — routes, startup, agent thread
├── agent.py            # Background fetch agent — loop, filter, save
├── config.py           # All settings from environment variables
├── db.py               # SQLite connection, schema init, save_job()
├── export_jobs.py      # Read layer — filtered queries for the UI and API
├── view_jobs.py        # Terminal viewer for quick local inspection
├── requirements.txt
│
├── sources/
│   ├── __init__.py     # SOURCES registry — maps names to fetch functions
│   ├── remotive.py     # Remotive REST API adapter
│   ├── greenhouse.py   # Greenhouse board API adapter (25 companies)
│   ├── indeed.py       # Indeed scraper via python-jobspy
│   ├── weworkremotely.py # We Work Remotely RSS adapter
│   └── glassdoor.py    # Glassdoor stub (not yet implemented)
│
└── templates/
    └── index.html      # Single-page UI — filters, table, pagination
```

---

## Local Development Setup

**Requirements:** Python 3.11+

```bash
# 1. Clone the repository
git clone <repo-url>
cd jobradar

# 2. Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Create a .env file (copy the example below)

# 5. Run the web app
python app.py
```

The app starts at `http://localhost:5000`. The background agent begins fetching immediately and runs every `RUN_INTERVAL_MINUTES` minutes.

To run the agent standalone without the web server:

```bash
python agent.py
```

To inspect the database from the terminal:

```bash
python view_jobs.py
```

---

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `KEYWORDS` | `python, backend, engineer` | Comma-separated job search terms |
| `ENABLED_SOURCES` | *(empty = all)* | Comma-separated source names to activate |
| `MAX_RESULTS_PER_KEYWORD` | `10` | Max jobs per keyword per company (Greenhouse) or per source run |
| `RUN_INTERVAL_MINUTES` | `5` | Minutes between agent fetch cycles |
| `DB_PATH` | `jobs.db` | Path to the SQLite database file |
| `TITLE_FILTER_KEYWORDS` | *(empty = no filter)* | Optional inclusion filter on job titles |
| `GREENHOUSE_COMPANIES` | *(built-in list of 25)* | Override Greenhouse company slugs |

### Example `.env` for local development

```env
KEYWORDS=python, backend, engineer
ENABLED_SOURCES=remotive,greenhouse
MAX_RESULTS_PER_KEYWORD=10
RUN_INTERVAL_MINUTES=5
DB_PATH=jobs.db
TITLE_FILTER_KEYWORDS=
```

---

## Deployment on Render

JobRadar deploys as a single **Web Service** on Render. The background agent runs inside the web process as a daemon thread — no separate worker service needed.

### Service configuration

| Field | Value |
|---|---|
| Runtime | Python 3 |
| Build Command | `pip install -r requirements.txt` |
| Start Command | `gunicorn --workers 1 app:app` |

`--workers 1` is required. Multiple gunicorn workers would each spawn their own agent thread, causing redundant fetches and concurrent SQLite writes.

### Environment variables (set in Render dashboard)

| Key | Recommended value |
|---|---|
| `KEYWORDS` | `python, backend, engineer` |
| `ENABLED_SOURCES` | `remotive,greenhouse` |
| `MAX_RESULTS_PER_KEYWORD` | `10` |
| `RUN_INTERVAL_MINUTES` | `5` |
| `DB_PATH` | `jobs.db` |
| `TITLE_FILTER_KEYWORDS` | *(leave blank)* |

### SQLite persistence note

Render's free tier uses an ephemeral filesystem. The `jobs.db` file is wiped on each new deploy. The agent repopulates the database within the first fetch cycle after restart. For persistent storage across deploys, attach a Render Disk and set `DB_PATH` to the disk mount path (e.g. `/data/jobs.db`).

### Verify deployment

```
https://your-app.onrender.com/health
```

Expected response:

```json
{
  "status": "ok",
  "total_jobs": 300,
  "enabled_sources": ["remotive", "greenhouse"],
  "keywords": ["python", "backend", "engineer"]
}
```

---

## How the Background Agent Works

1. **Startup** — `init_db()` creates the `jobs` table if it doesn't exist (idempotent).
2. **Source selection** — the agent checks `ENABLED_SOURCES` and builds the active source map. If `ENABLED_SOURCES` is empty, all registered sources run.
3. **Fetch loop** — for each `source × keyword` pair, `fetch_jobs(keyword, max_results)` is called. Each adapter handles its own HTTP requests, parsing, and normalisation.
4. **Title filter** — if `TITLE_FILTER_KEYWORDS` is set, jobs whose titles don't contain any of the keywords are dropped before saving. If the list is empty, all jobs pass through.
5. **Save** — `save_job()` attempts an `INSERT`. The `UNIQUE` constraint on `url` causes a silent `IntegrityError` for duplicates, which returns `False` without raising.
6. **Sleep** — after committing, the agent sleeps for `RUN_INTERVAL_MINUTES` minutes and repeats.

---

## Future Improvements

- **Persistent storage** — migrate from SQLite to PostgreSQL for multi-instance deployments and data durability across deploys
- **Glassdoor adapter** — complete the stub once a stable scraping method is confirmed
- **Email / Slack alerts** — notify on new matching jobs rather than requiring manual checks
- **Relevance scoring** — rank jobs by keyword match quality, recency, and company signal
- **User-defined searches** — allow per-user keyword and source configuration
- **Deduplication across sources** — detect the same role posted on multiple boards
- **Cron-based scheduling** — replace the sleep loop with a proper cron trigger for more reliable intervals
