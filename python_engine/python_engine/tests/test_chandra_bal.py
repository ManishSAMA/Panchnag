"""Chandra Bal: the birth Rashis for which the day's Moon is strong.

Count from the birth Rashi to the Moon's Rashi, the birth Rashi itself being 1.
The 1st, 3rd, 6th, 7th, 10th and 11th are good (Shubh Panchang, "Chandra
Balam"); the 8th (Ashtama Chandra) is the worst. The app shows the six good
Rashis for the day, so no birth Rashi is asked for. Design: plans/muhurat-section.md.
"""

from __future__ import annotations

import pytest

from panchang import chandra_bal_rashis

RASHIS = range(12)  # 0 = Mesha … 11 = Meena
GOOD_COUNTS = {1, 3, 6, 7, 10, 11}


def _count_from(birth: int, moon: int) -> int:
    return (moon - birth) % 12 + 1


@pytest.mark.parametrize("moon", RASHIS)
def test_six_rashis_have_chandra_bal(moon: int) -> None:
    assert len(chandra_bal_rashis(moon)) == 6


@pytest.mark.parametrize("moon", RASHIS)
def test_every_listed_rashi_counts_a_good_place(moon: int) -> None:
    assert {_count_from(birth, moon) for birth in chandra_bal_rashis(moon)} == GOOD_COUNTS


@pytest.mark.parametrize("moon", RASHIS)
def test_the_moons_own_rashi_has_chandra_bal(moon: int) -> None:
    assert moon in chandra_bal_rashis(moon)


@pytest.mark.parametrize("moon", RASHIS)
def test_ashtama_chandra_has_none(moon: int) -> None:
    eighth = (moon - 7) % 12
    assert eighth not in chandra_bal_rashis(moon)


def test_moon_in_mesha() -> None:
    # Mesha 1st, Kumbha 3rd, Vrishchika 6th, Tula 7th, Karka 10th, Mithuna 11th.
    assert chandra_bal_rashis(0) == (0, 2, 3, 6, 7, 10)


@pytest.mark.parametrize("moon", RASHIS)
def test_rashis_come_in_zodiac_order(moon: int) -> None:
    rashis = chandra_bal_rashis(moon)
    assert list(rashis) == sorted(rashis)


@pytest.mark.parametrize("moon", (-1, 12))
def test_a_rashi_outside_the_zodiac_is_refused(moon: int) -> None:
    with pytest.raises(ValueError):
        chandra_bal_rashis(moon)
