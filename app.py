"""
app.py — Flask web application.

Serves the job discovery UI and JSON API. On startup, initialises the database
and launches the background agent thread so a single Render Web Service handles
both web traffic and job fetching without needing a separate worker process.

Routes:
  GET /          — HTML job listing with filters and pagination
  GET /jobs      — JSON API returning saved jobs (filterable)
  GET /health    — health check with DB stats and config summary
"""

import threading

from flask import Flask, jsonify, render_template, request

import agent
from config import ENABLED_SOURCES, KEYWORDS
from db import get_connection, init_db
from export_jobs import get_jobs
from sources import SOURCES

app = Flask(__name__)

# Ensure the DB schema exists before any request can arrive.
# init_db() is idempotent — safe to call on every startup.
init_db()

# Launch the job-fetching agent as a daemon thread alongside the web server.
# Daemon=True means the thread exits automatically when the main process exits.
# Requires gunicorn --workers 1 so only one agent thread runs per deployment.
_agent_thread = threading.Thread(target=agent.start_worker, daemon=True)
_agent_thread.start()


PAGE_SIZE = 20

@app.route("/")
def index():
    source   = request.args.get("source")
    keyword  = request.args.get("keyword")
    days     = request.args.get("days", type=int)
    job_type = request.args.get("job_type")
    page     = request.args.get("page", 1, type=int)
    offset   = (page - 1) * PAGE_SIZE

    # Fetch one extra row to determine whether a next page exists.
    jobs     = get_jobs(limit=PAGE_SIZE + 1, offset=offset, source=source,
                        keyword=keyword, days=days, job_type=job_type)
    has_next = len(jobs) > PAGE_SIZE
    jobs     = jobs[:PAGE_SIZE]

    conn = get_connection()
    total_jobs   = conn.execute("SELECT COUNT(*) FROM jobs").fetchone()[0]
    last_updated = conn.execute("SELECT MAX(found_at) FROM jobs").fetchone()[0]
    conn.close()

    return render_template("index.html", jobs=jobs,
        sources=list(SOURCES.keys()), selected_source=source,
        keywords=KEYWORDS, selected_keyword=keyword,
        selected_days=days, selected_job_type=job_type,
        page=page, has_next=has_next,
        total_jobs=total_jobs, last_updated=last_updated,
    )


@app.route("/jobs")
def jobs():
    source   = request.args.get("source")
    keyword  = request.args.get("keyword")
    job_type = request.args.get("job_type")
    limit    = request.args.get("limit", 50, type=int)
    return jsonify(get_jobs(limit=limit, source=source, keyword=keyword, job_type=job_type))


@app.route("/health")
def health():
    conn = get_connection()
    total_jobs = conn.execute("SELECT COUNT(*) FROM jobs").fetchone()[0]
    conn.close()
    return jsonify({
        "status": "ok",
        "total_jobs": total_jobs,
        "enabled_sources": ENABLED_SOURCES,
        "keywords": KEYWORDS,
    })


if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
