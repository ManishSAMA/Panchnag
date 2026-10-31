import 'package:panchang_engine/panchang_engine.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../engine/day_reading.dart';
import '../../format/festival_text.dart';
import '../../format/panchang_text.dart';
import '../../l10n/app_localizations.dart';
import '../../l10n/city_name.dart';
import '../../location/cities.dart';
import '../../location/city_time.dart';
import '../../location/location_store.dart';
import '../../settings/settings_store.dart';
import '../../shared/date_navigator.dart';
import '../../shared/day_notes.dart';
import '../../shared/festival_mark.dart';
import '../../shared/navpad_widgets.dart';
import '../../shared/pachchakkhan_row.dart';
import '../../shared/settings_button.dart';
import '../../theme/navpad.dart';
import '../choghadiya/choghadiya_band.dart';
import '../festivals/festival_state.dart';
import '../month/month_state.dart';
import 'today_state.dart';

/// Today (mobile-ui-design.md §3.1). The festival bands and the upcoming
/// festivals fill in when the year arrives from its own worker, after the hero.
class TodayScreen extends ConsumerWidget {
  const TodayScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final city = ref.watch(locationProvider)!;
    final date = ref.watch(selectedDateProvider);
    final reading = ref.watch(
      dayReadingProvider(
        DayRequest(
          date: date,
          lat: city.lat,
          lon: city.lon,
          timezone: city.timezone,
          rule: ref.watch(sunriseRuleProvider),
        ),
      ),
    );
    return Scaffold(
      appBar: AppBar(titleSpacing: 6, title: _LocationButton(city: city), actions: const [SettingsButton()]),
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

  final Place city;

  @override
  Widget build(BuildContext context) {
    final name = city.nameFor(context);
    return Semantics(
      label: AppLocalizations.of(context).changeCity(name),
      button: true,
      excludeSemantics: true,
      child: TextButton(
        key: const Key('today-location'),
        onPressed: () => context.push('/settings'),
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

  final PanchangDay reading;
  final String timezone;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l10n = AppLocalizations.of(context);
    final lang = langOf(context);
    final now = currentTime(ref);
    final isToday = reading.date == todayIn(timezone, now);
    final phase = isToday ? reading.pachchakkhan.phaseAt(now) : null;
    final next = switch (phase) {
      NextCompletion(:final kind) => kind,
      _ => null,
    };
    DateTime wall(DateTime utc) => cityWall(utc, timezone);
    String completionTime(DateTime utc) => clockTime(roundUpToMinute(wall(utc)), lang).time;
    final eveningTime = clockTime(roundDownToMinute(wall(reading.pachchakkhan.evening)), lang).time;
    final band = switch (phase) {
      NextCompletion(:final kind, :final at) => (
        name: pachchakkhanName(kind, lang),
        subtitle: l10n.bandNextSubtitle,
        time: completionTime(at),
        at: at,
      ),
      EveningDeadline(:final at) => (name: l10n.chauvihar, subtitle: l10n.eveningHeading, time: eveningTime, at: at),
      AllDone() || null => null,
    };
    final notes = dayNotes(reading: reading, l10n: l10n, lang: lang, wall: wall);
    final festivals = festivalYear(ref, reading.date.year);
    final lines = festivalLines(festivalsOn(festivals ?? const [], reading.date), lang);
    final soon = upcomingFestivals(festivals ?? const [], after: reading.date, lang: lang);
    final nextYear = festivals != null && soon.length < 4 && reading.date.year < lastDay.year
        ? festivalYear(ref, reading.date.year + 1)
        : null;
    final upcoming = [...soon, ...upcomingFestivals(nextYear ?? const [], after: reading.date, lang: lang)].take(4);

    void openMonth() {
      ref.read(monthViewProvider.notifier).show(reading.date);
      context.go('/month');
    }

    Band? festivalBand(BandColour colour, String key, List<FestivalLine> shown) => switch (shown) {
      [] => null,
      [final first, ...final rest] => Band(
        key: Key(key),
        colour: colour,
        title: first.name,
        subtitle: rest.isEmpty ? festivalKindLabel(first.kind, l10n) : l10n.festivalsMore(rest.length),
        value: first.start == first.end ? '' : dateRange(first.start, first.end, lang),
        onTap: openMonth,
      ),
    };
    // DESIGN.md's fixed order: red, yellow, green, then navy.
    final bands = [
      ?festivalBand(BandColour.red, 'today-band-parva', [for (final l in lines) if (!l.kind.isVrat) l]),
      if (band != null)
        Band(
          key: const Key('today-band-pachchakkhan'),
          colour: BandColour.yellow,
          title: l10n.bandNextTitle(band.name),
          subtitle: band.subtitle,
          value: l10n.timeAndCountdown(band.time, durationText(band.at.difference(now), lang)),
          onTap: () => context.go('/pachchakkhan'),
        ),
      ?festivalBand(BandColour.green, 'today-band-vrat', [for (final l in lines) if (l.kind.isVrat) l]),
    ];
    final firstGap = notes.isEmpty ? 0.0 : 10.0;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        _Hero(reading: reading, month: lunarMonthOf(reading, ref.watch(monthSystemProvider)), wall: wall),
        if (notes.isNotEmpty)
          KeyedSubtree(
            key: const Key('today-note'),
            child: Column(
              children: [for (final note in notes) Padding(padding: const EdgeInsets.only(bottom: 8), child: note)],
            ),
          ),
        for (final (i, b) in bands.indexed) Padding(padding: EdgeInsets.only(top: i == 0 ? firstGap : 2), child: b),
        ChoghadiyaBand(date: reading.date, topGap: bands.isNotEmpty ? 2 : firstGap),
        SectionHeading(title: isToday ? l10n.timesToday : l10n.timesOfDay),
        const ListTop(),
        _clockRow(l10n.sunrise, reading.sunrise, wall, lang),
        _clockRow(l10n.sunset, reading.sunset, wall, lang),
        _nakshatraRow(l10n, lang, wall),
        SectionHeading(title: l10n.pachchakkhan, linkLabel: l10n.seeAll, onLink: () => context.go('/pachchakkhan')),
        const ListTop(),
        for (final p in reading.pachchakkhan.completions)
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
          time: eveningTime,
          state: switch (phase) {
            null => null,
            EveningDeadline() => RowState.next,
            AllDone() => RowState.done,
            NextCompletion() => RowState.plain,
          },
          prefix: l10n.bySunset,
        ),
        if (upcoming.isNotEmpty)
          KeyedSubtree(
            key: const Key('today-upcoming'),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                SectionHeading(title: l10n.upcomingFestivals),
                const ListTop(),
                for (final day in upcoming)
                  InkWell(
                    key: Key('upcoming-${day.date.iso}'),
                    onTap: () => ref.read(selectedDateProvider.notifier).goTo(day.date),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.stretch,
                      children: [
                        for (final (i, line) in day.lines.indexed)
                          FestivalRow(
                            line: line,
                            subtitle: festivalKindLabel(line.kind, l10n),
                            value: i == 0 ? shortDate(day.date, lang) : null,
                          ),
                      ],
                    ),
                  ),
              ],
            ),
          ),
      ],
    );
  }

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
    final local = wall(reading.nakshatra.endsAt);
    final (:period, :time) = clockTime(local, lang);
    final day = CivilDate(local.year, local.month, local.day);
    final when = day == reading.date ? period : '${shortDate(day, lang)}, $period';
    return TimeRow(
      name: l10n.nakshatra,
      subtitle: l10n.nakshatraDetail(
        nakshatraName(reading.nakshatra.index, lang),
        reading.nakshatra.pada,
        nakshatraName(reading.nakshatra.index % 27 + 1, lang),
      ),
      time: l10n.until(lang == Lang.hi ? time : '$time $when'),
      prefix: lang == Lang.hi ? when : null,
    );
  }

}

class _Hero extends StatelessWidget {
  const _Hero({required this.reading, required this.month, required this.wall});

  final PanchangDay reading;
  final LunarMonth month;
  final DateTime Function(DateTime) wall;

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    final lang = langOf(context);
    final n = Theme.of(context).extension<Navpad>()!;
    final text = Theme.of(context).textTheme;
    final ends = instantPhrase(wall(reading.jainTithi.endsAt), day: reading.date, lang: lang);
    return Semantics(
      container: true,
      child: Padding(
        padding: const EdgeInsets.fromLTRB(18, 10, 18, 18),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              tithiName(reading.jainTithi.index, lang),
              key: const Key('today-hero-tithi'),
              style: NavpadType.displayHero.copyWith(color: n.ink),
            ),
            const SizedBox(height: 6),
            Text.rich(
              TextSpan(
                style: text.bodyLarge!.copyWith(color: n.ink2, height: 1.4),
                children: [
                  TextSpan(
                    text: monthName(month, lang),
                    style: TextStyle(color: n.ink, fontWeight: FontWeight.w600),
                  ),
                  TextSpan(text: ' · ${l10n.heroUntil(ends, tithiName(reading.jainTithi.index % 30 + 1, lang))}\n'),
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
