from jobspy import scrape_jobs

JOB_TYPE_MAP = {
    "fulltime": "full_time",
    "parttime": "part_time",
    "contract": "contract",
    "temporary": "contract",
    "internship": "part_time",
}


def fetch_jobs(keyword, max_results=10):
    """Fetch job listings from Indeed for a given keyword."""
    try:
        df = scrape_jobs(
            site_name=["indeed"],
            search_term=keyword,
            results_wanted=max_results,
            hours_old=72,
            verbose=False,
        )
    except Exception as e:
        print(f"[indeed] Error fetching '{keyword}': {e}")
        return []

    jobs = []
    for _, row in df.iterrows():
        raw_type = str(row.get("job_type") or "").lower()
        jobs.append({
            "title": row.get("title") or "",
            "company": row.get("company") or "",
            "location": row.get("location") or "",
            "url": row.get("job_url") or "",
            "job_type": JOB_TYPE_MAP.get(raw_type, raw_type),
            "posted_at": str(row.get("date_posted") or ""),
        })

    return jobs


if __name__ == "__main__":
    results = fetch_jobs("python developer", max_results=3)
    for job in results:
        print(job)
