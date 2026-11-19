import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:panchang_engine/panchang_engine.dart';

import '../../engine/day_reading.dart';
import '../../format/muhurat_text.dart';
import '../../format/panchang_text.dart';
import '../../l10n/app_localizations.dart';
import '../../location/city_time.dart';
import '../../location/location_store.dart';
import '../../settings/settings_store.dart';
import '../../shared/mark.dart';
import '../../shared/navpad_icons.dart';
import '../../shared/navpad_widgets.dart';
import '../choghadiya/choghadiya_screen.dart';
import '../choghadiya/choghadiya_state.dart';
import '../today/today_state.dart';
import 'muhurat_state.dart';

/// The windows the band names, in its order when several run at once.
/// Panchak and Gandmool are left to the grid: they run for days, and the
/// band would hide the choghadiya all that time (user decision 2026-11-19).
enum BadWindow { rahuKaal, bhadra, yamaganda, gulika }

/// The first [BadWindow] running at [now], with its end; null when none runs.
({BadWindow kind, DateTime end})? badWindowAt(PanchangMuhurat m, DateTime now) {
  final windows = <(BadWindow, TimeWindow)>[
    (BadWindow.rahuKaal, m.rahuKaal),
    for (final w in m.bhadra)
      if (w.residence == BhadraResidence.earth) (BadWindow.bhadra, (start: w.start, end: w.end)),
    (BadWindow.yamaganda, m.yamaganda),
    (BadWindow.gulika, m.gulika),
  ];
  for (final (kind, w) in windows) {
    if (runsAt(now, start: w.start, end: w.end)) return (kind: kind, end: w.end);
  }
  return null;
}

/// The first Amrit, Shubh or Labh slot that starts after [now].
ChoghadiyaPeriod? nextGoodChoghadiya(List<ChoghadiyaPeriod> slots, DateTime now) {
  for (final slot in slots) {
    if (slot.start.isAfter(now) && slot.name.nature == ChoghadiyaNature.auspicious) return slot;
  }
  return null;
}

/// Today's navy band: a window to avoid while one runs, else the choghadiya
/// slot running now; when it ends; and the next good choghadiya. Shown only
/// when [date] is today. A push opens the Muhurat grid.
class MuhuratBand extends ConsumerWidget {
  const MuhuratBand({super.key, required this.date, this.topGap = 0});

  final CivilDate date;
  final double topGap;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final city = ref.watch(locationProvider)!;
    final now = currentTime(ref);
    if (date != todayIn(city.timezone, now)) return const SizedBox.shrink();
    final reading = watchChoghadiya(ref, city: city, date: date, now: now);
    final live = reading == null ? null : liveChoghadiya(reading.day, now, following: reading.following);
    if (reading == null || live == null) return const SizedBox.shrink();
    // Before sunrise the night running is the previous day's, and so are its windows.
    final day = DayRequest(
      date: reading.day.date,
      lat: city.lat,
      lon: city.lon,
      timezone: city.timezone,
      rule: ref.watch(sunriseRuleProvider),
    );
    final muhurat = ref.watch(muhuratReadingProvider(MuhuratRequest(day))).value;
    final bad = muhurat == null ? null : badWindowAt(muhurat, now);
    final l10n = AppLocalizations.of(context);
    final lang = langOf(context);
    DateTime wall(DateTime utc) => roundDownToMinute(cityWall(utc, city.timezone));
    final next = nextGoodChoghadiya([...reading.day.choghadiya, ...?reading.following?.choghadiya], now);
    final end = bad?.end ?? live.slot.end;
    // A night slot can end after midnight: an end past today carries its date.
    final endWall = wall(end);
    final endText = CivilDate(endWall.year, endWall.month, endWall.day) == date
        ? clockTime(endWall, lang).time
        : glued(instantPhrase(endWall, day: date, lang: lang));
    final title = switch (bad?.kind) {
      null => l10n.choghadiyaBandTitle(choghadiyaName(live.slot.name, lang), qualityText(l10n, live.slot.name.nature)),
      final kind => '${_badName(l10n, kind)} · ${markText(l10n, Mark.avoid)}',
    };
    return Padding(
      padding: EdgeInsets.only(top: topGap),
      child: Band(
        colour: BandColour.navy,
        icon: const NavpadIcon(NavpadGlyph.abhijit),
        title: title,
        subtitle: next == null
            ? l10n.muhuratTitle
            : l10n.muhuratBandNextGood(
                choghadiyaName(next.name, lang),
                glued(clockRange(wall(next.start), wall(next.end), lang)),
              ),
        value: l10n.untilAndCountdown(endText, durationText(end.difference(now), lang)),
        onTap: () => context.push('/muhurat'),
      ),
    );
  }
}

String _badName(AppLocalizations l10n, BadWindow kind) => switch (kind) {
  BadWindow.rahuKaal => l10n.rahuKaal,
  BadWindow.bhadra => l10n.bhadra,
  BadWindow.yamaganda => l10n.yamaganda,
  BadWindow.gulika => l10n.gulika,
};
