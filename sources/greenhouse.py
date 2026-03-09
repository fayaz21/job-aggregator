"""
sources/greenhouse.py — Greenhouse job board adapter.

Uses Greenhouse's public JSON API (no auth required) to fetch open roles from
a curated list of tech companies. Each company board is queried independently
using its Greenhouse slug (e.g. "stripe", "anthropic").

Fetch strategy: traverse ALL companies and collect up to max_results matches
per company. This prevents large companies (e.g. Stripe with 500+ jobs) from
dominating results and ensures diversity across the company list.
Companies that do not use Greenhouse return 404 and are skipped silently.

The company list can be overridden via GREENHOUSE_COMPANIES in the environment.
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

GREENHOUSE_API = "https://boards-api.greenhouse.io/v1/boards/{slug}/jobs"

# Default company list — all confirmed Greenhouse boards.
# Override via .env: GREENHOUSE_COMPANIES=stripe,figma,notion
DEFAULT_COMPANIES = [
    # Payments / fintech
    "stripe", "brex", "chime", "affirm", "gusto", "carta",
    "mercury", "robinhood", "coinbase", "tripactions",
    # AI / ML
    "anthropic", "databricks",
    # Dev tools / data infra
    "netlify", "postman", "vercel",
    # Design / productivity
    "figma", "airtable",
    # Enterprise SaaS / HR
    "lattice", "remote",
    # Consumer / marketplace
    "duolingo", "discord", "lyft", "dropbox", "faire", "checkr",
    # Misc high-signal
    "intercom",
]

def _get_companies():
    raw = os.getenv("GREENHOUSE_COMPANIES", "")
    if raw.strip():
        return [c.strip() for c in raw.split(",") if c.strip()]
    return DEFAULT_COMPANIES


def _fetch_company_jobs(slug):
    """Fetch all open jobs for one Greenhouse company board."""
    try:
        r = requests.get(
            GREENHOUSE_API.format(slug=slug),
            timeout=10,
        )
        r.raise_for_status()
        return r.json().get("jobs", [])
    except requests.RequestException as e:
        print(f"[greenhouse] Error fetching '{slug}': {e}")
        return []


def _normalize(job):
    posted = job.get("first_published") or job.get("updated_at") or ""
    # Trim to date only: '2026-02-13T12:39:30-05:00' → '2026-02-13'
    if posted and "T" in posted:
        posted = posted.split("T")[0]
    return {
        "title": job.get("title") or "",
        "company": job.get("company_name") or "",
        "location": (job.get("location") or {}).get("name") or None,
        "url": job.get("absolute_url") or None,
        "job_type": None,   # Greenhouse does not expose job type
        "posted_at": posted or None,
    }


def fetch_jobs(keyword, max_results=10):
    """Fetch jobs from all Greenhouse company boards, filtered by keyword in title.

    Traverses every company in the list. Collects up to max_results matches
    per company so no single company dominates the results.
    """
    companies = _get_companies()
    keyword_lower = keyword.lower()
    results = []

    for slug in companies:
        per_company = 0
        raw_jobs = _fetch_company_jobs(slug)
        for job in raw_jobs:
            if keyword_lower in job.get("title", "").lower():
                results.append(_normalize(job))
                per_company += 1
                if per_company >= max_results:
                    break

    return results


if __name__ == "__main__":
    import json
    print("Companies:", _get_companies())
    print()
    results = fetch_jobs("engineer", max_results=10)
    print(f"Found {len(results)} jobs\n")
    for job in results:
        print(json.dumps(job, indent=2))
