import 'package:panchang_engine/src/panchang/choghadiya.dart';
import 'package:panchang_engine/src/panchang/pachchakkhan.dart';
import 'package:test/test.dart';

const minute = 1 / 1440;

void main() {
  // Delhi, 22 Oct 2026 (the mockup day): sunrise 06:26:12, sunset 17:44:41 IST.
  const sunrise = 2461335.538, sunset = 2461336.0012, nextSunrise = 2461336.5385;
  final times = pachchakkhanTimes(sunrise: sunrise, sunset: sunset, nextSunrise: nextSunrise);
  double fractionOfDay(double at) => (at - sunrise) / (sunset - sunrise);
  double at(TimedPachchakkhan kind) => times.completions.firstWhere((c) => c.kind == kind).at;

  test('lists the five completion times in order', () {
    expect(times.completions.map((c) => c.kind), TimedPachchakkhan.values);
  });

  test('completion times are strictly increasing and fall between sunrise and sunset', () {
    final instants = times.completions.map((c) => c.at).toList();

    for (var i = 1; i < instants.length; i++) {
      expect(instants[i], greaterThan(instants[i - 1]));
    }
    expect(instants.first, greaterThan(sunrise));
    expect(instants.last, lessThan(sunset));
  });

  test('Navkarsi is 48 minutes after sunrise', () {
    expect(at(TimedPachchakkhan.navkarsi) - sunrise, closeTo(48 * minute, 1e-9));
  });

  test('Porsi, Sadh-Porsi, Purimaddh and Avaddh are 1/4, 3/8, 1/2 and 3/4 of the day', () {
    expect(fractionOfDay(at(TimedPachchakkhan.porsi)), closeTo(1 / 4, 1e-9));
    expect(fractionOfDay(at(TimedPachchakkhan.sadhPorsi)), closeTo(3 / 8, 1e-9));
    expect(fractionOfDay(at(TimedPachchakkhan.purimaddh)), closeTo(1 / 2, 1e-9));
    expect(fractionOfDay(at(TimedPachchakkhan.avaddh)), closeTo(3 / 4, 1e-9));
  });

  // mobile-ui-design.md §3 · Pachchakkhan: both divide the same day into fractions.
  test('Porsi, Sadh-Porsi, Purimaddh and Avaddh start day choghadiya slots 3, 4, 5 and 7', () {
    final slots = choghadiyaSlots(sunrise: sunrise, sunset: sunset, nextSunrise: nextSunrise, vara: 4);

    expect(at(TimedPachchakkhan.porsi), closeTo(slots[2].start, 1e-9));
    expect(at(TimedPachchakkhan.sadhPorsi), closeTo(slots[3].start, 1e-9));
    expect(at(TimedPachchakkhan.purimaddh), closeTo(slots[4].start, 1e-9));
    expect(at(TimedPachchakkhan.avaddh), closeTo(slots[6].start, 1e-9));
  });

  test('the evening pachchakkhans end at sunset', () {
    expect(times.evening, sunset);
  });

  test("Ayambil and Upvas parana is the next day's Navkarsi", () {
    final tomorrow = pachchakkhanTimes(sunrise: nextSunrise, sunset: sunset + 1, nextSunrise: nextSunrise + 1);

    expect(times.parana, tomorrow.completions.first.at);
  });
}
