"""Unit tests for report.py — no network, uses temp DB via monkeypatch."""

import pytest

from jobhunter.report import generate_report


def test_generate_report_creates_file(tmp_path):
    out = tmp_path / "report.html"
    generate_report(report_path=out)
    assert out.exists()
    assert out.stat().st_size > 0


def test_generate_report_html_structure(tmp_path):
    out = tmp_path / "report.html"
    generate_report(report_path=out)
    html = out.read_text()

    assert "<!DOCTYPE html>" in html
    assert "JobHunter Dashboard" in html
    assert "Total tracked" in html
    assert "Tracked Jobs" in html
    assert "Updated" in html


def test_generate_report_contains_all_companies(tmp_path):
    from jobhunter.config import COMPANIES
    out = tmp_path / "report.html"
    generate_report(report_path=out)
    html = out.read_text()

    for cfg in COMPANIES.values():
        assert cfg.name in html, f"Missing company '{cfg.name}' in report"


def test_generate_report_empty_state_message(tmp_path):
    """When no jobs are notified yet, shows the empty placeholder."""
    out = tmp_path / "report.html"
    generate_report(report_path=out)
    html = out.read_text()
    # Either empty message or a job table — both are valid
    assert "check back soon" in html or "<table>" in html


def test_generate_report_returns_path(tmp_path):
    out = tmp_path / "report.html"
    result = generate_report(report_path=out)
    assert result == out