import 'package:panchang_engine/src/panchang/choghadiya.dart';
import 'package:panchang_engine/src/time/civil_day.dart';
import 'package:test/test.dart';

void main() {
  // Delhi, 22 Oct 2026, a Thursday.
  const sunrise = 2461335.538, sunset = 2461336.0012, nextSunrise = 2461336.5385;
  final slots = choghadiyaSlots(sunrise: sunrise, sunset: sunset, nextSunrise: nextSunrise, vara: 4);

  test('the vara is the civil weekday, 0 = Sunday', () {
    expect(const CivilDate(2026, 10, 25).vara, 0);
    expect(const CivilDate(2026, 10, 22).vara, 4);
    expect(const CivilDate(2026, 10, 24).vara, 6);
  });

  test('eight day slots run sunrise to sunset and eight night slots sunset to the next sunrise', () {
    expect(slots, hasLength(16));
    expect(slots.where((s) => !s.isNight), hasLength(8));
    expect(slots.first.start, sunrise);
    expect(slots[7].end, closeTo(sunset, 1e-9));
    expect(slots[8].start, closeTo(sunset, 1e-9));
    expect(slots.last.end, closeTo(nextSunrise, 1e-9));
  });

  test('slots are contiguous and equal within the day and within the night', () {
    for (var i = 1; i < 16; i++) {
      expect(slots[i].start, closeTo(slots[i - 1].end, 1e-9));
    }
    for (final half in [slots.sublist(0, 8), slots.sublist(8)]) {
      final length = half.first.end - half.first.start;
      for (final s in half) {
        expect(s.end - s.start, closeTo(length, 1e-9));
      }
    }
  });

  // The order and starting slots of choghadiya_service.py (the Python reference).
  test('Sunday starts the day with Udveg and the night with Shubh', () {
    final sunday = choghadiyaSlots(sunrise: sunrise, sunset: sunset, nextSunrise: nextSunrise, vara: 0);
    expect(sunday.map((s) => s.name), <Choghadiya>[
      .udveg, .char, .labh, .amrit, .kaal, .shubh, .rog, .udveg, //
      .shubh, .amrit, .char, .rog, .kaal, .labh, .udveg, .shubh,
    ]);
  });

  test('Thursday starts the day with Shubh and the night with Labh', () {
    expect(slots.first.name, Choghadiya.shubh);
    expect(slots[8].name, Choghadiya.labh);
  });

  test('each day half begins and ends on the same choghadiya, as 8 slots walk a 7-name cycle', () {
    for (var vara = 0; vara < 7; vara++) {
      final day = choghadiyaSlots(sunrise: sunrise, sunset: sunset, nextSunrise: nextSunrise, vara: vara);
      expect(day[7].name, day[0].name, reason: 'vara $vara day');
      expect(day[15].name, day[8].name, reason: 'vara $vara night');
    }
  });

  test('Amrit, Shubh and Labh are auspicious, Char neutral, Udveg, Kaal and Rog inauspicious', () {
    expect(
      {for (final c in Choghadiya.values) c: c.nature},
      {
        Choghadiya.udveg: ChoghadiyaNature.inauspicious,
        Choghadiya.char: ChoghadiyaNature.neutral,
        Choghadiya.labh: ChoghadiyaNature.auspicious,
        Choghadiya.amrit: ChoghadiyaNature.auspicious,
        Choghadiya.kaal: ChoghadiyaNature.inauspicious,
        Choghadiya.shubh: ChoghadiyaNature.auspicious,
        Choghadiya.rog: ChoghadiyaNature.inauspicious,
      },
    );
  });
}
