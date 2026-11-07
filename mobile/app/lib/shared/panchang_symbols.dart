import 'package:flutter/widgets.dart';

import '../format/panchang_text.dart';
import 'navpad_icons.dart';

enum PanchangGlyph {
  sun,
  moon,
  mercury,
  venus,
  mars,
  jupiter,
  saturn,
  uranus,
  neptune,
  pluto,
  moonsNode,
  aries,
  taurus,
  gemini,
  cancer,
  leo,
  virgo,
  libra,
  scorpio,
  sagittarius,
  capricorn,
  aquarius,
  pisces,
  conjunction,
  semisextile,
  semisquare,
  sextile,
  square,
  trine,
  sesquisquare,
  quincunx,
  opposition,
  newMoon,
  firstQuarterMoon,
  fullMoon,
  thirdQuarterMoon,
  solarEclipse,
  lunarEclipse,
}

enum PanchangSymbolGroup { planets, zodiac, aspects, moonPhases, eclipses }

PanchangSymbolGroup panchangSymbolGroup(PanchangGlyph glyph) {
  if (glyph.index <= PanchangGlyph.moonsNode.index) {
    return PanchangSymbolGroup.planets;
  }
  if (glyph.index <= PanchangGlyph.pisces.index) {
    return PanchangSymbolGroup.zodiac;
  }
  if (glyph.index <= PanchangGlyph.opposition.index) {
    return PanchangSymbolGroup.aspects;
  }
  if (glyph.index <= PanchangGlyph.thirdQuarterMoon.index) {
    return PanchangSymbolGroup.moonPhases;
  }
  return PanchangSymbolGroup.eclipses;
}

String? panchangAspectDegrees(PanchangGlyph glyph) => switch (glyph) {
  PanchangGlyph.conjunction => '0°',
  PanchangGlyph.semisextile => '30°',
  PanchangGlyph.semisquare => '45°',
  PanchangGlyph.sextile => '60°',
  PanchangGlyph.square => '90°',
  PanchangGlyph.trine => '120°',
  PanchangGlyph.sesquisquare => '135°',
  PanchangGlyph.quincunx => '150°',
  PanchangGlyph.opposition => '180°',
  _ => null,
};

const _names = <PanchangGlyph, (String, String)>{
  PanchangGlyph.sun: ('Sun', 'सूर्य'),
  PanchangGlyph.moon: ('Moon', 'चंद्रमा'),
  PanchangGlyph.mercury: ('Mercury', 'बुध'),
  PanchangGlyph.venus: ('Venus', 'शुक्र'),
  PanchangGlyph.mars: ('Mars', 'मंगल'),
  PanchangGlyph.jupiter: ('Jupiter', 'गुरु'),
  PanchangGlyph.saturn: ('Saturn', 'शनि'),
  PanchangGlyph.uranus: ('Uranus', 'यूरेनस'),
  PanchangGlyph.neptune: ('Neptune', 'नेपच्यून'),
  PanchangGlyph.pluto: ('Pluto', 'प्लूटो'),
  PanchangGlyph.moonsNode: ('Moon’s Node', 'चंद्र नोड'),
  PanchangGlyph.aries: ('Aries', 'मेष'),
  PanchangGlyph.taurus: ('Taurus', 'वृषभ'),
  PanchangGlyph.gemini: ('Gemini', 'मिथुन'),
  PanchangGlyph.cancer: ('Cancer', 'कर्क'),
  PanchangGlyph.leo: ('Leo', 'सिंह'),
  PanchangGlyph.virgo: ('Virgo', 'कन्या'),
  PanchangGlyph.libra: ('Libra', 'तुला'),
  PanchangGlyph.scorpio: ('Scorpio', 'वृश्चिक'),
  PanchangGlyph.sagittarius: ('Sagittarius', 'धनु'),
  PanchangGlyph.capricorn: ('Capricorn', 'मकर'),
  PanchangGlyph.aquarius: ('Aquarius', 'कुंभ'),
  PanchangGlyph.pisces: ('Pisces', 'मीन'),
  PanchangGlyph.conjunction: ('Conjunction', 'संयोग'),
  PanchangGlyph.semisextile: ('Semisextile', 'सेमीसेक्स्टाइल'),
  PanchangGlyph.semisquare: ('Semisquare', 'सेमीस्क्वायर'),
  PanchangGlyph.sextile: ('Sextile', 'सेक्स्टाइल'),
  PanchangGlyph.square: ('Square', 'स्क्वायर'),
  PanchangGlyph.trine: ('Trine', 'ट्राइन'),
  PanchangGlyph.sesquisquare: ('Sesquisquare', 'सेस्क्विस्क्वायर'),
  PanchangGlyph.quincunx: ('Quincunx', 'क्विनकंक्स'),
  PanchangGlyph.opposition: ('Opposition', 'विपरीत योग'),
  PanchangGlyph.newMoon: ('New Moon', 'अमावस्या'),
  PanchangGlyph.firstQuarterMoon: ('First Quarter Moon', 'प्रथम चरण चंद्रमा'),
  PanchangGlyph.fullMoon: ('Full Moon', 'पूर्णिमा'),
  PanchangGlyph.thirdQuarterMoon: ('Third Quarter Moon', 'तृतीय चरण चंद्रमा'),
  PanchangGlyph.solarEclipse: ('Solar Eclipse', 'सूर्य ग्रहण'),
  PanchangGlyph.lunarEclipse: ('Lunar Eclipse', 'चंद्र ग्रहण'),
};

String panchangSymbolName(PanchangGlyph glyph, Lang lang) {
  final (english, hindi) = _names[glyph]!;
  return lang == Lang.en ? english : hindi;
}

sealed class _Part {
  const _Part();
}

final class _Stroke extends _Part {
  const _Stroke(this.d);
  final String d;
}

final class _Fill extends _Part {
  const _Fill(this.d);
  final String d;
}

final class _Circle extends _Part {
  const _Circle(this.x, this.y, this.r, {this.filled = false});
  final double x, y, r;
  final bool filled;
}

const _sunRays = _Stroke(
  'M12 2v2M12 20v2M2 12h2M20 12h2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M19.1 4.9l-1.4 1.4M6.3 17.7l-1.4 1.4',
);
const _cross = _Stroke('M12 14v7M8.5 17.5h7');
const _quarterRight = _Fill('M12 3a9 9 0 0 1 0 18z');
const _quarterLeft = _Fill('M12 3a9 9 0 0 0 0 18z');

const _paths = <PanchangGlyph, List<_Part>>{
  PanchangGlyph.sun: [_Circle(12, 12, 4.5), _sunRays],
  PanchangGlyph.moon: [
    _Stroke('M15.8 3.6a9 9 0 1 0 4.7 15.6A10 10 0 0 1 15.8 3.6z'),
  ],
  PanchangGlyph.mercury: [
    _Stroke('M7.5 6a5 5 0 0 1 9 0'),
    _Circle(12, 10.5, 3.8),
    _cross,
  ],
  PanchangGlyph.venus: [_Circle(12, 9, 4.5), _cross],
  PanchangGlyph.mars: [
    _Circle(9, 15, 4.5),
    _Stroke('M12.2 11.8 20 4M14.5 4H20v5.5'),
  ],
  PanchangGlyph.jupiter: [
    _Stroke(
      'M4 5.5c5-2 10-.5 8 3-1.5 2.5-5 2.5-8 1M10 3v13M5 15h11c3 0 3 5 0 5h-3',
    ),
  ],
  PanchangGlyph.saturn: [
    _Stroke('M8 3v12c0 5 7 5 7 0V8c0-3-4-3-4 0v6M5 8h10M14 4l3-2v7'),
  ],
  PanchangGlyph.uranus: [
    _Circle(12, 16, 3),
    _Stroke('M12 13V3M5 6v7M19 6v7M5 9l7 4 7-4'),
    _Circle(5, 5, 1.5),
    _Circle(19, 5, 1.5),
  ],
  PanchangGlyph.neptune: [
    _Stroke(
      'M12 3v13M5 4v5c0 4 14 4 14 0V4M3.5 5.5 5 4l1.5 1.5M10.5 4.5 12 3l1.5 1.5M17.5 5.5 19 4l1.5 1.5M12 16v5M8.5 18.5h7',
    ),
  ],
  PanchangGlyph.pluto: [
    _Circle(12, 7, 3),
    _Stroke('M5 13a7 7 0 0 0 14 0M12 14v7M8.5 17.5h7'),
  ],
  PanchangGlyph.moonsNode: [
    _Stroke('M5 5a8 8 0 0 0 14 0M5 5v7M19 5v7'),
    _Circle(5, 14, 2),
    _Circle(19, 14, 2),
  ],
  PanchangGlyph.aries: [
    _Stroke(
      'M12 21V9C12 1 3 1 3 7c0 3 3 4 5 2M12 9C12 1 21 1 21 7c0 3-3 4-5 2',
    ),
  ],
  PanchangGlyph.taurus: [_Circle(12, 15, 5.5), _Stroke('M5 4c0 6 14 6 14 0')],
  PanchangGlyph.gemini: [
    _Stroke('M4 4c5 2 11 2 16 0M4 20c5-2 11-2 16 0M8 5v14M16 5v14'),
  ],
  PanchangGlyph.cancer: [
    _Stroke('M3 10c4-7 12-5 15 0M21 14c-4 7-12 5-15 0'),
    _Circle(6, 9, 2.3),
    _Circle(18, 15, 2.3),
  ],
  PanchangGlyph.leo: [
    _Circle(6, 15, 3.5),
    _Stroke('M9 14c4-2-1-9 3-11 5-2 7 4 4 8-2 3-1 8 3 8 2 0 3-1 3-3'),
  ],
  PanchangGlyph.virgo: [
    _Stroke(
      'M3 5v12M3 8c3-5 6-3 6 1v8M9 8c3-5 6-3 6 1v8M15 8c3-5 6-2 5 3-1 6-5 9-8 10M17 13c4 0 5 3 2 5',
    ),
  ],
  PanchangGlyph.libra: [_Stroke('M3 20h18M3 16h6a6 6 0 0 1 6 0h6')],
  PanchangGlyph.scorpio: [
    _Stroke('M3 5v13M3 8c3-5 6-3 6 1v8M9 8c3-5 6-3 6 1v8l5 3M16 16l5 4-4 1'),
  ],
  PanchangGlyph.sagittarius: [_Stroke('M4 20 20 4M10 4h10v10M5 10l9 9')],
  PanchangGlyph.capricorn: [
    _Stroke(
      'M3 5v12M3 8c3-5 6-3 6 1v5c0 6 8 6 8 0 0-5-7-5-7 0 0 4 4 5 7 3l3 2',
    ),
  ],
  PanchangGlyph.aquarius: [
    _Stroke('M2 9l4-4 4 4 4-4 4 4 4-4M2 17l4-4 4 4 4-4 4 4 4-4'),
  ],
  PanchangGlyph.pisces: [
    _Stroke('M5 3c7 5 7 13 0 18M19 3c-7 5-7 13 0 18M3 12h18'),
  ],
  PanchangGlyph.conjunction: [
    _Circle(7.5, 12, 4),
    _Circle(16.5, 12, 4),
    _Stroke('M11.5 12h1'),
  ],
  PanchangGlyph.semisextile: [_Stroke('M4 5l8 15 8-15M3 5h18')],
  PanchangGlyph.semisquare: [_Stroke('M4 19V6l16 13z')],
  PanchangGlyph.sextile: [_Stroke('M12 3v18M4.2 7.5l15.6 9M4.2 16.5l15.6-9')],
  PanchangGlyph.square: [_Stroke('M4 4h16v16H4z')],
  PanchangGlyph.trine: [_Stroke('M12 3 21 20H3z')],
  PanchangGlyph.sesquisquare: [_Stroke('M3 9h12v12H3zM15 9l6-6M15 3h6v6')],
  PanchangGlyph.quincunx: [_Stroke('M3 19 12 4l9 15M6 14h12M12 4v16')],
  PanchangGlyph.opposition: [
    _Circle(5, 12, 3),
    _Circle(19, 12, 3),
    _Stroke('M8 12h8'),
  ],
  PanchangGlyph.newMoon: [_Circle(12, 12, 9, filled: true)],
  PanchangGlyph.firstQuarterMoon: [_Circle(12, 12, 9), _quarterRight],
  PanchangGlyph.fullMoon: [_Circle(12, 12, 9)],
  PanchangGlyph.thirdQuarterMoon: [_Circle(12, 12, 9), _quarterLeft],
  PanchangGlyph.solarEclipse: [
    _Circle(10, 12, 7, filled: true),
    _Circle(16, 9, 5),
  ],
  PanchangGlyph.lunarEclipse: [
    _Circle(12, 12, 8),
    _Stroke('M4 19 20 5'),
    _Circle(18, 17, 2.5, filled: true),
  ],
};

class PanchangSymbol extends StatelessWidget {
  const PanchangSymbol(
    this.glyph, {
    super.key,
    this.size = 32,
    this.color,
    this.semanticLabel,
  });

  final PanchangGlyph glyph;
  final double size;
  final Color? color;
  final String? semanticLabel;

  @override
  Widget build(BuildContext context) {
    final painted = CustomPaint(
      size: Size.square(size),
      painter: _SymbolPainter(
        _paths[glyph]!,
        color ?? IconTheme.of(context).color ?? const Color(0xFF000000),
      ),
    );
    return semanticLabel == null
        ? ExcludeSemantics(child: painted)
        : Semantics(
            container: true,
            image: true,
            label: semanticLabel,
            excludeSemantics: true,
            child: painted,
          );
  }
}

class _SymbolPainter extends CustomPainter {
  const _SymbolPainter(this.parts, this.color);

  final List<_Part> parts;
  final Color color;

  @override
  void paint(Canvas canvas, Size size) {
    canvas.scale(size.width / 24);
    final stroke = Paint()
      ..color = color
      ..style = PaintingStyle.stroke
      ..strokeWidth = 1.55
      ..strokeCap = StrokeCap.round
      ..strokeJoin = StrokeJoin.round;
    final fill = Paint()..color = color;
    for (final part in parts) {
      switch (part) {
        case _Stroke(:final d):
          canvas.drawPath(svgPath(d), stroke);
        case _Fill(:final d):
          canvas.drawPath(svgPath(d), fill);
        case _Circle(:final x, :final y, :final r, :final filled):
          canvas.drawCircle(Offset(x, y), r, filled ? fill : stroke);
      }
    }
  }

  @override
  bool shouldRepaint(_SymbolPainter old) =>
      old.parts != parts || old.color != color;
}
