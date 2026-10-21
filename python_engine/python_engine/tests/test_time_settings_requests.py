"""Every request accepts the two time settings: clock and sunrise rule.

Defaults (user decision, 2026-10-16): clock "standard" (standard time all
year), sunrise "modern" (upper limb, refraction).
"""

from __future__ import annotations

import pytest

from request_parsing import parse_clock, parse_laghu_panchang_request, parse_sunrise_rule

DELHI = {"lat": 28.6139, "lon": 77.2090}


@pytest.mark.parametrize("value, expected", [(None, "standard"), ("", "standard"), ("Daylight", "daylight"), (" standard ", "standard")])
def test_clock_defaults_to_standard_and_is_case_insensitive(value, expected):
    assert parse_clock(value) == expected


@pytest.mark.parametrize("value, expected", [(None, "modern"), ("", "modern"), ("TRADITIONAL", "traditional")])
def test_sunrise_rule_defaults_to_modern_and_is_case_insensitive(value, expected):
    assert parse_sunrise_rule(value) == expected


@pytest.mark.parametrize("parser, field", [(parse_clock, "clock"), (parse_sunrise_rule, "sunrise")])
def test_unknown_values_are_rejected_with_the_field_named(parser, field):
    with pytest.raises(ValueError, match=field):
        parser("summer")


def test_the_laghu_request_carries_both_settings():
    parsed = parse_laghu_panchang_request({"year": 2027, "clock": "daylight", "sunrise": "traditional", **DELHI})

    assert (parsed.clock, parsed.sunrise_rule) == ("daylight", "traditional")


def test_the_laghu_request_defaults_both_settings():
    parsed = parse_laghu_panchang_request({"year": 2027, **DELHI})

    assert (parsed.clock, parsed.sunrise_rule) == ("standard", "modern")
