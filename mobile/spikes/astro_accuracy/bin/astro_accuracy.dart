// Phase 0 spike: measure persis_times (VSOP87D + ELP/MPP02) against the
// Swiss Ephemeris reference dumped by tool/dump_reference.py.
//
// Throwaway exploration code (see plans/mobile-app-flutter.md, Phase 0).
// ignore_for_file: implementation_imports
import 'dart:convert';
import 'dart:io';
import 'dart:math' as math;

import 'package:persis_times/persis_times.dart';
import 'package:persis_times/src/core/astronomy/moon_longitude.dart';
import 'package:persis_times/src/core/astronomy/nutation.dart';

final _sun = SunFunction();
final _moon = MoonLongitude();
final _nut = NutationAndObliquity();
final _dyn = DynamicalTime();

// Lahiri as defined by Swiss Ephemeris: ayanamsa value at the 1956 epoch.
const _lahiriT0 = 2435553.5;
const _lahiriAyanT0 = 23.250182778 - 0.004658035;

late final List<Map<String, dynamic>> _samples;
late final double _sampleJd0;

void main(List<String> args) {
  final ref = jsonDecode(File('reference/reference.json').readAsStringSync())
      as Map<String, dynamic>;
  _samples = (ref['samples'] as List).cast<Map<String, dynamic>>();
  _sampleJd0 = (_samples.first['jd'] as num).toDouble();
  print('# Astro accuracy spike — reference: Swiss Ephemeris ${ref['swe_version']}'
      ' (${ref['range'][0]} → ${ref['range'][1]})\n');

  final ayanFit = _fitAyanamsa();
  _positions(ayanFit);
  _transitions('Tithi', ref['tithi'] as List, _tithiResidual(), 12.19);
  _transitions('Nakshatra (fitted ayanamsa)', ref['nakshatra'] as List,
      _nakshatraResidual(ayanFit.eval), 13.18);
  _transitions('Nakshatra (precession-model ayanamsa)', ref['nakshatra'] as List,
      _nakshatraResidual(_ayanPrecession), 13.18);
  _transitions('Sankranti (fitted ayanamsa)', ref['sankranti'] as List,
      _sankrantiResidual(ayanFit.eval), 0.9856);
  _transitions('Tithi with persis ΔT model', ref['tithi'] as List,
      _tithiResidual(dtFn: _dyn.deltaT), 12.19);
  _riseSet((ref['riseSet'] as List).cast<Map<String, dynamic>>());
  _performance();
}

// ── Time ────────────────────────────────────────────────────────────────
double _refDeltaT(double jd) {
  final i = ((jd - _sampleJd0) * 2).round().clamp(0, _samples.length - 1);
  return (_samples[i]['dt'] as num).toDouble();
}

typedef DeltaT = double Function(double jd);

// ── Positions ───────────────────────────────────────────────────────────
double _sunApp(double jd, DeltaT dt) =>
    _sun.sunGeocentricLongitude(jd, dt(jd), 'Appa');
double _moonApp(double jd, DeltaT dt) =>
    _moon.moonGeocentricLongitude(jd, dt(jd), 'Appa');

// Swiss Ephemeris FLG_SIDEREAL excludes nutation (verified by _positions).
double _sidereal(double tropicalApparent, double jd, DeltaT dt,
        double Function(double) ayan) =>
    _norm360(tropicalApparent - _nut.nutationInLongitude(jd, dt(jd)) - ayan(jd));

double _ayanPrecession(double jdUt) {
  double pA(double jd) {
    final t = (jd - 2451545.0) / 36525.0;
    return (5028.796195 * t +
            1.1054348 * t * t +
            0.00007964 * t * t * t -
            0.000023857 * t * t * t * t) /
        3600.0;
  }

  return _lahiriAyanT0 + pA(jdUt) - pA(_lahiriT0);
}

class _Poly {
  _Poly(this.coeffs, this.jdMid);
  final List<double> coeffs;
  final double jdMid;
  double eval(double jd) {
    final x = (jd - jdMid) / 36525.0;
    return coeffs.reversed.fold(0.0, (acc, c) => acc * x + c);
  }
}

_Poly _fitAyanamsa() {
  const degree = 3;
  final jds = _samples.map((s) => (s['jd'] as num).toDouble()).toList();
  final ys = _samples.map((s) => (s['ayan'] as num).toDouble()).toList();
  final mid = (jds.first + jds.last) / 2;
  final n = degree + 1;
  final a = List.generate(n, (_) => List.filled(n + 1, 0.0));
  for (var k = 0; k < jds.length; k++) {
    final x = (jds[k] - mid) / 36525.0;
    for (var i = 0; i < n; i++) {
      for (var j = 0; j < n; j++) {
        a[i][j] += math.pow(x, i + j).toDouble();
      }
      a[i][n] += ys[k] * math.pow(x, i);
    }
  }
  for (var c = 0; c < n; c++) {
    for (var r = c + 1; r < n; r++) {
      final f = a[r][c] / a[c][c];
      for (var k = c; k <= n; k++) {
        a[r][k] -= f * a[c][k];
      }
    }
  }
  final coeffs = List.filled(n, 0.0);
  for (var i = n - 1; i >= 0; i--) {
    var s = a[i][n];
    for (var j = i + 1; j < n; j++) {
      s -= a[i][j] * coeffs[j];
    }
    coeffs[i] = s / a[i][i];
  }
  return _Poly(coeffs, mid);
}

void _positions(_Poly ayanFit) {
  final sunErr = <double>[], moonErr = <double>[], ayanFitErr = <double>[];
  final ayanPrecErr = <double>[], sidVsMean = <double>[], sunSidErr = <double>[];
  final moonSidErr = <double>[];
  for (final s in _samples) {
    final jd = (s['jd'] as num).toDouble();
    final sunT = _sunApp(jd, _refDeltaT), moonT = _moonApp(jd, _refDeltaT);
    final ayan = (s['ayan'] as num).toDouble();
    sunErr.add(_arcsec(sunT, s['sunT']));
    moonErr.add(_arcsec(moonT, s['moonT']));
    ayanFitErr.add(_arcsec(ayanFit.eval(jd), ayan));
    ayanPrecErr.add(_arcsec(_ayanPrecession(jd), ayan));
    // How does swe FLG_SIDEREAL relate to (tropical apparent − ayanamsa)?
    final dpsi = _nut.nutationInLongitude(jd, _refDeltaT(jd));
    sidVsMean.add(_arcsec((s['sunT'] as num) - ayan - dpsi, s['sunS']));
    sunSidErr.add(_arcsec(_sidereal(sunT, jd, _refDeltaT, ayanFit.eval), s['sunS']));
    moonSidErr.add(_arcsec(_sidereal(moonT, jd, _refDeltaT, ayanFit.eval), s['moonS']));
  }
  print('## L1 — positions (${_samples.length} instants, arcseconds)\n');
  _header('Quantity');
  _row('Sun tropical apparent', sunErr);
  _row('Moon tropical apparent', moonErr);
  _row('Ayanamsa: cubic fit', ayanFitErr);
  _row('Ayanamsa: precession model', ayanPrecErr);
  _row('swe sidereal vs (trop − Δψ − ayan)', sidVsMean);
  _row('Sun sidereal (end-to-end)', sunSidErr);
  _row('Moon sidereal (end-to-end)', moonSidErr);
  print('\nCubic ayanamsa coefficients (deg, x = centuries from JD '
      '${ayanFit.jdMid}): ${ayanFit.coeffs}\n');
}

// ── Transitions (L2) ────────────────────────────────────────────────────
typedef Residual = double Function(double jd, int to);

Residual _tithiResidual({DeltaT dtFn = _refDeltaT}) => (jd, to) =>
    _wrap180(_moonApp(jd, dtFn) - _sunApp(jd, dtFn) - (to - 1) * 12.0);

Residual _nakshatraResidual(double Function(double) ayan) => (jd, to) =>
    _wrap180(_sidereal(_moonApp(jd, _refDeltaT), jd, _refDeltaT, ayan) -
        (to - 1) * 360.0 / 27.0);

Residual _sankrantiResidual(double Function(double) ayan) => (jd, to) =>
    _wrap180(_sidereal(_sunApp(jd, _refDeltaT), jd, _refDeltaT, ayan) - to * 30.0);

double _solve(double jd0, int to, Residual f, double degPerDay) {
  var jd = jd0;
  for (var i = 0; i < 8; i++) {
    final step = f(jd, to) / degPerDay;
    jd -= step;
    if (step.abs() < 1e-8) break;
  }
  return jd;
}

void _transitions(String label, List events, Residual f, double degPerDay) {
  final errs = <double>[];
  for (final e in events.cast<Map<String, dynamic>>()) {
    final ref = (e['jd'] as num).toDouble();
    errs.add((_solve(ref, e['to'] as int, f, degPerDay) - ref) * 86400.0);
  }
  print('## L2 — $label transitions (${errs.length} events, seconds)\n');
  _header('');
  _row(label, errs);
  print('');
}

// ── Sunrise / sunset ────────────────────────────────────────────────────
double _altitude(double jd, double lat, double lon) {
  final dt = _refDeltaT(jd);
  final ra = _sun.sunGeocentricRightAscension(jd, dt);
  final dec = _sun.sunGeocentricDeclination(jd, dt);
  final h = _rad(_sun.greenwichApparentSiderialTime(jd, dt) + lon - ra);
  final phi = _rad(lat), d = _rad(dec);
  return _deg(math.asin(math.sin(phi) * math.sin(d) + math.cos(phi) * math.cos(d) * math.cos(h)));
}

double _semidiameterDeg(double jd) =>
    959.63 / _sun.sunGeocentricDistance(jd, _refDeltaT(jd), 'AU') / 3600.0;

// `anchor` is local civil midnight expressed as a UT Julian Day.
double _riseSetJd(double anchor, double lat, double lon, double refraction,
    {required bool rise}) {
  var jd = anchor + (rise ? 0.25 : 0.75);
  for (var i = 0; i < 10; i++) {
    final target = -(refraction + _semidiameterDeg(jd));
    final h = _altitude(jd, lat, lon);
    final slope = (_altitude(jd + 1e-4, lat, lon) - h) / 1e-4;
    final step = (h - target) / slope;
    jd -= step;
    if (step.abs() < 1e-7) break;
  }
  return jd;
}

void _riseSet(List<Map<String, dynamic>> rows) {
  // Implied refraction: the altitude swe used at its own rise instants.
  final implied = rows.map((r) {
    final jd = (r['rise'] as num).toDouble();
    return -_altitude(jd, (r['lat'] as num).toDouble(), (r['lon'] as num).toDouble()) -
        _semidiameterDeg(jd);
  }).toList();
  final refraction = implied.reduce((a, b) => a + b) / implied.length;
  print('## L1 — sunrise / sunset (${rows.length} city-days, seconds)\n');
  print('Implied horizon refraction used by swe: ${(refraction * 60).toStringAsFixed(3)}′ '
      '(max deviation ${(_maxAbsDev(implied) * 3600).toStringAsFixed(2)}″)\n');
  _header('City');
  for (final city in rows.map((r) => r['city']).toSet()) {
    final rise = <double>[], set = <double>[];
    for (final r in rows.where((r) => r['city'] == city)) {
      final lat = (r['lat'] as num).toDouble(), lon = (r['lon'] as num).toDouble();
      final anchor = (r['anchor'] as num).toDouble();
      rise.add((_riseSetJd(anchor, lat, lon, refraction, rise: true) - r['rise']) * 86400);
      set.add((_riseSetJd(anchor, lat, lon, refraction, rise: false) - r['set']) * 86400);
    }
    _row('$city sunrise', rise);
    _row('$city sunset', set);
  }
  print('');
}

// ── Performance ─────────────────────────────────────────────────────────
void _performance() {
  double time(int n, void Function(int) body) {
    final sw = Stopwatch()..start();
    for (var i = 0; i < n; i++) {
      body(i);
    }
    return sw.elapsedMicroseconds / n / 1000.0;
  }

  const base = 2461000.5;
  print('## Performance (this PC; ms per call)\n');
  print('| Operation | ms |\n|---|---:|');
  print('| Sun apparent longitude | ${time(2000, (i) => _sunApp(base + i * 0.37, _refDeltaT)).toStringAsFixed(3)} |');
  print('| Moon apparent longitude | ${time(2000, (i) => _moonApp(base + i * 0.37, _refDeltaT)).toStringAsFixed(3)} |');
  print('| Sunrise (Delhi) | ${time(500, (i) => _riseSetJd(base + i, 28.6139, 77.209, 0.57, rise: true)).toStringAsFixed(3)} |');
  print('| Tithi end solve | ${time(500, (i) => _solve(base + i * 0.98, 1 + i % 30, _tithiResidual(), 12.19)).toStringAsFixed(3)} |');
}

// ── Stats / formatting ──────────────────────────────────────────────────
double _arcsec(num a, num b) => _wrap180(a - b) * 3600.0;
double _wrap180(num d) => (d + 540.0) % 360.0 - 180.0;
double _norm360(double d) => (d % 360.0 + 360.0) % 360.0;
double _rad(double d) => d * math.pi / 180.0;
double _deg(double r) => r * 180.0 / math.pi;
double _maxAbsDev(List<double> xs) {
  final m = xs.reduce((a, b) => a + b) / xs.length;
  return xs.map((x) => (x - m).abs()).reduce(math.max);
}

void _header(String first) {
  print('| $first | mean | p99 abs | max abs |\n|---|---:|---:|---:|');
}

void _row(String label, List<double> xs) {
  final abs = xs.map((x) => x.abs()).toList()..sort();
  final mean = xs.reduce((a, b) => a + b) / xs.length;
  final p99 = abs[((abs.length - 1) * 0.99).round()];
  print('| $label | ${mean.toStringAsFixed(3)} | ${p99.toStringAsFixed(3)} | '
      '${abs.last.toStringAsFixed(3)} |');
}
