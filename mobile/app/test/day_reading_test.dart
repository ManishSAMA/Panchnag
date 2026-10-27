import 'package:flutter_test/flutter_test.dart';
import 'package:jainpanchang/engine/day_reading.dart';
import 'package:panchang_engine/panchang_engine.dart';

const delhiRequest = (lat: 28.6139, lon: 77.2090, timezone: 'Asia/Kolkata');

PanchangDay delhi(int year, int month, int day) => readDay(
  DayRequest(
    date: CivilDate(year, month, day),
    lat: delhiRequest.lat,
    lon: delhiRequest.lon,
    timezone: delhiRequest.timezone,
  ),
);

/// The calendar itself (vriddhi, kshaya, pachchakkhan, parity with Python) is
/// tested in the engine; the app adds only the boundary note.
void main() {
  test('the request reaches the engine: date, place and sunrise rule', () {
    const request = DayRequest(
      date: CivilDate(2026, 10, 22),
      lat: 28.6139,
      lon: 77.2090,
      timezone: 'Asia/Kolkata',
      rule: SunriseRule.traditional,
    );
    final day = readDay(request);
    final modern = delhi(2026, 10, 22);

    expect(day.date, request.date);
    expect(day.sunrise.isAfter(modern.sunrise), isTrue);
    expect((day.vikramSamvat, day.viraNirvanaSamvat), (2083, 2552));
  });

  group('tithi boundary near the reference instant', () {
    test('is flagged exactly when the Jain tithi starts or ends within 45 minutes of it', () {
      for (var d = 1; d <= 30; d++) {
        final jain = delhi(2026, 11, d).jainTithi;
        final startsNear = jain.reference.difference(jain.startsAt) <= boundaryWindow;
        final endsNear = jain.endsAt.difference(jain.reference) <= boundaryWindow;

        expect(tithiBoundary(jain) != null, startsNear || endsNear, reason: 'Nov $d');
      }
    });

    test('27 Nov 2026: Krishna Tritiya ends 32 minutes after the reference (mockup board 1b)', () {
      final boundary = tithiBoundary(delhi(2026, 11, 27).jainTithi)!;

      expect(boundary.isStart, isFalse);
      expect(boundary.gap.inMinutes, inInclusiveRange(31, 32));
    });

    // Found by scanning the engine (Delhi, modern sunrise); the Dart Jain tithi
    // matches Python exactly on every core/delhi day 2016-2040.
    test('23 Feb 2026: the Jain tithi began 7 minutes before the reference', () {
      final boundary = tithiBoundary(delhi(2026, 2, 23).jainTithi)!;

      expect(boundary.isStart, isTrue);
      expect(boundary.gap.inMinutes, inInclusiveRange(6, 7));
    });

    test('the nearer change wins when both fall in the window', () {
      final reference = DateTime.utc(2026, 1, 1, 3);
      final jain = (
        index: 5,
        startsAt: reference.subtract(const Duration(minutes: 40)),
        endsAt: reference.add(const Duration(minutes: 30)),
        reference: reference,
      );

      expect(tithiBoundary(jain), (at: jain.endsAt, isStart: false, gap: const Duration(minutes: 30)));
    });

    test('a change exactly 45 minutes away still counts; one a second further does not', () {
      final reference = DateTime.utc(2026, 1, 1, 3);
      JainTithi ending(Duration after) => (
        index: 5,
        startsAt: reference.subtract(const Duration(hours: 20)),
        endsAt: reference.add(after),
        reference: reference,
      );

      expect(tithiBoundary(ending(boundaryWindow)), isNotNull);
      expect(tithiBoundary(ending(boundaryWindow + const Duration(seconds: 1))), isNull);
    });
  });
}
