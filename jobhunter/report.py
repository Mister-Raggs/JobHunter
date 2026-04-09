"""Generates a static HTML dashboard from the jobs database."""

from datetime import datetime, timezone
from pathlib import Path

from .config import COMPANIES
from .database import get_notified_jobs, job_count

REPORT_PATH = Path(__file__).parent.parent / "data" / "report.html"


def generate_report(report_path: Path | None = None) -> Path:
    """Write a static HTML dashboard and return the path."""
    out = report_path or REPORT_PATH
    out.parent.mkdir(parents=True, exist_ok=True)

    jobs = get_notified_jobs()
    now = datetime.now(timezone.utc)
    now_str = now.strftime("%Y-%m-%d %H:%M UTC")

    # Per-company stats
    company_stats = []
    for key, cfg in COMPANIES.items():
        count = job_count(key)
        company_stats.append((cfg.name, count))

    total = sum(c for _, c in company_stats)

    # Stat cards HTML
    cards_html = "\n".join(
        f'<div class="card"><div class="card-count">{count}</div><div class="card-name">{name}</div></div>'
        for name, count in company_stats
    )

    # Job rows HTML
    if jobs:
        rows = []
        for job in jobs:
            company_name = COMPANIES[job.company].name if job.company in COMPANIES else job.company
            discovered = job.discovered_at.strftime("%b %d") if job.discovered_at else ""
            rows.append(
                f"<tr>"
                f'<td><a href="{job.url}" target="_blank" rel="noopener">{job.title}</a></td>'
                f"<td>{company_name}</td>"
                f"<td>{job.location or '—'}</td>"
                f"<td>{discovered}</td>"
                f"</tr>"
            )
        table_html = f"""
        <table>
            <thead>
                <tr>
                    <th>Role</th>
                    <th>Company</th>
                    <th>Location</th>
                    <th>Found</th>
                </tr>
            </thead>
            <tbody>
                {"".join(rows)}
            </tbody>
        </table>"""
    else:
        table_html = '<p class="empty">No jobs tracked yet — check back soon.</p>'

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>JobHunter Dashboard</title>
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            background: #0f1117;
            color: #e2e8f0;
            min-height: 100vh;
            padding: 2rem 1rem;
        }}
        header {{
            max-width: 1000px;
            margin: 0 auto 2rem;
            display: flex;
            justify-content: space-between;
            align-items: baseline;
            flex-wrap: wrap;
            gap: 0.5rem;
        }}
        h1 {{
            font-size: 1.5rem;
            font-weight: 700;
            letter-spacing: -0.02em;
        }}
        h1 span {{ color: #6366f1; }}
        .meta {{ font-size: 0.8rem; color: #64748b; }}
        .stats {{
            max-width: 1000px;
            margin: 0 auto 2.5rem;
            display: flex;
            flex-wrap: wrap;
            gap: 1rem;
        }}
        .card {{
            background: #1e2130;
            border: 1px solid #2d3148;
            border-radius: 10px;
            padding: 1rem 1.4rem;
            min-width: 130px;
            flex: 1;
        }}
        .card-count {{
            font-size: 2rem;
            font-weight: 700;
            color: #6366f1;
            line-height: 1;
        }}
        .card-name {{
            font-size: 0.8rem;
            color: #94a3b8;
            margin-top: 0.3rem;
        }}
        .total-card .card-count {{ color: #10b981; }}
        section {{
            max-width: 1000px;
            margin: 0 auto;
        }}
        h2 {{
            font-size: 1rem;
            font-weight: 600;
            color: #94a3b8;
            margin-bottom: 1rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 0.875rem;
        }}
        thead tr {{
            border-bottom: 1px solid #2d3148;
        }}
        th {{
            text-align: left;
            padding: 0.6rem 0.75rem;
            color: #64748b;
            font-weight: 500;
            font-size: 0.75rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }}
        td {{
            padding: 0.75rem;
            border-bottom: 1px solid #1e2130;
            vertical-align: top;
        }}
        tr:hover td {{ background: #1a1e2e; }}
        a {{
            color: #818cf8;
            text-decoration: none;
        }}
        a:hover {{ color: #a5b4fc; text-decoration: underline; }}
        .empty {{ color: #475569; font-size: 0.9rem; padding: 2rem 0; }}
        footer {{
            max-width: 1000px;
            margin: 3rem auto 0;
            font-size: 0.75rem;
            color: #334155;
            text-align: center;
        }}
    </style>
</head>
<body>
    <header>
        <h1>Job<span>Hunter</span> Dashboard</h1>
        <span class="meta">Updated {now_str} &nbsp;·&nbsp; {total} jobs tracked</span>
    </header>

    <div class="stats">
        <div class="card total-card">
            <div class="card-count">{total}</div>
            <div class="card-name">Total tracked</div>
        </div>
        {cards_html}
    </div>

    <section>
        <h2>Tracked Jobs</h2>
        {table_html}
    </section>

    <footer>Jobs shown here were already emailed. New postings appear after the next 30-min check.</footer>
</body>
</html>"""

    out.write_text(html, encoding="utf-8")
    return out