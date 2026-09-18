"""Purnimanta projection of the lunar month.

`get_hindu_month` implements the Amanta rule: the month ends at Amavasya. North
Indian physical panchangs use Purnimanta: the month ends at Purnima, so a new
month begins the next day with Krishna paksha. The two therefore disagree by
one month name across every Krishna paksha, and agree exactly on every Shukla
paksha.

Ground truth below is the Pt. Jaini Jiyalal / North Indian reckoning for
VS 2083 (2026), the year the discrepancy was reported against. 2026 carries an
Adhika Jyeshtha, which also exercises the adhik/nija inversion: a Krishna
paksha's adhika flag is opposite between the two systems.
"""

from datetime import date

import pytest

from astronomy import local_date_anchor_jd, get_sunrise
from panchang import (
    JAIN_TITHI_OFFSET_DAYS,
    get_hindu_month,
    get_purnimanta_month,
    get_tithi_at_jd,
)


LAT, LON, TZ = 26.9124, 75.7873, "Asia/Kolkata"  # Jaipur
AYANAMSA = "Lahiri"


def _reference_jd(d: date) -> float:
    """The 6-ghati day-identity anchor -- the same instant the app labels a day by."""
    sunrise = get_sunrise(local_date_anchor_jd(d, TZ, hour=0), LAT, LON)
    return sunrise + JAIN_TITHI_OFFSET_DAYS


# (date, purnimanta month, purnimanta is_adhika) -- from the physical panchang.
_GROUND_TRUTH = [
    (date(2026, 4, 1), "Chaitra", False),      # Purnima: Chaitra's last day
    (date(2026, 4, 2), "Vaishakha", False),    # Krishna 1: Vaishakh begins
    (date(2026, 4, 17), "Vaishakha", False),   # Amavasya: still Vaishakh
    (date(2026, 4, 18), "Vaishakha", False),   # Shukla 1: both systems agree
    (date(2026, 5, 1), "Vaishakha", False),    # Purnima: Vaishakh's last day
    (date(2026, 5, 2), "Jyeshtha", True),      # Krishna 1: Pratham (Adhik) Jyeshtha
    (date(2026, 5, 16), "Jyeshtha", True),     # Amavasya, still Adhik
    (date(2026, 5, 17), "Jyeshtha", True),     # Shukla 1 of Adhik Jyeshtha
    (date(2026, 6, 1), "Jyeshtha", False),     # Krishna 1: Nija Jyeshtha
    (date(2026, 6, 15), "Jyeshtha", False),    # Amavasya, still Nija
]


@pytest.mark.parametrize("day,expected_month,expected_adhika", _GROUND_TRUTH)
def test_matches_the_physical_panchang(day, expected_month, expected_adhika):
    name, _common, is_adhika = get_purnimanta_month(_reference_jd(day), AYANAMSA)

    assert name.removeprefix("Adhika ") == expected_month
    assert is_adhika is expected_adhika


def test_shukla_pakshas_are_identical_in_both_systems():
    """The invariant that makes a Shukla mismatch always a real defect."""
    checked = 0
    for offset in range(120):
        day = date(2026, 3, 1) + __import__("datetime").timedelta(days=offset)
        jd = _reference_jd(day)
        if get_tithi_at_jd(jd, AYANAMSA) > 15:
            continue  # Krishna paksha -- expected to differ
        checked += 1
        assert get_purnimanta_month(jd, AYANAMSA) == get_hindu_month(jd, AYANAMSA), (
            f"{day}: Shukla paksha must read the same in both systems"
        )
    assert checked > 40, "window should contain plenty of Shukla days"


def test_krishna_pakshas_take_the_next_month_in_sequence():
    """Purnimanta names a Krishna paksha for the following month, never the earlier.

    "Following" means the next month in the amanta sequence, in which an Adhika
    month precedes the nija month of the same name. So there are two shapes:
    ordinarily the name advances one position, but stepping out of an Adhika
    month the name stays put and the adhika flag clears. The second shape is the
    Adhik-Maas inversion -- 2026-06-01 reads Adhika Jyeshtha under amanta and
    Nija Jyeshtha in the book.
    """
    from datetime import timedelta
    from jain_observances.months import PURNIMANTA_MONTHS, canonical

    order = [canonical(m) for m in PURNIMANTA_MONTHS]
    checked = {"advanced": 0, "inverted": 0}
    for offset in range(120):
        day = date(2026, 3, 1) + timedelta(days=offset)
        jd = _reference_jd(day)
        if get_tithi_at_jd(jd, AYANAMSA) <= 15:
            continue
        amanta, _, amanta_adhika = get_hindu_month(jd, AYANAMSA)
        purnimanta, _, purn_adhika = get_purnimanta_month(jd, AYANAMSA)
        a = order.index(canonical(amanta.removeprefix("Adhika ")))
        p = order.index(canonical(purnimanta.removeprefix("Adhika ")))

        if amanta_adhika:
            assert (p, purn_adhika) == (a, False), (
                f"{day}: leaving Adhika {amanta} must land on nija {amanta}, got {purnimanta}"
            )
            checked["inverted"] += 1
        else:
            assert p == (a + 1) % 12, f"{day}: amanta {amanta} -> purnimanta {purnimanta}"
            checked["advanced"] += 1

    assert checked["advanced"] > 30, "window should contain plenty of ordinary Krishna days"
    assert checked["inverted"] > 0, "2026 is an Adhik-Maas year; the inversion must be exercised"
