import 'package:panchang_engine/src/astro/rise_set.dart';
import 'package:panchang_engine/src/time/civil_day.dart';
import 'package:test/test.dart';

import '../support/reference_rise_set.dart';

void main() {
  const delhi = (lat: 28.6139, lon: 77.2090);
  final anchor = civilDayAnchor(const CivilDate(2026, 10, 21), 'Asia/Kolkata');

  for (final rule in SunriseRule.values) {
    group('${rule.name} rule', () {
      test('sunrise comes after the anchor and before sunset, within the day', () {
        final rise = sunrise(anchor, delhi.lat, delhi.lon, rule);
        final set = sunset(anchor, delhi.lat, delhi.lon, rule);

        expect(rise, greaterThan(anchor));
        expect(rise, lessThan(set));
        expect(set - anchor, lessThan(1));
      });

      test('sunrise is the first rising after the anchor, even far from India', () {
        // Etc/GMT-4 at 65°E: local midnight is 20:00 UT, sunrise a few hours later.
        final oceanAnchor = civilDayAnchor(const CivilDate(2026, 6, 1), 'Etc/GMT-4');
        final rise = sunrise(oceanAnchor, 15.0, 65.0, rule);

        expect(rise - oceanAnchor, inExclusiveRange(0, 0.5));
      });
    });
  }

  test('the traditional sunrise (disc centre, no refraction) is later than the modern one', () {
    final modern = sunrise(anchor, delhi.lat, delhi.lon, SunriseRule.modern);
    final traditional = sunrise(anchor, delhi.lat, delhi.lon, SunriseRule.traditional);

    // Refraction (~34′) plus semidiameter (~16′) take roughly 3-4 minutes at Delhi.
    expect((traditional - modern) * 1440, inInclusiveRange(2.5, 5));
  });

  test('rejects a polar day with no sunrise instead of returning a wrong time', () {
    final midsummer = civilDayAnchor(const CivilDate(2026, 6, 21), 'Europe/Oslo');

    expect(() => sunrise(midsummer, 78.22, 15.65, SunriseRule.modern), throwsStateError);
  });

  // A faster solver must find the very same doubles: festival days are chosen
  // from tithis read at these instants.
  test('finds the same sunrise and sunset, bit for bit, as the solver it replaced', () {
    const places = [
      (lat: 28.6139, lon: 77.2090, zone: 'Asia/Kolkata'),
      (lat: 51.5074, lon: -0.1278, zone: 'Europe/London'),
      (lat: 40.7128, lon: -74.0060, zone: 'America/New_York'),
      (lat: -33.8688, lon: 151.2093, zone: 'Australia/Sydney'),
    ];
    final dates = [for (var d = const CivilDate(2016, 1, 3); d.year < 2041; d = d.plusDays(67)) d];
    final differences = [
      for (final place in places)
        for (final date in dates)
          for (final rule in SunriseRule.values)
            if (civilDayAnchor(date, place.zone) case final anchor)
              if (sunrise(anchor, place.lat, place.lon, rule) != referenceSunrise(anchor, place.lat, place.lon, rule) ||
                  sunset(anchor, place.lat, place.lon, rule) != referenceSunset(anchor, place.lat, place.lon, rule))
                '${place.zone} $date ${rule.name}',
    ];

    expect(dates, hasLength(greaterThan(130)));
    expect(differences, isEmpty);
  });
}
