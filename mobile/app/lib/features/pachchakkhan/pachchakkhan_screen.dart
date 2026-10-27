import 'package:panchang_engine/panchang_engine.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../engine/day_reading.dart';
import '../../format/panchang_text.dart';
import '../../l10n/app_localizations.dart';
import '../../l10n/city_name.dart';
import '../../location/city_time.dart';
import '../../location/location_store.dart';
import '../../shared/date_navigator.dart';
import '../../shared/navpad_widgets.dart';
import '../../shared/pachchakkhan_row.dart';
import '../../theme/navpad.dart';
import '../today/today_state.dart';

/// Pachchakkhan (mobile-ui-design.md §3 · Pachchakkhan). The date is Today's:
/// both tabs read [selectedDateProvider]. After Avaddh the hero counts down to
/// sunset for the evening pachchakkhans; after sunset it is a quiet ink row.
class PachchakkhanScreen extends ConsumerWidget {
  const PachchakkhanScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l10n = AppLocalizations.of(context);
    final city = ref.watch(locationProvider)!;
    final date = ref.watch(selectedDateProvider);
    final reading = ref.watch(
      dayReadingProvider(DayRequest(date: date, lat: city.lat, lon: city.lon, timezone: city.timezone)),
    );
    return Scaffold(
      appBar: AppBar(title: Text(l10n.tabPachchakkhan)),
      body: SingleChildScrollView(
        padding: const EdgeInsets.only(bottom: 24),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            DateNavigator(date: date, timezone: city.timezone),
            ...switch (reading) {
              AsyncData(:final value) => [
                _PachchakkhanView(reading: value, cityName: city.nameFor(context), timezone: city.timezone),
              ],
              AsyncError(:final error) => [Note(icon: NoteIcon.alert, title: l10n.appTitle, body: '$error')],
              _ => const <Widget>[],
            },
          ],
        ),
      ),
    );
  }
}

const _fractions = {
  TimedPachchakkhan.porsi: '¼',
  TimedPachchakkhan.sadhPorsi: '⅜',
  TimedPachchakkhan.purimaddh: '½',
  TimedPachchakkhan.avaddh: '¾',
};

class _PachchakkhanView extends ConsumerWidget {
  const _PachchakkhanView({required this.reading, required this.cityName, required this.timezone});

  final PanchangDay reading;
  final String cityName, timezone;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l10n = AppLocalizations.of(context);
    final lang = langOf(context);
    final n = Theme.of(context).extension<Navpad>()!;
    final text = Theme.of(context).textTheme;
    final now = currentTime(ref);
    final phase = reading.date == todayIn(timezone, now) ? reading.pachchakkhan.phaseAt(now) : null;
    DateTime wall(DateTime utc) => cityWall(utc, timezone);
    String completionTime(DateTime utc) => clockTime(roundUpToMinute(wall(utc)), lang).time;
    final eveningTime = clockTime(roundDownToMinute(wall(reading.pachchakkhan.evening)), lang).time;

    RowState? stateOf(DateTime at, {required bool isNext}) => switch (phase) {
      null => null,
      _ when !at.isAfter(now) => RowState.done,
      _ => isNext ? RowState.next : RowState.plain,
    };

    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Padding(
          padding: const EdgeInsets.fromLTRB(18, 0, 18, 12),
          child: Text(
            l10n.pachchakkhanHeader(
              cityName,
              clockPhrase(wall(reading.sunrise), lang),
              clockPhrase(wall(reading.sunset), lang),
            ),
            textAlign: TextAlign.center,
            style: text.bodyMedium!.copyWith(color: n.ink2),
          ),
        ),
        ...switch (phase) {
          NextCompletion(:final kind, :final at) => [
            _Hero(
              name: pachchakkhanName(kind, lang),
              line: l10n.pachchakkhanHeroNext(completionTime(at)),
              remaining: at.difference(now),
            ),
          ],
          EveningDeadline(:final at) => [
            _Hero(
              name: l10n.chauvihar,
              line: l10n.pachchakkhanHeroEvening(clockPhrase(roundDownToMinute(wall(at)), lang)),
              remaining: at.difference(now),
            ),
          ],
          AllDone(:final parana) => [
            Padding(
              key: const Key('pachchakkhan-all-done'),
              padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 14),
              child: Text(
                l10n.pachchakkhanAllDone(clockPhrase(roundUpToMinute(wall(parana)), lang)),
                style: text.bodyLarge!.copyWith(color: n.ink),
              ),
            ),
          ],
          null => const <Widget>[],
        },
        SectionHeading(title: l10n.completionHeading),
        Padding(
          padding: const EdgeInsets.fromLTRB(18, 0, 18, 8),
          child: Text(l10n.completionNote, style: text.bodyMedium!.copyWith(color: n.ink2)),
        ),
        const ListTop(),
        for (final p in reading.pachchakkhan.completions)
          pachchakkhanRow(
            l10n: l10n,
            name: pachchakkhanName(p.kind, lang),
            subtitle: switch (_fractions[p.kind]) {
              final fraction? => l10n.ruleFraction(fraction),
              null => l10n.ruleNavkarsi,
            },
            time: completionTime(p.at),
            state: stateOf(p.at, isNext: phase is NextCompletion && phase.kind == p.kind),
          ),
        SectionHeading(title: l10n.eveningHeading),
        const ListTop(),
        pachchakkhanRow(
          l10n: l10n,
          name: l10n.eveningNames,
          time: eveningTime,
          state: stateOf(reading.pachchakkhan.evening, isNext: phase is EveningDeadline),
        ),
        SectionHeading(title: l10n.otherHeading),
        const ListTop(),
        TimeRow(name: l10n.mutthiSahiyam, subtitle: l10n.noFixedTime, time: ''),
        TimeRow(name: l10n.ekasanuBiyasanu, subtitle: l10n.withATimeAbove, time: ''),
        TimeRow(
          name: l10n.ayambilUpvas,
          subtitle: l10n.paranaNextNavkarsi,
          time: instantPhrase(roundUpToMinute(wall(reading.pachchakkhan.parana)), day: reading.date, lang: lang),
        ),
      ],
    );
  }
}

/// The yellow band grown into a 132 dp header: the name in display type, a
/// line under it and a live countdown on the right.
class _Hero extends StatelessWidget {
  const _Hero({required this.name, required this.line, required this.remaining});

  final String name, line;
  final Duration remaining;

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    final n = Theme.of(context).extension<Navpad>()!;
    final text = Theme.of(context).textTheme;
    final stacked = MediaQuery.textScalerOf(context).scale(1) >= 1.6;
    final countdown = Text(countdownClock(remaining), style: NavpadType.countdown.copyWith(color: n.onYellow));
    final label = Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      mainAxisSize: MainAxisSize.min,
      children: [
        Text(name, style: NavpadType.displayBand.copyWith(color: n.onYellow)),
        const SizedBox(height: 4),
        Text(line, style: text.bodyLarge!.copyWith(color: n.onYellow2)),
        if (stacked) ...[const SizedBox(height: 6), countdown],
      ],
    );
    return Semantics(
      key: const Key('pachchakkhan-hero'),
      container: true,
      label: l10n.pachchakkhanHeroSemantics(name, line, durationText(remaining, langOf(context))),
      child: Container(
        color: n.yellow,
        constraints: const BoxConstraints(minHeight: 132),
        padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 16),
        child: ExcludeSemantics(
          child: Row(
            children: [
              Expanded(child: label),
              if (!stacked) ...[const SizedBox(width: 12), countdown],
            ],
          ),
        ),
      ),
    );
  }
}
