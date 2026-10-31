import 'package:flutter/material.dart';

import '../theme/navpad.dart';

/// How much of the moon is lit on [tithi] 1–30: i/15 through Shukla, then
/// back down through Krishna to dark on Amavas.
double moonLitFraction(int tithi) => tithi <= 15 ? tithi / 15 : 1 - (tithi - 15) / 15;

/// The moon as it looks on the night of [tithi]: lit side white, dark side
/// navy (so Purnima is a white disc and Amavas a solid one), lit on the right
/// while waxing. Navy rather than ink, because dark mode's ink is light.
class MoonPhase extends StatelessWidget {
  const MoonPhase({super.key, required this.tithi, required this.size, this.semanticLabel});

  final int tithi;
  final double size;
  final String? semanticLabel;

  @override
  Widget build(BuildContext context) {
    final n = Theme.of(context).extension<Navpad>() ?? Navpad.light;
    final painted = CustomPaint(
      size: Size.square(size),
      painter: _MoonPainter(tithi: tithi, dark: n.navy, outline: n.ink),
    );
    return semanticLabel == null
        ? ExcludeSemantics(child: painted)
        : Semantics(container: true, label: semanticLabel, image: true, excludeSemantics: true, child: painted);
  }
}

class _MoonPainter extends CustomPainter {
  const _MoonPainter({required this.tithi, required this.dark, required this.outline});

  final int tithi;
  final Color dark, outline;

  // On the mockup's 24-unit grid: a 10-unit disc at the centre.
  static const _r = 10.0;
  static const _top = Offset(12, 2), _bottom = Offset(12, 22);

  @override
  void paint(Canvas canvas, Size size) {
    canvas.scale(size.width / 24);
    const centre = Offset(12, 12);
    canvas.drawCircle(centre, _r, Paint()..color = dark);
    final lit = moonLitFraction(tithi);
    final waxing = tithi <= 15;
    if (lit > 0) {
      // Half the rim on the lit side, then back along the terminator: an
      // ellipse whose width shrinks to nothing at the half moon.
      final terminator = Path()
        ..moveTo(_top.dx, _top.dy)
        ..arcToPoint(_bottom, radius: const Radius.circular(_r), clockwise: waxing)
        ..arcToPoint(_top, radius: Radius.elliptical((1 - 2 * lit).abs() * _r, _r), clockwise: (lit > 0.5) == waxing)
        ..close();
      canvas.drawPath(terminator, Paint()..color = const Color(0xFFFFFFFF));
    }
    canvas.drawCircle(
      centre,
      _r,
      Paint()
        ..color = outline
        ..style = PaintingStyle.stroke
        ..strokeWidth = 1.4,
    );
  }

  @override
  bool shouldRepaint(_MoonPainter old) => old.tithi != tithi || old.dark != dark || old.outline != outline;
}
