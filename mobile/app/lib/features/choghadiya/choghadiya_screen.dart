import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:panchang_engine/panchang_engine.dart';

import '../../engine/day_reading.dart';
import '../../format/panchang_text.dart';
import '../../l10n/app_localizations.dart';
import '../../location/city_time.dart';
import '../../location/location_store.dart';
import '../../settings/settings_store.dart';
import '../../shared/date_navigator.dart';
import '../../shared/date_picker_button.dart';
import '../../shared/mark.dart';
import '../../shared/navpad_icons.dart';
import '../../shared/navpad_widgets.dart';
import '../../theme/navpad.dart';
import '../today/today_state.dart';
import '../../shared/pothi_page.dart';
import 'choghadiya_state.dart';

/// Choghadiya (mobile-ui-design.md §3 · Choghadiya): a full screen opened from
/// Today's navy band, outside the tabs. The date is Today's [selectedDateProvider].
class ChoghadiyaScreen extends ConsumerWidget {
  const ChoghadiyaScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l10n = AppLocalizations.of(context);
    final city = ref.watch(locationProvider)!;
    final date = ref.watch(selectedDateProvider);
    final now = currentTime(ref);
    final selected = ref.watch(
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
    final reading = watchChoghadiya(ref, city: city, date: date, now: now);
    return Scaffold(
      appBar: AppBar(title: Text(l10n.choghadiyaTitle), actions: const [DatePickerButton()]),
      body: PothiPage(child: SingleChildScrollView(
        padding: const EdgeInsets.only(bottom: 24),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            DateNavigator(date: date, timezone: city.timezone),
            if (selected case AsyncError(:final error))
              Note(icon: NoteIcon.alert, title: l10n.appTitle, body: '$error')
            else if (reading != null)
              _ChoghadiyaView(reading: reading, now: now, timezone: city.timezone),
          ],
        ),
      )),
    );
  }
}

String natureLabel(AppLocalizations l10n, ChoghadiyaNature nature) => switch (nature) {
  ChoghadiyaNature.auspicious => l10n.natureGood,
  ChoghadiyaNature.neutral => l10n.natureNeutral,
  ChoghadiyaNature.inauspicious => l10n.natureAvoid,
};

/// The glyph and the word, so quality never rests on colour.
String qualityText(AppLocalizations l10n, ChoghadiyaNature nature) =>
    '${natureGlyph(nature)} ${natureLabel(l10n, nature)}';

class _ChoghadiyaView extends StatelessWidget {
  const _ChoghadiyaView({required this.reading, required this.now, required this.timezone});

  final ChoghadiyaReading reading;
  final DateTime now;
  final String timezone;

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    final lang = langOf(context);
    final day = reading.day;
    final live = liveChoghadiya(day, now, following: reading.following);
    DateTime wall(DateTime utc) => roundDownToMinute(cityWall(utc, timezone));
    String range(ChoghadiyaPeriod slot) => clockRange(wall(slot.start), wall(slot.end), lang);

    Widget row(int index) {
      final slot = day.choghadiya[index];
      return _SlotRow(
        slot: slot,
        range: range(slot),
        state: switch (live?.index) {
          final current? when index == current => _SlotState.now,
          final current? when index < current => _SlotState.past,
          _ => _SlotState.plain,
        },
      );
    }

    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        if (live != null) _Hero(live: live, range: range(live.slot)),
        if (reading.beforeSunrise && reading.following != null)
          Padding(
            padding: const EdgeInsets.only(top: 12),
            child: Note(
              icon: NoteIcon.info,
              title: l10n.beforeSunriseTitle,
              body: l10n.beforeSunriseBody(clockPhrase(wall(reading.following!.sunrise), lang)),
            ),
          ),
        SectionHeading(title: l10n.dayHeading),
        for (var i = 0; i < 8; i++) row(i),
        SectionHeading(title: l10n.nightHeading),
        for (var i = 8; i < 16; i++) row(i),
        const SizedBox(height: 24),
        Note(icon: NoteIcon.info, title: l10n.choghadiyaFootnoteTitle, body: l10n.choghadiyaFootnote),
      ],
    );
  }
}

/// The navy band grown into a 120 dp header: the slot in display type, its
/// quality and range under it, a live countdown on the right and a progress bar.
class _Hero extends StatelessWidget {
  const _Hero({required this.live, required this.range});

  final LiveChoghadiya live;
  final String range;

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    final lang = langOf(context);
    final n = Theme.of(context).extension<Navpad>()!;
    final text = Theme.of(context).textTheme;
    final stacked = MediaQuery.textScalerOf(context).scale(1) >= 1.6;
    final name = choghadiyaName(live.slot.name, lang);
    final line = [
      qualityText(l10n, live.slot.name.nature),
      range,
      if (live.next case final next?) l10n.choghadiyaThen(choghadiyaName(next.name, lang)),
    ].join(' · ');
    final countdown = Text(
      countdownClock(live.remaining),
      style: NavpadType.countdown.copyWith(color: n.onNavy, fontSize: 28),
    );
    final label = Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      mainAxisSize: MainAxisSize.min,
      children: [
        Text(name, style: NavpadType.displayBand.copyWith(color: n.onNavy)),
        const SizedBox(height: 4),
        Text(line, style: text.bodyLarge!.copyWith(color: n.onNavy2)),
        if (stacked) ...[const SizedBox(height: 6), countdown],
      ],
    );
    return Semantics(
      key: const Key('choghadiya-hero'),
      container: true,
      liveRegion: true,
      label: l10n.choghadiyaHeroSemantics(name, line, durationText(live.remaining, lang)),
      child: Container(
        color: n.navy,
        constraints: const BoxConstraints(minHeight: 120),
        padding: const EdgeInsets.fromLTRB(18, 16, 18, 14),
        child: ExcludeSemantics(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Row(
                children: [
                  IconBadge(
                    background: n.onNavy.withAlpha(0x1F),
                    foreground: n.onNavy,
                    child: const NavpadIcon(NavpadGlyph.ghatika),
                  ),
                  const SizedBox(width: 12),
                  Expanded(child: label),
                  if (!stacked) ...[const SizedBox(width: 12), countdown],
                ],
              ),
              const SizedBox(height: 12),
              LinearProgressIndicator(
                value: live.progress,
                minHeight: 4,
                color: n.onNavy,
                backgroundColor: n.onNavy2.withValues(alpha: 0.3),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

enum _SlotState { plain, past, now }

/// A hairline row: quality glyph, name and quality word left, the range right.
/// The current row is filled light green, as every window running now is
/// (Navpad.nowFill); past rows are muted.
class _SlotRow extends StatelessWidget {
  const _SlotRow({required this.slot, required this.range, required this.state});

  final ChoghadiyaPeriod slot;
  final String range;
  final _SlotState state;

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    final lang = langOf(context);
    final n = Theme.of(context).extension<Navpad>()!;
    final text = Theme.of(context).textTheme;
    final (background, ink, secondary) = switch (state) {
      _SlotState.plain => (n.ground, n.ink, n.ink2),
      _SlotState.past => (n.ground, n.ink3, n.ink3),
      _SlotState.now => (n.nowFill, n.ink, n.ink2),
    };
    final nature = slot.name.nature;
    final good = nature == ChoghadiyaNature.auspicious;
    final name = choghadiyaName(slot.name, lang);
    final suffix = switch (state) {
      _SlotState.plain => '',
      _SlotState.past => ', ${l10n.slotPast}',
      _SlotState.now => ', ${l10n.slotNow}',
    };
    return Semantics(
      label: '$name ${qualityText(l10n, nature)} $range$suffix',
      excludeSemantics: true,
      child: Container(
        constraints: const BoxConstraints(minHeight: 52),
        padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 8),
        decoration: BoxDecoration(
          color: background,
          border: Border(
            left: state == _SlotState.now ? BorderSide(color: n.markGood, width: 4) : BorderSide.none,
            bottom: BorderSide(color: n.hair),
          ),
        ),
        child: Row(
          children: [
            SizedBox(
              width: 28,
              child: Text(
                natureGlyph(nature),
                textAlign: TextAlign.center,
                style: text.bodyLarge!.copyWith(
                  color: state == _SlotState.past ? ink : markColour(n, markOfNature(nature)),
                  fontWeight: FontWeight.w700,
                ),
              ),
            ),
            const SizedBox(width: 10),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    name,
                    style: text.bodyLarge!.copyWith(color: ink, fontWeight: good ? FontWeight.w700 : FontWeight.w400),
                  ),
                  Text(natureLabel(l10n, nature), style: text.labelMedium!.copyWith(color: secondary)),
                ],
              ),
            ),
            const SizedBox(width: 12),
            Flexible(
              flex: 2,
              child: Text(
                range,
                textAlign: TextAlign.end,
                style: text.bodyLarge!.copyWith(color: ink, fontWeight: FontWeight.w600),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

/// The band grows into the hero (DESIGN.md, the Grow-Into-Header Rule): the
/// page is revealed through a navy rectangle that expands from the band's
/// [Rect], passed as the route's `extra`. Instant with "Remove animations" on.
CustomTransitionPage<void> choghadiyaPage(BuildContext context, GoRouterState state) {
  final from = state.extra is Rect ? state.extra! as Rect : null;
  final duration = MediaQuery.disableAnimationsOf(context) ? Duration.zero : const Duration(milliseconds: 300);
  return CustomTransitionPage<void>(
    key: state.pageKey,
    transitionDuration: duration,
    reverseTransitionDuration: duration,
    child: const ChoghadiyaScreen(),
    transitionsBuilder: (context, animation, secondaryAnimation, child) {
      final grow = CurvedAnimation(parent: animation, curve: Curves.fastOutSlowIn);
      final reveal = CurvedAnimation(parent: animation, curve: const Interval(0.3, 1));
      final page = FadeTransition(opacity: reveal, child: child);
      if (from == null) return page;
      return AnimatedBuilder(
        animation: grow,
        child: page,
        builder: (context, page) => ClipRect(
          clipper: _GrowClipper(Rect.lerp(from, Offset.zero & MediaQuery.sizeOf(context), grow.value)!),
          child: ColoredBox(color: Theme.of(context).extension<Navpad>()!.navy, child: page),
        ),
      );
    },
  );
}

class _GrowClipper extends CustomClipper<Rect> {
  const _GrowClipper(this.rect);

  final Rect rect;

  @override
  Rect getClip(Size size) => rect;

  @override
  bool shouldReclip(_GrowClipper oldClipper) => oldClipper.rect != rect;
}
