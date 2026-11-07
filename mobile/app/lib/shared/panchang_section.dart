/// The Panchang section's lines: a name with, when it ends, its end time.
/// Times are slightly bold and the connective word ("तक", "until") is
/// quieter, so the eye lands on the name and the time
/// (plans/panchang-section-and-pothi.md).
library;

import 'package:flutter/material.dart';
import 'package:panchang_engine/panchang_engine.dart';

import '../format/panchang_text.dart';
import '../l10n/app_localizations.dart';
import '../location/city_time.dart';
import '../theme/navpad.dart';
import '../theme/pothi.dart';
import 'panchang_symbols.dart';

/// The signs are drawn inside their square with a margin, and Devanagari
/// stands tall: at 1.25× the font size a sign reads as tall as the text.
const double glyphScale = 1.25;

PanchangGlyph zodiacGlyph(int rashi) =>
    PanchangGlyph.values[PanchangGlyph.aries.index + rashi];

/// One line: zodiac signs (Rashi indices, 0 = Mesha), a name and, if given,
/// "until" the end, dated when the end falls off [day].
class SectionLine extends StatelessWidget {
  const SectionLine({
    super.key,
    required this.name,
    required this.day,
    required this.timezone,
    this.rashis = const [],
    this.until,
  });

  final String name;
  final CivilDate day;
  final String timezone;
  final List<int> rashis;
  final DateTime? until;

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    final lang = langOf(context);
    final p = Theme.of(context).extension<Pothi>() ?? Pothi.light;
    final base = Theme.of(context).textTheme.bodyLarge!.copyWith(color: p.ink);
    final quiet = TextStyle(color: p.secondary);
    const strong = TextStyle(fontWeight: FontWeight.w600);
    final end = switch (until) {
      null => const <InlineSpan>[],
      final utc => _endSpans(
        roundDownToMinute(cityWall(utc, timezone)),
        lang,
        l10n,
        quiet,
        strong,
      ),
    };
    return Text.rich(
      TextSpan(
        style: base,
        children: [
          for (final (k, rashi) in rashis.indexed)
            WidgetSpan(
              alignment: PlaceholderAlignment.middle,
              child: Padding(
                padding: EdgeInsets.only(right: k == rashis.length - 1 ? 6 : 2),
                child: PanchangSymbol(
                  zodiacGlyph(rashi),
                  size: base.fontSize! * glyphScale,
                  color: p.ink,
                ),
              ),
            ),
          TextSpan(text: name),
          ...end,
        ],
      ),
      textAlign: TextAlign.end,
    );
  }

  List<InlineSpan> _endSpans(
    DateTime wall,
    Lang lang,
    AppLocalizations l10n,
    TextStyle quiet,
    TextStyle strong,
  ) {
    final date = CivilDate(wall.year, wall.month, wall.day);
    // Non-breaking spaces keep a date, a time and its period word, and the
    // time and तक, on one line: a wrap never strands "AM" or "तक".
    final dated = date == day ? '' : '${_glued(shortDate(date, lang))}, ';
    final time = TextSpan(text: _glued(clockPhrase(wall, lang)), style: strong);
    final word = TextSpan(text: l10n.untilWord, style: quiet);
    return switch (lang) {
      Lang.hi => [
        TextSpan(text: ' $dated'),
        time,
        const TextSpan(text: _nbsp),
        word,
      ],
      Lang.en => [
        const TextSpan(text: ' '),
        word,
        TextSpan(text: ' $dated'),
        time,
      ],
    };
  }
}

/// "तुला 21 गते" / "Tula (Libra), day 21", the count slightly bold.
class GataLine extends StatelessWidget {
  const GataLine({super.key, required this.gata});

  final Gata gata;

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    final lang = langOf(context);
    final p = Theme.of(context).extension<Pothi>() ?? Pothi.light;
    final quiet = TextStyle(color: p.secondary);
    final count = TextSpan(
      text: '${gata.day}',
      style: const TextStyle(fontWeight: FontWeight.w600),
    );
    final word = TextSpan(text: l10n.gataWord, style: quiet);
    final rashi = rashiName(gata.rashi, lang);
    return Text.rich(
      TextSpan(
        style: Theme.of(context).textTheme.bodyLarge!.copyWith(color: p.ink),
        children: switch (lang) {
          Lang.hi => [
            TextSpan(text: '$rashi '),
            count,
            const TextSpan(text: ' '),
            word,
          ],
          Lang.en => [
            TextSpan(text: '$rashi, '),
            word,
            const TextSpan(text: ' '),
            count,
          ],
        },
      ),
      textAlign: TextAlign.end,
    );
  }
}

/// A Pothi group heading: red, with a red rule under it.
class PothiHeading extends StatelessWidget {
  const PothiHeading({super.key, required this.title});

  final String title;

  @override
  Widget build(BuildContext context) {
    final p = Theme.of(context).extension<Pothi>() ?? Pothi.light;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Semantics(
          header: true,
          child: Text(
            title,
            style: NavpadType.displayGroup.copyWith(
              color: p.accent,
              fontSize: 23,
            ),
          ),
        ),
        Container(
          margin: const EdgeInsets.only(top: 5),
          height: 2,
          color: p.accent,
        ),
      ],
    );
  }
}

/// A label on the left and its lines on the right, ruled underneath.
class SectionRow extends StatelessWidget {
  const SectionRow({super.key, required this.label, required this.lines});

  final String label;
  final List<Widget> lines;

  @override
  Widget build(BuildContext context) {
    final p = Theme.of(context).extension<Pothi>() ?? Pothi.light;
    return Container(
      constraints: const BoxConstraints(minHeight: 48),
      padding: const EdgeInsets.symmetric(vertical: 10),
      decoration: BoxDecoration(
        border: Border(bottom: BorderSide(color: p.rule)),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Both columns are Expanded, so every row's values end on the same edge.
          Expanded(
            flex: 2,
            child: Padding(
              padding: const EdgeInsets.only(top: 2),
              child: Text(
                label,
                style: Theme.of(context).textTheme.bodyMedium!
                    .copyWith(color: p.secondary),
              ),
            ),
          ),
          const SizedBox(width: 12),
          Expanded(
            flex: 5,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.end,
              children: [
                for (final (k, line) in lines.indexed)
                  Padding(
                    padding: EdgeInsets.only(top: k == 0 ? 0 : 4),
                    child: line,
                  ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

const _nbsp = '\u00A0';

String _glued(String words) => words.replaceAll(' ', _nbsp);
