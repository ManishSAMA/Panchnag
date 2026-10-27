/// Everything Today shows about one civil day, read from the Dart engine.
///
/// The only place the app reaches into the engine's `src/` modules for a day;
/// the M4 `PanchangEngine.day` façade replaces it (plans/mobile-phase2-dart-engine.md).
library;

import 'package:panchang_engine/src/astro/rise_set.dart';
import 'package:panchang_engine/src/calendar/month.dart';
import 'package:panchang_engine/src/calendar/samvat.dart';
import 'package:panchang_engine/src/panchang/elements.dart';
import 'package:panchang_engine/src/panchang/pachchakkhan.dart';
import 'package:panchang_engine/src/time/civil_day.dart';
import 'package:panchang_engine/src/time/julian_day.dart';

/// Plain values only, so a request can cross into a background isolate.
final class DayRequest {
  const DayRequest({
    required this.date,
    required this.lat,
    required this.lon,
    required this.timezone,
    this.rule = SunriseRule.modern,
  });

  final CivilDate date;
  final double lat;
  final double lon;
  final String timezone;
  final SunriseRule rule;

  @override
  bool operator ==(Object other) =>
      other is DayRequest &&
      other.date == date &&
      other.lat == lat &&
      other.lon == lon &&
      other.timezone == timezone &&
      other.rule == rule;

  @override
  int get hashCode => Object.hash(date, lat, lon, timezone, rule);
}

/// Which day of a vriddhi (a Jain tithi holding on two days) this is.
enum Vriddhi { firstDay, secondDay }

/// A tithi that holds at no reference instant, lost between yesterday's and today's.
typedef Kshaya = ({int lost, DateTime starts, DateTime ends});

/// A tithi change close to the reference instant: [isStart] when the Jain tithi
/// began shortly before it, otherwise it ends shortly after.
typedef TithiBoundary = ({DateTime at, bool isStart, Duration gap});

typedef PachchakkhanAt = ({TimedPachchakkhan kind, DateTime at});

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

/// How close to the reference instant a tithi change gets a note
/// (mobile-ui-design.md §3.1; a proposal until tied to the parity tolerance).
const Duration boundaryWindow = Duration(minutes: 45);

final class DayReading {
  const DayReading({
    required this.date,
    required this.sunrise,
    required this.sunset,
    required this.nextSunrise,
    required this.reference,
    required this.jainTithi,
    required this.jainTithiEnds,
    required this.month,
    required this.vikramSamvat,
    required this.viraNirvanaSamvat,
    required this.nakshatra,
    required this.nakshatraPada,
    required this.nakshatraEnds,
    required this.vriddhi,
    required this.kshaya,
    required this.boundary,
    required this.pachchakkhan,
    required this.pachchakkhanEvening,
    required this.pachchakkhanParana,
  });

  final CivilDate date;

  /// UTC instants.
  final DateTime sunrise, sunset, nextSunrise;

  /// Sunrise + 6 ghati: the instant the Jain tithi is read at.
  final DateTime reference;
  final int jainTithi;
  final DateTime jainTithiEnds;
  final LunarMonth month;
  final int vikramSamvat, viraNirvanaSamvat;
  final int nakshatra, nakshatraPada;
  final DateTime nakshatraEnds;
  final Vriddhi? vriddhi;
  final Kshaya? kshaya;
  final TithiBoundary? boundary;
  final List<PachchakkhanAt> pachchakkhan;
  final DateTime pachchakkhanEvening;

  /// The next day's Navkarsi: when an Ayambil or Upvas may be completed.
  final DateTime pachchakkhanParana;

  /// The first pachchakkhan still ahead of [now], or null once Avaddh has passed.
  TimedPachchakkhan? nextPachchakkhan(DateTime now) {
    for (final p in pachchakkhan) {
      if (p.at.isAfter(now)) return p.kind;
    }
    return null;
  }

  PachchakkhanPhase pachchakkhanPhase(DateTime now) {
    for (final p in pachchakkhan) {
      if (p.at.isAfter(now)) return NextCompletion(p.kind, p.at);
    }
    return pachchakkhanEvening.isAfter(now) ? EveningDeadline(pachchakkhanEvening) : AllDone(pachchakkhanParana);
  }
}

DateTime _utc(double jd) => utcFromJulianDay(jd);

/// Past a transition, so a solver started here finds the next one.
const double _nudgeDays = 30 / 86400;

CivilDate _previous(CivilDate date) {
  final day = DateTime.utc(date.year, date.month, date.day - 1);
  return CivilDate(day.year, day.month, day.day);
}

DayReading readDay(DayRequest request) {
  final DayRequest(:date, :lat, :lon, :timezone, :rule) = request;
  double sunriseOf(CivilDate d) => sunrise(civilDayAnchor(d, timezone), lat, lon, rule);

  final rise = sunriseOf(date);
  final set = sunset(civilDayAnchor(date, timezone), lat, lon, rule);
  final nextRise = sunriseOf(date.next());
  final reference = rise + jainTithiOffsetDays;
  final previousReference = sunriseOf(_previous(date)) + jainTithiOffsetDays;

  final jain = tithiAt(reference);
  final jainEnds = tithiEnd(reference);
  final yesterday = tithiAt(previousReference);
  final tomorrow = tithiAt(nextRise + jainTithiOffsetDays);

  final offset = standardOffset(date, timezone);
  final chaitraShukla1 = chaitraShuklaPratipada(date.year, lat: lat, lon: lon, utcOffset: offset, rule: rule);
  final diwaliDay = diwali(date.year, lat: lat, lon: lon, utcOffset: offset, rule: rule);
  final times = pachchakkhanTimes(sunrise: rise, sunset: set, nextSunrise: nextRise);

  return DayReading(
    date: date,
    sunrise: _utc(rise),
    sunset: _utc(set),
    nextSunrise: _utc(nextRise),
    reference: _utc(reference),
    jainTithi: jain,
    jainTithiEnds: _utc(jainEnds),
    month: purnimantaMonth(reference),
    vikramSamvat: vikramSamvat(date, chaitraShukla1: chaitraShukla1),
    viraNirvanaSamvat: viraNirvanaSamvat(date, diwali: diwaliDay),
    nakshatra: nakshatraAt(rise),
    nakshatraPada: nakshatraPadaAt(rise),
    nakshatraEnds: _utc(nakshatraEnd(rise)),
    vriddhi: yesterday == jain ? Vriddhi.secondDay : (tomorrow == jain ? Vriddhi.firstDay : null),
    kshaya: _kshaya(yesterday: yesterday, today: jain, previousReference: previousReference),
    boundary: _boundary(reference: reference, jain: jain, jainEnds: jainEnds),
    pachchakkhan: [for (final c in times.completions) (kind: c.kind, at: _utc(c.at))],
    pachchakkhanEvening: _utc(times.evening),
    pachchakkhanParana: _utc(times.parana),
  );
}

Kshaya? _kshaya({required int yesterday, required int today, required double previousReference}) {
  final lost = yesterday % 30 + 1;
  if (today != lost % 30 + 1) return null;
  final starts = tithiEnd(previousReference);
  return (lost: lost, starts: _utc(starts), ends: _utc(tithiEnd(starts + _nudgeDays)));
}

TithiBoundary? _boundary({required double reference, required int jain, required double jainEnds}) {
  final window = boundaryWindow.inSeconds / 86400;
  final after = jainEnds - reference <= window ? jainEnds : null;
  final before = _lastChangeBefore(jain: jain, since: reference - window);
  final candidates = [if (before != null) (at: before, isStart: true), if (after != null) (at: after, isStart: false)]
    ..sort((a, b) => (a.at - reference).abs().compareTo((b.at - reference).abs()));
  if (candidates.isEmpty) return null;
  final nearest = candidates.first;
  return (
    at: _utc(nearest.at),
    isStart: nearest.isStart,
    gap: Duration(microseconds: ((nearest.at - reference).abs() * Duration.microsecondsPerDay).round()),
  );
}

/// When the [jain] tithi began, if that was after [since]. The [jain] tithi
/// holds at the reference instant, so a change found here is always before it.
double? _lastChangeBefore({required int jain, required double since}) {
  if (tithiAt(since) == jain) return null;
  var change = tithiEnd(since);
  while (tithiAt(change + _nudgeDays) != jain) {
    change = tithiEnd(change + _nudgeDays);
  }
  return change;
}
