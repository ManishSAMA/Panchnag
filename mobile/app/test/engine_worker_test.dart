import 'dart:io';
import 'dart:isolate';

import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:jainpanchang/engine/day_reading.dart';
import 'package:jainpanchang/engine/engine_worker.dart';
import 'package:jainpanchang/engine/festival_reading.dart';
import 'package:jainpanchang/features/festivals/festival_state.dart';
import 'package:jainpanchang/features/today/today_state.dart';
import 'package:panchang_engine/panchang_engine.dart';

const delhi2026 = FestivalRequest(
  year: 2026,
  lat: 28.6139,
  lon: 77.2090,
  timezone: 'Asia/Kolkata',
  profile: 'shwetambar_murtipujak_tapagachchha',
);

String registryJson() => File('assets/festival_registry.json').readAsStringSync();

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

  test('reads a whole month in one request, the same days as reading them one by one', () async {
    final worker = await EngineWorker.spawn();
    addTearDown(worker.close);
    const request = MonthRequest(year: 2026, month: 10, lat: 28.6139, lon: 77.2090, timezone: 'Asia/Kolkata');

    final (month, day) = await (worker.readMonth(request), worker.read(delhi(const CivilDate(2026, 10, 18)))).wait;

    expect(month, hasLength(31));
    expect(month.first.date, const CivilDate(2026, 10, 1));
    expect(month[17].jainTithi, day.jainTithi);
    expect(month[17].vriddhi, day.vriddhi);
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

  test('reads a festival year with the registry it was started with: the engine list', () async {
    final json = registryJson();
    final worker = await EngineWorker.spawn(registry: json);
    addTearDown(worker.close);

    final year = await worker.readFestivals(delhi2026);

    final direct = const PanchangEngine().festivals(
      location: const Location(lat: 28.6139, lon: 77.2090, timezone: 'Asia/Kolkata'),
      year: 2026,
      profile: 'shwetambar_murtipujak_tapagachchha',
      registry: FestivalRegistry.fromJson(json),
    );
    expect(year.map((f) => (f.occurrenceId, f.start, f.end)), direct.map((f) => (f.occurrenceId, f.start, f.end)));
    expect(worker.isolate, isNot(Isolate.current));
  });

  test('a festival year is computed once per place, profile, sunrise rule and year', () {
    final registry = FestivalRegistry.fromJson(registryJson());
    final first = readFestivals(delhi2026, registry: registry);

    expect(identical(readFestivals(delhi2026, registry: registry), first), isTrue);
    const sthanakvasi = FestivalRequest(
      year: 2026,
      lat: 28.6139,
      lon: 77.2090,
      timezone: 'Asia/Kolkata',
      profile: 'shwetambar_sthanakvasi',
    );
    expect(sthanakvasi, isNot(delhi2026));
    expect(identical(readFestivals(sthanakvasi, registry: registry), first), isFalse);
  });

  test('festivals have a worker of their own, so a festival year never holds up a day', () async {
    TestWidgetsFlutterBinding.ensureInitialized();
    final container = ProviderContainer();
    addTearDown(container.dispose);

    final year = await container.read(festivalReaderProvider)(delhi2026);

    expect(year, isNotEmpty);
    expect(container.read(festivalWorkerProvider).value?.reads, 1);
    expect(container.exists(engineWorkerProvider), isFalse);
  });
}
