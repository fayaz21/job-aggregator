"""
config.py — centralised settings loaded from environment variables.

All values can be overridden via environment variables (Render dashboard, etc.)
or a local .env file for development. Sensible defaults are provided so the
app works out of the box without any configuration.
"""

import os
from dotenv import load_dotenv

# Load .env for local development. No-op if the file is absent (e.g. on Render).
load_dotenv()

# Comma-separated job search terms the agent will query across all sources.
KEYWORDS = [k.strip() for k in os.getenv("KEYWORDS", "python, backend, engineer").split(",")]

# Path to the SQLite database file.
DB_PATH = os.getenv("DB_PATH", "jobs.db")

# Maximum jobs to collect per keyword per company (Greenhouse) or per source run.
MAX_RESULTS_PER_KEYWORD = int(os.getenv("MAX_RESULTS_PER_KEYWORD", "10"))

# Comma-separated list of source names to activate. Empty string = all sources.
# Example: "remotive,greenhouse"
_enabled = os.getenv("ENABLED_SOURCES", "")
ENABLED_SOURCES = [s.strip() for s in _enabled.split(",") if s.strip()]

# Optional inclusion filter on job titles. Jobs whose titles do NOT contain any
# of these keywords will be dropped before saving. Empty = no filtering (recommended).
# Example: "engineer, developer, backend"
_title_filter = os.getenv("TITLE_FILTER_KEYWORDS", "")
TITLE_FILTER_KEYWORDS = [k.strip().lower() for k in _title_filter.split(",") if k.strip()]

# How many minutes the agent sleeps between fetch cycles.
RUN_INTERVAL_MINUTES = int(os.getenv("RUN_INTERVAL_MINUTES", "5"))
