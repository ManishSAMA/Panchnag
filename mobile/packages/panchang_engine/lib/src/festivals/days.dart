/// The daily readings festival rules choose their days from (Python
/// `festival_service._build_snapshots`).
library;

import '../astro/rise_set.dart';
import '../calendar/month.dart';
import '../day.dart';
import '../panchang/elements.dart';
import '../time/civil_day.dart';

/// One civil day as the festival rules see it. Tithis are 1-30; 1-15 Shukla.
final class FestivalDay {
  const FestivalDay({
    required this.date,
    required this.sunrise,
    required this.sunset,
    required this.sunriseTithi,
    required this.jainTithi,
    required this.eveningTithi,
    required this.month,
    required this.purnimantaMonth,
    required this.standardOffset,
  });

  final CivilDate date;

  /// UT Julian Days.
  final double sunrise, sunset;

  /// At sunrise (udaya). Python keeps it private (`_sunrise_tithi`): only the
  /// 6-ghati pull-back and Kalyanak day selection may compare against it.
  final int sunriseTithi;

  /// At the Jain day-start, sunrise + 2 h 24 min: the day's public tithi.
  final int jainTithi;

  /// At sunset, for pradosh-vyapini observances.
  final int eveningTithi;

  /// The Amanta month at the Jain day-start (Python `hindu_month` + `is_adhika`).
  final LunarMonth month;

  /// Python `purnimanta_month` + `purnimanta_is_adhika`, see [festivalDays].
  final LunarMonth purnimantaMonth;

  /// The zone's standard UTC offset on [date]: the clock Python's vrat
  /// providers read local times on.
  final Duration standardOffset;
}

/// Readings for every civil day from 1 Dec of `year - 1` to 31 Jan of
/// `year + 1`, the window Python resolves a year's festivals in. [amanta] lets a
/// caller that already named the months share them.
List<FestivalDay> festivalDays({
  required Location location,
  required int year,
  required SunriseRule sunriseRule,
  LunarMonth Function(double)? amanta,
}) {
  final Location(:lat, :lon, :timezone) = location;
  final dates = [
    for (var d = CivilDate(year - 1, 12, 1); d.compareTo(CivilDate(year + 1, 2, 1)) < 0; d = d.next()) d,
  ];
  final anchors = [for (final d in dates) civilDayAnchor(d, timezone)];
  final monthAt = amanta ?? amantaLookup(lunarMonthsBetween(anchors.first, anchors.last + 2));

  final readings = [
    for (final (i, date) in dates.indexed)
      () {
        final rise = sunrise(anchors[i], lat, lon, sunriseRule);
        final set = sunset(anchors[i], lat, lon, sunriseRule);
        final reference = rise + jainTithiOffsetDays;
        return (
          date: date,
          sunrise: rise,
          sunset: set,
          sunriseTithi: tithiAt(rise),
          jainTithi: tithiAt(reference),
          eveningTithi: tithiAt(set),
          month: monthAt(reference),
          standardOffset: standardOffset(date, timezone),
        );
      }(),
  ];

  final purnimanta = _purnimantaMonths([for (final r in readings) (shukla: r.jainTithi <= 15, month: r.month)]);
  return [
    for (final (i, r) in readings.indexed)
      FestivalDay(
        date: r.date,
        sunrise: r.sunrise,
        sunset: r.sunset,
        sunriseTithi: r.sunriseTithi,
        jainTithi: r.jainTithi,
        eveningTithi: r.eveningTithi,
        month: r.month,
        purnimantaMonth: purnimanta[i],
        standardOffset: r.standardOffset,
      ),
  ];
}

const Set<String> _vratCategories = {'vrat', 'monthly_vrat', 'tap_vrat', 'parva_vrat', 'mahaparv_vrat'};

/// Vrats that keep their own vriddhi rule (Python `KEEPS_OWN_VRIDDHI_RULE`):
/// Karma Nirjara keeps the first day, the Ashtahnika markers follow the
/// Ashtahnika span, the Ravi vrats are bound to Sunday, and Gyan + Labh Panchami
/// keep their documented first Panchami.
const Set<String> _keepsOwnVriddhiRule = {
  'karma_nirjara_vrat', 'kartika_nandishwar_ashtami', 'kartika_purnima_ashtahnika_purna',
  'phalguna_purnima_ashtahnika_purna', 'ravi_vrat', 'ravivara', 'kartika_shukla_panchami',
};

/// Whether an observance follows वृद्धौ कार्या तथोत्तरा and so reads [vratView].
/// Kalyanaks keep the first day and parva tithis show on both, so neither is a vrat category.
bool takesSecondDayOfVriddhi(String ruleId, String category) =>
    _vratCategories.contains(category) && !_keepsOwnVriddhiRule.contains(ruleId);

/// The days as vrat rules read them: वृद्धौ कार्या तथोत्तरा (Python
/// `vrat_view_of_snapshots`). When a tithi holds the Jain day-start on two
/// consecutive days, the first reads as the preceding tithi, so a vrat lands on
/// the second. It takes the months of the day before when that day holds the
/// preceding tithi; the sunrise and evening tithis stay as computed.
List<FestivalDay> vratView(List<FestivalDay> days) => [
  for (final (i, day) in days.indexed)
    if (i + 1 < days.length && days[i + 1].jainTithi == day.jainTithi)
      _asPreviousTithi(day, before: i > 0 ? days[i - 1] : null)
    else
      day,
];

FestivalDay _asPreviousTithi(FestivalDay day, {required FestivalDay? before}) {
  final previous = (day.jainTithi + 28) % 30 + 1;
  final months = before != null && before.jainTithi == previous ? before : day;
  return FestivalDay(
    date: day.date,
    sunrise: day.sunrise,
    sunset: day.sunset,
    sunriseTithi: day.sunriseTithi,
    jainTithi: previous,
    eveningTithi: day.eveningTithi,
    month: months.month,
    purnimantaMonth: months.purnimantaMonth,
    standardOffset: day.standardOffset,
  );
}

/// Python `_assign_purnimanta`: a paksha's Purnimanta month is the month of the
/// Shukla paksha that ends at its Purnima. A Krishna day takes the next Shukla
/// day's Amanta month and Adhik flag, which inverts the flag in an Adhik year;
/// Krishna days after the last Shukla day take the following month's name.
List<LunarMonth> _purnimantaMonths(List<({bool shukla, LunarMonth month})> days) {
  LunarMonth? nextShukla;
  final reversed = [
    for (final day in days.reversed)
      if (day.shukla)
        nextShukla = day.month
      else
        nextShukla ?? LunarMonth(index: (day.month.index + 1) % 12, isAdhika: day.month.isAdhika),
  ];
  return reversed.reversed.toList();
}
