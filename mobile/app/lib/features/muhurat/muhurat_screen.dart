import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:panchang_engine/panchang_engine.dart';

import '../../engine/day_reading.dart';
import '../../format/muhurat_text.dart';
import '../../format/panchang_text.dart';
import '../../l10n/app_localizations.dart';
import '../../location/city_time.dart';
import '../../location/location_store.dart';
import '../../shared/date_navigator.dart';
import '../../shared/mark.dart';
import '../../shared/navpad_widgets.dart';
import '../../shared/pothi_page.dart';
import '../today/today_state.dart';
import 'muhurat_grid.dart';
import 'muhurat_state.dart';

/// The Muhurat section (plans/muhurat-section.md): the nine tiles for the
/// date Today shows, opened from Today's मुहूर्त tile, outside the tabs.
class MuhuratScreen extends ConsumerWidget {
  const MuhuratScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l10n = AppLocalizations.of(context);
    final city = ref.watch(locationProvider)!;
    return Scaffold(
      appBar: AppBar(title: Text(l10n.muhuratTitle)),
      body: PothiPage(
        child: SingleChildScrollView(
          padding: const EdgeInsets.only(bottom: 24),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              DateNavigator(date: ref.watch(selectedDateProvider), timezone: city.timezone),
              const MuhuratGrid(),
            ],
          ),
        ),
      ),
    );
  }
}

/// One tile's screen: its windows for the day, each with its time and mark.
class MuhuratDetailScreen extends ConsumerWidget {
  const MuhuratDetailScreen({super.key, required this.kind});

  final MuhuratKind kind;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l10n = AppLocalizations.of(context);
    final city = ref.watch(locationProvider)!;
    final day = watchMuhuratDay(ref);
    final reading = ref.watch(muhuratReadingProvider(MuhuratRequest(day)));
    final section = ref.watch(sectionReadingProvider(SectionRequest(day))).value;
    return Scaffold(
      appBar: AppBar(title: Text(kind.title(l10n))),
      body: PothiPage(
        child: SingleChildScrollView(
          padding: const EdgeInsets.only(bottom: 24),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              DateNavigator(date: day.date, timezone: city.timezone),
              ...switch (reading) {
                AsyncError(:final error) => [Note(icon: NoteIcon.alert, title: l10n.appTitle, body: '$error')],
                AsyncData(:final value) => _rows(
                  context,
                  muhurat: value,
                  section: section,
                  reading: ref.watch(dayReadingProvider(day)).value,
                  date: day.date,
                  timezone: city.timezone,
                  now: currentTime(ref),
                ),
                _ => const [],
              },
            ],
          ),
        ),
      ),
    );
  }

  List<Widget> _rows(
    BuildContext context, {
    required PanchangMuhurat muhurat,
    required PanchangSection? section,
    required PanchangDay? reading,
    required CivilDate date,
    required String timezone,
    required DateTime now,
  }) {
    final l10n = AppLocalizations.of(context);
    final lang = langOf(context);
    DateTime wall(DateTime utc) => roundDownToMinute(cityWall(utc, timezone));
    final bounds = reading == null
        ? null
        : (sunrise: wall(reading.sunrise), nextSunrise: wall(reading.choghadiya.last.end));
    String range(DateTime start, DateTime end) => dayWindowText(
      start: wall(start),
      end: wall(end),
      bounds: bounds,
      day: date,
      lang: lang,
      allDay: l10n.allDay,
    );
    String span(DateTime start, DateTime end) {
      final (from, to) = spanPhrases(wall(start), wall(end), day: date, lang: lang);
      return '${glued(from)} – ${glued(to)}';
    }

    final none = TimeRow(name: kind.title(l10n), time: l10n.noneToday);

    /// A window running now is filled light green and says "अभी", so it
    /// never rests on colour alone. [time] defaults to the day's range.
    Widget timed(String name, DateTime start, DateTime end, {Mark? mark, String? subtitle, String? time}) {
      final running = runsAt(now, start: start, end: end);
      final shown = time ?? range(start, end);
      return TimeRow(
        name: name,
        time: shown,
        subtitle: subtitle,
        mark: mark,
        state: running ? RowState.now : RowState.plain,
        suffix: running ? l10n.slotNow : null,
        semanticsLabel: [
          '$name $shown',
          ?subtitle,
          if (mark != null) markText(l10n, mark),
          if (running) l10n.slotNow,
        ].join(', '),
      );
    }

    return switch (kind) {
      MuhuratKind.rahuKaal => [
        const ListTop(),
        timed(l10n.rahuKaal, muhurat.rahuKaal.start, muhurat.rahuKaal.end, mark: Mark.avoid),
        timed(l10n.yamaganda, muhurat.yamaganda.start, muhurat.yamaganda.end, mark: Mark.avoid),
        timed(l10n.gulika, muhurat.gulika.start, muhurat.gulika.end, mark: Mark.avoid),
      ],
      MuhuratKind.abhijit => [
        const ListTop(),
        timed(l10n.abhijit, muhurat.abhijit.start, muhurat.abhijit.end, mark: Mark.good),
      ],
      MuhuratKind.panchak => [
        const ListTop(),
        switch (muhurat.panchak) {
          (window: final w?, period: _, nextPeriod: _) => timed(l10n.panchakToday, w.start, w.end, mark: Mark.avoid),
          _ => TimeRow(name: l10n.panchakToday, time: l10n.noneToday),
        },
        if (muhurat.panchak.period case final p?) timed(l10n.panchakPeriod, p.start, p.end, time: span(p.start, p.end)),
        if (muhurat.panchak.nextPeriod case final p?) TimeRow(name: l10n.panchakNext, time: span(p.start, p.end)),
      ],
      MuhuratKind.bhadra => [
        const ListTop(),
        if (muhurat.bhadra.isEmpty) none,
        for (final w in muhurat.bhadra)
          timed(
            l10n.bhadra,
            w.start,
            w.end,
            subtitle: bhadraResidenceText(w.residence, lang),
            mark: w.residence == BhadraResidence.earth ? Mark.avoid : Mark.plain,
          ),
      ],
      MuhuratKind.gandmool => [
        const ListTop(),
        if (muhurat.gandmool.isEmpty) none,
        for (final w in muhurat.gandmool)
          timed(nakshatraName(w.nakshatra, lang), w.start, w.end, mark: Mark.avoid),
      ],
      MuhuratKind.chandraBal => [
        const ListTop(),
        for (final s in muhurat.chandraBal)
          TimeRow(
            name: l10n.moonRashiHeading(rashiName(s.moonRashi, lang)),
            time: switch (s.endsAt) {
              null => '',
              final end => glued(l10n.untilTime(instantPhrase(wall(end), day: date, lang: lang))),
            },
            subtitle: s.rashis.map((r) => rashiName(r, lang)).join(', '),
          ),
      ],
      MuhuratKind.agniVaas => [
        const ListTop(),
        TimeRow(
          name: agniVaasName(muhurat.agniVaas, lang),
          time: '',
          mark: muhurat.agniVaas.isAuspicious ? Mark.good : Mark.avoid,
        ),
      ],
      MuhuratKind.yoga => _yogaRows(context, muhurat: muhurat, section: section, span: span, wall: wall, date: date, now: now),
      MuhuratKind.choghadiya => const [],
    };
  }

  List<Widget> _yogaRows(
    BuildContext context, {
    required PanchangMuhurat muhurat,
    required PanchangSection? section,
    required String Function(DateTime, DateTime) span,
    required DateTime Function(DateTime) wall,
    required CivilDate date,
    required DateTime now,
  }) {
    final l10n = AppLocalizations.of(context);
    final lang = langOf(context);
    String kindName(DayYogaKind kind) => switch (kind) {
      DayYogaKind.dainika => l10n.yogaKindDainika,
      DayYogaKind.aanandadi => l10n.yogaKindAanandadi,
      DayYogaKind.ravi => l10n.yogaKindRavi,
      DayYogaKind.jwalamukhi => l10n.yogaKindJwalamukhi,
    };
    Widget row(DayYoga y) => TimeRow(
      name: dayYogaName(y.name, lang),
      time: span(y.start, y.end),
      state: runsAt(now, start: y.start, end: y.end) ? RowState.now : RowState.plain,
      suffix: runsAt(now, start: y.start, end: y.end) ? l10n.slotNow : null,
      subtitle: [
        kindName(y.kind),
        if (y.isNullified) l10n.yogaNullified,
        if (y.cancelled) l10n.yogaCancelled,
        if (y.diminished) l10n.yogaDiminished,
        if (y.varjya case final v?) l10n.yogaVarjya(span(v.start, v.end)),
      ].join(' · '),
    );
    List<Widget> group(String title, YogaNature nature) {
      final yogas = muhurat.yogas.where((y) => y.nature == nature);
      return [
        SectionHeading(title: title),
        if (yogas.isEmpty) TimeRow(name: l10n.noneToday, time: ''),
        for (final y in yogas) row(y),
      ];
    }

    return [
      SectionHeading(title: l10n.nityaYoga),
      if (section?.yogas.first case final nitya?)
        TimeRow(
          name: yogaName(nitya.index, lang),
          time: glued(l10n.untilTime(instantPhrase(wall(nitya.endsAt), day: date, lang: lang))),
          mark: nityaYogaIsAuspicious(nitya.index) ? Mark.good : Mark.avoid,
        ),
      ...group(l10n.goodYogas, YogaNature.shubh),
      ...group(l10n.badYogas, YogaNature.ashubh),
    ];
  }
}
