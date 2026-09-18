"""
Shared fixtures for Playwright browser smoke tests.

Each test module imports `live_server` and `browser_page` from here.

Setup
-----
pip install -r requirements-dev.txt
python -m playwright install chromium
"""
from __future__ import annotations

import socket
import threading
import time
import unittest
from typing import Generator
from unittest.mock import MagicMock, patch

from playwright.sync_api import Page, sync_playwright

# ── Deterministic stub data ────────────────────────────────────────────────────

STUB_PANCHANG = {
    "date": "2025-06-01",
    "panchang": {
        "tithi": [
            {"name": "Shashthi", "index": 6, "ends": {"time": "20:00:00"}, "paksha": "Shukla"}
        ],
        "nakshatra": {"name": "Ashlesha", "index": 9, "ends": {"time": "21:36:00"}},
        "vara": {"name": "Ravivara (Sunday)", "index": 0},
        "yoga": {"name": "Shubha", "ends": {"time": "22:00:00"}},
        "karana": {"name": "Bava"},
        "hindu_month": {"name": "Jyeshtha", "index": 3},
        "vikram_samvat": 2082,
        "vira_nirvana_samvat": 2552,
    },
    "events": {
        "sunrise": {"time": "05:52:00"},
        "sunset": {"time": "19:15:00"},
        "moonrise": {"time": "10:30:00"},
    },
    "sun_rashi": {"name": "Vrishabha"},
    "moon_rashi": {"name": "Karka"},
    "jain_tithi": {"name": "Shashthi", "index": 6},
    "choghadiya": {"day": [], "night": []},
    "hora": [],
    "rahu_kaal": {"start": "17:00:00", "end": "18:30:00"},
    "bhadra_kaal": [],
}

STUB_MONTH = {
    "year": 2025,
    "month": 6,
    "location": "Ahmedabad",
    "timezone": "Asia/Kolkata",
    "hindu_month": "Jyeshtha",
    "hindu_month_index": 3,
    "vikram_samvat": 2082,
    "days": [
        {
            "date": f"2025-06-{d:02d}",
            "tithi_index": 6,
            "tithi_name": "Shashthi",
            "tithi_end_time": "20:00",
            "nakshatra_index": 9,
            "nakshatra_name": "Ashlesha",
            "nakshatra_end_time": "21:36",
            "vara_index": 0,
            "vara_name": "Ravivara (Sunday)",
            "is_purnima": False,
            "is_amavasya": False,
            "is_ekadashi": False,
            "sunrise_time": "05:52",
            "sunset_time": "19:15",
            "jain_festivals": [],
        }
        for d in range(1, 31)
    ],
}

STUB_LOCATION = MagicMock()
STUB_LOCATION.lat = 23.0225
STUB_LOCATION.lon = 72.5714
STUB_LOCATION.name = "Ahmedabad"
STUB_LOCATION.timezone = "Asia/Kolkata"


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def make_live_server() -> tuple[str, list]:
    """Start a Flask dev server in a background thread. Returns (base_url, patches)."""
    port = _free_port()

    patches = [
        patch("app.generate_location_panchang", return_value=STUB_PANCHANG),
        patch("app.resolve_location", return_value=STUB_LOCATION),
    ]
    for p in patches:
        p.start()

    import app as flask_app  # import after patching

    flask_app.app.config["TESTING"] = True
    server_thread = threading.Thread(
        target=lambda: flask_app.app.run(port=port, use_reloader=False, threaded=True),
        daemon=True,
    )
    server_thread.start()

    # Wait until the port is open (up to 5 s)
    deadline = time.time() + 5
    while time.time() < deadline:
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=0.2):
                break
        except OSError:
            time.sleep(0.1)

    return f"http://127.0.0.1:{port}", patches


class BrowserTestCase(unittest.TestCase):
    """
    Base class for Playwright smoke tests.

    Spins up a single Flask server and Playwright browser for the whole
    test class (setUpClass/tearDownClass) to keep the suite fast.
    """

    base_url: str = ""
    _playwright = None
    _browser = None
    _patches: list = []

    @classmethod
    def setUpClass(cls):
        cls.base_url, cls._patches = make_live_server()
        cls._playwright = sync_playwright().start()
        cls._browser = cls._playwright.chromium.launch(headless=True)

    @classmethod
    def tearDownClass(cls):
        if cls._browser:
            cls._browser.close()
        if cls._playwright:
            cls._playwright.stop()
        for p in cls._patches:
            p.stop()

    def new_page(self, viewport: dict | None = None) -> Page:
        ctx = self._browser.new_context(
            viewport=viewport or {"width": 390, "height": 844}
        )
        page = ctx.new_page()
        # Collect uncaught JS errors
        page._js_errors: list[str] = []
        page.on("pageerror", lambda err: page._js_errors.append(str(err)))
        return page
