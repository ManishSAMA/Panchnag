"""The sunrise rule reaches the festival engine.

16 Mar 2027, Delhi: the Jain tithi (sunrise + 6 ghati) changes from Ashtami to
Navami within the ~4 minutes between the modern and the traditional sunrise, so
the day's identity depends on the rule. Found by scanning 2026-2027 for days
where the two rules disagree.
"""

from __future__ import annotations

import pytest

from jain_observances.festival_service import generate_jain_festivals
from panchang import find_chaitra_shukla_1, find_diwali

DELHI = (28.6139, 77.2090)
PROFILE = "shwetambar_murtipujak_tapagachchha"


def _calendar(rule: str) -> dict:
    return generate_jain_festivals(2027, *DELHI, "Lahiri", PROFILE, sunrise_rule=rule)


def test_the_day_identity_follows_the_chosen_sunrise_rule():
    assert "Ashtami" in _calendar("modern")["panchang_tithi_map"]["2027-03-16"]
    assert "Navami" in _calendar("traditional")["panchang_tithi_map"]["2027-03-16"]


def test_the_default_rule_is_modern():
    default = generate_jain_festivals(2027, *DELHI, "Lahiri", PROFILE)

    assert default["panchang_tithi_map"] == _calendar("modern")["panchang_tithi_map"]


def test_an_unknown_rule_is_rejected():
    with pytest.raises(ValueError, match="sunrise rule"):
        generate_jain_festivals(2027, *DELHI, "Lahiri", PROFILE, sunrise_rule="vedic")


@pytest.mark.parametrize("finder", [find_chaitra_shukla_1, find_diwali])
def test_samvat_anchors_accept_the_rule_and_agree_on_ordinary_years(finder):
    """Neither anchor sits on a rule-sensitive day in 2027, so both rules agree."""
    modern = finder(2027, *DELHI, 5.5, "Lahiri", sunrise_rule="modern")
    traditional = finder(2027, *DELHI, 5.5, "Lahiri", sunrise_rule="traditional")

    assert modern == traditional
