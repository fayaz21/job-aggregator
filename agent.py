"""
agent.py — background job-fetching agent.

Orchestrates the full fetch cycle:
  1. Iterates over every enabled source (SOURCES filtered by ENABLED_SOURCES).
  2. For each source × keyword combination, calls fetch_jobs().
  3. Optionally filters results by title keywords (TITLE_FILTER_KEYWORDS).
  4. Saves new jobs to SQLite, skipping duplicates via URL uniqueness constraint.
  5. Sleeps for RUN_INTERVAL_MINUTES, then repeats indefinitely.

Entry points:
  - `python agent.py`      — run standalone (local dev / manual trigger)
  - `agent.start_worker()` — called in a daemon thread by app.py in production
"""

import time

from config import ENABLED_SOURCES, KEYWORDS, MAX_RESULTS_PER_KEYWORD, RUN_INTERVAL_MINUTES, TITLE_FILTER_KEYWORDS
from db import get_connection, init_db, save_job
from sources import SOURCES


def title_matches(job, filters):
    """Return True if the job title contains any of the filter keywords.
    If filters is empty, all jobs pass through."""
    if not filters:
        return True
    title = job.get("title", "").lower()
    return any(f in title for f in filters)


def run():
    """Execute one full fetch cycle across all active sources and keywords."""
    init_db()
    conn = get_connection()
    total_new = 0

    # Respect ENABLED_SOURCES; if empty, all sources are active.
    active = {k: v for k, v in SOURCES.items() if not ENABLED_SOURCES or k in ENABLED_SOURCES}
    print(f"[agent] Active sources: {list(active.keys())}")

    for source_name, fetch_jobs in active.items():
        for keyword in KEYWORDS:
            print(f"\n[agent] [{source_name}] Searching: '{keyword}'")
            jobs = fetch_jobs(keyword, max_results=MAX_RESULTS_PER_KEYWORD)
            new = 0

            for job in jobs:
                if not title_matches(job, TITLE_FILTER_KEYWORDS):
                    print(f"  ~ filtered out: {job['title']}")
                    continue
                saved = save_job(conn, job, keyword, source=source_name)
                if saved:
                    new += 1
                    print(f"  NEW JOB FOUND")
                    print(f"  Title:   {job['title']}")
                    print(f"  Company: {job['company']}")
                    print(f"  Source:  {source_name}")
                    print(f"  URL:     {job['url']}")
                    print(f"  {'-'*40}")
                else:
                    # URL already in DB — UNIQUE constraint prevented insert.
                    print(f"  ~ skipped (duplicate): {job['url']}")

            print(f"  {new} new job(s) saved for '{keyword}' via {source_name}")
        total_new += new

    conn.commit()
    conn.close()
    print(f"\n[agent] Done. {total_new} total new job(s) saved.")


def start_worker():
    """Run the agent loop continuously. Intended to be called in a background thread."""
    print(f"[agent] Starting. Will run every {RUN_INTERVAL_MINUTES} minute(s).\n")
    while True:
        try:
            run()
            print(f"[agent] Sleeping for {RUN_INTERVAL_MINUTES} minute(s)...")
            time.sleep(RUN_INTERVAL_MINUTES * 60)
        except KeyboardInterrupt:
            print("\n[agent] Stopped by user.")
            break


if __name__ == "__main__":
    start_worker()
