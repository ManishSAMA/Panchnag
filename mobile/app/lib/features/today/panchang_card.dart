import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:panchang_engine/panchang_engine.dart';

import '../../engine/day_reading.dart';
import '../../format/panchang_text.dart';
import '../../l10n/app_localizations.dart';
import '../../shared/panchang_section.dart';
import '../../theme/pothi.dart';
import 'today_state.dart';

/// Today's Panchang under the hero: the Jain tithi, the nakshatra (with its
/// pada and signs), the yoga and the karana, each with its end, and the
/// weekday, then the way into Full Panchang (plans/panchang-section-and-pothi.md).
/// The yoga and karana lines arrive with the section read; the rest paint
/// at once.
class PanchangCard extends ConsumerWidget {
  const PanchangCard({
    super.key = const Key('today-panchang-card'),
    required this.day,
    required this.request,
    required this.isToday,
  });

  final PanchangDay day;
  final DayRequest request;
  final bool isToday;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l10n = AppLocalizations.of(context);
    final lang = langOf(context);
    final p = Theme.of(context).extension<Pothi>() ?? Pothi.light;
    final section = ref
        .watch(sectionReadingProvider(SectionRequest(request)))
        .value;
    SectionLine line(
      String key,
      String name, {
      DateTime? until,
      List<int> rashis = const [],
    }) => SectionLine(
      key: Key('today-panchang-$key'),
      name: name,
      day: day.date,
      timezone: request.timezone,
      until: until,
      rashis: rashis,
    );
    return Padding(
      padding: const EdgeInsets.fromLTRB(18, 0, 18, 12),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          PothiHeading(
            title: isToday ? l10n.todayPanchangHeading : l10n.panchangHeading,
          ),
          SectionRow(
            label: l10n.tithiLabel,
            lines: [
              line(
                'tithi',
                tithiName(day.jainTithi.index, lang),
                until: day.jainTithi.endsAt,
              ),
            ],
          ),
          SectionRow(
            label: l10n.nakshatra,
            lines: [
              line(
                'nakshatra',
                l10n.nakshatraWithPada(
                  nakshatraName(day.nakshatra.index, lang),
                  day.nakshatra.pada,
                ),
                until: day.nakshatra.endsAt,
                rashis: nakshatraRashis(day.nakshatra.index),
              ),
            ],
          ),
          if (section != null) ...[
            SectionRow(
              label: l10n.yogaLabel,
              lines: [
                line(
                  'yoga',
                  yogaName(section.yogas.first.index, lang),
                  until: section.yogas.first.endsAt,
                ),
              ],
            ),
            SectionRow(
              label: l10n.karanaLabel,
              lines: [
                line(
                  'karana',
                  karanaName(section.karanas.first.index, lang),
                  until: section.karanas.first.endsAt,
                ),
              ],
            ),
          ],
          SectionRow(
            label: l10n.varaLabel,
            lines: [line('vara', weekdayName(day.date, lang))],
          ),
          Align(
            alignment: AlignmentDirectional.centerEnd,
            // The arrow is an icon: Mukta has no "→".
            child: TextButton.icon(
              key: const Key('today-full-panchang'),
              style: TextButton.styleFrom(
                foregroundColor: p.accent,
                minimumSize: const Size(48, 48),
              ),
              onPressed: () => context.push('/full-panchang'),
              icon: const Icon(Icons.arrow_forward, size: 18),
              iconAlignment: IconAlignment.end,
              label: Text(l10n.seeFullPanchang),
            ),
          ),
        ],
      ),
    );
  }
}
