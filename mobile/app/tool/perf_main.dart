// Engine timings in AOT (profile or release) on a device:
//   flutter run --profile -t tool/perf_main.dart
// Prints PERF lines to the log (plans/mobile-phase2-dart-engine.md, M4 budget:
// Today < 100 ms, a 31-day month < 1 s; plans/mobile-phase5-festivals.md §4:
// one profile's festival year well under 1 s). The festival timings read the
// registry from the app's assets/festival_registry.json.
import 'dart:async';
import 'dart:isolate';

import 'package:flutter/services.dart';
import 'package:flutter/widgets.dart';
import 'package:jainpanchang/engine/day_reading.dart';
import 'package:jainpanchang/engine/engine_worker.dart';
import 'package:panchang_engine/panchang_engine.dart';

DayRequest delhi(CivilDate date) => DayRequest(date: date, lat: 28.6139, lon: 77.2090, timezone: 'Asia/Kolkata');

const delhiPlace = Location(lat: 28.6139, lon: 77.2090, timezone: 'Asia/Kolkata');
const tapagachchha = 'shwetambar_murtipujak_tapagachchha';
const sthanakvasi = 'shwetambar_sthanakvasi';

int ms(Stopwatch s) => s.elapsedMilliseconds;

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  runApp(const Center(child: Text('perf', textDirection: TextDirection.ltr)));

  final first = Stopwatch()..start();
  readDay(delhi(const CivilDate(2026, 10, 22)));
  debugPrint('PERF first read (cold, time zones loading): ${ms(first)} ms');

  final days = [for (var d = 1; d <= 31; d++) CivilDate(2026, 12, d)];
  final each = <int>[];
  for (final date in days.take(20)) {
    final s = Stopwatch()..start();
    readDay(delhi(date));
    each.add(s.elapsedMicroseconds);
  }
  each.sort();
  debugPrint('PERF one day (warm): median ${each[10] ~/ 1000} ms, worst ${each.last ~/ 1000} ms');

  final month = Stopwatch()..start();
  for (final date in days) {
    readDay(delhi(date));
  }
  debugPrint('PERF 31-day month (one isolate, warm): ${ms(month)} ms');

  final spawn = Stopwatch()..start();
  final worker = await EngineWorker.spawn();
  final spawned = ms(spawn);
  final firstRead = Stopwatch()..start();
  await worker.read(delhi(days.first));
  final firstWorkerRead = 'spawn $spawned ms, first read ${ms(firstRead)} ms';
  final viaWorker = <int>[];
  for (final date in days.skip(1).take(10)) {
    final s = Stopwatch()..start();
    await worker.read(delhi(date));
    viaWorker.add(ms(s));
  }
  viaWorker.sort();
  debugPrint(
    'PERF worker: $firstWorkerRead; then median ${viaWorker[5]} ms, worst ${viaWorker.last} ms',
  );
  final months = <int>[];
  for (final (year, month) in [(2026, 12), (2026, 10), (2026, 3), (2026, 11)]) {
    final s = Stopwatch()..start();
    await worker.readMonth(
      MonthRequest(year: year, month: month, lat: 28.6139, lon: 77.2090, timezone: 'Asia/Kolkata'),
    );
    months.add(ms(s));
  }
  debugPrint('PERF month call via worker (Dec, Oct, Mar, Nov 2026): ${months.join(', ')} ms');
  worker.close();
  await festivalTimings();
  debugPrint('PERF done');
}

/// One profile's year from scratch: on the engine API in this isolate, then in
/// a long-lived background isolate as the engine worker runs it.
Future<void> festivalTimings() async {
  final json = await rootBundle.loadString('assets/festival_registry.json');
  final registry = FestivalRegistry.fromJson(json);

  final direct = <String>[];
  for (final (year, profile) in [(2026, tapagachchha), (2027, tapagachchha), (2028, tapagachchha), (2026, sthanakvasi)]) {
    final s = Stopwatch()..start();
    final rows = festivalYear(registry, year, profile).length;
    direct.add('$year $profile ${ms(s)} ms ($rows rows)');
  }
  debugPrint('PERF festival year, engine API (Delhi): ${direct.join('; ')}');

  final answers = ReceivePort();
  final replies = StreamIterator<Object?>(answers);
  final spawn = Stopwatch()..start();
  final isolate = await Isolate.spawn(_serveFestivals, (answers.sendPort, json));
  await replies.moveNext();
  final requests = replies.current! as SendPort;
  final spawned = ms(spawn);
  final viaIsolate = <int>[];
  for (final year in [2026, 2027, 2028, 2029]) {
    final s = Stopwatch()..start();
    requests.send(year);
    await replies.moveNext();
    viaIsolate.add(ms(s));
  }
  answers.close();
  isolate.kill(priority: Isolate.immediate);
  debugPrint('PERF festival year via a background isolate (spawn and registry $spawned ms; '
      '2026-2029, $tapagachchha): ${viaIsolate.join(', ')} ms');
}

List<FestivalOccurrence> festivalYear(FestivalRegistry registry, int year, String profile) =>
    const PanchangEngine().festivals(location: delhiPlace, year: year, profile: profile, registry: registry);

/// Stands in for the engine worker until it serves festival years: parses the
/// registry once, then answers each year with its row count.
void _serveFestivals((SendPort, String) start) {
  final (answers, json) = start;
  final registry = FestivalRegistry.fromJson(json);
  final requests = ReceivePort();
  answers.send(requests.sendPort);
  requests.listen((year) => answers.send(festivalYear(registry, year! as int, tapagachchha).length));
}
