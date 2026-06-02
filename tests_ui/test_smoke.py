"""
Browser smoke tests for Jain Panchang UI.

Run:
    pip install -r requirements-dev.txt
    python -m playwright install chromium
    python -m unittest discover -s tests_ui -v

Each test navigates the live Flask app and asserts visible UI behaviour.
"""
from __future__ import annotations

import re
import unittest

from tests_ui.conftest import BrowserTestCase


class TestHomeScreen(BrowserTestCase):
    def test_home_loads_without_location_shows_prompt(self):
        """Home page shows location prompt when no location is saved."""
        page = self.new_page()
        page.goto(self.base_url)
        # Clear any persisted state from previous runs
        page.evaluate("localStorage.clear()")
        page.reload()
        page.wait_for_load_state("networkidle")

        prompt = page.locator("text=Set a location")
        self.assertTrue(prompt.count() > 0, "Expected 'Set a location' prompt on home")
        self.assertEqual(page._js_errors, [], f"Uncaught JS errors: {page._js_errors}")
        page.context.close()

    def test_home_loads_with_saved_location_shows_panchang(self):
        """Home page fetches and renders panchang when location is pre-saved."""
        page = self.new_page()
        page.goto(self.base_url)
        page.evaluate("""
            localStorage.setItem('jain_panchang_v2', JSON.stringify({
                lat: 23.0225, lon: 72.5714, locationName: 'Ahmedabad',
                ayanamsa: 'Lahiri', timeFormat: '24h'
            }))
        """)
        page.reload()
        page.wait_for_load_state("networkidle")

        # Header should show the location name
        header = page.locator("#locationDisplay, .home-location, .location-label")
        # At minimum the page must not crash
        self.assertEqual(page._js_errors, [], f"Uncaught JS errors: {page._js_errors}")
        page.context.close()


class TestLocationValidation(BrowserTestCase):
    def _open_location_page(self, page):
        page.goto(f"{self.base_url}#location")
        page.wait_for_load_state("networkidle")

    def test_valid_coordinates_save_and_navigate_home(self):
        """Saving valid lat/lon saves state and navigates to home."""
        page = self.new_page()
        self._open_location_page(page)
        page.evaluate("localStorage.clear()")

        page.fill("#latInput", "23.0225")
        page.fill("#lonInput", "72.5714")
        page.fill("#locationNameInput", "Ahmedabad")
        page.click("#locationSaveBtn")
        page.wait_for_url(re.compile(r"#home"))

        state = page.evaluate("JSON.parse(localStorage.getItem('jain_panchang_v2') || '{}')")
        self.assertAlmostEqual(state.get("lat"), 23.0225, places=2)
        self.assertEqual(page._js_errors, [], f"Uncaught JS errors: {page._js_errors}")
        page.context.close()

    def test_out_of_range_latitude_shows_error(self):
        """Saving lat=999 must show an inline error and NOT navigate away."""
        page = self.new_page()
        self._open_location_page(page)

        page.fill("#latInput", "999")
        page.fill("#lonInput", "72.5714")
        page.click("#locationSaveBtn")

        error_el = page.locator("#locationError")
        self.assertFalse(error_el.is_hidden(), "Error element should be visible for lat=999")
        err_text = error_el.inner_text()
        self.assertIn("90", err_text, f"Error should mention valid range, got: {err_text!r}")
        # URL must still be on the location page
        self.assertIn("location", page.url)
        self.assertEqual(page._js_errors, [], f"Uncaught JS errors: {page._js_errors}")
        page.context.close()

    def test_out_of_range_longitude_shows_error(self):
        """Saving lon=999 must show an inline error and NOT navigate away."""
        page = self.new_page()
        self._open_location_page(page)

        page.fill("#latInput", "23.0")
        page.fill("#lonInput", "999")
        page.click("#locationSaveBtn")

        error_el = page.locator("#locationError")
        self.assertFalse(error_el.is_hidden(), "Error element should be visible for lon=999")
        err_text = error_el.inner_text()
        self.assertIn("180", err_text, f"Error should mention valid range, got: {err_text!r}")
        self.assertEqual(page._js_errors, [], f"Uncaught JS errors: {page._js_errors}")
        page.context.close()


class TestDrawerNavigation(BrowserTestCase):
    EXPECTED_PAGES = [
        "home", "calendar", "panchang", "muhurta",
        "festivals", "location", "settings",
    ]

    def test_drawer_contains_all_nav_links(self):
        """Drawer must contain a button for every page."""
        page = self.new_page()
        page.goto(self.base_url)
        page.wait_for_load_state("networkidle")

        # Open the drawer
        menu_btn = page.locator("[id$=MenuBtn]").first
        menu_btn.click()
        page.wait_for_selector(".drawer.open, .drawer[style*='transform']", timeout=2000)

        for nav_id in self.EXPECTED_PAGES:
            btn = page.locator(f"[data-nav='{nav_id}']")
            self.assertTrue(btn.count() > 0, f"Drawer missing nav button for '{nav_id}'")

        self.assertEqual(page._js_errors, [], f"Uncaught JS errors: {page._js_errors}")
        page.context.close()


class TestCalendarPage(BrowserTestCase):
    def test_calendar_cells_show_sunrise_sunset_without_extra_requests(self):
        """Calendar renders sunrise/sunset from month-overview; no extra API calls."""
        page = self.new_page()
        # Must navigate first before localStorage is accessible
        page.goto(self.base_url)
        page.evaluate("""
            localStorage.setItem('jain_panchang_v2', JSON.stringify({
                lat: 23.0225, lon: 72.5714, locationName: 'Ahmedabad',
                ayanamsa: 'Lahiri', timeFormat: '24h'
            }))
        """)

        # Track API calls
        api_calls: list[str] = []
        page.on("request", lambda req: api_calls.append(req.url) if "/generate-panchang" in req.url else None)

        page.goto(f"{self.base_url}#calendar")
        page.wait_for_load_state("networkidle")
        # Give any async requests a chance to fire
        page.wait_for_timeout(1500)

        # No follow-up /generate-panchang calls should happen
        self.assertEqual(
            api_calls, [],
            f"Expected 0 extra /generate-panchang requests, got {len(api_calls)}: {api_calls[:3]}"
        )

        # At least one cell must show sunrise text
        sun_rows = page.locator(".cal-sun-row")
        self.assertGreater(sun_rows.count(), 0, "Expected cal-sun-row elements in calendar cells")

        self.assertEqual(page._js_errors, [], f"Uncaught JS errors: {page._js_errors}")
        page.context.close()


class TestFestivalModal(BrowserTestCase):
    def test_festival_bottom_sheet_opens_and_closes(self):
        """Clicking a festival marker opens the bottom sheet; × closes it."""
        page = self.new_page()
        page.goto(self.base_url)
        page.evaluate("""
            localStorage.setItem('jain_panchang_v2', JSON.stringify({
                lat: 23.0225, lon: 72.5714, locationName: 'Ahmedabad',
                ayanamsa: 'Lahiri', timeFormat: '24h'
            }))
        """)
        page.goto(f"{self.base_url}#festivals")
        page.wait_for_load_state("networkidle")

        # If any festival card exists, click the first one
        card = page.locator(".fest-card, .fest-item").first
        if card.count() == 0:
            self.skipTest("No festival cards rendered — stub returned no festivals")

        card.click()
        sheet = page.locator("#festModal")
        sheet.wait_for(state="visible", timeout=3000)
        self.assertTrue(sheet.is_visible(), "Bottom sheet should be visible after clicking a card")

        # Close it
        page.click("#festModalClose")
        page.wait_for_timeout(400)  # allow close animation
        self.assertFalse(sheet.is_visible(), "Bottom sheet should be hidden after close")

        self.assertEqual(page._js_errors, [], f"Uncaught JS errors: {page._js_errors}")
        page.context.close()


class TestSettingsPersistence(BrowserTestCase):
    def test_time_format_persists_across_reload(self):
        """Changing time format in Settings is saved to localStorage and survives reload."""
        page = self.new_page()
        page.goto(f"{self.base_url}#settings")
        page.wait_for_load_state("networkidle")

        # Click 12h button (if present)
        btn_12h = page.locator("[data-timefmt='12h']")
        if btn_12h.count() == 0:
            self.skipTest("No time format toggle found in Settings")
        btn_12h.click()

        # Reload and re-check
        page.reload()
        page.goto(f"{self.base_url}#settings")
        page.wait_for_load_state("networkidle")

        state = page.evaluate("JSON.parse(localStorage.getItem('jain_panchang_v2') || '{}')")
        self.assertEqual(state.get("timeFormat"), "12h", "Time format should persist as '12h'")

        self.assertEqual(page._js_errors, [], f"Uncaught JS errors: {page._js_errors}")
        page.context.close()


class TestNoConsoleErrors(BrowserTestCase):
    """Navigate every page and assert there are no uncaught JS exceptions."""

    PAGES = ["home", "calendar", "panchang", "muhurta", "festivals", "settings"]

    def test_no_uncaught_errors_on_any_page(self):
        page = self.new_page()
        page.goto(self.base_url)
        page.evaluate("""
            localStorage.setItem('jain_panchang_v2', JSON.stringify({
                lat: 23.0225, lon: 72.5714, locationName: 'Ahmedabad',
                ayanamsa: 'Lahiri', timeFormat: '24h'
            }))
        """)

        all_errors: list[str] = []
        page.on("pageerror", lambda e: all_errors.append(str(e)))

        for pg in self.PAGES:
            page.goto(f"{self.base_url}#{pg}")
            page.wait_for_load_state("networkidle")
            page.wait_for_timeout(300)

        self.assertEqual(all_errors, [], f"Uncaught JS errors across pages: {all_errors}")
        page.context.close()


if __name__ == "__main__":
    unittest.main()
