import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:panchang_engine/panchang_engine.dart';

import '../../engine/day_reading.dart';
import '../../location/location_store.dart';
import '../../settings/settings_store.dart';
import '../today/today_state.dart';

typedef MuhuratReader = Future<PanchangMuhurat> Function(MuhuratRequest request);

/// A day's Muhurat windows, read in the background isolate like the day.
final muhuratReaderProvider = Provider<MuhuratReader>(
  (ref) =>
      (request) async => (await ref.read(engineWorkerProvider.future)).readMuhurat(request),
);

final muhuratReadingProvider = FutureProvider.autoDispose.family<PanchangMuhurat, MuhuratRequest>(
  (ref, request) => ref.watch(muhuratReaderProvider)(request),
);

/// The day the Muhurat screens show: Today's date, place and sunrise rule.
DayRequest watchMuhuratDay(WidgetRef ref) {
  final city = ref.watch(locationProvider)!;
  return DayRequest(
    date: ref.watch(selectedDateProvider),
    lat: city.lat,
    lon: city.lon,
    timezone: city.timezone,
    rule: ref.watch(sunriseRuleProvider),
  );
}
