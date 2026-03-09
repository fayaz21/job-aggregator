import requests

REMOTIVE_URL = "https://remotive.com/api/remote-jobs"


def fetch_jobs(keyword, max_results=10):
    """Fetch job listings from Remotive for a given keyword."""
    try:
        response = requests.get(
            REMOTIVE_URL,
            params={"search": keyword},
            timeout=10,
        )
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"[remotive] Error fetching '{keyword}': {e}")
        return []

    raw_jobs = response.json().get("jobs", [])[:max_results]

    jobs = []
    for job in raw_jobs:
        jobs.append({
            "title": job.get("title", ""),
            "company": job.get("company_name", ""),
            "location": job.get("candidate_required_location", ""),
            "url": job.get("url", ""),
            "job_type": job.get("job_type", ""),
            "posted_at": job.get("publication_date", ""),
        })

    return jobs
