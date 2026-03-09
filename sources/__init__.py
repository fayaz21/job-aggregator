"""
sources/__init__.py — source adapter registry.

Each entry maps a source name to its fetch_jobs(keyword, max_results) function.
The agent iterates over SOURCES at runtime and calls only the sources listed in
ENABLED_SOURCES (config.py). To add a new source: create sources/mysource.py
with a fetch_jobs() function that returns a list of normalised job dicts, then
add it here.

Normalised job dict schema:
  title     (str)        job title
  company   (str)        company name
  location  (str|None)   location string or None
  url       (str)        unique job URL — used as the dedup key in the DB
  job_type  (str|None)   "full_time" | "part_time" | "contract" | None
  posted_at (str|None)   ISO date string "YYYY-MM-DD" or None
"""

from sources import glassdoor, greenhouse, indeed, remotive, weworkremotely

SOURCES = {
    "remotive":       remotive.fetch_jobs,
    "greenhouse":     greenhouse.fetch_jobs,
    "indeed":         indeed.fetch_jobs,
    "glassdoor":      glassdoor.fetch_jobs,
    "weworkremotely": weworkremotely.fetch_jobs,
}
