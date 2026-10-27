/// The engine's one entry point: everything about a civil day at a place.
/// Instants are UTC `DateTime`s; every value is immutable and plain, so a day
/// can be sent between isolates.
library;

import 'astro/rise_set.dart';
import 'calendar/month.dart';
import 'calendar/samvat.dart';
import 'panchang/choghadiya.dart';
import 'panchang/elements.dart';
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
    required this.vikramSamvat,
    required this.viraNirvanaSamvat,
    required this.choghadiya,
    required this.vriddhi,
    required this.kshaya,
    required this.pachchakkhan,
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
  final int vikramSamvat, viraNirvanaSamvat;

  /// Eight day slots from sunrise, then eight night slots from sunset.
  final List<ChoghadiyaPeriod> choghadiya;
  final Vriddhi? vriddhi;
  final Kshaya? kshaya;
  final PachchakkhanDay pachchakkhan;
}

final class PanchangEngine {
  const PanchangEngine();

  /// Throws [StateError] where the Sun does not rise or set that day (polar day or night).
  PanchangDay day({required Location location, required CivilDate date, SunriseRule sunriseRule = SunriseRule.modern}) {
    final Location(:lat, :lon, :timezone) = location;
    double sunriseOf(CivilDate d) => sunrise(civilDayAnchor(d, timezone), lat, lon, sunriseRule);

    final rise = sunriseOf(date);
    final set = sunset(civilDayAnchor(date, timezone), lat, lon, sunriseRule);
    final nextRise = sunriseOf(date.next());
    final reference = rise + jainTithiOffsetDays;
    final previousReference = sunriseOf(_previous(date)) + jainTithiOffsetDays;

    final jain = tithiAt(reference);
    final yesterday = tithiAt(previousReference);
    final tomorrow = tithiAt(nextRise + jainTithiOffsetDays);

    final samvats = samvatsOn(date, lat: lat, lon: lon, utcOffset: standardOffset(date, timezone), rule: sunriseRule);
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
      month: purnimantaMonth(reference),
      vikramSamvat: samvats.vikram,
      viraNirvanaSamvat: samvats.viraNirvana,
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
    );
  }
}

DateTime _utc(double jd) => utcFromJulianDay(jd);

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
