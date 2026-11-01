import 'dart:typed_data';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:panchang_engine/panchang_engine.dart';
import 'package:share_plus/share_plus.dart';

import '../../engine/day_reading.dart';
import '../../engine/festival_reading.dart';
import '../../l10n/app_localizations.dart';
import '../../l10n/city_name.dart';
import '../../location/location_store.dart';
import '../../settings/settings_store.dart';
import '../festivals/festival_state.dart';
import '../today/today_state.dart';
import 'share_card.dart';

typedef SharedDay = ({Uint8List png, String text, String fileName});

typedef Sharer = Future<void> Function(SharedDay day);

/// Android's share sheet. Nothing leaves the phone except through the app the user picks there.
final sharerProvider = Provider<Sharer>(
  (ref) =>
      (day) => SharePlus.instance.share(
        ShareParams(
          text: day.text,
          files: [XFile.fromData(day.png, mimeType: 'image/png', name: day.fileName)],
          fileNameOverrides: [day.fileName],
        ),
      ),
);

/// Today's share action: the date shown, as a card and as text.
class ShareButton extends ConsumerWidget {
  const ShareButton({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) => IconButton(
    icon: const Icon(Icons.share_outlined),
    tooltip: AppLocalizations.of(context).share,
    onPressed: () => _share(context, ref),
  );

  Future<void> _share(BuildContext context, WidgetRef ref) async {
    final l10n = AppLocalizations.of(context);
    final place = ref.read(locationProvider)!;
    final placeName = place.nameFor(context);
    final view = View.of(context);
    final date = ref.read(selectedDateProvider);
    final rule = ref.read(sunriseRuleProvider);
    final reading = await ref.read(
      dayReadingProvider(DayRequest(date: date, lat: place.lat, lon: place.lon, timezone: place.timezone, rule: rule))
          .future,
    );
    final festivals = await ref.read(
      festivalYearProvider(
        FestivalRequest(
          year: date.year,
          lat: place.lat,
          lon: place.lon,
          timezone: place.timezone,
          profile: ref.read(traditionProvider).id,
          rule: rule,
        ),
      ).future,
    );
    final content = shareCardContent(
      reading: reading,
      month: lunarMonthOf(reading, ref.read(monthSystemProvider)),
      festivals: festivals,
      place: placeName,
      timezone: place.timezone,
      l10n: l10n,
    );
    final png = await renderShareCard(content, view: view);
    await ref.read(sharerProvider)((png: png, text: shareText(content), fileName: _fileName(date)));
  }
}

String _fileName(CivilDate date) => 'jain-panchang-${date.iso}.png';
