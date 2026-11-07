import 'package:panchang_engine/panchang_engine.dart';
import 'package:test/test.dart';

const delhi = Location(lat: 28.6139, lon: 77.2090, timezone: 'Asia/Kolkata');
const london = Location(lat: 51.5074, lon: -0.1278, timezone: 'Europe/London');

/// Every field of a day, so two readings compare by value.
List<Object?> fieldsOf(PanchangDay d) => [
  d.date,
  d.sunrise,
  d.sunset,
  d.nextSunrise,
  d.tithis,
  d.jainTithi,
  d.nakshatra,
  d.vara,
  d.month,
  d.amantaMonth,
  d.vikramSamvat,
  d.viraNirvanaSamvat,
  d.shakaSamvat,
  d.choghadiya,
  d.vriddhi,
  d.kshaya,
  d.pachchakkhan.completions,
  d.pachchakkhan.evening,
  d.pachchakkhan.parana,
];

void main() {
  // The Month tab's read (plans/mobile-month-tab.md) shares its lunar months,
  // sunrises and samvat searches across the month; it must answer exactly as
  // a day read of each date does.
  group('a month read equals a day read of each of its dates', () {
    for (final (name, location, year, month, rule) in [
      ('Delhi Oct 2026: kshaya on 3rd and 27th, vriddhi 18th-19th', delhi, 2026, 10, SunriseRule.modern),
      ('Delhi Nov 2026: VNS turns over after Diwali', delhi, 2026, 11, SunriseRule.modern),
      ('Delhi Mar 2029: VS turns over at Adhika Chaitra', delhi, 2029, 3, SunriseRule.traditional),
      ('Delhi Feb 2028: a leap-year February', delhi, 2028, 2, SunriseRule.modern),
      ('London Mar 2026: the clocks change on the 29th', london, 2026, 3, SunriseRule.modern),
    ]) {
      test(name, () {
        const engine = PanchangEngine();
        final days = engine.month(location: location, year: year, month: month, sunriseRule: rule);

        final dates = [for (var d = CivilDate(year, month, 1); d.month == month; d = d.next()) d];
        expect([for (final d in days) d.date], dates);
        for (final day in days) {
          final single = engine.day(location: location, date: day.date, sunriseRule: rule);
          expect(fieldsOf(day), fieldsOf(single), reason: '${day.date}');
        }
      });
    }
  });

  test('the first and last months of the verified range read without leaving it', () {
    const engine = PanchangEngine();
    expect(engine.month(location: delhi, year: 2016, month: 1).first.date, const CivilDate(2016, 1, 1));
    expect(engine.month(location: delhi, year: 2040, month: 12).last.date, const CivilDate(2040, 12, 31));
  });
}
