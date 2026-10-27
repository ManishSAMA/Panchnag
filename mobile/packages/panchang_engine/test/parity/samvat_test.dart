// L3 parity: Vikram Samvat and Vira Nirvana Samvat (exact) for every core
// fixture day, against Python.
import 'package:panchang_engine/src/astro/rise_set.dart';
import 'package:panchang_engine/src/calendar/samvat.dart';
import 'package:panchang_engine/src/time/civil_day.dart';
import 'package:test/test.dart';

import '../support/fixtures.dart';

void main() {
  for (final loc in coreLocations()) {
    for (final rule in SunriseRule.values) {
      test('${loc.slug} ${rule.name}', () {
        // Both new-year days depend only on the year and the day's clock offset.
        final newYears = <(int, Duration), (CivilDate, CivilDate)>{};
        (CivilDate, CivilDate) newYearsOf(CivilDate date) {
          final offset = standardOffset(date, loc.timezone);
          return newYears.putIfAbsent((date.year, offset), () {
            final args = (lat: loc.lat, lon: loc.lon, offset: offset);
            return (
              chaitraShuklaPratipada(date.year, lat: args.lat, lon: args.lon, utcOffset: args.offset, rule: rule),
              diwali(date.year, lat: args.lat, lon: args.lon, utcOffset: args.offset, rule: rule),
            );
          });
        }

        final mismatches = <String>[];
        for (final row in dayRows(loc.slug, rule.name)) {
          final date = CivilDate.parse(row['date']! as String);
          final (chaitraShukla1, diwaliDay) = newYearsOf(date);
          final vs = vikramSamvat(date, chaitraShukla1: chaitraShukla1);
          final vns = viraNirvanaSamvat(date, diwali: diwaliDay);
          if (vs != row['vikram_samvat'] || vns != row['vira_nirvana_samvat']) {
            mismatches.add('$date VS $vs/${row['vikram_samvat']} VNS $vns/${row['vira_nirvana_samvat']} '
                '(new year $chaitraShukla1, Diwali $diwaliDay)');
          }
        }

        expect(mismatches, isEmpty);
      });
    }
  }
}
