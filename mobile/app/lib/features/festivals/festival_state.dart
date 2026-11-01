import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:panchang_engine/panchang_engine.dart';

import '../../engine/engine_worker.dart';
import '../../engine/festival_reading.dart';
import '../../format/festival_text.dart';
import '../../location/location_store.dart';
import '../../settings/settings_store.dart';

typedef FestivalReader = Future<List<FestivalOccurrence>> Function(FestivalRequest request);

/// A worker of its own: a festival year takes a second or more on a phone, and
/// queued behind it a day or month read would hold up Today's or Month's first paint.
final festivalWorkerProvider = FutureProvider<EngineWorker>((ref) async {
  final worker = await EngineWorker.spawn(registry: await rootBundle.loadString('assets/festival_registry.json'));
  ref.onDispose(worker.close);
  return worker;
});

final festivalReaderProvider = Provider<FestivalReader>(
  (ref) =>
      (request) async => (await ref.read(festivalWorkerProvider.future)).readFestivals(request),
);

final festivalYearProvider = FutureProvider.family<List<FestivalOccurrence>, FestivalRequest>(
  (ref, request) => ref.watch(festivalReaderProvider)(request),
);

/// The [year]'s festivals for the current place, tradition and sunrise rule;
/// null until they arrive, so screens paint without them first.
List<FestivalOccurrence>? festivalYear(WidgetRef ref, int year) {
  final place = ref.watch(locationProvider)!;
  final request = FestivalRequest(
    year: year,
    lat: place.lat,
    lon: place.lon,
    timezone: place.timezone,
    profile: ref.watch(traditionProvider).id,
    rule: ref.watch(sunriseRuleProvider),
  );
  return ref.watch(festivalYearProvider(request)).value;
}

/// The Festivals tab's chip, kept across restarts (mobile-ui-design.md §3).
final festivalFilterProvider = NotifierProvider<EnumSetting<FestivalFilter>, FestivalFilter>(
  () => EnumSetting('festivals.filter', FestivalFilter.values, FestivalFilter.all),
);
