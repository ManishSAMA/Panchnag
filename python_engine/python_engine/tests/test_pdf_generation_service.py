from __future__ import annotations

import tempfile
from pathlib import Path
from unittest.mock import patch

from pdf_generation_service import generate_pdf_export
from range_generation_service import generate_year_range_exports


def test_generate_pdf_export_defaults_to_system_temp_dir():
    with patch("pdf_generation_service.generate_pdf_calendar") as mock_cal:
        result = generate_pdf_export(
            year=2026,
            city="Delhi",
            lat=28.6139,
            lon=77.2090,
            ayanamsa_name="Lahiri",
        )

    file_path = Path(result["file"]["path"]).resolve()
    temp_dir = Path(tempfile.gettempdir()).resolve()
    assert temp_dir in file_path.parents


def test_generate_year_range_exports_defaults_to_system_temp_dir():
    with patch("range_generation_service.run_generation", return_value=[]), \
         patch("range_generation_service.apply_element_continuity_formatting", return_value=[]), \
         patch("range_generation_service.export_data") as mock_export:
        result = generate_year_range_exports(
            start_year=2026,
            end_year=2026,
            city="Delhi",
            lat=28.6139,
            lon=77.2090,
            ayanamsa_name="Lahiri",
            output_format="csv",
            monthly=False,
            workers=1,
        )

    temp_dir = Path(tempfile.gettempdir()).resolve()
    # The output target directory should be inside the system temp directory
    call_args = mock_export.call_args[0]
    base_name = Path(call_args[1]).resolve()
    assert temp_dir in base_name.parents
