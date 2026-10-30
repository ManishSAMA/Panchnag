import 'package:flutter/widgets.dart';
import 'package:panchang_engine/panchang_engine.dart';

import '../engine/day_reading.dart';
import '../format/panchang_text.dart';
import '../l10n/app_localizations.dart';
import 'navpad_widgets.dart';

/// The vriddhi, kshaya and tithi-boundary notes for a day, as Today and the
/// Month day panel show them (mobile-ui-design.md §3.1 notes).
List<Widget> dayNotes({
  required PanchangDay reading,
  required AppLocalizations l10n,
  required Lang lang,
  required DateTime Function(DateTime) wall,
}) {
  final tithi = tithiName(reading.jainTithi.index, lang);
  String at(DateTime utc) => instantPhrase(wall(utc), day: reading.date, lang: lang);
  final previousDate = DateTime.utc(reading.date.year, reading.date.month, reading.date.day - 1);
  return [
    if (reading.vriddhi == Vriddhi.firstDay)
      Note(
        icon: NoteIcon.info,
        title: l10n.vriddhiFirstTitle,
        body: l10n.vriddhiFirstBody(shortDate(reading.date.next(), lang), tithi),
      ),
    if (reading.vriddhi == Vriddhi.secondDay)
      Note(
        icon: NoteIcon.info,
        title: l10n.vriddhiSecondTitle,
        body: l10n.vriddhiSecondBody(
          shortDate(CivilDate(previousDate.year, previousDate.month, previousDate.day), lang),
          tithi,
        ),
      ),
    if (reading.kshaya case final kshaya?)
      Note(
        icon: NoteIcon.info,
        title: l10n.kshayaTitle,
        body: switch (spanPhrases(wall(kshaya.startsAt), wall(kshaya.endsAt), day: reading.date, lang: lang)) {
          (final start, final end) => l10n.kshayaBody(
            tithiName(kshaya.lost, lang),
            start,
            end,
            tithiName((kshaya.lost + 28) % 30 + 1, lang),
            tithi,
          ),
        },
      ),
    if (tithiBoundary(reading.jainTithi) case final boundary?)
      Note(
        icon: NoteIcon.alert,
        title: l10n.boundaryTitle,
        body: (boundary.isStart ? l10n.boundaryStartsBody : l10n.boundaryEndsBody)(
          tithi,
          at(boundary.at),
          clockPhrase(wall(reading.jainTithi.reference), lang),
          (boundary.gap.inSeconds / 60).round(),
        ),
      ),
  ];
}
