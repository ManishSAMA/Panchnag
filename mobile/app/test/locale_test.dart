import 'package:flutter/widgets.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:jainpanchang/app.dart';

// mobile-ui-design.md §1: English if the phone is set to English, otherwise Hindi.
void main() {
  test('an English phone gets English', () {
    expect(appLocaleFor(const [Locale('en', 'US')]), const Locale('en'));
    expect(appLocaleFor(const [Locale('en', 'IN')]), const Locale('en'));
  });

  test('a Hindi phone gets Hindi', () {
    expect(appLocaleFor(const [Locale('hi', 'IN')]), const Locale('hi'));
  });

  test('any other language gets Hindi', () {
    expect(appLocaleFor(const [Locale('gu', 'IN')]), const Locale('hi'));
    expect(appLocaleFor(const [Locale('fr')]), const Locale('hi'));
  });

  test("only the phone's first language counts", () {
    expect(appLocaleFor(const [Locale('gu'), Locale('en')]), const Locale('hi'));
  });

  test('no reported language gets Hindi', () {
    expect(appLocaleFor(null), const Locale('hi'));
    expect(appLocaleFor(const []), const Locale('hi'));
  });
}
