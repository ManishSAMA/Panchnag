import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:panchang_engine/panchang_engine.dart';

import '../../engine/day_reading.dart';
import '../../location/city_time.dart';
import '../../location/location_store.dart';
import '../today/today_state.dart';

typedef MonthReader = Future<List<PanchangDay>> Function(MonthRequest request);

/// A month is one engine call, sharing its lunar months and sunrises (plans/mobile-month-tab.md).
final monthReaderProvider = Provider<MonthReader>(
  (ref) =>
      (request) async => (await ref.read(engineWorkerProvider.future)).readMonth(request),
);

final monthReadingProvider = FutureProvider.autoDispose.family<List<PanchangDay>, MonthRequest>(
  (ref, request) => ref.watch(monthReaderProvider)(request),
);

/// The month on show and the day picked in it. The pick is the Month tab's
/// own: only "Open full day" moves Today's [selectedDateProvider].
typedef MonthView = ({int year, int month, CivilDate selected});

final monthViewProvider = NotifierProvider<MonthViewNotifier, MonthView>(MonthViewNotifier.new);

final class MonthViewNotifier extends Notifier<MonthView> {
  @override
  MonthView build() {
    ref.watch(locationProvider);
    return _current();
  }

  MonthView _current() {
    final today = _today();
    return (year: today.year, month: today.month, selected: today);
  }

  CivilDate _today() => todayIn(ref.read(locationProvider)!.timezone, ref.read(clockProvider)());

  /// The header disables its arrows at [firstDay]'s and [lastDay]'s months.
  void shift(int months) {
    final first = DateTime.utc(state.year, state.month + months);
    final today = _today();
    final holdsToday = today.year == first.year && today.month == first.month;
    state = (year: first.year, month: first.month, selected: holdsToday ? today : CivilDate(first.year, first.month, 1));
  }

  void goToday() => state = _current();

  /// Today's bands open Month on their date.
  void show(CivilDate date) => state = (year: date.year, month: date.month, selected: date);

  void select(CivilDate date) => state = (year: state.year, month: state.month, selected: date);
}
