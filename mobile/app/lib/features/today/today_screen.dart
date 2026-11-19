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
import '../../shared/festival_icon.dart';
import '../../shared/festival_mark.dart';
import '../../shared/moon_phase.dart';
import '../../shared/navpad_icons.dart';
import '../../shared/navpad_widgets.dart';
import '../../shared/pachchakkhan_row.dart';
import '../../shared/settings_button.dart';
import '../../theme/navpad.dart';
import '../muhurat/muhurat_band.dart';
import '../festivals/festival_state.dart';
import '../month/month_state.dart';
import 'feature_tiles.dart';
import 'panchang_card.dart';
import '../share/share_button.dart';
import '../../shared/pothi_page.dart';
import 'today_state.dart';

/// Today (mobile-ui-design.md §3.1). The festival bands and the upcoming
/// festivals fill in when the year arrives from its own worker, after the hero.
class TodayScreen extends ConsumerWidget {
  const TodayScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final city = ref.watch(locationProvider)!;
    final date = ref.watch(selectedDateProvider);
    final request = DayRequest(
      date: date,
      lat: city.lat,
      lon: city.lon,
      timezone: city.timezone,
      rule: ref.watch(sunriseRuleProvider),
    );
    final reading = ref.watch(dayReadingProvider(request));
    return Scaffold(
      appBar: AppBar(
        titleSpacing: 6,
        title: _LocationButton(city: city),
        actions: const [ShareButton(), SettingsButton()],
      ),
      body: PothiPage(child: SingleChildScrollView(
        padding: const EdgeInsets.only(bottom: 24),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            DateNavigator(date: date, timezone: city.timezone),
            ...switch (reading) {
              AsyncData(:final value) => [_DayView(reading: value, request: request, timezone: city.timezone)],
              AsyncError(:final error) => [
                Note(icon: NoteIcon.alert, title: AppLocalizations.of(context).appTitle, body: '$error'),
              ],
              _ => const <Widget>[],
            },
          ],
        ),
      )),
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
  const _DayView({required this.reading, required this.request, required this.timezone});

  final PanchangDay reading;
  final DayRequest request;
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
        icon: NavpadIcon(festivalGlyph(first.kind)),
        title: first.name,
        subtitle: rest.isEmpty ? festivalKindLabel(first.kind, l10n) : l10n.festivalsMore(rest.length),
        value: first.start == first.end ? '' : dateRange(first.start, first.end, lang),
        onTap: openMonth,
      ),
    };
    // DESIGN.md's fixed order: red, yellow, green, then navy.
    final bands = [
      ?festivalBand(BandColour.red, 'today-band-parva', [
        for (final l in lines)
          if (!l.kind.isVrat) l,
      ]),
      if (band != null)
        Band(
          key: const Key('today-band-pachchakkhan'),
          colour: BandColour.yellow,
          icon: SunPathIcon(fraction: dayFraction(band.at, reading)),
          title: l10n.bandNextTitle(band.name),
          subtitle: band.subtitle,
          value: l10n.timeAndCountdown(band.time, durationText(band.at.difference(now), lang)),
          onTap: () => context.go('/pachchakkhan'),
        ),
      ?festivalBand(BandColour.green, 'today-band-vrat', [
        for (final l in lines)
          if (l.kind.isVrat) l,
      ]),
    ];
    final firstGap = notes.isEmpty ? 0.0 : 10.0;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        _Hero(reading: reading, month: lunarMonthOf(reading, ref.watch(monthSystemProvider)), wall: wall),
        PanchangCard(day: reading, request: request, isToday: isToday),
        FeatureTiles(onMonth: openMonth),
        if (notes.isNotEmpty)
          KeyedSubtree(
            key: const Key('today-note'),
            child: Column(
              children: [for (final note in notes) Padding(padding: const EdgeInsets.only(bottom: 8), child: note)],
            ),
          ),
        for (final (i, b) in bands.indexed)
          Padding(
            padding: EdgeInsets.only(top: i == 0 ? firstGap : 2),
            child: b,
          ),
        MuhuratBand(date: reading.date, topGap: bands.isNotEmpty ? 2 : firstGap),
        SectionHeading(title: isToday ? l10n.timesToday : l10n.timesOfDay),
        _clockRow(l10n.sunrise, NavpadGlyph.sunrise, reading.sunrise, wall, lang),
        _clockRow(l10n.sunset, NavpadGlyph.sunset, reading.sunset, wall, lang),
        SectionHeading(title: l10n.pachchakkhan, linkLabel: l10n.seeAll, onLink: () => context.go('/pachchakkhan')),
        for (final p in reading.pachchakkhan.completions)
          pachchakkhanRow(
            l10n: l10n,
            name: pachchakkhanName(p.kind, lang),
            icon: SunPathIcon(fraction: dayFraction(p.at, reading)),
            time: completionTime(p.at),
            state: !isToday
                ? null
                : (!p.at.isAfter(now) ? RowState.done : (p.kind == next ? RowState.next : RowState.plain)),
            prefix: p.kind == next ? l10n.countdownPrefix(durationText(p.at.difference(now), lang)) : null,
          ),
        pachchakkhanRow(
          l10n: l10n,
          name: l10n.chauvihar,
          icon: const SunPathIcon(fraction: 1),
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
                for (final day in upcoming)
                  _UpcomingDate(
                    day: day,
                    from: reading.date,
                    onTap: () => ref.read(selectedDateProvider.notifier).goTo(day.date),
                  ),
              ],
            ),
          ),
      ],
    );
  }

  Widget _clockRow(String name, NavpadGlyph glyph, DateTime utc, DateTime Function(DateTime) wall, Lang lang) {
    final local = wall(utc);
    final (:period, :time) = clockTime(local, lang);
    final day = CivilDate(local.year, local.month, local.day);
    final when = day == reading.date ? period : '${shortDate(day, lang)}, $period';
    return TimeRow(
      name: name,
      icon: NavpadIcon(glyph),
      time: time,
      prefix: lang == Lang.hi ? when : null,
      suffix: lang == Lang.en ? when : null,
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
    final tithi = reading.jainTithi.index;
    return Semantics(
      container: true,
      child: Padding(
        padding: const EdgeInsets.fromLTRB(18, 10, 18, 18),
        child: Row(
          children: [
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    tithiName(tithi, lang),
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
                        TextSpan(text: ' · ${l10n.heroUntil(ends, tithiName(tithi % 30 + 1, lang))}\n'),
                        TextSpan(
                          text: samvatLine(
                            viraNirvana: reading.viraNirvanaSamvat,
                            vikram: reading.vikramSamvat,
                            lang: lang,
                          ),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(width: 12),
            Column(
              children: [
                MoonPhase(tithi: tithi, size: 58, semanticLabel: l10n.moonOfTithi(tithiName(tithi, lang))),
                const SizedBox(height: 2),
                ExcludeSemantics(
                  child: Text(
                    tithiShort(tithi, lang),
                    style: text.labelMedium!.copyWith(color: n.ink2, fontSize: 12, fontWeight: FontWeight.w600),
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}

/// An upcoming festival date: a heading with the day in Tiro, then its month,
/// weekday and how far it is from [from], and under it one row per festival.
class _UpcomingDate extends StatelessWidget {
  const _UpcomingDate({required this.day, required this.from, required this.onTap});

  final FestivalDate day;
  final CivilDate from;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    final lang = langOf(context);
    final n = Theme.of(context).extension<Navpad>()!;
    final text = Theme.of(context).textTheme;
    final date = day.date;
    final ahead = DateTime.utc(
      date.year,
      date.month,
      date.day,
    ).difference(DateTime.utc(from.year, from.month, from.day));
    return InkWell(
      key: Key('upcoming-${date.iso}'),
      onTap: onTap,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Container(
            padding: const EdgeInsets.fromLTRB(18, 12, 18, 4),
            decoration: BoxDecoration(
              border: Border(top: BorderSide(color: n.hair)),
            ),
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.baseline,
              textBaseline: TextBaseline.alphabetic,
              children: [
                Text('${date.day}', style: NavpadType.displayGroup.copyWith(color: n.ink)),
                const SizedBox(width: 8),
                Expanded(
                  child: Text(
                    l10n.upcomingDateLine(
                      gregorianMonthName(date.month, lang),
                      weekdayName(date, lang),
                      l10n.daysAhead(ahead.inDays),
                    ),
                    style: text.labelMedium!.copyWith(color: n.ink2),
                  ),
                ),
              ],
            ),
          ),
          for (final line in day.lines)
            Container(
              constraints: const BoxConstraints(minHeight: 48),
              padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 6),
              child: Row(
                children: [
                  FestivalIcon(kind: line.kind, badge: true),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(line.name, style: text.bodyLarge!.copyWith(color: n.ink)),
                        Text(festivalKindLabel(line.kind, l10n), style: text.labelMedium!.copyWith(color: n.ink2)),
                      ],
                    ),
                  ),
                ],
              ),
            ),
        ],
      ),
    );
  }
}
