/// The day as a picture for WhatsApp (mobile-ui-design.md §3.6, DESIGN.md
/// Display brand): the card's words, the card, and its PNG.
library;

import 'dart:typed_data';
import 'dart:ui' as ui;

import 'package:flutter/material.dart';
import 'package:flutter/rendering.dart';
import 'package:panchang_engine/panchang_engine.dart';

import '../../format/festival_text.dart';
import '../../format/panchang_text.dart';
import '../../l10n/app_localizations.dart';
import '../../location/city_time.dart';
import '../../shared/festival_mark.dart';
import '../../theme/navpad.dart';
import '../../theme/theme.dart';

/// The greeting stays in Devanagari on an English card too: it is the greeting itself.
const greeting = 'जय जिनेन्द्र';

typedef CardStrip = ({String title, String subtitle});

/// Everything the card and its text say, already in the app's language.
final class ShareCardContent {
  const ShareCardContent({
    required this.lang,
    required this.date,
    required this.tithi,
    required this.month,
    required this.tithiEnds,
    required this.samvat,
    required this.parva,
    required this.vrat,
    required this.sunriseLabel,
    required this.sunrise,
    required this.sunsetLabel,
    required this.sunset,
    required this.place,
    required this.appName,
  });

  final Lang lang;
  final String date, tithi, month, tithiEnds, samvat, place, appName;
  final CardStrip? parva, vrat;
  final String sunriseLabel, sunsetLabel;
  final ({String period, String time}) sunrise, sunset;
}

ShareCardContent shareCardContent({
  required PanchangDay reading,
  required LunarMonth month,
  required List<FestivalOccurrence> festivals,
  required String place,
  required String timezone,
  required AppLocalizations l10n,
}) {
  final lang = l10n.localeName == 'en' ? Lang.en : Lang.hi;
  DateTime wall(DateTime utc) => cityWall(utc, timezone);
  final lines = festivalLines(festivalsOn(festivals, reading.date), lang);
  // As Today's bands say it: the first name, then its kind or how many more.
  CardStrip? strip(List<FestivalLine> shown) => switch (shown) {
    [] => null,
    [final first, ...final rest] => (
      title: first.name,
      subtitle: rest.isEmpty ? festivalKindLabel(first.kind, l10n) : l10n.festivalsMore(rest.length),
    ),
  };
  final ends = instantPhrase(wall(reading.jainTithi.endsAt), day: reading.date, lang: lang);
  return ShareCardContent(
    lang: lang,
    date: longDate(reading.date, lang),
    tithi: tithiName(reading.jainTithi.index, lang),
    month: monthName(month, lang),
    tithiEnds: l10n.heroUntil(ends, tithiName(reading.jainTithi.index % 30 + 1, lang)),
    samvat: samvatLine(viraNirvana: reading.viraNirvanaSamvat, vikram: reading.vikramSamvat, lang: lang),
    parva: strip([
      for (final l in lines)
        if (!l.kind.isVrat) l,
    ]),
    vrat: strip([
      for (final l in lines)
        if (l.kind.isVrat) l,
    ]),
    sunriseLabel: l10n.sunrise,
    sunrise: clockTime(wall(reading.sunrise), lang),
    sunsetLabel: l10n.sunset,
    sunset: clockTime(wall(reading.sunset), lang),
    place: place,
    appName: l10n.appTitle,
  );
}

String _clock(({String period, String time}) clock, Lang lang) =>
    lang == Lang.hi ? '${clock.period} ${clock.time}' : '${clock.time} ${clock.period}';

/// The plain-text version WhatsApp shows as the image's caption.
String shareText(ShareCardContent c) => [
  greeting,
  '${c.date} · ${c.place}',
  '${c.tithi} · ${c.month}',
  c.samvat,
  for (final strip in [c.parva, c.vrat])
    if (strip != null) '${strip.title} · ${strip.subtitle}',
  '${c.sunriseLabel} ${_clock(c.sunrise, c.lang)} · ${c.sunsetLabel} ${_clock(c.sunset, c.lang)}',
  '— ${c.appName}',
].join('\n');

/// 360 dp wide and at least 450 tall: 1080 × 1350 px at [_pixelRatio], taller on a busy day.
const _width = 360.0, _minHeight = 450.0, _pixelRatio = 3.0;

/// The card in the light scheme whatever the phone's theme, at a fixed text
/// size: it is a picture for someone else's phone.
class ShareCard extends StatelessWidget {
  const ShareCard({super.key, required this.content});

  final ShareCardContent content;

  @override
  Widget build(BuildContext context) {
    final theme = navpadTheme(Brightness.light);
    final n = theme.extension<Navpad>()!;
    final text = theme.textTheme;
    final c = content;
    return Directionality(
      textDirection: TextDirection.ltr,
      child: MediaQuery(
        data: const MediaQueryData(textScaler: TextScaler.noScaling),
        child: Theme(
          data: theme,
          child: ColoredBox(
            key: const Key('share-card'),
            color: n.ground,
            child: ConstrainedBox(
              constraints: const BoxConstraints(minWidth: _width, maxWidth: _width, minHeight: _minHeight),
              child: IntrinsicHeight(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    Padding(
                      padding: const EdgeInsets.fromLTRB(18, 22, 18, 0),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          CustomPaint(size: const Size(28, 22), painter: _Siddhashila(n.ink)),
                          const SizedBox(height: 4),
                          Text(greeting, style: NavpadType.displayBrand.copyWith(color: n.ink)),
                          Text(c.date, style: text.bodyLarge!.copyWith(color: n.ink2)),
                          const SizedBox(height: 14),
                          Text(c.tithi, style: NavpadType.displayHero.copyWith(color: n.ink)),
                          const SizedBox(height: 4),
                          Text.rich(
                            TextSpan(
                              style: text.bodyLarge!.copyWith(color: n.ink2, height: 1.4),
                              children: [
                                TextSpan(
                                  text: c.month,
                                  style: TextStyle(color: n.ink, fontWeight: FontWeight.w600),
                                ),
                                TextSpan(text: ' · ${c.tithiEnds}\n${c.samvat}'),
                              ],
                            ),
                          ),
                        ],
                      ),
                    ),
                    if (c.parva case final strip?)
                      _Strip(
                        key: const Key('share-strip-parva'),
                        strip: strip,
                        colours: (n.red, n.onRed, n.onRed2),
                        top: 14,
                      ),
                    if (c.vrat case final strip?)
                      _Strip(
                        key: const Key('share-strip-vrat'),
                        strip: strip,
                        colours: (n.green, n.onGreen, n.onGreen2),
                        top: c.parva == null ? 14 : 2,
                      ),
                    const Spacer(),
                    const SizedBox(height: 14),
                    Divider(height: 1, thickness: 1, color: n.hair),
                    _SunRow(label: c.sunriseLabel, clock: c.sunrise, lang: c.lang),
                    _SunRow(label: c.sunsetLabel, clock: c.sunset, lang: c.lang),
                    Padding(
                      padding: const EdgeInsets.fromLTRB(18, 10, 18, 14),
                      child: Row(
                        children: [
                          Expanded(
                            child: Text(c.place, style: text.labelMedium!.copyWith(color: n.ink3)),
                          ),
                          Text(c.appName, style: text.labelMedium!.copyWith(color: n.ink3)),
                        ],
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }
}

/// A festival strip: DESIGN.md's band without the chevron, since a picture has nothing to tap.
class _Strip extends StatelessWidget {
  const _Strip({super.key, required this.strip, required this.colours, required this.top});

  final CardStrip strip;
  final (Color, Color, Color) colours;
  final double top;

  @override
  Widget build(BuildContext context) {
    final (background, foreground, secondary) = colours;
    return Container(
      margin: EdgeInsets.only(top: top),
      color: background,
      padding: const EdgeInsets.fromLTRB(18, 9, 12, 9),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            strip.title,
            maxLines: 2,
            overflow: TextOverflow.ellipsis,
            style: NavpadType.titleBand.copyWith(color: foreground),
          ),
          Text(strip.subtitle, style: Theme.of(context).textTheme.labelMedium!.copyWith(color: secondary)),
        ],
      ),
    );
  }
}

class _SunRow extends StatelessWidget {
  const _SunRow({required this.label, required this.clock, required this.lang});

  final String label;
  final ({String period, String time}) clock;
  final Lang lang;

  @override
  Widget build(BuildContext context) {
    final n = Theme.of(context).extension<Navpad>()!;
    final text = Theme.of(context).textTheme;
    final period = TextSpan(
      text: clock.period,
      style: TextStyle(color: n.ink2, fontWeight: FontWeight.w400),
    );
    final time = TextSpan(
      text: clock.time,
      style: const TextStyle(fontWeight: FontWeight.w600),
    );
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 8),
      decoration: BoxDecoration(
        border: Border(bottom: BorderSide(color: n.hair)),
      ),
      child: Row(
        children: [
          Expanded(
            child: Text(label, style: text.bodyLarge!.copyWith(color: n.ink)),
          ),
          // DESIGN.md's Time Column Rule: the period word lighter, before the value in Hindi.
          Text.rich(
            TextSpan(
              style: text.bodyLarge!.copyWith(color: n.ink),
              children: lang == Lang.hi
                  ? [period, const TextSpan(text: ' '), time]
                  : [time, const TextSpan(text: ' '), period],
            ),
          ),
        ],
      ),
    );
  }
}

/// The siddhashila mark: the crescent of the abode of the liberated, with a soul above it.
class _Siddhashila extends CustomPainter {
  const _Siddhashila(this.colour);

  final Color colour;

  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()..color = colour;
    canvas.drawCircle(Offset(size.width / 2, size.height * 0.23), size.width * 0.115, paint);
    final crescent = Path()
      ..moveTo(size.width * 0.1, size.height * 0.45)
      ..quadraticBezierTo(size.width / 2, size.height * 1.1, size.width * 0.9, size.height * 0.45);
    canvas.drawPath(
      crescent,
      paint
        ..style = PaintingStyle.stroke
        ..strokeWidth = 2.4
        ..strokeCap = StrokeCap.round,
    );
  }

  @override
  bool shouldRepaint(_Siddhashila old) => old.colour != colour;
}

/// Paints the card away from the screen, in its own pipeline, and encodes it as a PNG.
Future<Uint8List> renderShareCard(ShareCardContent content, {required ui.FlutterView view}) async {
  final boundary = RenderRepaintBoundary();
  final renderView = RenderView(
    view: view,
    child: RenderPositionedBox(alignment: Alignment.topLeft, child: boundary),
    configuration: const ViewConfiguration(
      logicalConstraints: BoxConstraints(maxWidth: _width, maxHeight: _minHeight * 3),
    ),
  );
  final pipeline = PipelineOwner()..rootNode = renderView;
  renderView.prepareInitialFrame();
  final build = BuildOwner(focusManager: FocusManager());
  final root = RenderObjectToWidgetAdapter<RenderBox>(
    container: boundary,
    child: ShareCard(content: content),
  ).attachToRenderTree(build);
  build
    ..buildScope(root)
    ..finalizeTree();
  pipeline
    ..flushLayout()
    ..flushCompositingBits()
    ..flushPaint();
  final image = await boundary.toImage(pixelRatio: _pixelRatio);
  try {
    final bytes = await image.toByteData(format: ui.ImageByteFormat.png);
    return bytes!.buffer.asUint8List();
  } finally {
    image.dispose();
  }
}
