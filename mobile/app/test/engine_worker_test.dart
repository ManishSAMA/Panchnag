import 'dart:isolate';

import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:jainpanchang/engine/day_reading.dart';
import 'package:jainpanchang/engine/engine_worker.dart';
import 'package:jainpanchang/features/today/today_state.dart';
import 'package:panchang_engine/panchang_engine.dart';

DayRequest delhi(CivilDate date) => DayRequest(date: date, lat: 28.6139, lon: 77.2090, timezone: 'Asia/Kolkata');

void main() {
  test('answers requests sent together, each with its own day, off the calling isolate', () async {
    final worker = await EngineWorker.spawn();
    addTearDown(worker.close);
    final dates = [for (var d = 20; d <= 23; d++) CivilDate(2026, 10, d)];

    final days = await Future.wait([for (final date in dates) worker.read(delhi(date))]);

    expect(days.map((day) => day.date), dates);
    expect(days.map((day) => day.jainTithi.index), [for (final date in dates) readDay(delhi(date)).jainTithi.index]);
    expect(worker.isolate, isNot(Isolate.current));
  });

  test('passes an engine error back to the caller and keeps working', () async {
    final worker = await EngineWorker.spawn();
    addTearDown(worker.close);
    // The Sun neither rises nor sets near the North Pole in June.
    const polar = DayRequest(date: CivilDate(2026, 6, 21), lat: 89.5, lon: 0, timezone: 'UTC');

    await expectLater(worker.read(polar), throwsA(isA<RemoteError>()));
    expect((await worker.read(delhi(const CivilDate(2026, 10, 22)))).jainTithi.index, 11);
  });

  test('the app reads through one worker, started once', () async {
    final container = ProviderContainer();
    addTearDown(container.dispose);
    final read = container.read(dayReaderProvider);

    final day = await read(delhi(const CivilDate(2026, 10, 22)));
    await read(delhi(const CivilDate(2026, 10, 23)));

    expect(day.jainTithi.index, 11);
    expect(container.read(engineWorkerProvider).value?.reads, 2);
  });
}
