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

  test('the evening pachchakkhans end at sunset', () {
    expect(times.evening, sunset);
  });

  test("Ayambil and Upvas parana is the next day's Navkarsi", () {
    final tomorrow = pachchakkhanTimes(sunrise: nextSunrise, sunset: sunset + 1, nextSunrise: nextSunrise + 1);

    expect(times.parana, tomorrow.completions.first.at);
  });

  group('next completion', () {
    test('before sunrise it is Navkarsi', () {
      expect(times.nextAt(sunrise - 0.1), TimedPachchakkhan.navkarsi);
    });

    test('from sunrise until Avaddh exactly one is next: the first still ahead', () {
      for (var now = sunrise; now < at(TimedPachchakkhan.avaddh); now += 7 * minute) {
        final next = times.nextAt(now)!;
        final ahead = times.completions.where((c) => c.at > now);

        expect(next, ahead.first.kind);
      }
    });

    test('a time is done from its own instant on', () {
      expect(times.nextAt(at(TimedPachchakkhan.porsi)), TimedPachchakkhan.sadhPorsi);
    });

    test('after Avaddh there is none', () {
      expect(times.nextAt(at(TimedPachchakkhan.avaddh)), isNull);
      expect(times.nextAt(sunset + 0.1), isNull);
    });
  });
}
