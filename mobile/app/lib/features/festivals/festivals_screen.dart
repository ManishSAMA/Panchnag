import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:panchang_engine/panchang_engine.dart';

import '../../format/festival_text.dart';
import '../../format/panchang_text.dart';
import '../../l10n/app_localizations.dart';
import '../../location/city_time.dart';
import '../../location/location_store.dart';
import '../../shared/festival_icon.dart';
import '../../shared/festival_mark.dart';
import '../../shared/settings_button.dart';
import '../../shared/year_month_picker.dart';
import '../../theme/navpad.dart';
import '../month/month_state.dart';
import '../today/today_state.dart';
import '../../shared/pothi_page.dart';
import 'festival_state.dart';

/// Festivals (mobile-ui-design.md §3 · Festivals): the rest of this year from
/// today, by Gregorian month, under the saved filter chip. The year comes from
/// the festival worker, so the chips paint first and the list follows.
class FestivalsScreen extends ConsumerWidget {
  const FestivalsScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l10n = AppLocalizations.of(context);
    final today = todayIn(ref.watch(locationProvider)!.timezone, ref.read(clockProvider)());
    final filter = ref.watch(festivalFilterProvider);
    final year = ref.watch(festivalsYearProvider) ?? today.year;
    // This year from today; any other year whole (user 2026-11-19).
    final from = year == today.year ? today : CivilDate(year, 1, 1);
    final festivals = festivalYear(ref, year);
    return Scaffold(
      appBar: AppBar(title: Text(l10n.tabFestivals), actions: const [SettingsButton()]),
      body: PothiPage(child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          _FilterChips(selected: filter, year: year),
          Expanded(
            child: festivals == null
                ? const _Loading()
                : _FestivalList(
                    dates: festivalDates(festivals, from: from, lang: langOf(context), filter: filter),
                  ),
          ),
        ],
      )),
    );
  }
}

class _FilterChips extends ConsumerWidget {
  const _FilterChips({required this.selected, required this.year});

  final FestivalFilter selected;
  final int year;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l10n = AppLocalizations.of(context);
    String label(FestivalFilter filter) => switch (filter.kind) {
      null => l10n.festivalsAll,
      final kind => festivalKindLabel(kind, l10n),
    };
    // Wrapped rather than scrolled, so no chip hides off a narrow screen.
    return Padding(
      padding: const EdgeInsets.fromLTRB(18, 4, 18, 8),
      child: Wrap(
        spacing: 8,
        children: [
          ActionChip(
            key: const Key('festivals-year'),
            label: Text('$year ▾'),
            tooltip: l10n.pickYear,
            onPressed: () async {
              final picked = await pickYear(context, selected: year);
              if (picked != null) ref.read(festivalsYearProvider.notifier).choose(picked);
            },
          ),
          for (final filter in FestivalFilter.values)
            FilterChip(
              label: Text(label(filter)),
              selected: filter == selected,
              onSelected: (_) => ref.read(festivalFilterProvider.notifier).choose(filter),
            ),
        ],
      ),
    );
  }
}

class _Loading extends StatelessWidget {
  const _Loading();

  @override
  Widget build(BuildContext context) => Center(
    key: const Key('festivals-loading'),
    child: Column(
      mainAxisSize: MainAxisSize.min,
      spacing: 16,
      children: [
        const CircularProgressIndicator(),
        Text(
          AppLocalizations.of(context).festivalsLoading,
          style: Theme.of(context).textTheme.bodyLarge!.copyWith(color: Theme.of(context).extension<Navpad>()!.ink2),
        ),
      ],
    ),
  );
}

sealed class _Item {}

final class _MonthHeading extends _Item {
  _MonthHeading(this.date);

  final CivilDate date;
}

final class _Date extends _Item {
  _Date(this.festivals);

  final FestivalDate festivals;
}

class _FestivalList extends StatelessWidget {
  const _FestivalList({required this.dates});

  final List<FestivalDate> dates;

  @override
  Widget build(BuildContext context) {
    final items = [
      for (final (i, day) in dates.indexed) ...[
        if (i == 0 || dates[i - 1].date.month != day.date.month) _MonthHeading(day.date),
        _Date(day),
      ],
    ];
    return ListView.builder(
      key: const Key('festivals-list'),
      padding: const EdgeInsets.only(bottom: 24),
      itemCount: items.length,
      itemBuilder: (context, i) => switch (items[i]) {
        _MonthHeading(:final date) => _Heading(date: date),
        _Date(:final festivals) => _DateRow(day: festivals),
      },
    );
  }
}

class _Heading extends StatelessWidget {
  const _Heading({required this.date});

  final CivilDate date;

  @override
  Widget build(BuildContext context) {
    final month = date.month.toString().padLeft(2, '0');
    return Padding(
      key: Key('festival-month-${date.year}-$month'),
      padding: const EdgeInsets.fromLTRB(18, 24, 18, 6),
      child: Semantics(
        header: true,
        child: Text(
          monthTitle(date.year, date.month, langOf(context)),
          style: NavpadType.displayGroup.copyWith(color: Theme.of(context).extension<Navpad>()!.ink),
        ),
      ),
    );
  }
}

/// A 58 dp date column beside the date's festival lines; it opens Month on the day.
class _DateRow extends ConsumerWidget {
  const _DateRow({required this.day});

  final FestivalDate day;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final n = Theme.of(context).extension<Navpad>()!;
    final text = Theme.of(context).textTheme;
    final lang = langOf(context);
    final weekday = DateTime.utc(day.date.year, day.date.month, day.date.day).weekday % 7;
    return InkWell(
      key: Key('festival-date-${day.date.iso}'),
      onTap: () {
        ref.read(monthViewProvider.notifier).show(day.date);
        context.go('/month');
      },
      child: Container(
        padding: const EdgeInsets.fromLTRB(10, 8, 10, 8),
        decoration: BoxDecoration(
          border: Border(bottom: BorderSide(color: n.hair)),
        ),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            SizedBox(
              width: 58,
              child: Column(
                children: [
                  Text('${day.date.day}', style: NavpadType.displayGroup.copyWith(color: n.ink)),
                  Text(varaShort(weekday, lang), style: text.labelMedium!.copyWith(color: n.ink2)),
                ],
              ),
            ),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                spacing: 4,
                children: [for (final line in day.lines) _Line(line: line)],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

/// A festival line; a mahaparva is DESIGN.md's filled red row, inset with 4 dp corners.
class _Line extends StatelessWidget {
  const _Line({required this.line});

  final FestivalLine line;

  @override
  Widget build(BuildContext context) {
    final n = Theme.of(context).extension<Navpad>()!;
    final text = Theme.of(context).textTheme;
    final lang = langOf(context);
    final filled = line.kind == FestivalKind.mahaparva;
    final (ink, ink2) = filled ? (n.onRed, n.onRed2) : (n.ink, n.ink2);
    final kind = festivalKindLabel(line.kind, AppLocalizations.of(context));
    final subtitle = line.start == line.end ? kind : '$kind · ${dateRange(line.start, line.end, lang)}';
    return Container(
      key: filled ? const Key('festival-line-mahaparva') : null,
      constraints: const BoxConstraints(minHeight: 52),
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
      decoration: filled ? BoxDecoration(color: n.red, borderRadius: BorderRadius.circular(4)) : null,
      child: Row(
        children: [
          FestivalIcon(kind: line.kind, size: 22, colour: filled ? n.onRed : null),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(line.name, style: text.bodyLarge!.copyWith(color: ink)),
                Text(subtitle, style: text.labelMedium!.copyWith(color: ink2)),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
