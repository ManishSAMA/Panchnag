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
      expect(sthanakvasi.where((f) => f.ruleId == 'namokar_35_vrat').map((f) => f.id),
          contains('namokar_vrat_step_1_2026'));
      expect(sthanakvasi.where((f) => f.ruleId == 'pushpanjali_vrat'), hasLength(greaterThanOrEqualTo(15)));
      // A sidereal month is 27.3 days, so Rohini comes round 13 or 14 times a year.
      expect(sthanakvasi.where((f) => f.id == 'rohini_nakshatra_parv_vrat'), hasLength(inInclusiveRange(12, 14)));
      final ravi = sthanakvasi.where((f) => f.id == 'ravi_vrat').toList();
      expect(ravi, hasLength(9));
      expect(ravi.every((f) => f.start.vara == 0), isTrue);
      expect(ids(sthanakvasi), containsAll(['samvatsari_mahaparv_2026', 'labdhi_vidhan_vrat_purna_2026']));
      final samvatsari = sthanakvasi.firstWhere((f) => f.id == 'samvatsari_mahaparv_2026').start;
      expect(sthanakvasi.firstWhere((f) => f.id == 'labdhi_vidhan_vrat_purna_2026').start, samvatsari);
    });

    test('the Diwali cluster: Nirvana on Amavasya, the new year the day after, Bhai Dooj the day after that', () {
      CivilDate on(String id) => sthanakvasi.firstWhere((f) => f.id == id).start;
      final nirvana = on('mahavira_nirvana_kalyanak_2026');
      expect(on('jain_new_year_2026').compareTo(nirvana), greaterThan(0));
      expect(on('bhai_dooj_2026').compareTo(on('jain_new_year_2026')), greaterThan(0));
      expect(on('chaturmas_nishthapan_2026'), nirvana);
    });

    test('a Prarambh precedes its Purna', () {
      CivilDate on(String id) => sthanakvasi.firstWhere((f) => f.id == id).start;
      for (final (start, end) in [
        ('navapad_oli_vrat_prarambh_chaitra_2026', 'navapad_oli_vrat_purna_chaitra_2026'),
        ('anant_vrat_prarambh_2026', 'anant_chaturdashi_purna_2026'),
        ('shraddha_vrat_prarambh_2026', 'shraddha_vrat_purna_2026'),
      ]) {
        expect(on(start).compareTo(on(end)), lessThan(0), reason: start);
      }
    });

    test('Karma Nirjara in each Chaturmas month; Ashtahnika three times, eight days or so each', () {
      expect(sthanakvasi.where((f) => f.ruleId == 'karma_nirjara_vrat'), hasLength(4));
      final ashtahnika = sthanakvasi.where((f) => f.ruleId == 'ashtahnika_mahaparv').toList();
      expect(ashtahnika, hasLength(3));
      for (final f in ashtahnika) {
        expect(f.start.plusDays(6).compareTo(f.end) <= 0 && f.end.compareTo(f.start.plusDays(9)) <= 0, isTrue, reason: f.id);
      }
    });

    test('a span vrat ends after it begins', () {
      for (final id in ['solah_karan_vrat_prarambh_2026', 'teen_chaubisi_vrat_prarambh_2026', 'bhaya_haran_vrat_2026']) {
        final vrat = sthanakvasi.firstWhere((f) => f.id == id);
        expect(vrat.end.compareTo(vrat.start), greaterThan(0), reason: id);
      }
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
