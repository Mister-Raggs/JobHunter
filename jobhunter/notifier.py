"""Email notification for new job postings."""

import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


def send_email(new_jobs: list[dict], to_email: str) -> bool:
    """Send an HTML email listing new job postings."""
    smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_USER", "")
    smtp_pass = os.getenv("SMTP_PASS", "")

    if not smtp_user or not smtp_pass:
        print("  Email not configured. Set SMTP_USER and SMTP_PASS in .env")
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

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = smtp_user
    msg["To"] = to_email
    msg.attach(MIMEText(html, "html"))

    with smtplib.SMTP(smtp_host, smtp_port) as server:
        server.starttls()
        server.login(smtp_user, smtp_pass)
        server.sendmail(smtp_user, to_email, msg.as_string())

    return True
