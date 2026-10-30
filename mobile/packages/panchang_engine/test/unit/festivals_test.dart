import 'package:panchang_engine/panchang_engine.dart';
import 'package:test/test.dart';

import 'festival_registry_test.dart' show sharedRegistryJson;

const delhiCity = Location(lat: 28.6139, lon: 77.2090, timezone: 'Asia/Kolkata');

void main() {
  final registry = FestivalRegistry.fromJson(sharedRegistryJson());

  List<FestivalOccurrence> festivals(String profile) =>
      const PanchangEngine().festivals(location: delhiCity, year: 2026, profile: profile, registry: registry);

  group('profiles', () {
    test('the three Shwetambar profiles are the ones offered', () {
      expect(festivalProfiles, [
        'shwetambar_murtipujak_tapagachchha',
        'shwetambar_sthanakvasi',
        'shwetambar_terapanthi',
      ]);
    });

    // Python quietly returned the wrong festivals for an unknown profile before
    // it learned to raise; Dart refuses from the start (plans/mobile-phase5-festivals.md §6.3).
    for (final profile in ['all', 'digambar', 'shwetambar', '']) {
      test("'$profile' is refused, naming the accepted profiles", () {
        expect(
          () => festivals(profile),
          throwsA(isA<ArgumentError>().having((e) => e.message, 'message', contains('shwetambar_sthanakvasi'))),
        );
      });
    }
  });
}
