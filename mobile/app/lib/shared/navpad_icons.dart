/// The app's own icons (DESIGN.md §Icons): small flat paintings in the
/// manuscript palette ([IconInk]) on a 24-unit grid, with a thin round-capped
/// outline in the [IconTheme] colour. Only the outline follows day and night;
/// the fills stay the same. The path data is the approved mockup's SVG
/// (`.impeccable/mocks/muhurat-icons.html`), kept verbatim so the drawings can
/// be compared with it line for line.
library;

import 'dart:math' as math;

import 'package:flutter/widgets.dart';

enum NavpadGlyph {
  sunrise,
  sunset,
  nakshatra,

  /// The choghadiya's water bowl, sinking as a ghatika passes.
  ghatika,

  /// The sun overhead on its day path: pachchakkhan.
  sunpath,

  /// Mahaparva.
  kalash,

  /// Five lights in a ring, one per kalyanak.
  kalyanak,

  /// The temple flag: parva.
  dhvaja,

  /// Vrat.
  diya,
  monthcal,
  fullPanchang,
  siddhashila,

  /// The Moon over the last five nakshatras.
  panchak,

  /// Sun and Moon joined.
  yoga,

  /// The noon Sun: Abhijit muhurta, and the Muhurat section itself.
  abhijit,

  /// The Sun under Rahu's dark disc.
  rahuKaal,

  /// Two paths crossing: the junction nakshatras.
  gandmool,

  /// The half-dark disc of the Vishti half-tithi.
  bhadra,

  /// The crescent with an arrow up.
  chandraBal,

  /// A flame in the havan kund.
  agniVaas,
}

/// The fills of the icon paintings: the same by day and by night.
abstract final class IconInk {
  static const vermilion = Color(0xFFC8432B);
  static const saffron = Color(0xFFE8902C);
  static const gold = Color(0xFFE2B33C);
  static const leaf = Color(0xFF4E8A4A);
  static const sky = Color(0xFF5B7FB8);
  static const clay = Color(0xFFB8653A);
  static const cream = Color(0xFFFFF4D6);
  static const silver = Color(0xFFE4DCC4);
  static const shade = Color(0xFF4A3350);
  static const wood = Color(0xFF8A5A34);

  static const palette = [vermilion, saffron, gold, leaf, sky, clay, cream, silver, shade, wood];
}

sealed class _Part {
  const _Part();
}

/// A line; [ink] null draws it in the outline colour, [width] null at the outline's width.
final class _Stroke extends _Part {
  const _Stroke(this.d, {this.dash, this.ink, this.width});

  final String d;
  final (double, double)? dash;
  final Color? ink;
  final double? width;
}

/// A shape filled with [ink], outlined unless [outlined] is false.
final class _Fill extends _Part {
  const _Fill(this.d, this.ink, {this.outlined = true});

  final String d;
  final Color ink;
  final bool outlined;
}

/// A disc filled with [ink] (the outline colour when null), outlined when [outlined].
final class _Dot extends _Part {
  const _Dot(this.cx, this.cy, this.r, {this.ink, this.outlined = false});

  final double cx, cy, r;
  final Color? ink;
  final bool outlined;
}

/// The outline is 1.3 grid units at the default 1.8 stroke width.
const double _outline = 1.3;

const _horizon = _Stroke('M2.5 18.5h19');
const _dayPath = _Stroke('M3.5 18.5a8.5 8.5 0 0 1 17 0', dash: (1.6, 2.6));

const _glyphs = <NavpadGlyph, List<_Part>>{
  NavpadGlyph.sunrise: [
    _Fill('M6.5 18.5a5.5 5.5 0 0 1 11 0z', IconInk.gold),
    _Stroke('M3.6 13.2l1.6.9M20.4 13.2l-1.6.9M6.2 9.6l1.2 1.3M17.8 9.6l-1.2 1.3', ink: IconInk.saffron, width: 1.6),
    _Stroke('M12 8V3M9.6 5.4 12 3l2.4 2.4', ink: IconInk.leaf, width: 1.6),
    _Stroke('M2.5 18.5h19M6.5 18.5a5.5 5.5 0 0 1 11 0M8 21.5h8'),
  ],
  NavpadGlyph.sunset: [
    _Fill('M6.5 18.5a5.5 5.5 0 0 1 11 0z', IconInk.saffron),
    _Stroke(
      'M3.6 13.2l1.6.9M20.4 13.2l-1.6.9M6.2 9.6l1.2 1.3M17.8 9.6l-1.2 1.3M12 3v5M9.6 5.6 12 8l2.4-2.4',
      ink: IconInk.vermilion,
      width: 1.6,
    ),
    _Stroke('M2.5 18.5h19M6.5 18.5a5.5 5.5 0 0 1 11 0M8 21.5h8'),
  ],
  NavpadGlyph.nakshatra: [
    _Fill('M11 3.5l1.7 4.6 4.6 1.7-4.6 1.7L11 16.1l-1.7-4.6-4.6-1.7 4.6-1.7z', IconInk.gold),
    _Dot(18.5, 17.5, 1.5, ink: IconInk.saffron),
    _Dot(5, 19.5, 1.2, ink: IconInk.gold),
    _Dot(19.5, 4.5, 1.1, ink: IconInk.gold),
  ],
  NavpadGlyph.ghatika: [
    _Fill('M2 18.6c1.6-1 3.2-1 4.8 0s3.2 1 4.8 0 3.2-1 4.8 0 3.2 1 5.6 0V22H2z', IconInk.sky, outlined: false),
    _Fill('M4.5 9.5h15a7.5 6 0 0 1-15 0z', IconInk.clay),
    _Stroke('M7 11.2h10', ink: IconInk.cream),
    _Stroke('M12 4.5v2.2M9.4 5.4l.9 1.4M14.6 5.4l-.9 1.4', ink: IconInk.sky, width: 1.6),
  ],
  NavpadGlyph.sunpath: [
    _Fill('M2 18.5h20V21H2z', IconInk.leaf, outlined: false),
    _dayPath,
    _Dot(12, 10, 2.8, ink: IconInk.gold, outlined: true),
    _horizon,
  ],
  NavpadGlyph.kalash: [
    _Fill('M10 8.6 6.4 6.2c1.2-.6 2.6-.2 3.6 2.4zM14 8.6l3.6-2.4c-1.2-.6-2.6-.2-3.6 2.4z', IconInk.leaf),
    _Dot(12, 5.8, 2.3, ink: IconInk.wood, outlined: true),
    _Fill('M8 11.5c-2.4 2-2.4 6.4.2 9h7.6c2.6-2.6 2.6-7 .2-9z', IconInk.clay),
    _Fill('M9.3 11.5V9.3h5.4v2.2zM6.5 11.5h11v1.2h-11z', IconInk.gold),
    _Stroke('M8.2 15.5h7.6', ink: IconInk.vermilion, width: 1.6),
  ],
  NavpadGlyph.kalyanak: [
    _Dot(12, 12, 8.2, ink: IconInk.cream, outlined: true),
    _Fill(
      'M12 4.6c-1 1.2-1.2 2.2 0 3.6 1.2-1.4 1-2.4 0-3.6zM17.1 8.3c-1 1.2-1.2 2.2 0 3.6 1.2-1.4 1-2.4 0-3.6z'
      'M15.2 14.4c-1 1.2-1.2 2.2 0 3.6 1.2-1.4 1-2.4 0-3.6zM8.8 14.4c-1 1.2-1.2 2.2 0 3.6 1.2-1.4 1-2.4 0-3.6z'
      'M6.9 8.3c-1 1.2-1.2 2.2 0 3.6 1.2-1.4 1-2.4 0-3.6z',
      IconInk.saffron,
      outlined: false,
    ),
    _Dot(12, 12, 1.4, ink: IconInk.vermilion),
  ],
  NavpadGlyph.dhvaja: [
    _Fill('M6 4h12l-3.2 4.2L18 12.4H6z', IconInk.vermilion),
    _Stroke('M8.5 8.2h4', ink: IconInk.gold, width: 1.4),
    _Stroke('M6 21.5V2.8', ink: IconInk.wood, width: 2),
    _Dot(6, 2.6, 1.3, ink: IconInk.gold),
  ],
  NavpadGlyph.diya: [
    _Fill('M12 3.8c-2.2 2.6-2.2 5.3 0 7.4 2.2-2.1 2.2-4.8 0-7.4z', IconInk.saffron),
    _Fill('M12 6.8c-.9 1.2-.9 2.4 0 3.3.9-.9.9-2.1 0-3.3z', IconInk.gold, outlined: false),
    _Fill('M3.5 14h17c-1 3.8-4.4 5.5-8.5 5.5S4.5 17.8 3.5 14z', IconInk.clay),
    _Stroke('M18 14l2.5-2'),
    _Stroke('M7 16.2h10', ink: IconInk.cream),
  ],
  NavpadGlyph.monthcal: [
    _Fill(
      'M5.5 5h13A2.5 2.5 0 0 1 21 7.5v11a2.5 2.5 0 0 1-2.5 2.5h-13A2.5 2.5 0 0 1 3 18.5v-11A2.5 2.5 0 0 1 5.5 5z',
      IconInk.cream,
    ),
    _Fill('M3 9.5V7.5A2.5 2.5 0 0 1 5.5 5h13A2.5 2.5 0 0 1 21 7.5v2z', IconInk.vermilion),
    _Stroke('M8 3v4M16 3v4'),
    _Fill('M13.8 12.6a3.4 3.4 0 1 0 1.6 5.6 3 3 0 0 1-1.6-5.6z', IconInk.gold),
  ],
  NavpadGlyph.fullPanchang: [
    _Fill('M2.5 6.5v12.5c3.5-1 6.5-.6 9.5 1.5 3-2.1 6-2.5 9.5-1.5V6.5', IconInk.vermilion),
    _Fill(
      'M12 6.5c-2.6-1.8-5.6-2.2-8.5-1.4v12.6c2.9-.8 5.9-.4 8.5 1.4 2.6-1.8 5.6-2.2 8.5-1.4V5.1c-2.9-.8-5.9-.4-8.5 1.4zM12 6.5v12.6',
      IconInk.cream,
    ),
    _Stroke('M6 9.5h3.5M6 12.5h3.5M14.5 9.5H18M14.5 12.5H18', ink: IconInk.saffron),
  ],
  NavpadGlyph.siddhashila: [
    _Fill('M3.5 12.5c2.2 3.4 5.2 5 8.5 5s6.3-1.6 8.5-5c-2.6 1.6-5.4 2.4-8.5 2.4S6.1 14.1 3.5 12.5z', IconInk.gold),
    _Dot(12, 7.5, 2.3, ink: IconInk.vermilion, outlined: true),
  ],
  NavpadGlyph.panchak: [
    _Fill('M13 3.8a6.5 6.5 0 1 0 5.6 9.4A5.2 5.2 0 0 1 13 3.8z', IconInk.silver),
    _Dot(4, 20.3, 1.4, ink: IconInk.gold),
    _Dot(8, 20.3, 1.4, ink: IconInk.saffron),
    _Dot(12, 20.3, 1.4, ink: IconInk.vermilion),
    _Dot(16, 20.3, 1.4, ink: IconInk.saffron),
    _Dot(20, 20.3, 1.4, ink: IconInk.gold),
  ],
  NavpadGlyph.yoga: [
    _Dot(8.8, 12, 5.6, ink: IconInk.gold, outlined: true),
    _Dot(15.2, 12, 5.6, ink: IconInk.silver, outlined: true),
    _Fill('M12 7.3a5.6 5.6 0 0 1 0 9.4 5.6 5.6 0 0 1 0-9.4z', IconInk.saffron, outlined: false),
    _Stroke('M14.4 12a5.6 5.6 0 1 1-11.2 0 5.6 5.6 0 1 1 11.2 0z'),
  ],
  NavpadGlyph.abhijit: [
    _Fill('M2 18.5h20V21H2z', IconInk.leaf, outlined: false),
    _Stroke('M12 2v1.4M6.6 4.4l1 1M17.4 4.4l-1 1M4.2 9h1.4M18.4 9h1.4', ink: IconInk.saffron, width: 1.6),
    _Stroke('M12 12.8v5.7', ink: IconInk.saffron, dash: (1.4, 1.8)),
    _Dot(12, 8.6, 3.2, ink: IconInk.gold, outlined: true),
    _horizon,
  ],
  NavpadGlyph.rahuKaal: [
    _Dot(12, 12, 8.6, ink: IconInk.gold),
    _Stroke(
      'M12 1.8v1.6M12 20.6v1.6M1.8 12h1.6M20.6 12h1.6M4.8 4.8l1.1 1.1M18.1 18.1l1.1 1.1M4.8 19.2l1.1-1.1M18.1 5.9l1.1-1.1',
      ink: IconInk.saffron,
      width: 1.4,
    ),
    _Dot(13, 11, 6.6, ink: IconInk.shade, outlined: true),
  ],
  NavpadGlyph.gandmool: [
    _Stroke('M4 6c6.5 0 9.5 12 16 12', ink: IconInk.vermilion, width: 2),
    _Stroke('M4 18c6.5 0 9.5-12 16-12', ink: IconInk.sky, width: 2),
    _Dot(12, 12, 2.4, ink: IconInk.gold, outlined: true),
  ],
  NavpadGlyph.bhadra: [
    _Dot(12, 12, 7.8, ink: IconInk.cream, outlined: true),
    _Fill('M12 4.2a7.8 7.8 0 0 0 0 15.6z', IconInk.shade),
    _Stroke('M12 2.2v19.6', ink: IconInk.vermilion, width: 1.8),
  ],
  NavpadGlyph.chandraBal: [
    _Fill('M11 6.6a6.5 6.5 0 1 0 5.6 9.8 5.2 5.2 0 0 1-5.6-9.8z', IconInk.silver),
    _Stroke('M18.5 11V3.5M16 6l2.5-2.5L21 6', ink: IconInk.leaf, width: 2),
  ],
  NavpadGlyph.agniVaas: [
    _Fill('M12 3.2c-3.2 3.1-4.2 5.8-2.6 8.7.6 1.1 1.6 1.7 2.6 1.7s2-.6 2.6-1.7c1.6-2.9.6-5.6-2.6-8.7z', IconInk.vermilion),
    _Fill('M12 7.6c-1.4 1.5-1.8 2.8-1 4.2.3.5.6.8 1 .8s.7-.3 1-.8c.8-1.4.4-2.7-1-4.2z', IconInk.gold, outlined: false),
    _Fill('M4 15.5h16l-2 5H6z', IconInk.clay),
    _Stroke('M7 18h10', ink: IconInk.cream),
  ],
};

/// One of the app's own icons. Silent to a screen reader unless [semanticLabel]
/// is given, since the words beside it say the same thing.
class NavpadIcon extends StatelessWidget {
  const NavpadIcon(
    this.glyph, {
    super.key,
    this.size,
    this.color,
    this.strokeWidth = 1.8,
    this.semanticLabel,
  });

  final NavpadGlyph glyph;
  final double? size;
  final Color? color;

  /// In grid units, so it scales with [size]; the Month grid's 13 dp marks use 2.2.
  final double strokeWidth;
  final String? semanticLabel;

  @override
  Widget build(BuildContext context) => _GlyphBox(
    parts: _glyphs[glyph]!,
    size: size,
    color: color,
    strokeWidth: strokeWidth,
    label: semanticLabel,
  );
}

/// The pachchakkhan icon with the sun where it stands at [fraction] of the day:
/// 0 at sunrise on the left, ½ overhead, 1 at sunset on the right.
class SunPathIcon extends StatelessWidget {
  const SunPathIcon({super.key, required this.fraction, this.size, this.color});

  final double fraction;
  final double? size;
  final Color? color;

  @override
  Widget build(BuildContext context) {
    final angle = math.pi * (1 - fraction.clamp(0, 1));
    return _GlyphBox(
      parts: [
        ..._glyphs[NavpadGlyph.sunpath]!.take(2),
        _Dot(12 + 8.5 * math.cos(angle), 18.5 - 8.5 * math.sin(angle), 2.8, ink: IconInk.gold, outlined: true),
        _horizon,
      ],
      size: size,
      color: color,
      strokeWidth: 1.8,
      label: null,
    );
  }
}

class _GlyphBox extends StatelessWidget {
  const _GlyphBox({
    required this.parts,
    required this.size,
    required this.color,
    required this.strokeWidth,
    required this.label,
  });

  final List<_Part> parts;
  final double? size;
  final Color? color;
  final double strokeWidth;
  final String? label;

  @override
  Widget build(BuildContext context) {
    final theme = IconTheme.of(context);
    final side = size ?? theme.size ?? 24;
    final painted = CustomPaint(
      size: Size.square(side),
      painter: _GlyphPainter(
        parts,
        color ?? theme.color ?? const Color(0xFF000000),
        strokeWidth,
      ),
    );
    return label == null
        ? ExcludeSemantics(child: painted)
        : Semantics(
            container: true,
            label: label,
            image: true,
            excludeSemantics: true,
            child: painted,
          );
  }
}

class _GlyphPainter extends CustomPainter {
  _GlyphPainter(this.parts, this.color, this.strokeWidth);

  final List<_Part> parts;
  final Color color;
  final double strokeWidth;

  @override
  void paint(Canvas canvas, Size size) {
    canvas.scale(size.width / 24);
    // Widths in the table are for the default 1.8; a heavier icon thickens every line.
    final scale = strokeWidth / 1.8;
    Paint line(Color? ink, double? width) => Paint()
      ..color = ink ?? color
      ..style = PaintingStyle.stroke
      ..strokeWidth = (width ?? _outline) * scale
      ..strokeCap = StrokeCap.round
      ..strokeJoin = StrokeJoin.round;
    Paint solid(Color? ink) => Paint()..color = ink ?? color;
    final outline = line(null, null);
    for (final part in parts) {
      switch (part) {
        case _Stroke(:final d, dash: null, :final ink, :final width):
          canvas.drawPath(svgPath(d), line(ink, width));
        case _Stroke(:final d, dash: (final on, final off), :final ink, :final width):
          canvas.drawPath(_dashed(svgPath(d), on, off), line(ink, width));
        case _Fill(:final d, :final ink, :final outlined):
          final path = svgPath(d);
          canvas.drawPath(path, solid(ink));
          if (outlined) canvas.drawPath(path, outline);
        case _Dot(:final cx, :final cy, :final r, :final ink, :final outlined):
          canvas.drawCircle(Offset(cx, cy), r, solid(ink));
          if (outlined) canvas.drawCircle(Offset(cx, cy), r, outline);
      }
    }
  }

  @override
  bool shouldRepaint(_GlyphPainter old) =>
      old.parts != parts ||
      old.color != color ||
      old.strokeWidth != strokeWidth;
}

Path _dashed(Path source, double on, double off) {
  final dashes = Path();
  for (final metric in source.computeMetrics()) {
    for (var start = 0.0; start < metric.length; start += on + off) {
      dashes.addPath(metric.extractPath(start, start + on), Offset.zero);
    }
  }
  return dashes;
}

final _token = RegExp(
  r'[MmLlHhVvAaCcSsZz]|[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?',
);

/// SVG path data as a [Path]: the commands the icon set uses (M L H V A C S Z,
/// absolute and relative, with implicit repeats).
Path svgPath(String d) {
  final tokens = _token.allMatches(d).map((m) => m.group(0)!).toList();
  final path = Path();
  var i = 0;
  var command = 'M';
  var current = Offset.zero, start = Offset.zero, lastControl = Offset.zero;
  bool isCommand(String t) => RegExp('[A-Za-z]').hasMatch(t);
  double next() => double.parse(tokens[i++]);

  while (i < tokens.length) {
    if (isCommand(tokens[i])) command = tokens[i++];
    final relative = command == command.toLowerCase();
    final base = relative ? current : Offset.zero;
    Offset point() {
      final x = next();
      return base + Offset(x, next());
    }

    switch (command.toUpperCase()) {
      case 'M':
        current = start = point();
        path.moveTo(current.dx, current.dy);
        // Pairs after a moveto are linetos.
        command = relative ? 'l' : 'L';
      case 'L':
        current = point();
        path.lineTo(current.dx, current.dy);
      case 'H':
        current = Offset(next() + (relative ? current.dx : 0), current.dy);
        path.lineTo(current.dx, current.dy);
      case 'V':
        current = Offset(current.dx, next() + (relative ? current.dy : 0));
        path.lineTo(current.dx, current.dy);
      case 'C':
        final c1 = point(), c2 = point(), end = point();
        path.cubicTo(c1.dx, c1.dy, c2.dx, c2.dy, end.dx, end.dy);
        (lastControl, current) = (c2, end);
      case 'S':
        final c1 = current * 2 - lastControl;
        final c2 = point(), end = point();
        path.cubicTo(c1.dx, c1.dy, c2.dx, c2.dy, end.dx, end.dy);
        (lastControl, current) = (c2, end);
      case 'A':
        final rx = next(),
            ry = next(),
            rotation = next(),
            large = next() != 0,
            sweep = next() != 0;
        current = point();
        path.arcToPoint(
          current,
          radius: Radius.elliptical(rx, ry),
          rotation: rotation,
          largeArc: large,
          clockwise: sweep,
        );
      case 'Z':
        path.close();
        current = start;
    }
    if (!'CcSs'.contains(command)) lastControl = current;
  }
  return path;
}
