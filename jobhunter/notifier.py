"""Email notification for new job postings via Resend."""

import os

import requests


def send_email(new_jobs: list[dict], to_email: str | None = None) -> bool:
    """Send an HTML email listing new job postings via Resend API."""
    api_key = os.getenv("RESEND_API_KEY", "")
    from_email = os.getenv("FROM_EMAIL", "")
    to_email = to_email or os.getenv("TO_EMAIL", "")

    if not api_key:
        print("  Email not configured. Set RESEND_API_KEY in .env")
        return False
    if not to_email:
        print("  Recipient not configured. Set TO_EMAIL in .env")
        return False
    if not from_email:
        print("  Sender not configured. Set FROM_EMAIL in .env")
        return False

    subject = f"JobHunter: {len(new_jobs)} new job(s) found"

    rows = "\n".join(
        f"<tr>"
        f"<td style='padding:6px 12px'>{j.get('company', '')}</td>"
        f"<td style='padding:6px 12px'><a href=\"{j['url']}\">{j['title']}</a></td>"
        f"<td style='padding:6px 12px'>{j.get('location', '')}</td>"
        f"</tr>"
        for j in new_jobs
    )

    html = (
        f"<h2>{len(new_jobs)} New Job Posting(s)</h2>"
        f"<table border='1' cellpadding='0' cellspacing='0' style='border-collapse:collapse'>"
        f"<tr><th style='padding:6px 12px'>Company</th>"
        f"<th style='padding:6px 12px'>Title</th>"
        f"<th style='padding:6px 12px'>Location</th></tr>"
        f"{rows}</table>"
    )

    resp = requests.post(
        "https://api.resend.com/emails",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={"from": from_email, "to": [to_email], "subject": subject, "html": html},
        timeout=15,
    )

    if resp.status_code == 200 or resp.status_code == 201:
        return True

    print(f"  Email failed: {resp.status_code} {resp.text}")
    return False
