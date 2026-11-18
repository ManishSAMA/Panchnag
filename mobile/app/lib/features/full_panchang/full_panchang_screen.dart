import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:panchang_engine/panchang_engine.dart';

import '../../engine/day_reading.dart';
import '../../format/festival_text.dart';
import '../../format/panchang_text.dart';
import '../../l10n/app_localizations.dart';
import '../../l10n/city_name.dart';
import '../../location/city_time.dart';
import '../../location/location_store.dart';
import '../../settings/settings_store.dart';
import '../../shared/date_navigator.dart';
import '../../shared/day_notes.dart';
import '../../shared/festival_icon.dart';
import '../../shared/festival_mark.dart';
import '../../shared/moon_phase.dart';
import '../../shared/pothi_page.dart';
import '../../shared/navpad_icons.dart';
import '../../shared/navpad_widgets.dart';
import '../../shared/panchang_section.dart';
import '../../theme/navpad.dart';
import '../../theme/pothi.dart';
import '../choghadiya/choghadiya_screen.dart';
import '../festivals/festival_state.dart';
import '../muhurat/muhurat_grid.dart';
import '../today/today_state.dart';

class FullPanchangScreen extends ConsumerStatefulWidget {
  const FullPanchangScreen({super.key});

  @override
  ConsumerState<FullPanchangScreen> createState() => _FullPanchangScreenState();
}

class _FullPanchangScreenState extends ConsumerState<FullPanchangScreen> {
  final _scroll = ScrollController();
  final _sectionKeys = <String, GlobalKey>{
    'panchang': GlobalKey(),
    'sun': GlobalKey(),
    'tithi': GlobalKey(),
    'pachchakkhan': GlobalKey(),
    'choghadiya': GlobalKey(),
    'muhurat': GlobalKey(),
  };
  String? _destination;
  Timer? _highlightTimer;

  @override
  void dispose() {
    _highlightTimer?.cancel();
    _scroll.dispose();
    super.dispose();
  }

  void _showSection(String id) {
    final target = _sectionKeys[id]!.currentContext;
    if (target == null) return;
    _highlightTimer?.cancel();
    setState(() => _destination = id);
    Scrollable.ensureVisible(
      target,
      duration: MediaQuery.disableAnimationsOf(context)
          ? Duration.zero
          : const Duration(milliseconds: 350),
      curve: Curves.easeOutCubic,
      alignment: 0.05,
    );
    _highlightTimer = Timer(const Duration(milliseconds: 900), () {
      if (mounted) setState(() => _destination = null);
    });
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    final p = Theme.of(context).extension<Pothi>() ?? Pothi.light;
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
      key: const Key('full-panchang-screen'),
      backgroundColor: p.ground,
      appBar: AppBar(
        backgroundColor: p.ground,
        foregroundColor: p.ink,
        title: Text(l10n.fullPanchang),
        actions: [
          IconButton(
            tooltip: l10n.symbolGuide,
            onPressed: () => context.push('/panchang-symbols'),
            icon: const Icon(Icons.auto_stories_outlined),
          ),
        ],
      ),
      body: PothiPage(
        child: SingleChildScrollView(
          controller: _scroll,
          padding: const EdgeInsets.only(bottom: 28),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              DateNavigator(date: date, timezone: city.timezone),
              Text(
                city.nameFor(context),
                textAlign: TextAlign.center,
                style: Theme.of(context).textTheme.labelMedium!
                    .copyWith(color: p.secondary),
              ),
              ...switch (reading) {
                AsyncData(:final value) => [
                  _AlmanacHeader(reading: value, timezone: city.timezone),
                  _SectionLinks(onSelect: _showSection),
                  _FullDay(
                    request: request,
                    reading: value,
                    timezone: city.timezone,
                    sectionKeys: _sectionKeys,
                    destination: _destination,
                  ),
                ],
                AsyncError(:final error) => [
                  Padding(
                    padding: const EdgeInsets.only(top: 20),
                    child: Note(
                      icon: NoteIcon.alert,
                      title: l10n.appTitle,
                      body: '$error',
                    ),
                  ),
                ],
                _ => const [
                  Padding(
                    padding: EdgeInsets.all(32),
                    child: Center(child: CircularProgressIndicator()),
                  ),
                ],
              },
            ],
          ),
        ),
      ),
    );
  }
}

class _AlmanacHeader extends StatelessWidget {
  const _AlmanacHeader({required this.reading, required this.timezone});

  final PanchangDay reading;
  final String timezone;

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    final lang = langOf(context);
    final p = Theme.of(context).extension<Pothi>() ?? Pothi.light;
    final tithi = tithiName(reading.jainTithi.index, lang);
    return Container(
      margin: const EdgeInsets.fromLTRB(8, 8, 18, 0),
      padding: const EdgeInsets.symmetric(vertical: 16),
      decoration: BoxDecoration(
        border: Border(
          top: BorderSide(color: p.accent),
          bottom: BorderSide(color: p.rule),
        ),
      ),
      child: Column(
        children: [
          Container(
            key: const Key('full-lunar-seal'),
            padding: const EdgeInsets.all(4),
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              border: Border.all(color: p.accent),
            ),
            child: Container(
              padding: const EdgeInsets.all(3),
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                border: Border.all(color: p.accent),
              ),
              child: MoonPhase(
                tithi: reading.jainTithi.index,
                size: 40,
                semanticLabel: l10n.moonOfTithi(tithi),
              ),
            ),
          ),
          const SizedBox(height: 12),
          Text(
            tithi,
            key: const Key('full-hero-tithi'),
            textAlign: TextAlign.center,
            style: NavpadType.displayBand.copyWith(color: p.ink, fontSize: 30),
          ),
          const SizedBox(height: 7),
          Text(
            '${monthName(reading.month, lang)} · ${tithiShort(reading.jainTithi.index, lang)}\n'
            '${samvatLine(viraNirvana: reading.viraNirvanaSamvat, vikram: reading.vikramSamvat, lang: lang)}',
            textAlign: TextAlign.center,
            style: Theme.of(context).textTheme.bodyMedium!
                .copyWith(color: p.secondary),
          ),
        ],
      ),
    );
  }
}

class _SectionLinks extends StatelessWidget {
  const _SectionLinks({required this.onSelect});

  final ValueChanged<String> onSelect;

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    final p = Theme.of(context).extension<Pothi>() ?? Pothi.light;
    final links = [
      ('sun', l10n.sunMoonHeading),
      ('tithi', l10n.tithiMonthHeading),
      ('pachchakkhan', l10n.pachchakkhan),
      ('choghadiya', l10n.choghadiyaTitle),
      ('muhurat', l10n.muhuratTitle),
    ];
    return SingleChildScrollView(
      scrollDirection: Axis.horizontal,
      padding: const EdgeInsets.symmetric(horizontal: 22),
      child: Row(
        children: [
          for (final (id, label) in links)
            TextButton(
              onPressed: () => onSelect(id),
              style: TextButton.styleFrom(
                foregroundColor: p.accent,
                minimumSize: const Size(48, 48),
              ),
              child: Text(
                label,
                style: Theme.of(context).textTheme.labelLarge!
                    .copyWith(decoration: TextDecoration.underline),
              ),
            ),
        ],
      ),
    );
  }
}

class _FullDay extends ConsumerWidget {
  const _FullDay({
    required this.request,
    required this.reading,
    required this.timezone,
    required this.sectionKeys,
    required this.destination,
  });

  final DayRequest request;
  final PanchangDay reading;
  final String timezone;
  final Map<String, GlobalKey> sectionKeys;
  final String? destination;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final section = ref
        .watch(sectionReadingProvider(SectionRequest(request)))
        .value;
    final l10n = AppLocalizations.of(context);
    final lang = langOf(context);
    DateTime wall(DateTime utc) => roundDownToMinute(cityWall(utc, timezone));
    String time(DateTime utc) => clockPhrase(wall(utc), lang);
    String? dateNote(DateTime utc) {
      final local = wall(utc);
      final day = CivilDate(local.year, local.month, local.day);
      return day == reading.date ? null : shortDate(day, lang);
    }

    final festivals = festivalYear(ref, reading.date.year);
    final lines = festivals == null
        ? null
        : festivalLines(festivalsOn(festivals, reading.date), lang);
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        KeyedSubtree(
          key: const Key('full-panchang-section'),
          child: _Group(
            id: 'panchang',
            title: l10n.panchangHeading,
            sectionKeys: sectionKeys,
            destination: destination,
            rows: const [],
            children: switch (section) {
              null => const [
                Padding(
                  padding: EdgeInsets.all(16),
                  child: Center(child: CircularProgressIndicator()),
                ),
              ],
              final value => panchangSectionRows(
                l10n: l10n,
                lang: lang,
                day: reading,
                section: value,
                month: lunarMonthOf(reading, ref.watch(monthSystemProvider)),
                timezone: timezone,
              ),
            },
          ),
        ),
        _Group(
          id: 'sun',
          title: l10n.sunMoonHeading,
          sectionKeys: sectionKeys,
          destination: destination,
          rows: [
            _Row(label: l10n.sunrise, value: time(reading.sunrise)),
            _Row(label: l10n.sunset, value: time(reading.sunset)),
            _Row(
              label: l10n.nextSunrise,
              value: time(reading.nextSunrise),
              subtitle: dateNote(reading.nextSunrise),
            ),
          ],
        ),
        _Group(
          id: 'tithi',
          title: l10n.tithiMonthHeading,
          sectionKeys: sectionKeys,
          destination: destination,
          rows: [
            _Row(
              label: l10n.jainReference,
              value: time(reading.jainTithi.reference),
            ),
            _Row(
              key: const Key('full-jain-tithi-start'),
              label: l10n.tithiStart,
              value: time(reading.jainTithi.startsAt),
              subtitle: dateNote(reading.jainTithi.startsAt),
            ),
          ],
          children: [
            _Subheading(title: l10n.tithiSequence),
            for (final (index, span) in reading.tithis.indexed)
              _Row(
                key: Key('full-tithi-span-$index'),
                label: tithiName(span.index, lang),
                value: span.endsAt == null
                    ? l10n.continuesNextSunrise
                    : time(span.endsAt!),
                subtitle: span.endsAt == null ? null : dateNote(span.endsAt!),
              ),
            ...dayNotes(reading: reading, l10n: l10n, lang: lang, wall: wall),
          ],
        ),
        _Group(
          id: 'pachchakkhan',
          title: l10n.pachchakkhan,
          sectionKeys: sectionKeys,
          destination: destination,
          rows: [
            for (final (index, completion)
                in reading.pachchakkhan.completions.indexed)
              _Row(
                key: Key('full-pachchakkhan-$index'),
                label: pachchakkhanName(completion.kind, lang),
                value: clockPhrase(
                  roundUpToMinute(cityWall(completion.at, timezone)),
                  lang,
                ),
              ),
            _Row(
              key: const Key('full-pachchakkhan-evening'),
              label: l10n.eveningNames,
              value: time(reading.pachchakkhan.evening),
              subtitle: l10n.bySunset,
            ),
            _Row(
              key: const Key('full-pachchakkhan-parana'),
              label: l10n.ayambilUpvas,
              value: time(reading.pachchakkhan.parana),
              subtitle: l10n.paranaNextNavkarsi,
            ),
            _Row(label: l10n.mutthiSahiyam, value: l10n.noFixedTime),
            _Row(label: l10n.ekasanuBiyasanu, value: l10n.withATimeAbove),
          ],
        ),
        _Group(
          id: 'choghadiya',
          title: l10n.choghadiyaTitle,
          sectionKeys: sectionKeys,
          destination: destination,
          rows: [
            for (final (index, slot) in reading.choghadiya.indexed) ...[
              if (index == 0) _Row(label: l10n.dayHeading, value: ''),
              if (index == 8) _Row(label: l10n.nightHeading, value: ''),
              _Row(
                key: Key('full-choghadiya-$index'),
                label: choghadiyaName(slot.name, lang),
                value: clockRange(wall(slot.start), wall(slot.end), lang),
                subtitle: natureLabel(l10n, slot.name.nature),
              ),
            ],
          ],
        ),
        _Group(
          id: 'muhurat',
          title: l10n.muhuratTitle,
          sectionKeys: sectionKeys,
          destination: destination,
          rows: const [],
          children: const [MuhuratGrid()],
        ),
        _Group(
          id: 'festivals',
          title: l10n.festivalsOnDay,
          sectionKeys: sectionKeys,
          destination: destination,
          rows: switch (lines) {
            null => [_Row(label: l10n.festivalsLoading, value: '')],
            [] => [_Row(label: l10n.noFestivalsOnDay, value: '')],
            final values => [
              for (final line in values)
                _Row(
                  label: line.name,
                  value: line.start == line.end
                      ? festivalKindLabel(line.kind, l10n)
                      : dateRange(line.start, line.end, lang),
                  subtitle: line.start == line.end
                      ? null
                      : festivalKindLabel(line.kind, l10n),
                  glyph: line.kind,
                ),
            ],
          },
        ),
        Padding(
          padding: const EdgeInsets.fromLTRB(32, 22, 18, 0),
          child: Text(
            l10n.fullPanchangFootnote,
            textAlign: TextAlign.center,
            style: Theme.of(context).textTheme.labelMedium!.copyWith(
              color: Theme.of(context).extension<Pothi>()?.secondary,
            ),
          ),
        ),
      ],
    );
  }
}

class _Group extends StatelessWidget {
  const _Group({
    required this.id,
    required this.title,
    required this.rows,
    required this.sectionKeys,
    required this.destination,
    this.children = const [],
  });

  final String id, title;
  final List<_Row> rows;
  final List<Widget> children;
  final Map<String, GlobalKey> sectionKeys;
  final String? destination;

  @override
  Widget build(BuildContext context) {
    final p = Theme.of(context).extension<Pothi>() ?? Pothi.light;
    final highlighted = destination == id;
    return AnimatedContainer(
      key: sectionKeys[id],
      duration: MediaQuery.disableAnimationsOf(context)
          ? Duration.zero
          : const Duration(milliseconds: 250),
      color: highlighted ? p.accent.withValues(alpha: 0.10) : null,
      margin: const EdgeInsets.only(left: 8, right: 18, top: 22),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          PothiHeading(title: title),
          ...rows,
          ...children,
        ],
      ),
    );
  }
}

class _Subheading extends StatelessWidget {
  const _Subheading({required this.title});
  final String title;

  @override
  Widget build(BuildContext context) {
    final p = Theme.of(context).extension<Pothi>() ?? Pothi.light;
    return Padding(
      padding: const EdgeInsets.only(top: 18, bottom: 4),
      child: Text(
        title,
        style: Theme.of(context).textTheme.titleMedium!
            .copyWith(color: p.ink, fontSize: 17),
      ),
    );
  }
}

class _Row extends StatelessWidget {
  const _Row({
    super.key,
    required this.label,
    required this.value,
    this.subtitle,
    this.glyph,
  });

  final String label, value;
  final String? subtitle;
  final FestivalKind? glyph;

  @override
  Widget build(BuildContext context) {
    final p = Theme.of(context).extension<Pothi>() ?? Pothi.light;
    final n = Theme.of(context).extension<Navpad>()!;
    final text = Theme.of(context).textTheme;
    return Container(
      constraints: const BoxConstraints(minHeight: 48),
      padding: const EdgeInsets.symmetric(vertical: 8),
      decoration: BoxDecoration(
        border: Border(bottom: BorderSide(color: p.rule)),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          if (glyph case final kind?) ...[
            Padding(
              padding: const EdgeInsets.only(top: 2, right: 8),
              child: NavpadIcon(
                festivalGlyph(kind),
                size: 22,
                color: kind.isVrat ? n.green : p.accent,
              ),
            ),
          ],
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(label, style: text.bodyLarge!.copyWith(color: p.ink)),
                if (subtitle != null)
                  Text(
                    subtitle!,
                    style: text.labelMedium!.copyWith(color: p.secondary),
                  ),
              ],
            ),
          ),
          if (value.isNotEmpty) ...[
            const SizedBox(width: 12),
            Flexible(
              child: Text(
                value,
                textAlign: TextAlign.end,
                style: text.bodyLarge!.copyWith(
                  color: p.ink,
                  fontWeight: FontWeight.w600,
                ),
              ),
            ),
          ],
        ],
      ),
    );
  }
}

/// The पंचांग section, in the user's order: tithi, nakshatra, yoga, karana
/// and weekday; then month, paksha, gata and the samvats; then the Rashis.
List<Widget> panchangSectionRows({
  required AppLocalizations l10n,
  required Lang lang,
  required PanchangDay day,
  required PanchangSection section,
  required LunarMonth month,
  required String timezone,
}) {
  SectionLine line(
    String key,
    String name, {
    DateTime? until,
    List<int> rashis = const [],
  }) => SectionLine(
    key: Key(key),
    name: name,
    day: day.date,
    timezone: timezone,
    until: until,
    rashis: rashis,
  );
  List<SectionLine> spans(
    String key,
    List<ElementSpan> values,
    String Function(int) name,
  ) => [
    for (final (k, span) in values.indexed)
      line('$key-$k', name(span.index), until: span.endsAt),
  ];
  const gap = SizedBox(height: 18);
  final nakshatras = [
    (index: day.nakshatra.index, endsAt: day.nakshatra.endsAt),
    section.nextNakshatra,
  ];
  return [
    SectionRow(
      label: l10n.tithiLabel,
      lines: spans('section-tithi', [
        (index: day.jainTithi.index, endsAt: day.jainTithi.endsAt),
        section.nextTithi,
      ], (i) => tithiName(i, lang)),
    ),
    SectionRow(
      label: l10n.nakshatra,
      lines: [
        for (final (k, span) in nakshatras.indexed)
          line(
            'section-nakshatra-$k',
            k == 0
                ? l10n.nakshatraWithPada(
                    nakshatraName(span.index, lang),
                    day.nakshatra.pada,
                  )
                : nakshatraName(span.index, lang),
            until: span.endsAt,
            rashis: nakshatraRashis(span.index),
          ),
      ],
    ),
    SectionRow(
      label: l10n.yogaLabel,
      lines: spans('section-yoga', section.yogas, (i) => yogaName(i, lang)),
    ),
    SectionRow(
      label: l10n.karanaLabel,
      lines: spans(
        'section-karana',
        section.karanas,
        (i) => karanaName(i, lang),
      ),
    ),
    SectionRow(
      label: l10n.varaLabel,
      lines: [line('section-vara', weekdayName(day.date, lang))],
    ),
    gap,
    SectionRow(
      label: l10n.lunarMonthLabel,
      lines: [line('section-month', monthName(month, lang))],
    ),
    SectionRow(
      label: l10n.pakshaLabel,
      lines: [line('section-paksha', pakshaName(day.jainTithi.index, lang))],
    ),
    SectionRow(
      label: l10n.gataLabel,
      lines: [GataLine(key: const Key('section-gata'), gata: section.gata)],
    ),
    SectionRow(
      label: l10n.vikramSamvat,
      lines: [line('section-vikram', '${day.vikramSamvat}')],
    ),
    SectionRow(
      label: l10n.viraNirvanaSamvat,
      lines: [line('section-vira-nirvana', '${day.viraNirvanaSamvat}')],
    ),
    SectionRow(
      label: l10n.shakaSamvat,
      lines: [line('section-shaka', '${day.shakaSamvat}')],
    ),
    gap,
    SectionRow(
      label: l10n.moonRashiLabel,
      lines: [
        for (final (k, span) in section.moonRashis.indexed)
          line(
            'section-moon-rashi-$k',
            rashiName(span.index, lang),
            // The next sign shows without an end: it lasts two days or more.
            until: k == 0 ? span.endsAt : null,
            rashis: [span.index],
          ),
      ],
    ),
    SectionRow(
      label: l10n.sunRashiLabel,
      lines: [
        for (final (k, span) in section.sunRashis.indexed)
          line(
            'section-sun-rashi-$k',
            rashiName(span.index, lang),
            until: span.endsAt,
            rashis: [span.index],
          ),
      ],
    ),
  ];
}
