"""RED test: export_pdf must have timedelta in scope.

Running this before the fix will raise NameError at the point where
`curr_d += timedelta(days=1)` executes.  After adding timedelta to the
import the test goes green.
"""
import importlib
import sys
import unittest


class TestPdfTimedeltaInScope(unittest.TestCase):
    """timedelta must be importable from the export_pdf module."""

    def test_timedelta_is_available_in_export_pdf(self):
        """export_pdf module namespace must contain timedelta after import."""
        # Remove cached module so we always get a fresh import
        sys.modules.pop("export_pdf", None)

        import export_pdf  # noqa: F401

        self.assertTrue(
            hasattr(export_pdf, "timedelta") or "timedelta" in dir(export_pdf),
            "timedelta is not available in export_pdf — add it to the datetime import",
        )


if __name__ == "__main__":
    unittest.main()
