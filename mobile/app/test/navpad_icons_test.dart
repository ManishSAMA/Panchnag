import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:jainpanchang/shared/moon_phase.dart';
import 'package:jainpanchang/shared/navpad_icons.dart';
import 'package:jainpanchang/theme/navpad.dart';

import 'support/pixels.dart';

const red = Color(0xFFB3261E);

void main() {
  group('the icon set', () {
    testWidgets('every glyph draws inside its 24 dp box in the IconTheme colour', (tester) async {
      for (final glyph in NavpadGlyph.values) {
        final pixels = await paint(
          tester,
          IconTheme(
            data: const IconThemeData(color: red, size: 24),
            child: SizedBox.square(dimension: 40, child: Center(child: NavpadIcon(glyph))),
          ),
        );
        final inked = pixels.painted.toList();
        expect(inked.where((p) => near(p.colour, red)), isNotEmpty, reason: '$glyph paints in the theme colour');
        expect(inked.every((p) => p.x >= 8 && p.x < 32 && p.y >= 8 && p.y < 32), isTrue, reason: '$glyph stays 24 dp');
      }
    });

    /// The palette colours a glyph fills with, drawn at 96 dp with [outline].
    Future<Set<Color>> fills(WidgetTester tester, NavpadGlyph glyph, Color outline) async {
      final pixels = (await paint(tester, NavpadIcon(glyph, size: 96, color: outline))).painted.toList();
      return {
        for (final ink in IconInk.palette)
          if (pixels.where((p) => near(p.colour, ink, tolerance: 0.03)).length > 12) ink,
      };
    }

    testWidgets('every glyph is a small painting, filled with palette colours', (tester) async {
      for (final glyph in NavpadGlyph.values) {
        expect(await fills(tester, glyph, red), isNotEmpty, reason: '$glyph');
      }
    });

    testWidgets('only the outline follows the text colour; the fills stay day and night', (tester) async {
      for (final glyph in NavpadGlyph.values) {
        final day = await paint(tester, NavpadIcon(glyph, size: 96, color: Navpad.light.ink));
        final night = await paint(tester, NavpadIcon(glyph, size: 96, color: Navpad.dark.ink));
        // Inside a fill: a palette colour with the same colour all round it,
        // so a blend at an outline's edge never counts.
        bool inside(({int x, int y, Color colour}) p) => [
          for (final (dx, dy) in [(-2, 0), (2, 0), (0, -2), (0, 2)])
            near(day.at((p.x + dx).toDouble(), (p.y + dy).toDouble()), p.colour, tolerance: 0.01),
        ].every((same) => same);
        final filled = [
          for (final p in day.painted)
            if (p.x > 2 && p.y > 2 && p.x < 93 && p.y < 93)
              if (IconInk.palette.any((ink) => near(p.colour, ink, tolerance: 0.01)) && inside(p)) p,
        ];
        expect(filled, isNotEmpty, reason: '$glyph');
        expect(
          filled.where((p) => !near(night.at(p.x.toDouble(), p.y.toDouble()), p.colour, tolerance: 0.01)),
          isEmpty,
          reason: '$glyph',
        );
      }
    });

    test('the Muhurat section has an icon for each of its tiles', () {
      expect(
        NavpadGlyph.values.map((g) => g.name),
        containsAll(['panchak', 'yoga', 'abhijit', 'rahuKaal', 'gandmool', 'bhadra', 'chandraBal', 'agniVaas']),
      );
    });

    testWidgets('takes its size from the IconTheme', (tester) async {
      await tester.pumpWidget(
        const IconTheme(
          data: IconThemeData(size: 36),
          child: Center(child: NavpadIcon(NavpadGlyph.kalash)),
        ),
      );
      expect(tester.getSize(find.byType(NavpadIcon)), const Size.square(36));
    });

    testWidgets('no two glyphs look the same', (tester) async {
      final drawings = <String>{};
      for (final glyph in NavpadGlyph.values) {
        final pixels = await paint(tester, NavpadIcon(glyph, color: red));
        drawings.add(
          [
            for (final p in pixels.painted)
              if (p.colour.a > 0.5) '${p.x},${p.y}',
          ].join(' '),
        );
      }
      expect(drawings, hasLength(NavpadGlyph.values.length));
    });

    testWidgets('is silent unless given a label', (tester) async {
      await tester.pumpWidget(
        const Directionality(
          textDirection: TextDirection.ltr,
          child: Column(
            children: [
              NavpadIcon(NavpadGlyph.diya),
              NavpadIcon(NavpadGlyph.dhvaja, semanticLabel: 'पर्व'),
            ],
          ),
        ),
      );
      expect(find.bySemanticsLabel('पर्व'), findsOneWidget);
    });
  });

  group('the path reader', () {
    double length(String d) => svgPath(d).computeMetrics().fold(0, (sum, m) => sum + m.length);

    test('reads pairs after a moveto as lines', () {
      expect(length('M0 0 10 0 10 5'), closeTo(15, 1e-6));
      expect(length('m2 2 10 0'), closeTo(10, 1e-6));
    });

    test('reflects the last control point for a smooth curve', () {
      expect(
        length('M0 0C0 10 10 10 10 0S20 -10 20 0'),
        closeTo(length('M0 0C0 10 10 10 10 0C10 -10 20 -10 20 0'), 1e-6),
      );
    });

    test('reads relative moves, lines and arcs from the current point', () {
      expect(svgPath('M5 5h4v3l-2 2').getBounds(), const Rect.fromLTRB(5, 5, 9, 10));
      expect(svgPath('M2 12a5 5 0 0 1 10 0').getBounds().left, closeTo(2, 1e-6));
    });
  });

  testWidgets('a colour given to the icon wins over the IconTheme', (tester) async {
    const blue = Color(0xFF1F4FB3);
    final pixels = await paint(
      tester,
      const IconTheme(
        data: IconThemeData(color: blue),
        child: NavpadIcon(NavpadGlyph.kalash, color: red),
      ),
    );
    expect(pixels.painted.where((p) => near(p.colour, red)), isNotEmpty);
    expect(pixels.painted.where((p) => near(p.colour, blue)), isEmpty);
  });

  group('the sun on its path', () {
    /// The sun's centre: the middle of its filled disc, the only solid blob.
    Future<Offset> sunAt(WidgetTester tester, double fraction) async {
      final pixels = await paint(tester, SunPathIcon(fraction: fraction, size: 96, color: red));
      final disc = [
        for (final p in pixels.painted)
          if (p.colour.a > 0.9 && p.y < 66) p,
      ];
      final xs = disc.map((p) => p.x), ys = disc.map((p) => p.y);
      return Offset(
        (xs.reduce((a, b) => a < b ? a : b) + xs.reduce((a, b) => a > b ? a : b)) / 2,
        (ys.reduce((a, b) => a < b ? a : b) + ys.reduce((a, b) => a > b ? a : b)) / 2,
      );
    }

    testWidgets('rises on the left, stands overhead at noon and sets on the right', (tester) async {
      final morning = await sunAt(tester, 0.1);
      final noon = await sunAt(tester, 0.5);
      final evening = await sunAt(tester, 0.9);

      expect(morning.dx, lessThan(noon.dx));
      expect(noon.dx, lessThan(evening.dx));
      expect(noon.dx, closeTo(48, 2));
      expect(noon.dy, lessThan(morning.dy));
      expect(morning.dy, closeTo(evening.dy, 2));
    });

    testWidgets('keeps to its path before sunrise and after sunset', (tester) async {
      expect(await sunAt(tester, -0.5), await sunAt(tester, 0));
      expect(await sunAt(tester, 1.7), await sunAt(tester, 1));
    });
  });

  group('the moon of the tithi', () {
    test('is lit i/15 while waxing and wanes back to dark', () {
      expect(moonLitFraction(1), closeTo(1 / 15, 1e-9));
      expect(moonLitFraction(8), closeTo(8 / 15, 1e-9));
      expect(moonLitFraction(15), 1);
      expect(moonLitFraction(21), closeTo(0.6, 1e-9));
      expect(moonLitFraction(30), 0);
    });

    const white = Color(0xFFFFFFFF);
    final navy = Navpad.light.navy;

    /// The moon at 60 dp: left, centre and right of its middle row.
    Future<List<Color>> across(WidgetTester tester, int tithi, {Brightness brightness = Brightness.light}) async {
      final pixels = await paint(tester, MoonPhase(tithi: tithi, size: 60), brightness: brightness);
      return [pixels.at(12, 30), pixels.at(30, 30), pixels.at(48, 30)];
    }

    testWidgets('Purnima is a white disc', (tester) async {
      expect((await across(tester, 15)).every((c) => near(c, white)), isTrue);
    });

    testWidgets('Amavas is a solid navy disc', (tester) async {
      expect((await across(tester, 30)).every((c) => near(c, navy)), isTrue);
    });

    testWidgets('a waxing crescent is lit on the right', (tester) async {
      final [left, centre, right] = await across(tester, 3);
      expect(near(left, navy), isTrue);
      expect(near(centre, navy), isTrue);
      expect(near(right, white), isTrue);
    });

    testWidgets('a waxing gibbous is lit past the middle', (tester) async {
      final [left, centre, right] = await across(tester, 12);
      expect(near(left, navy), isTrue);
      expect(near(centre, white), isTrue);
      expect(near(right, white), isTrue);
    });

    testWidgets('a waning moon is lit on the left', (tester) async {
      final [left, centre, right] = await across(tester, 27);
      expect(near(left, white), isTrue);
      expect(near(centre, navy), isTrue);
      expect(near(right, navy), isTrue);
    });

    testWidgets('keeps navy for the dark part in dark mode, where ink is light', (tester) async {
      final [left, _, right] = await across(tester, 27, brightness: Brightness.dark);
      expect(near(left, white), isTrue);
      expect(near(right, Navpad.dark.navy), isTrue);
    });

    testWidgets('names its tithi to a screen reader', (tester) async {
      await tester.pumpWidget(
        const Directionality(
          textDirection: TextDirection.ltr,
          child: MoonPhase(tithi: 21, size: 58, semanticLabel: 'कृष्ण षष्ठी'),
        ),
      );
      expect(find.bySemanticsLabel('कृष्ण षष्ठी'), findsOneWidget);
    });
  });
}
