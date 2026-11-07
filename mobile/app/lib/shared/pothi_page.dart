import 'package:flutter/material.dart';

import '../theme/pothi.dart';

/// A Pothi leaf: the stitched binding runs down the left edge and the page
/// begins to its right. Every screen but the Month grid, which needs the
/// full width for seven columns, sits on one.
class PothiPage extends StatelessWidget {
  const PothiPage({super.key, required this.child});

  /// The binding's width; content starts here.
  static const stitchInset = 22.0;

  final Widget child;

  @override
  Widget build(BuildContext context) {
    final p = Theme.of(context).extension<Pothi>() ?? Pothi.light;
    return CustomPaint(
      key: const Key('pothi-stitch'),
      painter: _StitchPainter(color: p.accent),
      child: Padding(
        padding: const EdgeInsets.only(left: stitchInset),
        child: child,
      ),
    );
  }
}

class _StitchPainter extends CustomPainter {
  const _StitchPainter({required this.color});

  final Color color;

  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()
      ..color = color
      ..strokeCap = StrokeCap.round;
    canvas.drawLine(const Offset(14, 0), Offset(14, size.height), paint..strokeWidth = 1.8);
    paint.strokeWidth = 1.4;
    for (var y = 18.0; y < size.height; y += 32) {
      canvas.drawLine(Offset(9, y), Offset(19, y + 4), paint);
    }
  }

  @override
  bool shouldRepaint(_StitchPainter old) => old.color != color;
}
