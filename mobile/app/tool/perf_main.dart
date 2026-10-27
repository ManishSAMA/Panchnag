// Engine timings in AOT (profile or release) on a device:
//   flutter run --profile -t tool/perf_main.dart
// Prints PERF lines to the log (plans/mobile-phase2-dart-engine.md, M4 budget:
// Today < 100 ms, a 31-day month < 1 s).
import 'package:flutter/widgets.dart';
import 'package:jainpanchang/engine/day_reading.dart';
import 'package:jainpanchang/engine/engine_worker.dart';
import 'package:panchang_engine/panchang_engine.dart';

DayRequest delhi(CivilDate date) => DayRequest(date: date, lat: 28.6139, lon: 77.2090, timezone: 'Asia/Kolkata');

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
  worker.close();
  debugPrint('PERF done');
}
