"""Hindi calendar PDF as a web-app export.

The Hindi calendar was CLI-only. The client bundle ships only the web app, so it
is exposed as a download like the yearly PDF. The PDF step needs a headless
browser (Playwright or Edge); when neither is present the caller must be handed
the HTML it did write, not a path to a PDF that does not exist.
"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

import hindi_calendar_pdf
from app import app
from hindi_calendar_pdf import generate_hindi_pdf_calendar
from request_parsing import parse_hindi_pdf_request


def _no_renderer(html_path: str, pdf_path: str) -> bool:
    return False


def _fake_renderer(html_path: str, pdf_path: str) -> bool:
    Path(pdf_path).write_bytes(b"%PDF-1.4 stub")
    return True


def _generate_one_month(out_path: Path) -> str:
    return generate_hindi_pdf_calendar(
        str(out_path), start_year=2026, start_month=3, month_count=1,
    )


def test_without_a_pdf_renderer_the_html_file_is_returned(tmp_path):
    with patch.object(hindi_calendar_pdf, "_html_to_pdf", _no_renderer):
        written = _generate_one_month(tmp_path / "calendar.pdf")

    assert written.endswith(".html")
    assert Path(written).exists()


def test_with_a_pdf_renderer_the_pdf_file_is_returned(tmp_path):
    with patch.object(hindi_calendar_pdf, "_html_to_pdf", _fake_renderer):
        written = _generate_one_month(tmp_path / "calendar.pdf")

    assert written.endswith(".pdf")
    assert Path(written).exists()



EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"


@pytest.mark.skipif(not Path(EDGE).exists(), reason="needs Microsoft Edge")
def test_edge_renders_the_pdf_when_playwright_is_absent(tmp_path, monkeypatch):
    """The client bundle has no Playwright, so Edge must do the printing.

    Edge hands a headless request to an already-open Edge window and exits
    without printing, so this also holds while the user has Edge open.
    """
    monkeypatch.setitem(sys.modules, "playwright", None)

    written = _generate_one_month(tmp_path / "calendar.pdf")

    assert written.endswith(".pdf")
    assert Path(written).read_bytes().startswith(b"%PDF")

# ── Request parsing ──────────────────────────────────────────────────────────


def _hindi_payload(**overrides) -> dict:
    return {"start_year": 2026, "lat": 26.9124, "lon": 75.7873, **overrides}


def test_hindi_request_defaults_to_a_chaitra_to_chaitra_purnimanta_year():
    parsed = parse_hindi_pdf_request(_hindi_payload())

    assert (parsed.start_year, parsed.start_month, parsed.month_count) == (2026, 3, 13)
    assert parsed.calendar_system == "purnimanta"
    assert parsed.ayanamsa_name == "Lahiri"


def test_hindi_request_carries_the_callers_choices():
    parsed = parse_hindi_pdf_request(_hindi_payload(
        start_month=10, months=6, ayanamsa="Raman", calendar_system="amanta",
    ))

    assert (parsed.start_month, parsed.month_count) == (10, 6)
    assert parsed.ayanamsa_name == "Raman"
    assert parsed.calendar_system == "amanta"
    assert (parsed.lat, parsed.lon) == (26.9124, 75.7873)


def test_hindi_request_requires_a_start_year():
    with pytest.raises(ValueError, match="start_year"):
        parse_hindi_pdf_request({"lat": 26.9, "lon": 75.8})


@pytest.mark.parametrize("start_month", [0, 13])
def test_hindi_request_rejects_a_start_month_outside_1_to_12(start_month):
    with pytest.raises(ValueError, match="start_month"):
        parse_hindi_pdf_request(_hindi_payload(start_month=start_month))


@pytest.mark.parametrize("months", [0, 25])
def test_hindi_request_rejects_a_month_count_outside_1_to_24(months):
    with pytest.raises(ValueError, match="months"):
        parse_hindi_pdf_request(_hindi_payload(months=months))


@pytest.mark.parametrize("months", [1, 24])
def test_hindi_request_accepts_the_month_count_bounds(months):
    assert parse_hindi_pdf_request(_hindi_payload(months=months)).month_count == months


def test_hindi_request_requires_a_location():
    with pytest.raises(ValueError):
        parse_hindi_pdf_request({"start_year": 2026})


# ── Web endpoint ─────────────────────────────────────────────────────────────

def _post_hindi_pdf(client, **overrides):
    return client.post("/generate-hindi-pdf", json=_hindi_payload(months=1, **overrides))


def test_hindi_endpoint_returns_a_downloadable_pdf():
    client = app.test_client()
    with patch.object(hindi_calendar_pdf, "_html_to_pdf", _fake_renderer):
        response = _post_hindi_pdf(client)

    assert response.status_code == 200
    file_info = response.get_json()["file"]
    assert file_info["format"] == "pdf"
    assert file_info["name"].endswith(".pdf")

    download = client.get(file_info["download_url"])
    assert download.status_code == 200
    assert download.data.startswith(b"%PDF")


def test_hindi_endpoint_hands_over_the_html_when_no_renderer_is_available():
    client = app.test_client()
    with patch.object(hindi_calendar_pdf, "_html_to_pdf", _no_renderer):
        response = _post_hindi_pdf(client)

    assert response.status_code == 200
    file_info = response.get_json()["file"]
    assert file_info["format"] == "html"
    assert file_info["name"].endswith(".html")

    download = client.get(file_info["download_url"])
    assert download.status_code == 200
    assert "पंचांग" in download.get_data(as_text=True)


def test_hindi_endpoint_reports_the_resolved_location():
    client = app.test_client()
    with patch.object(hindi_calendar_pdf, "_html_to_pdf", _no_renderer):
        response = _post_hindi_pdf(client)

    location = response.get_json()["location"]
    assert (location["lat"], location["lon"]) == (26.9124, 75.7873)
    assert location["timezone"] == "Asia/Kolkata"


def test_hindi_endpoint_rejects_an_invalid_request():
    response = _post_hindi_pdf(app.test_client(), start_month=13)

    assert response.status_code == 400
    assert "start_month" in response.get_json()["error"]
