import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:panchang_engine/src/panchang/pachchakkhan.dart';
import 'package:panchang_engine/src/time/civil_day.dart';

import '../../engine/day_reading.dart';
import '../../format/panchang_text.dart';
import '../../l10n/app_localizations.dart';
import '../../l10n/city_name.dart';
import '../../location/cities.dart';
import '../../location/city_time.dart';
import '../../location/location_store.dart';
import '../../shared/date_navigator.dart';
import '../../shared/navpad_widgets.dart';
import '../../shared/pachchakkhan_row.dart';
import '../../theme/navpad.dart';
import 'today_state.dart';

/// Today (mobile-ui-design.md §3.1). The red, green and navy bands and the
/// upcoming festivals join with the festival port and the choghadiya (M4).
class TodayScreen extends ConsumerWidget {
  const TodayScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final city = ref.watch(locationProvider)!;
    final date = ref.watch(selectedDateProvider);
    final reading = ref.watch(
      dayReadingProvider(DayRequest(date: date, lat: city.lat, lon: city.lon, timezone: city.timezone)),
    );
    return Scaffold(
      appBar: AppBar(titleSpacing: 6, title: _LocationButton(city: city)),
      body: SingleChildScrollView(
        padding: const EdgeInsets.only(bottom: 24),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            DateNavigator(date: date, timezone: city.timezone),
            ...switch (reading) {
              AsyncData(:final value) => [_DayView(reading: value, timezone: city.timezone)],
              AsyncError(:final error) => [
                Note(icon: NoteIcon.alert, title: AppLocalizations.of(context).appTitle, body: '$error'),
              ],
              _ => const <Widget>[],
            },
          ],
        ),
      ),
    );
  }
}

class _LocationButton extends StatelessWidget {
  const _LocationButton({required this.city});

  final PresetCity city;

  @override
  Widget build(BuildContext context) {
    final name = city.nameFor(context);
    return Semantics(
      label: AppLocalizations.of(context).changeCity(name),
      button: true,
      excludeSemantics: true,
      child: TextButton(
        onPressed: () => context.push('/location'),
        style: TextButton.styleFrom(
          foregroundColor: Theme.of(context).colorScheme.onSurface,
          textStyle: NavpadType.titleBand.copyWith(fontWeight: FontWeight.w600),
          padding: const EdgeInsets.fromLTRB(10, 0, 12, 0),
          minimumSize: const Size(48, 48),
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Icon(Icons.place_outlined, size: 20),
            const SizedBox(width: 6),
            Flexible(child: Text(name, overflow: TextOverflow.ellipsis)),
            const Icon(Icons.expand_more, size: 18),
          ],
        ),
      ),
    );
  }
}

class _DayView extends ConsumerWidget {
  const _DayView({required this.reading, required this.timezone});

  final DayReading reading;
  final String timezone;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l10n = AppLocalizations.of(context);
    final lang = langOf(context);
    final now = currentTime(ref);
    final isToday = reading.date == todayIn(timezone, now);
    final next = isToday ? reading.nextPachchakkhan(now) : null;
    DateTime wall(DateTime utc) => cityWall(utc, timezone);
    String completionTime(DateTime utc) => clockTime(roundUpToMinute(wall(utc)), lang).time;
    final notes = _notes(l10n, lang, wall);

    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        _Hero(reading: reading, wall: wall),
        if (notes.isNotEmpty)
          KeyedSubtree(
            key: const Key('today-note'),
            child: Column(
              children: [for (final note in notes) Padding(padding: const EdgeInsets.only(bottom: 8), child: note)],
            ),
          ),
        if (next != null)
          Padding(
            padding: EdgeInsets.only(top: notes.isEmpty ? 0 : 10),
            child: Band(
              colour: BandColour.yellow,
              title: l10n.bandNextTitle(pachchakkhanName(next, lang)),
              subtitle: l10n.bandNextSubtitle,
              value: l10n.timeAndCountdown(
                completionTime(_at(reading, next)),
                durationText(_at(reading, next).difference(now), lang),
              ),
              onTap: () => context.go('/pachchakkhan'),
            ),
          ),
        SectionHeading(title: isToday ? l10n.timesToday : l10n.timesOfDay),
        const ListTop(),
        _clockRow(l10n.sunrise, reading.sunrise, wall, lang),
        _clockRow(l10n.sunset, reading.sunset, wall, lang),
        _nakshatraRow(l10n, lang, wall),
        SectionHeading(title: l10n.pachchakkhan, linkLabel: l10n.seeAll, onLink: () => context.go('/pachchakkhan')),
        const ListTop(),
        for (final p in reading.pachchakkhan)
          pachchakkhanRow(
            l10n: l10n,
            name: pachchakkhanName(p.kind, lang),
            time: completionTime(p.at),
            state: !isToday
                ? null
                : (!p.at.isAfter(now) ? RowState.done : (p.kind == next ? RowState.next : RowState.plain)),
            prefix: p.kind == next ? l10n.countdownPrefix(durationText(p.at.difference(now), lang)) : null,
          ),
        pachchakkhanRow(
          l10n: l10n,
          name: l10n.chauvihar,
          time: clockTime(roundDownToMinute(wall(reading.pachchakkhanEvening)), lang).time,
          state: !isToday ? null : (reading.pachchakkhanEvening.isAfter(now) ? RowState.plain : RowState.done),
          prefix: l10n.bySunset,
        ),
      ],
    );
  }

  static DateTime _at(DayReading reading, TimedPachchakkhan kind) =>
      reading.pachchakkhan.firstWhere((p) => p.kind == kind).at;

  Widget _clockRow(String name, DateTime utc, DateTime Function(DateTime) wall, Lang lang) {
    final local = wall(utc);
    final (:period, :time) = clockTime(local, lang);
    final day = CivilDate(local.year, local.month, local.day);
    final when = day == reading.date ? period : '${shortDate(day, lang)}, $period';
    return TimeRow(
      name: name,
      time: time,
      prefix: lang == Lang.hi ? when : null,
      suffix: lang == Lang.en ? when : null,
    );
  }

  Widget _nakshatraRow(AppLocalizations l10n, Lang lang, DateTime Function(DateTime) wall) {
    final local = wall(reading.nakshatraEnds);
    final (:period, :time) = clockTime(local, lang);
    final day = CivilDate(local.year, local.month, local.day);
    final when = day == reading.date ? period : '${shortDate(day, lang)}, $period';
    return TimeRow(
      name: l10n.nakshatra,
      subtitle: l10n.nakshatraDetail(
        nakshatraName(reading.nakshatra, lang),
        reading.nakshatraPada,
        nakshatraName(reading.nakshatra % 27 + 1, lang),
      ),
      time: l10n.until(lang == Lang.hi ? time : '$time $when'),
      prefix: lang == Lang.hi ? when : null,
    );
  }

  List<Widget> _notes(AppLocalizations l10n, Lang lang, DateTime Function(DateTime) wall) {
    final tithi = tithiName(reading.jainTithi, lang);
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
          body: switch (spanPhrases(wall(kshaya.starts), wall(kshaya.ends), day: reading.date, lang: lang)) {
            (final start, final end) => l10n.kshayaBody(
              tithiName(kshaya.lost, lang),
              start,
              end,
              tithiName((kshaya.lost + 28) % 30 + 1, lang),
              tithi,
            ),
          },
        ),
      if (reading.boundary case final boundary?)
        Note(
          icon: NoteIcon.alert,
          title: l10n.boundaryTitle,
          body: (boundary.isStart ? l10n.boundaryStartsBody : l10n.boundaryEndsBody)(
            tithi,
            at(boundary.at),
            clockPhrase(wall(reading.reference), lang),
            (boundary.gap.inSeconds / 60).round(),
          ),
        ),
    ];
  }
}

class _Hero extends StatelessWidget {
  const _Hero({required this.reading, required this.wall});

  final DayReading reading;
  final DateTime Function(DateTime) wall;

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    final lang = langOf(context);
    final n = Theme.of(context).extension<Navpad>()!;
    final text = Theme.of(context).textTheme;
    final ends = instantPhrase(wall(reading.jainTithiEnds), day: reading.date, lang: lang);
    return Semantics(
      container: true,
      child: Padding(
        padding: const EdgeInsets.fromLTRB(18, 10, 18, 18),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              tithiName(reading.jainTithi, lang),
              key: const Key('today-hero-tithi'),
              style: NavpadType.displayHero.copyWith(color: n.ink),
            ),
            const SizedBox(height: 6),
            Text.rich(
              TextSpan(
                style: text.bodyLarge!.copyWith(color: n.ink2, height: 1.4),
                children: [
                  TextSpan(
                    text: monthName(reading.month, lang),
                    style: TextStyle(color: n.ink, fontWeight: FontWeight.w600),
                  ),
                  TextSpan(text: ' · ${l10n.heroUntil(ends, tithiName(reading.jainTithi % 30 + 1, lang))}\n'),
                  TextSpan(
                    text: samvatLine(viraNirvana: reading.viraNirvanaSamvat, vikram: reading.vikramSamvat, lang: lang),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}
