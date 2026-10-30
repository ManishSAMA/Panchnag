import 'package:panchang_engine/panchang_engine.dart';
import 'package:test/test.dart';

import 'festival_registry_test.dart' show sharedRegistryJson;

const delhiCity = Location(lat: 28.6139, lon: 77.2090, timezone: 'Asia/Kolkata');

void main() {
  final registry = FestivalRegistry.fromJson(sharedRegistryJson());

  List<FestivalOccurrence> festivals(String profile) =>
      const PanchangEngine().festivals(location: delhiCity, year: 2026, profile: profile, registry: registry);

  group('a year (Delhi 2026)', () {
    final sthanakvasi = festivals('shwetambar_sthanakvasi');
    final tapagachchha = festivals('shwetambar_murtipujak_tapagachchha');
    Set<String> ids(List<FestivalOccurrence> list) => {for (final f in list) f.id};

    test('holds only festivals whose first day is in the year, sorted by date', () {
      expect(sthanakvasi, isNotEmpty);
      expect(sthanakvasi.every((f) => f.start.year == 2026), isTrue);
      for (var i = 1; i < sthanakvasi.length; i++) {
        expect(sthanakvasi[i].start.compareTo(sthanakvasi[i - 1].start), greaterThanOrEqualTo(0));
      }
    });

    test("runs a profile's own rules and the shared ones, not another profile's", () {
      expect(ids(sthanakvasi), containsAll(['samvatsari_sthanakvasi', 'pakhi_chaudas_shukla']));
      expect(ids(sthanakvasi), isNot(contains('samvatsari_tapagachchha')));
      expect(ids(tapagachchha), contains('samvatsari_tapagachchha'));
    });

    // Not the occurrence id alone: Python names a Bhaktambar day by its fortnight,
    // and the Pausha fortnight falls at both ends of a year.
    test('never lists the same occurrence twice on one day', () {
      final keys = [for (final f in sthanakvasi) '${f.occurrenceId} ${f.start}'];
      expect(keys.toSet(), hasLength(keys.length));
    });

    test('includes the vrats with ids of their own, attributed to their registry entry', () {
      final bhaktambar = sthanakvasi.where((f) => f.ruleId == 'bhaktambar_vrat').toList();
      expect(bhaktambar, isNotEmpty);
      expect(bhaktambar.every((f) => f.id.startsWith('bhaktambar_vrat_2026_')), isTrue);
    });
  });

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
