import 'package:panchang_engine/src/time/delta_t.dart';
import 'package:panchang_engine/src/time/delta_t_table.g.dart';
import 'package:test/test.dart';

void main() {
  test('equals the reference value at every table sample', () {
    for (final (jd, seconds) in deltaTTable) {
      expect(deltaTSeconds(jd), seconds);
    }
  });

  test('interpolates linearly between samples', () {
    final (jd0, dt0) = deltaTTable[40];
    final (jd1, dt1) = deltaTTable[41];

    expect(deltaTSeconds((jd0 + jd1) / 2), closeTo((dt0 + dt1) / 2, 1e-9));
  });

  test('refuses instants outside the table instead of extrapolating', () {
    expect(() => deltaTSeconds(deltaTTable.first.$1 - 1), throwsRangeError);
    expect(() => deltaTSeconds(deltaTTable.last.$1 + 1), throwsRangeError);
  });

  test('converts UT to TT', () {
    const jd = 2461041.5;

    expect(terrestrialTime(jd), jd + deltaTSeconds(jd) / 86400);
  });
}
