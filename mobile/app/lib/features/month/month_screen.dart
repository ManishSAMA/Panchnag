import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:panchang_engine/panchang_engine.dart';

import '../../engine/day_reading.dart';
import '../../format/festival_text.dart';
import '../../format/panchang_text.dart';
import '../../l10n/app_localizations.dart';
import '../../location/city_time.dart';
import '../../location/location_store.dart';
import '../../settings/settings_store.dart';
import '../../shared/day_notes.dart';
import '../../shared/festival_mark.dart';
import '../../shared/navpad_widgets.dart';
import '../../shared/settings_button.dart';
import '../../theme/navpad.dart';
import '../festivals/festival_state.dart';
import '../today/today_state.dart';
import 'month_state.dart';

/// Below this height the grid and a docked day panel don't fit together, so
/// the day opens in a modal sheet instead (plans/mobile-month-tab.md).
const double dockedPanelMinHeight = 640;

/// Month (mobile-ui-design.md §3 · Month): the Gregorian grid. The festival
/// marks fill in when the year arrives from its own worker, after the grid.
class MonthScreen extends ConsumerWidget {
  const MonthScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l10n = AppLocalizations.of(context);
    final city = ref.watch(locationProvider)!;
    final view = ref.watch(monthViewProvider);
    final reading = ref.watch(
      monthReadingProvider(
        MonthRequest(
          year: view.year,
          month: view.month,
          lat: city.lat,
          lon: city.lon,
          timezone: city.timezone,
          rule: ref.watch(sunriseRuleProvider),
        ),
      ),
    );
    final docked = MediaQuery.sizeOf(context).height >= dockedPanelMinHeight;
    final today = todayIn(city.timezone, currentTime(ref));
    final festivals = festivalYear(ref, view.year);
    final lang = langOf(context);
    List<FestivalLine>? linesOn(CivilDate date) =>
        festivals == null ? null : festivalLines(festivalsOn(festivals, date), lang);
    return Scaffold(
      appBar: AppBar(title: Text(l10n.tabMonth), actions: const [SettingsButton()]),
      body: SingleChildScrollView(
        padding: const EdgeInsets.only(bottom: 24),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            _Header(view: view, today: today, days: reading.value),
            ...switch (reading) {
              AsyncData(:final value) => [
                _Grid(
                  days: value,
                  today: today,
                  selected: view.selected,
                  linesOn: linesOn,
                  onTap: (day) {
                    ref.read(monthViewProvider.notifier).select(day.date);
                    if (!docked) _openSheet(context, day, city.timezone, linesOn(day.date));
                  },
                ),
                _Legend(withMarks: festivals != null),
                if (docked)
                  _DayPanel(
                    day: value.firstWhere((d) => d.date == view.selected),
                    timezone: city.timezone,
                    festivals: linesOn(view.selected),
                  ),
              ],
              AsyncError(:final error) => [Note(icon: NoteIcon.alert, title: l10n.appTitle, body: '$error')],
              _ => const <Widget>[],
            },
          ],
        ),
      ),
    );
  }

  void _openSheet(BuildContext context, PanchangDay day, String timezone, List<FestivalLine>? festivals) =>
      showModalBottomSheet<void>(
    context: context,
    isScrollControlled: true,
    showDragHandle: true,
    builder: (sheet) => SafeArea(
      child: SingleChildScrollView(
        child: _DayPanel(day: day, timezone: timezone, festivals: festivals, inSheet: true),
      ),
    ),
  );
}

class _Header extends ConsumerWidget {
  const _Header({required this.view, required this.today, required this.days});

  final MonthView view;
  final CivilDate today;
  final List<PanchangDay>? days;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l10n = AppLocalizations.of(context);
    final lang = langOf(context);
    final n = Theme.of(context).extension<Navpad>()!;
    final text = Theme.of(context).textTheme;
    final months = ref.read(monthViewProvider.notifier);
    final system = ref.watch(monthSystemProvider);
    final shown = (view.year, view.month);
    final showsToday = shown == (today.year, today.month);
    final shownDays = days;
    return Padding(
      padding: const EdgeInsets.fromLTRB(6, 4, 6, 10),
      child: Row(
        children: [
          IconButton(
            icon: const Icon(Icons.chevron_left),
            tooltip: l10n.previousMonth,
            onPressed: shown != (firstDay.year, firstDay.month) ? () => months.shift(-1) : null,
          ),
          Expanded(
            child: Column(
              children: [
                Semantics(
                  header: true,
                  child: Text(
                    monthTitle(view.year, view.month, lang),
                    textAlign: TextAlign.center,
                    style: NavpadType.displayMonth.copyWith(color: n.ink),
                  ),
                ),
                if (shownDays != null && shownDays.first.date.month == view.month)
                  Text(
                    monthSpanLine(
                      months: [for (final d in shownDays) lunarMonthOf(d, system)],
                      vikrams: [for (final d in shownDays) d.vikramSamvat],
                      lang: lang,
                    ),
                    textAlign: TextAlign.center,
                    style: text.labelMedium!.copyWith(color: n.ink2),
                  ),
                if (!showsToday)
                  Padding(
                    padding: const EdgeInsets.only(top: 6),
                    child: OutlinedButton(onPressed: months.goToday, child: Text(l10n.today)),
                  ),
              ],
            ),
          ),
          IconButton(
            icon: const Icon(Icons.chevron_right),
            tooltip: l10n.nextMonth,
            onPressed: shown != (lastDay.year, lastDay.month) ? () => months.shift(1) : null,
          ),
        ],
      ),
    );
  }
}

class _Grid extends StatelessWidget {
  const _Grid({
    required this.days,
    required this.today,
    required this.selected,
    required this.linesOn,
    required this.onTap,
  });

  final List<PanchangDay> days;
  final CivilDate today, selected;

  /// Null while the festival year is on its way.
  final List<FestivalLine>? Function(CivilDate) linesOn;
  final void Function(PanchangDay) onTap;

  @override
  Widget build(BuildContext context) {
    final lang = langOf(context);
    final n = Theme.of(context).extension<Navpad>()!;
    final text = Theme.of(context).textTheme;
    final lead = days.first.vara;
    final slots = <PanchangDay?>[
      ...List.filled(lead, null),
      ...days,
      ...List.filled((7 - (lead + days.length) % 7) % 7, null),
    ];
    final weeks = [for (var i = 0; i < slots.length; i += 7) slots.sublist(i, i + 7)];
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 10),
      child: Column(
        children: [
          Row(
            children: [
              for (var vara = 0; vara < 7; vara++)
                Expanded(
                  child: Padding(
                    padding: const EdgeInsets.only(bottom: 6),
                    child: Text(
                      varaShort(vara, lang),
                      textAlign: TextAlign.center,
                      style: text.labelMedium!.copyWith(color: n.ink2),
                    ),
                  ),
                ),
            ],
          ),
          DecoratedBox(
            decoration: BoxDecoration(
              border: Border(top: BorderSide(color: n.hair), left: BorderSide(color: n.hair)),
            ),
            child: Column(
              children: [
                for (final week in weeks)
                  IntrinsicHeight(
                    child: Row(
                      crossAxisAlignment: CrossAxisAlignment.stretch,
                      children: [
                        for (final day in week)
                          Expanded(
                            child: day == null
                                ? const _Cell.blank()
                                : _Cell(
                                    day: day,
                                    isToday: day.date == today,
                                    isSelected: day.date == selected,
                                    marks: cellMarks(linesOn(day.date) ?? const []),
                                    onTap: () => onTap(day),
                                  ),
                          ),
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

class _Cell extends StatelessWidget {
  const _Cell({
    required PanchangDay this.day,
    required this.isToday,
    required this.isSelected,
    required this.marks,
    required this.onTap,
  });

  const _Cell.blank() : day = null, isToday = false, isSelected = false, marks = const [], onTap = null;

  final PanchangDay? day;
  final bool isToday, isSelected;
  final List<FestivalKind> marks;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    final n = Theme.of(context).extension<Navpad>()!;
    final border = BoxDecoration(
      color: isSelected ? n.pill : n.ground,
      border: Border(right: BorderSide(color: n.hair), bottom: BorderSide(color: n.hair)),
    );
    final day = this.day;
    if (day == null) return Container(constraints: const BoxConstraints(minHeight: 64), decoration: border);

    final l10n = AppLocalizations.of(context);
    final lang = langOf(context);
    final flag = switch (day) {
      PanchangDay(kshaya: _?) => l10n.flagKshaya,
      PanchangDay(vriddhi: _?) => l10n.flagVriddhi,
      _ => null,
    };
    final flagMeaning = switch (day) {
      PanchangDay(kshaya: _?) => l10n.legendKshaya,
      PanchangDay(vriddhi: _?) => l10n.legendVriddhi,
      _ => null,
    };
    return Semantics(
      key: Key('month-cell-${day.date.iso}'),
      button: true,
      selected: isSelected,
      label: [
        shortDate(day.date, lang),
        tithiName(day.jainTithi.index, lang),
        ?flagMeaning,
        for (final kind in marks) festivalKindLabel(kind, l10n),
      ].join(', '),
      excludeSemantics: true,
      child: Material(
        type: MaterialType.transparency,
        child: InkWell(
          onTap: onTap,
          child: Container(
            constraints: const BoxConstraints(minHeight: 64),
            decoration: border,
            foregroundDecoration: isToday ? BoxDecoration(border: Border.all(color: n.navy, width: 2)) : null,
            padding: const EdgeInsets.fromLTRB(5, 4, 3, 4),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Expanded(child: Text('${day.date.day}', style: NavpadType.cellDay.copyWith(color: n.ink))),
                    if (flag != null) Text(flag, style: NavpadType.cellFlag.copyWith(color: n.ink)),
                  ],
                ),
                const SizedBox(height: 2),
                Text(tithiShort(day.jainTithi.index, lang), style: NavpadType.cellTithi.copyWith(color: n.ink2)),
                if (marks.isNotEmpty)
                  Padding(
                    padding: const EdgeInsets.only(top: 4),
                    child: Wrap(
                      spacing: 3,
                      children: [for (final kind in marks) FestivalMark(kind: kind, size: 7)],
                    ),
                  ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

class _Legend extends StatelessWidget {
  const _Legend({required this.withMarks});

  /// The marks join the legend with the festival year, as they join the grid.
  final bool withMarks;

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    final n = Theme.of(context).extension<Navpad>()!;
    final text = Theme.of(context).textTheme;
    Widget entry(Widget sign, String meaning, {Key? key}) => Row(
      key: key,
      mainAxisSize: MainAxisSize.min,
      children: [
        ExcludeSemantics(child: sign),
        const SizedBox(width: 6),
        Text(meaning, style: text.labelMedium!.copyWith(color: n.ink2)),
      ],
    );
    Widget flag(String letters) => Text(letters, style: NavpadType.cellFlag.copyWith(color: n.ink, fontSize: 13));
    return Padding(
      padding: const EdgeInsets.fromLTRB(18, 10, 18, 0),
      child: Wrap(
        spacing: 20,
        runSpacing: 4,
        children: [
          if (withMarks)
            for (final kind in FestivalKind.values)
              entry(FestivalMark(kind: kind), festivalKindLabel(kind, l10n), key: Key('legend-${kind.name}')),
          entry(flag(l10n.flagKshaya), l10n.legendKshaya),
          entry(flag(l10n.flagVriddhi), l10n.legendVriddhi),
        ],
      ),
    );
  }
}

/// The picked day: docked under the grid, or the body of the modal sheet.
class _DayPanel extends ConsumerWidget {
  const _DayPanel({required this.day, required this.timezone, required this.festivals, this.inSheet = false});

  final PanchangDay day;
  final String timezone;

  /// Null while the festival year is on its way.
  final List<FestivalLine>? festivals;
  final bool inSheet;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l10n = AppLocalizations.of(context);
    final lang = langOf(context);
    final n = Theme.of(context).extension<Navpad>()!;
    DateTime wall(DateTime utc) => cityWall(utc, timezone);
    final notes = dayNotes(reading: day, l10n: l10n, lang: lang, wall: wall);

    void openFullDay() {
      if (inSheet) Navigator.of(context).pop();
      ref.read(selectedDateProvider.notifier).goTo(day.date);
      context.go('/today');
    }

    return Container(
      key: const Key('month-day-panel'),
      margin: EdgeInsets.only(top: inSheet ? 0 : 16),
      color: inSheet ? null : n.surface,
      padding: const EdgeInsets.only(bottom: 18),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          if (!inSheet)
            Center(
              child: Container(
                margin: const EdgeInsets.only(top: 10),
                width: 32,
                height: 4,
                decoration: BoxDecoration(color: n.ink3, borderRadius: BorderRadius.circular(2)),
              ),
            ),
          Padding(
            padding: EdgeInsets.fromLTRB(18, inSheet ? 0 : 14, 18, 10),
            child: Semantics(
              header: true,
              child: Text(longDate(day.date, lang), style: NavpadType.displayHeading.copyWith(color: n.ink)),
            ),
          ),
          const ListTop(),
          TimeRow(
            name: tithiName(day.jainTithi.index, lang),
            subtitle: monthName(lunarMonthOf(day, ref.watch(monthSystemProvider)), lang),
            time: l10n.until(instantPhrase(wall(day.jainTithi.endsAt), day: day.date, lang: lang)),
          ),
          TimeRow(name: l10n.sunrise, time: clockPhrase(wall(day.sunrise), lang)),
          TimeRow(name: l10n.sunset, time: clockPhrase(wall(day.sunset), lang)),
          for (final line in festivals ?? const <FestivalLine>[])
            FestivalRow(
              line: line,
              subtitle: festivalKindLabel(line.kind, l10n),
              value: line.start == line.end ? null : dateRange(line.start, line.end, lang),
            ),
          for (final note in notes) Padding(padding: const EdgeInsets.only(top: 10), child: note),
          Padding(
            padding: const EdgeInsets.fromLTRB(18, 16, 18, 0),
            child: Align(
              alignment: AlignmentDirectional.centerStart,
              child: FilledButton(onPressed: openFullDay, child: Text(l10n.openFullDay)),
            ),
          ),
        ],
      ),
    );
  }
}
