/// The engine's one entry point: everything about a civil day at a place.
/// Instants are UTC `DateTime`s; every value is immutable and plain, so a day
/// can be sent between isolates.
library;

import 'astro/rise_set.dart';
import 'astro/sidereal.dart';
import 'calendar/month.dart';
import 'calendar/samvat.dart';
import 'festivals/festivals.dart';
import 'festivals/registry.dart';
import 'panchang/choghadiya.dart';
import 'panchang/day_elements.dart';
import 'panchang/elements.dart';
import 'panchang/day_yogas.dart';
import 'panchang/muhurat.dart';
import 'panchang/pachchakkhan.dart';
import 'time/civil_day.dart';
import 'time/julian_day.dart';

final class Location {
  const Location({required this.lat, required this.lon, required this.timezone});

  final double lat, lon;

  /// An IANA name, such as 'Asia/Kolkata'.
  final String timezone;
}

/// A tithi of the day; [endsAt] is null for the one still holding at the next sunrise.
typedef TithiSpan = ({int index, DateTime? endsAt});

/// The tithi holding at [reference], sunrise + 2 h 24 min: the day's Jain tithi.
typedef JainTithi = ({int index, DateTime startsAt, DateTime endsAt, DateTime reference});

/// The nakshatra and its pada (1-4) at sunrise.
typedef NakshatraReading = ({int index, int pada, DateTime endsAt});

/// A tithi, nakshatra, yoga, karana or Rashi and when it ends.
typedef ElementSpan = ({int index, DateTime endsAt});

/// The Sun's Rashi within a day; [endsAt] is null when it lasts past the next sunrise.
typedef RashiSpan = ({int index, DateTime? endsAt});

/// The Rashi the Sun is in (0 = Mesha) and the day of its stay, the
/// Sankranti day being day 1.
typedef Gata = ({int rashi, int day});

/// A tithi that holds at no reference instant, lost between yesterday's and today's.
typedef Kshaya = ({int lost, DateTime startsAt, DateTime endsAt});

typedef ChoghadiyaPeriod = ({Choghadiya name, DateTime start, DateTime end, bool isNight});

typedef PachchakkhanAt = ({TimedPachchakkhan kind, DateTime at});

/// Which day of a vriddhi (a Jain tithi holding on two days) this is.
enum Vriddhi { firstDay, secondDay }

/// Where a day's pachchakkhans stand at one instant.
sealed class PachchakkhanPhase {
  const PachchakkhanPhase();
}

/// [kind] may be completed after [at], the first completion still ahead.
final class NextCompletion extends PachchakkhanPhase {
  const NextCompletion(this.kind, this.at);

  final TimedPachchakkhan kind;
  final DateTime at;

  @override
  bool operator ==(Object other) => other is NextCompletion && other.kind == kind && other.at == at;

  @override
  int get hashCode => Object.hash(kind, at);
}

/// Every completion has passed; the evening pachchakkhan is due before [at].
final class EveningDeadline extends PachchakkhanPhase {
  const EveningDeadline(this.at);

  final DateTime at;

  @override
  bool operator ==(Object other) => other is EveningDeadline && other.at == at;

  @override
  int get hashCode => at.hashCode;
}

/// The day is over; the next is the parana at [parana].
final class AllDone extends PachchakkhanPhase {
  const AllDone(this.parana);

  final DateTime parana;

  @override
  bool operator ==(Object other) => other is AllDone && other.parana == parana;

  @override
  int get hashCode => parana.hashCode;
}

final class PachchakkhanDay {
  const PachchakkhanDay({required this.completions, required this.evening, required this.parana});

  /// The five completion times in order; each may be completed from its instant on.
  final List<PachchakkhanAt> completions;

  /// Chauvihar, Tivihar and Duvihar must be taken before this instant: sunset.
  final DateTime evening;

  /// The next day's Navkarsi: when an Ayambil or Upvas may be completed.
  final DateTime parana;

  PachchakkhanPhase phaseAt(DateTime now) {
    for (final c in completions) {
      if (c.at.isAfter(now)) return NextCompletion(c.kind, c.at);
    }
    return evening.isAfter(now) ? EveningDeadline(evening) : AllDone(parana);
  }
}

final class PanchangDay {
  const PanchangDay({
    required this.date,
    required this.sunrise,
    required this.sunset,
    required this.nextSunrise,
    required this.tithis,
    required this.jainTithi,
    required this.nakshatra,
    required this.vara,
    required this.month,
    required this.amantaMonth,
    required this.vikramSamvat,
    required this.viraNirvanaSamvat,
    required this.choghadiya,
    required this.vriddhi,
    required this.kshaya,
    required this.pachchakkhan,
    required this.shakaSamvat,
  });

  final CivilDate date;
  final DateTime sunrise, sunset, nextSunrise;
  final List<TithiSpan> tithis;
  final JainTithi jainTithi;
  final NakshatraReading nakshatra;

  /// 0 = Sunday.
  final int vara;

  /// The Purnimanta month at the Jain reference instant.
  final LunarMonth month;

  /// The Amanta month at the same instant: the same as [month] in a Shukla
  /// paksha, the month before it in a Krishna paksha.
  final LunarMonth amantaMonth;
  final int vikramSamvat, viraNirvanaSamvat;

  /// Eight day slots from sunrise, then eight night slots from sunset.
  final List<ChoghadiyaPeriod> choghadiya;
  final Vriddhi? vriddhi;
  final Kshaya? kshaya;
  final PachchakkhanDay pachchakkhan;

  final int shakaSamvat;
}

/// The Panchang section's readings for a day, beyond [PanchangDay]: a
/// separate read, so the Month tab's [PanchangEngine.month] does not pay for
/// them (they double a day's cost).
final class PanchangSection {
  const PanchangSection({
    required this.nextTithi,
    required this.nextNakshatra,
    required this.yogas,
    required this.karanas,
    required this.moonRashis,
    required this.sunRashis,
    required this.gata,
  });

  /// The tithi after the Jain tithi, until its own end (which may be after
  /// the next sunrise).
  final ElementSpan nextTithi;

  /// The nakshatra after the one at sunrise.
  final ElementSpan nextNakshatra;

  /// The yoga (1-27) at sunrise, then the next.
  final List<ElementSpan> yogas;

  /// Every karana (1-60) from sunrise up to the one holding at the next
  /// sunrise: two to four.
  final List<ElementSpan> karanas;

  /// The Moon's Rashi (0 = Mesha) at sunrise, then the next.
  final List<ElementSpan> moonRashis;

  /// The Sun's Rashi, and on a Sankranti day the one it enters.
  final List<RashiSpan> sunRashis;
  final Gata gata;
}

typedef TimeWindow = ({DateTime start, DateTime end});

/// Today's Panchak [window] and its whole [period], or, on a day without
/// Panchak, the [nextPeriod].
typedef PanchakReading = ({TimeWindow? window, TimeWindow? period, TimeWindow? nextPeriod});

/// A Vishti karana window, cut at a Moon Rashi change (0 = Mesha).
typedef BhadraWindow = ({DateTime start, DateTime end, int moonRashi, BhadraResidence residence});

/// The Moon in a junction nakshatra (1-27).
typedef GandmoolWindow = ({DateTime start, DateTime end, int nakshatra});

/// The Moon's Rashi until [endsAt] (null: past the next sunrise), and the
/// six birth [rashis] with Chandra Bal in it.
typedef ChandraBalSpan = ({int moonRashi, DateTime? endsAt, List<int> rashis});

/// One of the day's yogas. [isNullified]: an inauspicious yoga a supreme
/// yoga overlaps; [cancelled]: Dusht Tithi on a Sarvartha Siddhi day;
/// [diminished]: Amrit Siddhi under an active Dusht Tithi; [varjya]: the
/// part of an Aanandadi yoga to avoid, from its start.
typedef DayYoga = ({
  DayYogaKind kind,
  String name,
  YogaNature nature,
  DateTime start,
  DateTime end,
  bool isNullified,
  bool cancelled,
  bool diminished,
  TimeWindow? varjya,
});

/// The Muhurat section's readings for a day: a separate read, as
/// [PanchangSection] is, so neither [PanchangEngine.day] nor
/// [PanchangEngine.month] pays for them.
final class PanchangMuhurat {
  const PanchangMuhurat({
    required this.rahuKaal,
    required this.yamaganda,
    required this.gulika,
    required this.abhijit,
    required this.panchak,
    required this.bhadra,
    required this.gandmool,
    required this.chandraBal,
    required this.agniVaas,
    required this.yogas,
  });

  /// Each one eighth of the daylight, by weekday.
  final TimeWindow rahuKaal, yamaganda, gulika;

  /// The 8th of the 15 daylight muhurtas.
  final TimeWindow abhijit;
  final PanchakReading panchak;
  final List<BhadraWindow> bhadra;
  final List<GandmoolWindow> gandmool;

  /// One span, or two when the Moon changes Rashi before the next sunrise.
  final List<ChandraBalSpan> chandraBal;

  /// From the tithi at sunrise and the weekday.
  final AgniVaas agniVaas;

  /// Dainika, then Aanandadi (one per Moon nakshatra), Ravi and Jwalamukhi.
  final List<DayYoga> yogas;
}

final class PanchangEngine {
  const PanchangEngine();

  /// Throws [StateError] where the Sun does not rise or set that day (polar day or night).
  PanchangDay day({required Location location, required CivilDate date, SunriseRule sunriseRule = SunriseRule.modern}) {
    final Location(:lat, :lon, :timezone) = location;
    return _read(
      date,
      location: location,
      sunriseRule: sunriseRule,
      sunriseOf: (d) => sunrise(civilDayAnchor(d, timezone), lat, lon, sunriseRule),
      amanta: amantaMonth,
      samvats: (d, {required utcOffset}) => samvatsOn(d, lat: lat, lon: lon, utcOffset: utcOffset, rule: sunriseRule),
    );
  }

  /// Every day of a Gregorian month, each exactly as [day] reads it. The month
  /// names its lunar months once, computes each sunrise once and searches each
  /// new year and Diwali once, which a run of [day] calls repeats per date.
  List<PanchangDay> month({
    required Location location,
    required int year,
    required int month,
    SunriseRule sunriseRule = SunriseRule.modern,
  }) {
    final Location(:lat, :lon, :timezone) = location;
    final dates = [for (var d = CivilDate(year, month, 1); d.month == month; d = d.next()) d];
    final rises = {
      for (final d in [_previous(dates.first), ...dates, dates.last.next()])
        d: sunrise(civilDayAnchor(d, timezone), lat, lon, sunriseRule),
    };
    // A Krishna paksha is named from the month 17 days on (purnimantaMonth).
    final lunarMonths = lunarMonthsBetween(
      rises[_previous(dates.first)]! + jainTithiOffsetDays,
      rises[dates.last.next()]! + jainTithiOffsetDays + 18,
    );
    final amanta = amantaLookup(lunarMonths);
    final samvats = samvatReader(lat: lat, lon: lon, rule: sunriseRule);
    return [
      for (final date in dates)
        _read(
          date,
          location: location,
          sunriseRule: sunriseRule,
          sunriseOf: (d) => rises[d]!,
          amanta: amanta,
          samvats: samvats,
        ),
    ];
  }

  PanchangDay _read(
    CivilDate date, {
    required Location location,
    required SunriseRule sunriseRule,
    required double Function(CivilDate) sunriseOf,
    required LunarMonth Function(double) amanta,
    required Samvats Function(CivilDate, {required Duration utcOffset}) samvats,
  }) {
    final Location(:lat, :lon, :timezone) = location;
    final rise = sunriseOf(date);
    final set = sunset(civilDayAnchor(date, timezone), lat, lon, sunriseRule);
    final nextRise = sunriseOf(date.next());
    final reference = rise + jainTithiOffsetDays;
    final previousReference = sunriseOf(_previous(date)) + jainTithiOffsetDays;

    final jain = tithiAt(reference);
    final yesterday = tithiAt(previousReference);
    final tomorrow = tithiAt(nextRise + jainTithiOffsetDays);

    final samvat = samvats(date, utcOffset: standardOffset(date, timezone));
    final times = pachchakkhanTimes(sunrise: rise, sunset: set, nextSunrise: nextRise);

    return PanchangDay(
      date: date,
      sunrise: _utc(rise),
      sunset: _utc(set),
      nextSunrise: _utc(nextRise),
      tithis: [
        for (final t in dayTithis(rise, nextRise)) (index: t.index, endsAt: t.endsAt == null ? null : _utc(t.endsAt!)),
      ],
      jainTithi: (
        index: jain,
        startsAt: _utc(_startOf(jain, before: reference)),
        endsAt: _utc(tithiEnd(reference)),
        reference: _utc(reference),
      ),
      nakshatra: (index: nakshatraAt(rise), pada: nakshatraPadaAt(rise), endsAt: _utc(nakshatraEnd(rise))),
      vara: date.vara,
      month: purnimantaMonth(reference, amanta: amanta),
      amantaMonth: amanta(reference),
      vikramSamvat: samvat.vikram,
      viraNirvanaSamvat: samvat.viraNirvana,
      choghadiya: [
        for (final s in choghadiyaSlots(sunrise: rise, sunset: set, nextSunrise: nextRise, vara: date.vara))
          (name: s.name, start: _utc(s.start), end: _utc(s.end), isNight: s.isNight),
      ],
      vriddhi: yesterday == jain ? Vriddhi.secondDay : (tomorrow == jain ? Vriddhi.firstDay : null),
      kshaya: _kshaya(yesterday: yesterday, today: jain, previousReference: previousReference),
      pachchakkhan: PachchakkhanDay(
        completions: [for (final c in times.completions) (kind: c.kind, at: _utc(c.at))],
        evening: _utc(times.evening),
        parana: _utc(times.parana),
      ),
      // Both eras turn over on Chaitra Shukla Pratipada: Shaka 1 is Vikram 136.
      shakaSamvat: samvat.vikram - 135,
    );
  }

  /// The Panchang section for [date]: Throws [StateError] where [day] does.
  PanchangSection section({
    required Location location,
    required CivilDate date,
    SunriseRule sunriseRule = SunriseRule.modern,
  }) {
    final Location(:lat, :lon, :timezone) = location;
    double sunriseAfter(double jd) => sunrise(jd, lat, lon, sunriseRule);
    final rise = sunriseAfter(civilDayAnchor(date, timezone));
    final nextRise = sunriseAfter(civilDayAnchor(date.next(), timezone));
    return PanchangSection(
      nextTithi: _spans(pairFrom(rise + jainTithiOffsetDays, tithiAt, tithiEnd)).last,
      nextNakshatra: _spans(pairFrom(rise, nakshatraAt, nakshatraEnd)).last,
      yogas: _spans(pairFrom(rise, yogaAt, yogaEnd)),
      karanas: _spans(dayKaranas(rise, nextRise)),
      moonRashis: _spans(pairFrom(rise, moonRashiAt, moonRashiEnd)),
      sunRashis: [
        for (final s in daySunRashis(rise, nextRise))
          (index: s.index, endsAt: s.endsAt == null ? null : _utc(s.endsAt!)),
      ],
      gata: gataOf(nextRise, sunriseAfter: sunriseAfter),
    );
  }

  /// The Muhurat section for [date]. Throws [StateError] where [day] does.
  PanchangMuhurat muhurat({
    required Location location,
    required CivilDate date,
    SunriseRule sunriseRule = SunriseRule.modern,
  }) {
    final Location(:lat, :lon, :timezone) = location;
    final rise = sunrise(civilDayAnchor(date, timezone), lat, lon, sunriseRule);
    final set = sunset(civilDayAnchor(date, timezone), lat, lon, sunriseRule);
    final nextRise = sunrise(civilDayAnchor(date.next(), timezone), lat, lon, sunriseRule);
    final panchak = panchakOf(rise, nextRise);
    final nakshatras = daySegments(rise, nextRise, nakshatraAt, nakshatraEnd);
    return PanchangMuhurat(
      rahuKaal: _window(rahuKaal(rise, set, date.vara)),
      yamaganda: _window(yamaganda(rise, set, date.vara)),
      gulika: _window(gulika(rise, set, date.vara)),
      abhijit: _window(abhijit(rise, set)),
      panchak: (
        window: _maybeWindow(panchak.window),
        period: _maybeWindow(panchak.period),
        nextPeriod: _maybeWindow(panchak.nextPeriod),
      ),
      bhadra: [
        for (final b in bhadraOf(rise, nextRise))
          (start: _utc(b.start), end: _utc(b.end), moonRashi: b.moonRashi, residence: bhadraResidenceOf(b.moonRashi)),
      ],
      gandmool: [
        for (final g in gandmoolOf(nakshatras)) (start: _utc(g.start), end: _utc(g.end), nakshatra: g.nakshatra),
      ],
      chandraBal: [
        for (final c in chandraBalSpans(rise, nextRise))
          (
            moonRashi: c.moonRashi,
            endsAt: c.endsAt == null ? null : _utc(c.endsAt!),
            rashis: chandraBalRashis(c.moonRashi),
          ),
      ],
      agniVaas: agniVaasOf(tithiAt(rise), date.vara),
      yogas: [
        for (final y in dayYogas(
          vara: date.vara,
          tithis: daySegments(rise, nextRise, tithiAt, tithiEnd),
          nakshatras: nakshatras,
          sunNakshatra: nakshatraOf(siderealSunLongitude(rise)),
        ))
          (
            kind: y.kind,
            name: y.name,
            nature: y.nature,
            start: _utc(y.start),
            end: _utc(y.end),
            isNullified: y.isNullified,
            cancelled: y.cancelled,
            diminished: y.diminished,
            varjya: _maybeWindow(y.varjya),
          ),
      ],
    );
  }

  /// The festivals whose first day falls in [year], sorted by date. Throws
  /// [ArgumentError] for a profile not in [festivalProfiles].
  List<FestivalOccurrence> festivals({
    required Location location,
    required int year,
    required String profile,
    required FestivalRegistry registry,
    SunriseRule sunriseRule = SunriseRule.modern,
  }) => festivalsOf(location: location, year: year, profile: profile, registry: registry, sunriseRule: sunriseRule);
}

DateTime _utc(double jd) => utcFromJulianDay(jd);

TimeWindow _window(JdWindow w) => (start: _utc(w.start), end: _utc(w.end));
TimeWindow? _maybeWindow(JdWindow? w) => w == null ? null : _window(w);

List<ElementSpan> _spans(List<Span> spans) => [for (final s in spans) (index: s.index, endsAt: _utc(s.endsAt))];

/// Past a transition, so a solver started here finds the next one.
const double _nudgeDays = 30 / 86400;

/// A tithi lasts under 27 hours, so the one holding this long before an
/// instant has always ended by then.
const double _longestTithiDays = 1.2;

CivilDate _previous(CivilDate date) {
  final day = DateTime.utc(date.year, date.month, date.day - 1);
  return CivilDate(day.year, day.month, day.day);
}

/// When the [tithi] holding at [before] began.
double _startOf(int tithi, {required double before}) {
  var change = tithiEnd(before - _longestTithiDays);
  while (tithiAt(change + _nudgeDays) != tithi) {
    change = tithiEnd(change + _nudgeDays);
  }
  return change;
}

Kshaya? _kshaya({required int yesterday, required int today, required double previousReference}) {
  final lost = yesterday % 30 + 1;
  if (today != lost % 30 + 1) return null;
  final starts = tithiEnd(previousReference);
  return (lost: lost, startsAt: _utc(starts), endsAt: _utc(tithiEnd(starts + _nudgeDays)));
}
