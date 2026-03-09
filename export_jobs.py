import json
import sqlite3

from db import get_connection


def get_jobs(limit=50, offset=0, source=None, keyword=None, days=None, job_type=None):
    """Return saved jobs from the database as a list of dicts.

    Optional filters:
      source  — exact match on source name (e.g. 'remotive')
      keyword — exact match on keyword used to find the job
      days    — only jobs posted within the last N days
      limit   — max number of results (default 50)
      offset  — number of rows to skip (for pagination)
    """
    conditions = []
    params = []

    if source:
        conditions.append("source = ?")
        params.append(source)
    if keyword:
        conditions.append("title LIKE ?")
        params.append(f"%{keyword}%")
    if days:
        conditions.append("posted_at >= datetime('now', ?)")
        params.append(f"-{days} days")
    if job_type:
        conditions.append("job_type = ?")
        params.append(job_type)

    where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    params.extend([limit, offset])

    conn = get_connection()
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        f"""
        SELECT found_at, title, company, source, keywords, job_type, posted_at, url
        FROM jobs
        {where}
        ORDER BY found_at DESC
        LIMIT ? OFFSET ?
        """,
        params,
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


if __name__ == "__main__":
    jobs = get_jobs()
    print(json.dumps(jobs, indent=2))
