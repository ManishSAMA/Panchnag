/// Family B (plans/mobile-phase5-festivals.md §3): festivals with one anchor
/// day in a named month and a fixed list of events on it. Each Python rule is
/// its own class (`ShravanaPurnimaRakshabandhanFestival`, `BhaiDoojFestival`,
/// ...); the shared shape is ported once, as a table, and the four that differ
/// are written out.
library;

import '../../time/civil_day.dart';
import '../days.dart';
import '../festivals.dart';
import '../primitives.dart';
import '../registry.dart';

const String _shukla = 'Shukla';
const String _krishna = 'Krishna';

/// Which reading names a day's month: Python `hindu_month` (Amanta) or
/// `get_jain_month` (Purnimanta). A Krishna tithi named the Purnimanta way sits
/// in the Amanta month before.
enum _Named { amanta, purnimanta }

/// An event on the anchor day: its id is `<prefix>_<year>`.
typedef _Event = (String prefix, String category);

final class _Anchor {
  const _Anchor(
    this.named,
    this.month,
    this.paksha,
    this.tithi, {
    required this.secondOnVriddhi,
    required this.fallback,
    required this.events,
  });

  final _Named named;
  final int month;
  final String paksha;
  final int tithi;

  /// Python's "Vriddhi -> 2nd" rules (the Purnimas and the Chaitra Varsha-ant).
  final bool secondOnVriddhi;

  /// The tithi whose last day stands in on a kshaya.
  final (String, int) fallback;

  final List<_Event> events;
}

const Map<String, _Anchor> _anchors = {
  'ShravanaPurnimaRakshabandhan': _Anchor(_Named.amanta, 4, _shukla, 15,
      secondOnVriddhi: true,
      fallback: (_shukla, 14),
      events: [
        ('rakshabandhan_700_muni_raksha_divas', 'mahaparv'),
        ('muni_vishnukumar_akampanacharya_pujan', 'poojan'),
        ('sorana_pujan', 'parv_vidhi'),
      ]),
  'PhalgunaPurnimaAshtahnikaPurna': _Anchor(_Named.amanta, 11, _shukla, 15,
      secondOnVriddhi: true,
      fallback: (_shukla, 14),
      events: [
        ('phalguna_ashtahnika_purna', 'mahaparv_vrat'),
        ('holika_dahan', 'utsav'),
        ('phalguna_purnima_vasantotsav', 'mahaparv'),
      ]),
  'MaghaShuklaPanchamiTri': _Anchor(_Named.amanta, 10, _shukla, 5,
      secondOnVriddhi: false,
      fallback: (_shukla, 4),
      events: [
        ('acharya_kundakunda_jayanti', 'jayanti'),
        ('jina_murti_sthapna', 'auspicious'),
        ('vasant_panchami_shrut', 'shastra'),
      ]),
  'TalaDharTapShantisagarPunyatithi': _Anchor(_Named.amanta, 5, _shukla, 2,
      secondOnVriddhi: false,
      fallback: (_shukla, 1),
      events: [('acharya_shantisagar_punyatithi', 'punyatithi'), ('tala_dhar_tap', 'tap_vrat')]),
  'BadiPanchamiMeruSthapana': _Anchor(_Named.amanta, 5, _shukla, 5,
      secondOnVriddhi: false,
      fallback: (_shukla, 4),
      events: [('badi_panchami', 'mahaparv'), ('meru_sthapana', 'parv_vidhi')]),
  'NihshalyaAshtamiManchinTithi': _Anchor(_Named.amanta, 5, _shukla, 8,
      secondOnVriddhi: false,
      fallback: (_shukla, 7),
      events: [('nihshalya_ashtami_vrat', 'vrat'), ('manchin_tithi_ashtami', 'parv_vidhi')]),
  'SugandhDashami': _Anchor(_Named.amanta, 5, _shukla, 10,
      secondOnVriddhi: false,
      fallback: (_shukla, 9),
      events: [('sugandh_dashami_mahaparv', 'mahaparv'), ('sugandh_dashami_vrat', 'vrat')]),
  'GyanDhanTrayodashi': _Anchor(_Named.purnimanta, 7, _krishna, 13,
      secondOnVriddhi: false,
      fallback: (_krishna, 12),
      events: [('gyan_trayodashi', 'mahaparv_vrat'), ('dhan_teras', 'mahaparv')]),
  'KartikaAmavasyaMahaviraNirvana': _Anchor(_Named.purnimanta, 7, _krishna, 15,
      secondOnVriddhi: false,
      fallback: (_krishna, 14),
      events: [('mahavira_nirvana_kalyanak', 'mahaparv'), ('varsha_yog_nishthapan', 'mahaparv')]),
  'KartikaShuklaEkamNewYear': _Anchor(_Named.purnimanta, 7, _shukla, 1,
      secondOnVriddhi: false,
      fallback: (_krishna, 15),
      events: [('jain_new_year', 'mahaparv'), ('gautam_swami_kevalgyan', 'mahaparv')]),
  'KartikaShuklaPanchami': _Anchor(_Named.amanta, 7, _shukla, 5,
      secondOnVriddhi: false,
      fallback: (_shukla, 4),
      events: [('gyan_panchami', 'mahaparv_vrat'), ('labh_panchami', 'mahaparv')]),
  'KartikaPurnimaAshtahnikaPurna': _Anchor(_Named.amanta, 7, _shukla, 15,
      secondOnVriddhi: true,
      fallback: (_shukla, 14),
      events: [('kartika_ashtahnika_purna', 'mahaparv_vrat'), ('kartika_purnima_dev_deepavali', 'mahaparv')]),
  'JeevDayaAshtami': _Anchor(_Named.amanta, 6, _shukla, 8,
      secondOnVriddhi: false, fallback: (_shukla, 7), events: [('jeev_daya_ashtami', 'mahaparv_vrat')]),
  'KartikaNandishwarAshtami': _Anchor(_Named.amanta, 7, _shukla, 8,
      secondOnVriddhi: false, fallback: (_shukla, 7), events: [('nandishwar_ashtami_kartika', 'mahaparv_vrat')]),
  'BhaiDooj': _Anchor(_Named.amanta, 7, _shukla, 2,
      secondOnVriddhi: false, fallback: (_shukla, 1), events: [('bhai_dooj', 'mahaparv')]),
  'MargashirshaSheetalnathStotram': _Anchor(_Named.amanta, 8, _shukla, 9,
      secondOnVriddhi: false, fallback: (_shukla, 8), events: [('sheetalnath_stotram_rachna', 'mahaparv')]),
  'ChaitraAmavasyaKalyanakVarshant': _Anchor(_Named.purnimanta, 0, _krishna, 15,
      secondOnVriddhi: true, fallback: (_krishna, 14), events: [('vikram_samvat_varshant', 'auspicious')]),
};

/// Every family B rule type, by registry `rule_type`.
final Map<String, FestivalRule> anchoredRules = {
  for (final MapEntry(:key, :value) in _anchors.entries) key: _tabled(value),
  'AkshayaTritiya': _akshayaTritiya,
  'DiwaliChaturmasNishthapan': _diwaliChaturmasNishthapan,
  'VeerShasanJayanti': _veerShasanJayanti,
  'SplitDayAhoiKarwaDampatya': _karwaAhoiDampatya,
};

FestivalRule _tabled(_Anchor anchor) => (entry, days, {required year}) {
  final month = _monthInYear(days, year, anchor.month, anchor.named);
  final date = _udayaDay(month, anchor.paksha, anchor.tithi, second: anchor.secondOnVriddhi, fallback: anchor.fallback);
  return [
    if (date != null)
      for (final (prefix, category) in anchor.events) _occurrence(entry, '${prefix}_$year', category, date),
  ];
};

List<FestivalDay> _monthInYear(List<FestivalDay> days, int year, int month, _Named named) => switch (named) {
  _Named.amanta => amantaMonthInYear(days, year, month),
  _Named.purnimanta => purnimantaMonthInYear(days, year, month),
};

/// The first (or [second]: last) day whose Jain day-start holds the tithi; on a
/// kshaya the last day of [fallback].
CivilDate? _udayaDay(List<FestivalDay> month, String paksha, int tithi,
    {required bool second, required (String, int) fallback}) {
  final holding = month.where((d) => holds(d, Reading.jain, paksha, tithi));
  final (fallbackPaksha, fallbackTithi) = fallback;
  return (second ? holding.lastOrNull : holding.firstOrNull)?.date ??
      month.where((d) => holds(d, Reading.jain, fallbackPaksha, fallbackTithi)).lastOrNull?.date;
}

/// Vaishakha Shukla 3. Python runs the first Tritiya through the 6-ghati
/// pull-back, but that day holds Tritiya at the Jain day-start by construction,
/// so the pull-back never moves it and is left out here.
List<FestivalOccurrence> _akshayaTritiya(FestivalEntry entry, List<FestivalDay> days, {required int year}) {
  final date = _udayaDay(amantaMonthInYear(days, year, 1), _shukla, 3, second: false, fallback: (_shukla, 2));
  return [if (date != null) _occurrence(entry, '${entry.id}_$year', 'mahaparv', date)];
}

/// Purnimanta Kartika Amavasya: Diwali on its last pradosh (sunset) day,
/// Chaturmas Nishthapan on its last udaya day; on a kshaya, the last Krishna 14
/// for both.
List<FestivalOccurrence> _diwaliChaturmasNishthapan(FestivalEntry entry, List<FestivalDay> days, {required int year}) {
  final month = purnimantaMonthInYear(days, year, 7);
  final nishthapan = _udayaDay(month, _krishna, 15, second: true, fallback: (_krishna, 14));
  if (nishthapan == null) return const [];
  final diwali = pradoshDays(month, 15, _krishna).lastOrNull?.date ?? nishthapan;
  return [
    _occurrence(entry, '${entry.id}_$year', 'mahaparv', diwali),
    _occurrence(entry, 'chaturmas_nishthapan_$year', 'mahaparv', nishthapan),
  ];
}

/// Purnimanta Shravana Krishna 1. Its kshaya fallback reaches outside the
/// month, to the last non-Adhik Amanta Ashadha Purnima of the year.
List<FestivalOccurrence> _veerShasanJayanti(FestivalEntry entry, List<FestivalDay> days, {required int year}) {
  final month = purnimantaMonthInYear(days, year, 4);
  if (month.isEmpty) return const [];
  final ashadhaPurnima = days.where((d) =>
      d.date.year == year && d.month.index == 3 && !d.month.isAdhika && holds(d, Reading.jain, _shukla, 15));
  final date =
      month.where((d) => holds(d, Reading.jain, _krishna, 1)).firstOrNull?.date ?? ashadhaPurnima.lastOrNull?.date;
  return [
    if (date != null) ...[
      _occurrence(entry, 'veer_shasan_jayanti_$year', 'jayanti', date),
      _occurrence(entry, 'shrut_udbhav_divas_$year', 'mahaparv', date),
    ],
  ];
}

/// Purnimanta Kartika Krishna: Karwa Chauth on Krishna 4 (udaya), Ahoi Ashtami
/// on the first pradosh Krishna 8 (Krishna 7 on a kshaya). Python puts
/// Dampatya Ashtami on the Ahoi day too, though its comments call it udaya.
List<FestivalOccurrence> _karwaAhoiDampatya(FestivalEntry entry, List<FestivalDay> days, {required int year}) {
  final month = purnimantaMonthInYear(days, year, 7);
  final karwa = _udayaDay(month, _krishna, 4, second: false, fallback: (_krishna, 3));
  final ahoi = [...pradoshDays(month, 8, _krishna), ...pradoshDays(month, 7, _krishna)].firstOrNull?.date;
  return [
    if (karwa != null) _occurrence(entry, 'karwa_chauth_$year', 'vrat', karwa),
    if (ahoi != null) ...[
      _occurrence(entry, 'ahoi_ashtami_$year', 'vrat', ahoi),
      _occurrence(entry, 'dampatya_ashtami_$year', 'vrat', ahoi),
    ],
  ];
}

FestivalOccurrence _occurrence(FestivalEntry entry, String id, String category, CivilDate date) => FestivalOccurrence(
  id: id,
  occurrenceId: id,
  ruleId: entry.id,
  category: category,
  name: entry.name,
  nameHindi: entry.nameHindi,
  start: date,
  end: date,
);
