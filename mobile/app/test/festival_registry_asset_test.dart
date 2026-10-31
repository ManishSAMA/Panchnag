import 'dart:io';

import 'package:flutter_test/flutter_test.dart';

void main() {
  test('the bundled festival registry is a copy of shared/festival_registry.json', () {
    final shared = File('../../shared/festival_registry.json');
    final bundled = File('assets/festival_registry.json');

    expect(
      bundled.readAsBytesSync(),
      shared.readAsBytesSync(),
      reason: 'Copy shared/festival_registry.json to mobile/app/assets/ after regenerating it.',
    );
  });
}
