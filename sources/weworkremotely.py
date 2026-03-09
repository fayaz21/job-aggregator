import feedparser
from datetime import datetime

WWR_RSS_URL = "https://weworkremotely.com/remote-jobs.rss"

JOB_TYPE_MAP = {
    "full-time": "full_time",
    "part-time": "part_time",
    "contract": "contract",
    "freelance": "contract",
}


def _parse_title(raw_title):
    """Split 'Company: Job Title' into (company, title)."""
    if ": " in raw_title:
        company, title = raw_title.split(": ", 1)
        return company.strip(), title.strip()
    return "", raw_title.strip()


def _normalize_job_type(raw_type):
    return JOB_TYPE_MAP.get((raw_type or "").lower(), (raw_type or "").lower() or None)


def _parse_date(published_parsed):
    if not published_parsed:
        return None
    try:
        return datetime(*published_parsed[:6]).strftime("%Y-%m-%d")
    except Exception:
        return None


def fetch_jobs(keyword, max_results=10):
    """Fetch remote job listings from We Work Remotely RSS, filtered by keyword."""
    try:
        feed = feedparser.parse(WWR_RSS_URL)
    except Exception as e:
        print(f"[weworkremotely] Error fetching feed: {e}")
        return []

    if feed.get("status") != 200:
        print(f"[weworkremotely] Unexpected status: {feed.get('status')}")
        return []

    keyword_lower = keyword.lower()
    jobs = []

    for entry in feed.entries:
        raw_title = entry.get("title", "")
        company, title = _parse_title(raw_title)

        if keyword_lower not in title.lower():
            continue

        jobs.append({
            "title": title,
            "company": company,
            "location": entry.get("region") or None,
            "url": entry.get("link") or None,
            "job_type": _normalize_job_type(entry.get("type")),
            "posted_at": _parse_date(entry.get("published_parsed")),
        })

        if len(jobs) >= max_results:
            break

    return jobs


if __name__ == "__main__":
    results = fetch_jobs("engineer", max_results=5)
    print(f"Found {len(results)} jobs\n")
    for job in results:
        print(job)
