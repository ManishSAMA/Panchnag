import 'package:flutter_test/flutter_test.dart';
import 'package:jainpanchang/engine/day_reading.dart';
import 'package:jainpanchang/features/choghadiya/choghadiya_state.dart';
import 'package:panchang_engine/panchang_engine.dart';

PanchangDay delhi(CivilDate date) =>
    readDay(DayRequest(date: date, lat: 28.6139, lon: 77.2090, timezone: 'Asia/Kolkata'));

void main() {
  final day = delhi(const CivilDate(2026, 10, 22));
  final following = delhi(const CivilDate(2026, 10, 23));
  const tick = Duration(microseconds: 1);

  test('exactly one slot is current at any instant from sunrise to the next sunrise', () {
    final instants = [
      for (var t = day.sunrise; t.isBefore(day.nextSunrise); t = t.add(const Duration(minutes: 7))) t,
      for (final slot in day.choghadiya) ...[slot.start, slot.end.subtract(tick)],
    ];
    for (final now in instants) {
      final live = liveChoghadiya(day, now)!;
      final holding = day.choghadiya.where((s) => !now.isBefore(s.start) && now.isBefore(s.end));
      expect(holding, [live.slot], reason: '$now');
      expect(live.index, day.choghadiya.indexOf(live.slot));
    }
  });

  test('nothing is current before sunrise or from the next sunrise on', () {
    expect(liveChoghadiya(day, day.sunrise.subtract(tick)), isNull);
    expect(liveChoghadiya(day, day.nextSunrise), isNull);
  });

  test('the countdown reaches 0 at the next slot\'s start, which is then current', () {
    for (var i = 0; i < 15; i++) {
      final end = day.choghadiya[i].end;
      final before = liveChoghadiya(day, end.subtract(tick))!;
      expect(before.index, i);
      expect(before.next, day.choghadiya[i + 1]);
      expect(before.remaining, tick);
      final at = liveChoghadiya(day, end)!;
      expect(at.index, i + 1);
      expect(at.remaining, day.choghadiya[i + 1].end.difference(end));
    }
  });

  test('the last night slot is followed by the next day\'s first slot, when that day is known', () {
    final last = day.choghadiya.last.start;
    expect(liveChoghadiya(day, last)!.next, isNull);
    expect(liveChoghadiya(day, last, following: following)!.next, following.choghadiya.first);
  });

  test('progress runs from 0 at a slot\'s start towards 1 at its end', () {
    final slot = day.choghadiya[4];
    expect(liveChoghadiya(day, slot.start)!.progress, 0);
    final middle = slot.start.add(slot.end.difference(slot.start) ~/ 2);
    expect(liveChoghadiya(day, middle)!.progress, closeTo(0.5, 1e-6));
  });
}
