import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:panchang_engine/panchang_engine.dart';

import '../../engine/day_reading.dart';
import '../../engine/engine_worker.dart';
import '../../location/city_time.dart';
import '../../location/location_store.dart';

/// The verified range (mobile-ui-design.md §1): date navigation stops here.
const CivilDate firstDay = CivilDate(2016, 1, 1);
const CivilDate lastDay = CivilDate(2040, 12, 31);

final clockProvider = Provider<DateTime Function()>((ref) => DateTime.now);

/// The current instant, ticking once a second for the countdowns.
final nowProvider = StreamProvider<DateTime>((ref) async* {
  final clock = ref.watch(clockProvider);
  yield clock();
  yield* Stream.periodic(const Duration(seconds: 1), (_) => clock());
});

typedef DayReader = Future<PanchangDay> Function(DayRequest request);

/// The engine's background isolate, started on the first read and kept for the app's life.
final engineWorkerProvider = FutureProvider<EngineWorker>((ref) async {
  final worker = await EngineWorker.spawn();
  ref.onDispose(worker.close);
  return worker;
});

/// Engine work runs in the background isolate so the UI never stalls on it.
final dayReaderProvider = Provider<DayReader>(
  (ref) =>
      (request) async => (await ref.read(engineWorkerProvider.future)).read(request),
);

final dayReadingProvider = FutureProvider.autoDispose.family<PanchangDay, DayRequest>(
  (ref, request) => ref.watch(dayReaderProvider)(request),
);

/// The date Today shows; it starts on the city's today.
final selectedDateProvider = NotifierProvider<SelectedDate, CivilDate>(SelectedDate.new);

final class SelectedDate extends Notifier<CivilDate> {
  @override
  CivilDate build() => _today();

  CivilDate _today() => todayIn(ref.watch(locationProvider)!.timezone, ref.read(clockProvider)());

  void shift(int days) {
    final moved = DateTime.utc(state.year, state.month, state.day + days);
    // The navigator disables its arrows at firstDay and lastDay.
    state = CivilDate(moved.year, moved.month, moved.day);
  }

  void goToday() => state = _today();
}

/// The ticking clock once it has started, the fixed clock before.
DateTime currentTime(WidgetRef ref) => ref.watch(nowProvider).value ?? ref.read(clockProvider)();
