/// Reads what a widget actually paints, for the drawings that carry meaning
/// in their shape: the moon's lit side, the sun's place on its path.
library;

import 'dart:typed_data';
import 'dart:ui' as ui;

import 'package:flutter/material.dart';
import 'package:flutter/rendering.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:jainpanchang/theme/theme.dart';

final class Pixels {
  const Pixels(this.width, this.height, this._rgba);

  final int width, height;
  final ByteData _rgba;

  Color at(double x, double y) {
    final offset = (y.floor() * width + x.floor()) * 4;
    return Color.fromARGB(
      _rgba.getUint8(offset + 3),
      _rgba.getUint8(offset),
      _rgba.getUint8(offset + 1),
      _rgba.getUint8(offset + 2),
    );
  }

  Iterable<({int x, int y, Color colour})> get painted sync* {
    for (var y = 0; y < height; y++) {
      for (var x = 0; x < width; x++) {
        final colour = at(x.toDouble(), y.toDouble());
        if (colour.a > 0) yield (x: x, y: y, colour: colour);
      }
    }
  }
}

/// [child] painted at one physical pixel per logical pixel, on a transparent ground.
Future<Pixels> paint(WidgetTester tester, Widget child, {Brightness brightness = Brightness.light}) async {
  final key = GlobalKey();
  await tester.pumpWidget(
    MaterialApp(
      theme: navpadTheme(brightness),
      home: Material(
        type: MaterialType.transparency,
        child: Center(
          child: RepaintBoundary(key: key, child: child),
        ),
      ),
    ),
  );
  return (await tester.runAsync(() async {
    final boundary = key.currentContext!.findRenderObject()! as RenderRepaintBoundary;
    final ui.Image image = await boundary.toImage();
    final bytes = await image.toByteData();
    return Pixels(image.width, image.height, bytes!);
  }))!;
}

/// Close enough to [expected] that antialiasing at an edge doesn't count.
bool near(Color actual, Color expected, {double tolerance = 0.08}) =>
    (actual.r - expected.r).abs() < tolerance &&
    (actual.g - expected.g).abs() < tolerance &&
    (actual.b - expected.b).abs() < tolerance &&
    actual.a > 0.9;
