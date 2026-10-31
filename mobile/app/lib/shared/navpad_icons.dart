/// The app's own line icons (DESIGN.md §Shapes): 24 dp on a 24-unit grid,
/// 1.8 stroke, round caps and joins, coloured and sized by [IconTheme]. The
/// path data is the approved mockup's SVG, kept verbatim so the drawings can be
/// compared with it line for line.
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
  siddhashila,
}

sealed class _Part {
  const _Part();
}

final class _Stroke extends _Part {
  const _Stroke(this.d, {this.dash});

  final String d;
  final (double, double)? dash;
}

final class _Dot extends _Part {
  const _Dot(this.cx, this.cy, this.r, {this.filled = true});

  final double cx, cy, r;
  final bool filled;
}

final class _Box extends _Part {
  const _Box(this.x, this.y, this.width, this.height, this.radius);

  final double x, y, width, height, radius;
}

const _horizon = _Stroke('M2.5 18.5h19');
const _dayPath = _Stroke('M3.5 18.5a8.5 8.5 0 0 1 17 0', dash: (1.6, 2.6));

const _glyphs = <NavpadGlyph, List<_Part>>{
  NavpadGlyph.sunrise: [
    _Stroke(
      'M2.5 18.5h19M6.5 18.5a5.5 5.5 0 0 1 11 0M12 3v5M9.6 5.4 12 3l2.4 2.4M3.6 13.2l1.6.9M20.4 13.2l-1.6.9'
      'M6.2 9.6l1.2 1.3M17.8 9.6l-1.2 1.3M8 21.5h8',
    ),
  ],
  NavpadGlyph.sunset: [
    _Stroke(
      'M2.5 18.5h19M6.5 18.5a5.5 5.5 0 0 1 11 0M12 3v5M9.6 5.6 12 8l2.4-2.4M3.6 13.2l1.6.9M20.4 13.2l-1.6.9'
      'M6.2 9.6l1.2 1.3M17.8 9.6l-1.2 1.3M8 21.5h8',
    ),
  ],
  NavpadGlyph.nakshatra: [
    _Stroke('M11 3.5l1.7 4.6 4.6 1.7-4.6 1.7L11 16.1l-1.7-4.6-4.6-1.7 4.6-1.7z'),
    _Dot(18.5, 17.5, 1.4),
    _Dot(5, 19.5, 1.1),
    _Dot(19.5, 4.5, 1),
  ],
  NavpadGlyph.ghatika: [
    _Stroke(
      'M4.5 9.5h15a7.5 6 0 0 1-15 0zM12 4.5v2.2M9.4 5.4l.9 1.4M14.6 5.4l-.9 1.4'
      'M2.5 19.5c1.6-1 3.2-1 4.8 0s3.2 1 4.8 0 3.2-1 4.8 0 2 .8 2.6.4',
    ),
  ],
  NavpadGlyph.sunpath: [_horizon, _dayPath, _Dot(12, 10, 2.6)],
  NavpadGlyph.kalash: [
    _Stroke('M6.5 11.5h11M8 11.5c-2.4 2-2.4 6.4.2 9h7.6c2.6-2.6 2.6-7 .2-9M9.3 11.5V9.3h5.4v2.2'),
    _Dot(12, 5.8, 2.2, filled: false),
    _Stroke('M10 8.6 6.8 6.7M14 8.6l3.2-1.9M8.2 15.5h7.6'),
  ],
  NavpadGlyph.kalyanak: [
    _Dot(12, 12, 8.2, filled: false),
    _Dot(12, 6.6, 1.5),
    _Dot(17.1, 10.3, 1.5),
    _Dot(15.2, 16.4, 1.5),
    _Dot(8.8, 16.4, 1.5),
    _Dot(6.9, 10.3, 1.5),
  ],
  NavpadGlyph.dhvaja: [_Stroke('M6 21.5V2.8M6 4h12l-3.2 4.2L18 12.4H6')],
  NavpadGlyph.diya: [
    _Stroke(
      'M3.5 14h17c-1 3.8-4.4 5.5-8.5 5.5S4.5 17.8 3.5 14zM12 3.8c-2.2 2.6-2.2 5.3 0 7.4 2.2-2.1 2.2-4.8 0-7.4zM18 14l2.5-2',
    ),
  ],
  NavpadGlyph.monthcal: [
    _Box(3, 5, 18, 16, 2.5),
    _Stroke('M3 9.5h18M8 3v4M16 3v4M13.8 12.6a3.4 3.4 0 1 0 1.6 5.6 3 3 0 0 1-1.6-5.6z'),
  ],
  NavpadGlyph.siddhashila: [
    _Stroke('M4.5 12.5a7.5 7.5 0 0 0 15 0c-2 2.6-4.6 3.6-7.5 3.6s-5.5-1-7.5-3.6z'),
    _Dot(12, 7, 2),
  ],
};

/// One of the app's own icons. Silent to a screen reader unless [semanticLabel]
/// is given, since the words beside it say the same thing.
class NavpadIcon extends StatelessWidget {
  const NavpadIcon(this.glyph, {super.key, this.size, this.color, this.strokeWidth = 1.8, this.semanticLabel});

  final NavpadGlyph glyph;
  final double? size;
  final Color? color;

  /// In grid units, so it scales with [size]; the Month grid's 13 dp marks use 2.2.
  final double strokeWidth;
  final String? semanticLabel;

  @override
  Widget build(BuildContext context) =>
      _GlyphBox(parts: _glyphs[glyph]!, size: size, color: color, strokeWidth: strokeWidth, label: semanticLabel);
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
      parts: [_horizon, _dayPath, _Dot(12 + 8.5 * math.cos(angle), 18.5 - 8.5 * math.sin(angle), 2.6)],
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
      painter: _GlyphPainter(parts, color ?? theme.color ?? const Color(0xFF000000), strokeWidth),
    );
    return label == null
        ? ExcludeSemantics(child: painted)
        : Semantics(container: true, label: label, image: true, excludeSemantics: true, child: painted);
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
    final stroke = Paint()
      ..color = color
      ..style = PaintingStyle.stroke
      ..strokeWidth = strokeWidth
      ..strokeCap = StrokeCap.round
      ..strokeJoin = StrokeJoin.round;
    final fill = Paint()..color = color;
    for (final part in parts) {
      switch (part) {
        case _Stroke(:final d, dash: null):
          canvas.drawPath(svgPath(d), stroke);
        case _Stroke(:final d, dash: (final on, final off)):
          canvas.drawPath(_dashed(svgPath(d), on, off), stroke);
        case _Dot(:final cx, :final cy, :final r, :final filled):
          canvas.drawCircle(Offset(cx, cy), r, filled ? fill : stroke);
        case _Box(:final x, :final y, :final width, :final height, :final radius):
          canvas.drawRRect(RRect.fromLTRBR(x, y, x + width, y + height, Radius.circular(radius)), stroke);
      }
    }
  }

  @override
  bool shouldRepaint(_GlyphPainter old) => old.parts != parts || old.color != color || old.strokeWidth != strokeWidth;
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

final _token = RegExp(r'[MmLlHhVvAaCcSsZz]|[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?');

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
        final rx = next(), ry = next(), rotation = next(), large = next() != 0, sweep = next() != 0;
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
