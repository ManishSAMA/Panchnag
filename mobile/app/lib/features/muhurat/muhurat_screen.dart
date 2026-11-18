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
    required CivilDate date,
    required String timezone,
    required DateTime now,
  }) {
    final l10n = AppLocalizations.of(context);
    final lang = langOf(context);
    DateTime wall(DateTime utc) => roundDownToMinute(cityWall(utc, timezone));
    String range(DateTime start, DateTime end) => glued(clockRange(wall(start), wall(end), lang));
    String span(DateTime start, DateTime end) {
      final (from, to) = spanPhrases(wall(start), wall(end), day: date, lang: lang);
      return '${glued(from)} – ${glued(to)}';
    }

    final none = TimeRow(name: kind.title(l10n), time: l10n.noneToday);

    /// A window that may be running now gets "अभी" in words, not only colour.
    Widget timed(String name, TimeWindow w, {String? subtitle}) {
      final running = !now.isBefore(w.start) && now.isBefore(w.end);
      final time = range(w.start, w.end);
      return TimeRow(
        name: name,
        time: time,
        subtitle: subtitle,
        suffix: running ? l10n.slotNow : null,
        semanticsLabel: '$name $time${subtitle == null ? '' : ', $subtitle'}${running ? ', ${l10n.slotNow}' : ''}',
      );
    }

    final avoid = markText(l10n, Mark.avoid);
    return switch (kind) {
      MuhuratKind.rahuKaal => [
        const ListTop(),
        timed(l10n.rahuKaal, muhurat.rahuKaal, subtitle: avoid),
        timed(l10n.yamaganda, muhurat.yamaganda, subtitle: avoid),
        timed(l10n.gulika, muhurat.gulika, subtitle: avoid),
      ],
      MuhuratKind.abhijit => [
        const ListTop(),
        timed(l10n.abhijit, muhurat.abhijit, subtitle: markText(l10n, Mark.good)),
      ],
      MuhuratKind.panchak => [
        const ListTop(),
        switch (muhurat.panchak) {
          (window: final w?, period: _, nextPeriod: _) => timed(l10n.panchakToday, w, subtitle: avoid),
          _ => TimeRow(name: l10n.panchakToday, time: l10n.noneToday),
        },
        if (muhurat.panchak.period case final p?) TimeRow(name: l10n.panchakPeriod, time: span(p.start, p.end)),
        if (muhurat.panchak.nextPeriod case final p?) TimeRow(name: l10n.panchakNext, time: span(p.start, p.end)),
      ],
      MuhuratKind.bhadra => [
        const ListTop(),
        if (muhurat.bhadra.isEmpty) none,
        for (final w in muhurat.bhadra)
          TimeRow(
            name: l10n.bhadra,
            time: span(w.start, w.end),
            subtitle:
                '${bhadraResidenceText(w.residence, lang)} · '
                '${markText(l10n, w.residence == BhadraResidence.earth ? Mark.avoid : Mark.plain)}',
          ),
      ],
      MuhuratKind.gandmool => [
        const ListTop(),
        if (muhurat.gandmool.isEmpty) none,
        for (final w in muhurat.gandmool)
          TimeRow(name: nakshatraName(w.nakshatra, lang), time: span(w.start, w.end), subtitle: avoid),
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
          time: markText(l10n, muhurat.agniVaas.isAuspicious ? Mark.good : Mark.avoid),
        ),
      ],
      MuhuratKind.yoga => _yogaRows(context, muhurat: muhurat, section: section, span: span, wall: wall, date: date),
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
          subtitle: markText(l10n, nityaYogaIsAuspicious(nitya.index) ? Mark.good : Mark.avoid),
        ),
      ...group(l10n.goodYogas, YogaNature.shubh),
      ...group(l10n.badYogas, YogaNature.ashubh),
    ];
  }
}
