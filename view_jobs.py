from db import get_connection


def view_jobs():
    conn = get_connection()
    rows = conn.execute(
        """
        SELECT found_at, title, company, keywords, source, url
        FROM jobs
        ORDER BY found_at DESC
        LIMIT 20
        """
    ).fetchall()
    conn.close()

    if not rows:
        print("No jobs found in database.")
        return

    print(f"{'='*60}")
    for found_at, title, company, keywords, source, url in rows:
        print(f"Saved:    {found_at}")
        print(f"Source:   {source or 'unknown'}")
        print(f"Title:    {title}")
        print(f"Company:  {company}")
        print(f"Keyword:  {keywords}")
        print(f"URL:      {url}")
        print(f"{'-'*60}")

    print(f"Total shown: {len(rows)}")


if __name__ == "__main__":
    view_jobs()
