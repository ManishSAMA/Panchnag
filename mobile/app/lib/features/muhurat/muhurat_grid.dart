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
import '../../shared/mark.dart';
import '../../shared/navpad_icons.dart';
import '../../theme/navpad.dart';
import '../choghadiya/choghadiya_screen.dart';
import '../choghadiya/choghadiya_state.dart';
import '../today/today_state.dart';
import 'muhurat_state.dart';

/// The Muhurat section's tiles, in the grid's reading order. [slug] is the
/// detail route (`/muhurat/<slug>`); Choghadiya opens its own screen.
enum MuhuratKind {
  rahuKaal('rahu-kaal', NavpadGlyph.rahuKaal),
  abhijit('abhijit', NavpadGlyph.abhijit),
  choghadiya('choghadiya', NavpadGlyph.ghatika),
  yoga('yoga', NavpadGlyph.yoga),
  panchak('panchak', NavpadGlyph.panchak),
  bhadra('bhadra', NavpadGlyph.bhadra),
  gandmool('gandmool', NavpadGlyph.gandmool),
  chandraBal('chandra-bal', NavpadGlyph.chandraBal),
  agniVaas('agni-vaas', NavpadGlyph.agniVaas);

  const MuhuratKind(this.slug, this.glyph);

  final String slug;
  final NavpadGlyph glyph;

  static MuhuratKind? fromSlug(String slug) => values.where((k) => k.slug == slug).firstOrNull;

  String title(AppLocalizations l10n) => switch (this) {
    rahuKaal => l10n.rahuKaal,
    abhijit => l10n.abhijit,
    choghadiya => l10n.choghadiyaTitle,
    yoga => l10n.yogaLabel,
    panchak => l10n.panchak,
    bhadra => l10n.bhadra,
    gandmool => l10n.gandmool,
    chandraBal => l10n.chandraBal,
    agniVaas => l10n.agniVaas,
  };
}

/// What a tile shows under its name: a reading and a mark, either empty
/// while the day loads. [tone] colours the mark; null for a mark that is a
/// count, not a judgement ("6 राशियाँ"). [now]: one of its windows runs at
/// this moment, so the tile is filled light green and says "अभी".
typedef TileFace = ({String face, String mark, Mark? tone, bool now});

/// The nine Muhurat tiles, two to a row at every text size, for the date
/// Today shows. Used by the Muhurat screen and Full Panchang.
class MuhuratGrid extends ConsumerWidget {
  const MuhuratGrid({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l10n = AppLocalizations.of(context);
    final lang = langOf(context);
    final day = watchMuhuratDay(ref);
    final city = ref.watch(locationProvider)!;
    final now = currentTime(ref);
    final muhurat = ref.watch(muhuratReadingProvider(MuhuratRequest(day))).value;
    final section = ref.watch(sectionReadingProvider(SectionRequest(day))).value;
    final choghadiya = watchChoghadiya(ref, city: city, date: day.date, now: now);
    DateTime wall(DateTime utc) => roundDownToMinute(cityWall(utc, city.timezone));
    final reading = ref.watch(dayReadingProvider(day)).value;
    final bounds = reading == null
        ? null
        : (sunrise: wall(reading.sunrise), nextSunrise: wall(reading.choghadiya.last.end));
    String range(DateTime start, DateTime end) => dayWindowText(
      start: wall(start),
      end: wall(end),
      bounds: bounds,
      day: day.date,
      lang: lang,
      allDay: l10n.allDay,
    );
    TileFace marked(String face, Mark mark, {bool now = false}) =>
        (face: face, mark: markText(l10n, mark), tone: mark, now: now);
    TileFace window(List<({DateTime start, DateTime end})> spans, Mark mark) => spans.isEmpty
        ? marked(l10n.noneToday, Mark.plain)
        : marked(
            range(spans.first.start, spans.last.end),
            mark,
            now: spans.any((w) => runsAt(now, start: w.start, end: w.end)),
          );

    TileFace faceOf(MuhuratKind kind) {
      const TileFace loading = (face: '', mark: '', tone: null, now: false);
      if (kind == MuhuratKind.choghadiya) {
        final live = choghadiya == null ? null : liveChoghadiya(choghadiya.day, now, following: choghadiya.following);
        if (live == null) return loading;
        final end = glued(l10n.untilTime(clockPhrase(wall(live.slot.end), lang)));
        final nature = live.slot.name.nature;
        return (
          face: '${choghadiyaName(live.slot.name, lang)} · $end',
          mark: qualityText(l10n, nature),
          tone: markOfNature(nature),
          now: false,
        );
      }
      if (kind == MuhuratKind.yoga) {
        final nitya = section?.yogas.first.index;
        if (nitya == null) return loading;
        return marked(yogaName(nitya, lang), nityaYogaIsAuspicious(nitya) ? Mark.good : Mark.avoid);
      }
      final m = muhurat;
      if (m == null) return loading;
      return switch (kind) {
        MuhuratKind.rahuKaal => window([m.rahuKaal], Mark.avoid),
        MuhuratKind.abhijit => window([m.abhijit], Mark.good),
        MuhuratKind.panchak => window([?m.panchak.window], Mark.avoid),
        MuhuratKind.bhadra => window(
          [for (final w in m.bhadra) (start: w.start, end: w.end)],
          m.bhadra.any((w) => w.residence == BhadraResidence.earth) ? Mark.avoid : Mark.plain,
        ),
        MuhuratKind.gandmool => window([for (final w in m.gandmool) (start: w.start, end: w.end)], Mark.avoid),
        MuhuratKind.chandraBal => (
          face: l10n.moonInRashi(rashiName(m.chandraBal.first.moonRashi, lang)),
          mark: l10n.sixRashis,
          tone: null,
          now: false,
        ),
        MuhuratKind.agniVaas => marked(agniVaasName(m.agniVaas, lang), m.agniVaas.isAuspicious ? Mark.good : Mark.avoid),
        MuhuratKind.choghadiya || MuhuratKind.yoga => loading,
      };
    }

    final tiles = [
      for (final kind in MuhuratKind.values)
        _MuhuratTile(
          key: Key('muhurat-tile-${kind.slug}'),
          kind: kind,
          title: kind.title(l10n),
          face: faceOf(kind),
          onTap: () => context.push(kind == MuhuratKind.choghadiya ? '/choghadiya' : '/muhurat/${kind.slug}'),
        ),
    ];
    return Padding(
      padding: const EdgeInsets.fromLTRB(12, 12, 12, 16),
      child: Column(
        spacing: 8,
        children: [
          for (var i = 0; i < tiles.length; i += 2)
            IntrinsicHeight(
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                spacing: 8,
                children: [
                  Expanded(child: tiles[i]),
                  // A short last row keeps its tile in the left column.
                  Expanded(child: i + 1 < tiles.length ? tiles[i + 1] : const SizedBox()),
                ],
              ),
            ),
        ],
      ),
    );
  }
}

/// A flat `surface` tile edged with a hairline: the picture left, the name,
/// reading and mark right.
class _MuhuratTile extends StatelessWidget {
  const _MuhuratTile({super.key, required this.kind, required this.title, required this.face, required this.onTap});

  final MuhuratKind kind;
  final String title;
  final TileFace face;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final n = Theme.of(context).extension<Navpad>()!;
    final text = Theme.of(context).textTheme;
    final nowWord = AppLocalizations.of(context).slotNow;
    return Semantics(
      button: true,
      label: [title, face.face, face.mark, if (face.now) nowWord].where((part) => part.isNotEmpty).join(', '),
      excludeSemantics: true,
      child: Material(
        color: face.now ? n.nowFill : n.surface,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(12),
          side: face.now ? BorderSide(color: n.markGood, width: 2) : BorderSide(color: n.hair),
        ),
        clipBehavior: Clip.antiAlias,
        child: InkWell(
          onTap: onTap,
          child: ConstrainedBox(
            constraints: const BoxConstraints(minHeight: 76),
            child: Padding(
              padding: const EdgeInsets.all(10),
              child: Row(
                spacing: 10,
                children: [
                  NavpadIcon(kind.glyph, size: 38, color: n.ink),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      mainAxisAlignment: MainAxisAlignment.center,
                      spacing: 1,
                      children: [
                        Text(title, style: text.labelLarge!.copyWith(color: n.ink, fontSize: 15, height: 1.2)),
                        if (face.face.isNotEmpty)
                          Text(face.face, style: text.labelMedium!.copyWith(color: n.ink2, fontSize: 13, height: 1.2)),
                        if (face.mark.isNotEmpty)
                          Text(
                            face.mark,
                            style: text.labelMedium!.copyWith(
                              color: switch (face.tone) {
                                final tone? => markColour(n, tone),
                                null => n.ink,
                              },
                              fontSize: 12,
                              fontWeight: FontWeight.w600,
                              height: 1.2,
                            ),
                          ),
                        if (face.now)
                          Text(
                            nowWord,
                            style: text.labelMedium!.copyWith(
                              color: n.ink,
                              fontSize: 12,
                              fontWeight: FontWeight.w700,
                              height: 1.2,
                            ),
                          ),
                      ],
                    ),
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}
