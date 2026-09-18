"""
tests/test_agni_vaas.py — Unit tests for Agni Vaas calculation logic.
"""

import pytest
from panchang import calculate_agni_vaas
from panchang_service import generate_location_panchang


def test_agni_vaas_test_case_1_shukla_11_tuesday():
    """Book Test Case 1: Shukla Paksha 11 on Tuesday -> Prithvi (Earth)."""
    # Shukla 11 -> Tithi index 11
    # Tuesday -> Vara index 2 (Sunday=0, Monday=1, Tuesday=2)
    result = calculate_agni_vaas(tithi_index=11, vara_index=2)

    assert result["tithi_index"] == 11
    assert result["absolute_tithi"] == 11
    assert result["vara_number"] == 3
    assert result["total_sum"] == 15
    assert result["remainder"] == 3
    assert result["residence"] == "Prithvi"
    assert result["residence_hindi"] == "पृथ्वी"
    assert result["is_auspicious"] is True
    assert "शुभ" in result["status"]


def test_agni_vaas_test_case_2_krishna_14_tuesday():
    """Book Test Case 2: Krishna Paksha 14 on Tuesday -> Aakash (Sky)."""
    # Krishna 14 -> Tithi index 29 (15 + 14)
    # Tuesday -> Vara index 2
    result = calculate_agni_vaas(tithi_index=29, vara_index=2)

    assert result["tithi_index"] == 29
    assert result["absolute_tithi"] == 29
    assert result["vara_number"] == 3
    assert result["total_sum"] == 33
    assert result["remainder"] == 1
    assert result["residence"] == "Aakash"
    assert result["residence_hindi"] == "आकाश"
    assert result["is_auspicious"] is False
    assert "प्राणनाश" in result["description_hindi"] or "प्राणनाशक" in result["status"]


def test_agni_vaas_remainder_2_patal():
    """Test Remainder 2 mapping to Patal (Underworld)."""
    # Shukla 1 on Wednesday: Absolute Tithi = 1, Vara Number = 4 (Wed)
    # Sum = 1 + 4 + 1 = 6. Mod 4 = 2.
    result = calculate_agni_vaas(tithi_index=1, vara_index=3)

    assert result["remainder"] == 2
    assert result["residence"] == "Patal"
    assert result["residence_hindi"] == "पाताल"
    assert result["is_auspicious"] is False
    assert "धन-ऐश्वर्य" in result["description_hindi"] or "हानि" in result["description_hindi"]


def test_agni_vaas_remainder_0_prithvi():
    """Test Remainder 0 mapping to Prithvi (Earth)."""
    # Krishna 15 (Amavasya) on Sunday: Absolute Tithi = 30, Vara Number = 1 (Sun)
    # Sum = 30 + 1 + 1 = 32. Mod 4 = 0.
    result = calculate_agni_vaas(tithi_index=30, vara_index=0)

    assert result["remainder"] == 0
    assert result["residence"] == "Prithvi"
    assert result["residence_hindi"] == "पृथ्वी"
    assert result["is_auspicious"] is True


def test_agni_vaas_integration_in_panchang_payload():
    """Verify that generate_location_panchang includes agni_vaas section."""
    payload = generate_location_panchang("2026-08-16", lat=28.6139, lon=77.2090)
    assert "agni_vaas" in payload
    av = payload["agni_vaas"]
    assert "residence" in av
    assert "residence_hindi" in av
    assert "status" in av
    assert "description_hindi" in av
    assert "is_auspicious" in av
