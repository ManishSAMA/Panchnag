// L4 parity: every festival occurrence (id, occurrence id, dates, status) of
// every ported rule type, for each core location, sunrise rule, year and
// Shwetambar profile, against Python. Rule types land one at a time
// (plans/mobile-phase5-festivals.md §5); fixture rows are attributed to their
// rule type by id (§6.4), and rows of types not yet ported are left out.
import 'dart:io';

import 'package:panchang_engine/panchang_engine.dart';
import 'package:panchang_engine/src/calendar/month.dart';
import 'package:panchang_engine/src/festivals/days.dart';
import 'package:panchang_engine/src/festivals/festivals.dart';
import 'package:panchang_engine/src/panchang/elements.dart';
import 'package:test/test.dart';

import '../support/fixtures.dart';

const toleranceDays = 10 / 86400;

/// Months do not depend on the location; name 2015-2041 once.
final amanta = amantaLookup(lunarMonthsBetween(2457357.5, 2466551.5 + 31));

final registry = FestivalRegistry.fromJson(File('../../../shared/festival_registry.json').readAsStringSync());

/// Rule types whose occurrences carry an id of their own rather than the
/// registry id, by the ids they emit. Filled in as each type is ported.
final Map<String, RegExp> emittedIds = {
  'BhaktambarVrat': RegExp(r'^bhaktambar_vrat_\d{4}_'),
  'Namokar35Vrat': RegExp(r'^namokar_vrat_step_\d+_\d{4}$'),
  'PushpanjaliVrat': RegExp(r'^pushpanjali_vrat_(spring|monsoon|winter)_\d{4}-\d\d-\d\d$'),
  'ShvetambaraParyushan50Day':
      RegExp(r'^(shvetambara_chaturmas_prarambh|paryushan_parv_day_[1-7]|samvatsari_mahaparv)_\d{4}$'),
  'LabdhiVidhanVrat': RegExp(r'^labdhi_vidhan_vrat_(prarambh|purna)_\d{4}$'),
  'DaslakshanVrat': RegExp(r'^daslakshan_(Bhadrapada|Magha|Chaitra)_\d{4}$'),
  'RatnatrayaVrat': RegExp(r'^ratnatraya_vrat_(prarambh|purna)_(chaitra|magha)_\d{4}$'),
  'ShodashkaranVrat': RegExp(r'^shodashkaran_[A-Z_]+_\d{4}$'),
  'RavivaraVrat': RegExp(r'^ravivara_\d{4}$'),
  'KarmaNirjaraVrat': RegExp(r'^karma_nirjara_vrat_(adhik_)?(ashadha|shravana|bhadrapada|ashwin)_\d{4}$'),
  for (final MapEntry(:key, :value) in yearlyEvents.entries) key: RegExp('^(${value.join('|')})' r'_\d{4}$'),
};

/// Family B, C and D rule types and Ashtahnika, by the `<prefix>_<year>` ids of their events.
const Map<String, List<String>> yearlyEvents = {
  'ShravanaPurnimaRakshabandhan': [
    'rakshabandhan_700_muni_raksha_divas', 'muni_vishnukumar_akampanacharya_pujan', 'sorana_pujan',
  ],
  'PhalgunaPurnimaAshtahnikaPurna': ['phalguna_ashtahnika_purna', 'holika_dahan', 'phalguna_purnima_vasantotsav'],
  'MaghaShuklaPanchamiTri': ['acharya_kundakunda_jayanti', 'jina_murti_sthapna', 'vasant_panchami_shrut'],
  'TalaDharTapShantisagarPunyatithi': ['acharya_shantisagar_punyatithi', 'tala_dhar_tap'],
  'BadiPanchamiMeruSthapana': ['badi_panchami', 'meru_sthapana'],
  'NihshalyaAshtamiManchinTithi': ['nihshalya_ashtami_vrat', 'manchin_tithi_ashtami'],
  'SugandhDashami': ['sugandh_dashami_mahaparv', 'sugandh_dashami_vrat'],
  'VeerShasanJayanti': ['veer_shasan_jayanti', 'shrut_udbhav_divas'],
  'GyanDhanTrayodashi': ['gyan_trayodashi', 'dhan_teras'],
  'KartikaAmavasyaMahaviraNirvana': ['mahavira_nirvana_kalyanak', 'varsha_yog_nishthapan'],
  'KartikaShuklaEkamNewYear': ['jain_new_year', 'gautam_swami_kevalgyan'],
  'KartikaShuklaPanchami': ['gyan_panchami', 'labh_panchami'],
  'KartikaPurnimaAshtahnikaPurna': ['kartika_ashtahnika_purna', 'kartika_purnima_dev_deepavali'],
  'JeevDayaAshtami': ['jeev_daya_ashtami'],
  'KartikaNandishwarAshtami': ['nandishwar_ashtami_kartika'],
  'BhaiDooj': ['bhai_dooj'],
  'MargashirshaSheetalnathStotram': ['sheetalnath_stotram_rachna'],
  'ChaitraAmavasyaKalyanakVarshant': ['vikram_samvat_varshant'],
  'AkshayaTritiya': ['akshaya_tritiya_dan_divas'],
  'DiwaliChaturmasNishthapan': ['diwali', 'chaturmas_nishthapan'],
  'SplitDayAhoiKarwaDampatya': ['karwa_chauth', 'ahoi_ashtami', 'dampatya_ashtami'],
  'ChaitraLabdhiVidhan': ['labdhi_vidhan_start_chaitra', 'labdhi_vidhan_purna_chaitra'],
  'MaghaLabdhiVidhan': ['labdhi_vidhan_start_magha', 'labdhi_vidhan_purna_magha'],
  'SaptaRishiVrat': ['sapta_rishi_vrat_prarambh', 'sapta_rishi_vrat_nishthapan'],
  'SaptaParamsthanVrat': ['sapta_paramsthan_vrat_prarambh', 'sapta_paramsthan_vrat_purna'],
  'RakshabandhanVrat': ['rakshabandhan_vrat_prarambh', 'rakshabandhan_vrat_purna'],
  'AkshayaNidhiVrat': ['akshaya_nidhi_vrat_prarambh', 'akshaya_nidhi_vrat_purna'],
  'AnantChaturdashiVrat': ['anant_vrat_prarambh', 'anant_chaturdashi_purna'],
  'RatnatrayaSankatHaranVrat': [
    'ratnatraya_vrat_prarambh', 'sankat_haran_vrat_prarambh', 'ratnatraya_vrat_purna', 'sankat_haran_vrat_purna',
  ],
  'ShraddhaVrat': ['shraddha_vrat_prarambh', 'shraddha_vrat_purna'],
  'NavapadOliVrat': [
    'navapad_oli_vrat_prarambh_chaitra', 'navapad_oli_vrat_purna_chaitra',
    'navapad_oli_vrat_prarambh_ashwin', 'navapad_oli_vrat_purna_ashwin',
  ],
  'MonthlyVrat': ['pratham_jeth_jinvani_vrat_start', 'pratham_jeth_jinvani_vrat_end'],
  'BhadrapadaKrishnaEkamMultiVrat': [
    'solah_karan_vrat_prarambh', 'shri_jin_mukhavlokan_vrat_prarambh', 'shrut_skandha_vrat_prarambh',
    'mushti_vidhan_vrat_prarambh', 'dhanda_kalash_vrat_prarambh', 'megh_mala_vrat_prarambh',
  ],
  'TeenChaubisiVrat': ['teen_chaubisi_vrat_prarambh'],
  'BhayaHaranVrat': ['bhaya_haran_vrat'],
  'AshtahnikaVrat': ['ashtahnika_ashadha', 'ashtahnika_kartika', 'ashtahnika_phalguna'],
};

String? ruleTypeOf(String id) {
  final entry = registry.entries.where((e) => e.id == id).firstOrNull;
  if (entry != null) return entry.ruleType;
  return emittedIds.entries.where((e) => e.value.hasMatch(id)).firstOrNull?.key;
}

String rowKey(Map<String, Object?> row) =>
    '${row['start_date']} ${row['occurrence_id']} id=${row['id']} end=${row['end_date']} ${row['status']}';

String occurrenceKey(FestivalOccurrence o) => '${o.start} ${o.occurrenceId} id=${o.id} end=${o.end} ${o.status}';

/// The keys of [from] not matched one for one in [other] (a multiset difference).
List<String> missing(List<String> from, List<String> other) {
  final unmatched = <String, int>{};
  for (final key in other) {
    unmatched.update(key, (n) => n + 1, ifAbsent: () => 1);
  }
  return [
    for (final key in from)
      if (unmatched.update(key, (n) => n - 1, ifAbsent: () => -1) < 0) key,
  ];
}

void main() {
  final ported = portedRuleTypes.toSet();

  for (final loc in coreLocations()) {
    for (final rule in SunriseRule.values) {
      test('${loc.slug} ${rule.name}', () {
        final location = Location(lat: loc.lat, lon: loc.lon, timezone: loc.timezone);
        final fixtures = {
          for (final profile in festivalProfiles)
            profile: readCoreFixture('${loc.slug}/${rule.name}/festivals.$profile.json.gz')['years']!
                as Map<String, Object?>,
        };
        final mismatches = <String>[];
        final boundaryCases = <String>[];
        var compared = 0;

        for (final year in fixtures.values.first.keys.map(int.parse)) {
          final days = festivalDays(location: location, year: year, sunriseRule: rule, amanta: amanta);

          // §6.6 boundary rule: a date may differ only when a reading near it
          // (sunrise, Jain day-start or evening tithi, or the month) lies within
          // 10 s of the transition that decides it.
          bool nearBoundary(String iso) {
            final date = CivilDate.parse(iso);
            for (final (i, d) in days.indexed) {
              if (d.date != date) continue;
              for (final near in days.sublist((i - 2).clamp(0, days.length), (i + 3).clamp(0, days.length))) {
                final reference = near.sunrise + jainTithiOffsetDays;
                for (final x in [near.sunrise, reference, near.sunset]) {
                  if (tithiAt(x - toleranceDays) != tithiAt(x + toleranceDays)) return true;
                }
                if (amanta(reference - toleranceDays) != amanta(reference + toleranceDays)) return true;
              }
            }
            return false;
          }

          for (final profile in festivalProfiles) {
            final rows = (fixtures[profile]!['$year']! as List<Object?>).cast<Map<String, Object?>>();
            final expected = [for (final row in rows) if (ported.contains(ruleTypeOf(row['id']! as String))) rowKey(row)];
            final ours = [
              for (final o in festivalsFromDays(days, year: year, profile: profile, registry: registry)) occurrenceKey(o),
            ];
            compared += expected.length;
            for (final (side, keys) in [('python only', missing(expected, ours)), ('dart only', missing(ours, expected))]) {
              for (final key in keys) {
                final line = '$profile $side: $key';
                (nearBoundary(key.substring(0, 10)) ? boundaryCases : mismatches).add(line);
              }
            }
          }
        }

        print('${loc.slug} ${rule.name}: compared $compared rows of $ported; '
            'boundary cases ${boundaryCases.length} $boundaryCases');
        expect(mismatches, isEmpty);
      });
    }
  }
}
