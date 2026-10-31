import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:panchang_engine/panchang_engine.dart';

import '../../format/panchang_text.dart';
import '../../l10n/app_localizations.dart';
import '../../location/city_time.dart';
import '../../location/location_store.dart';
import '../../shared/navpad_widgets.dart';
import '../today/today_state.dart';
import 'choghadiya_screen.dart';
import 'choghadiya_state.dart';

/// Today's navy band (mobile-ui-design.md §3.1): the current choghadiya, its
/// quality, the next slot and when this one ends. Shown only when [date] is today.
class ChoghadiyaBand extends ConsumerWidget {
  const ChoghadiyaBand({super.key, required this.date, this.topGap = 0});

  final CivilDate date;
  final double topGap;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final city = ref.watch(locationProvider)!;
    final now = currentTime(ref);
    if (date != todayIn(city.timezone, now)) return const SizedBox.shrink();
    final reading = watchChoghadiya(ref, city: city, date: date, now: now);
    final live = reading == null ? null : liveChoghadiya(reading.day, now, following: reading.following);
    if (live == null) return const SizedBox.shrink();
    final l10n = AppLocalizations.of(context);
    final lang = langOf(context);
    final next = live.next;
    return Padding(
      padding: EdgeInsets.only(top: topGap),
      child: Builder(
        builder: (context) => Band(
          colour: BandColour.navy,
          title: l10n.choghadiyaBandTitle(
            choghadiyaName(live.slot.name, lang),
            qualityText(l10n, live.slot.name.nature),
          ),
          subtitle: next == null
              ? l10n.choghadiyaTitle
              : l10n.choghadiyaBandNext(choghadiyaName(next.name, lang), qualityText(l10n, next.name.nature)),
          value: l10n.untilAndCountdown(
            clockTime(roundDownToMinute(cityWall(live.slot.end, city.timezone)), lang).time,
            durationText(live.remaining, lang),
          ),
          onTap: () {
            final box = context.findRenderObject()! as RenderBox;
            context.push('/choghadiya', extra: box.localToGlobal(Offset.zero) & box.size);
          },
        ),
      ),
    );
  }
}
