import 'dart:convert';
import 'dart:io';

/// Fixture schema this engine understands; the Python exporter's SCHEMA_VERSION.
const supportedSchemaVersion = 2;

/// Reads a gzip JSON fixture from test/fixtures/core/ (run tests from the package root).
Map<String, Object?> readCoreFixture(String relativePath) {
  final file = File('test/fixtures/core/$relativePath');
  final json = jsonDecode(utf8.decode(gzip.decode(file.readAsBytesSync())));
  final fixture = json as Map<String, Object?>;
  final version = fixture['schema_version'];
  if (version != supportedSchemaVersion) {
    throw StateError('$relativePath has schema $version; regenerate the fixtures '
        '(python scripts/export_parity_fixtures.py --set core).');
  }
  return fixture;
}

List<Map<String, Object?>> astroSamples() =>
    (readCoreFixture('astro.json.gz')['samples']! as List<Object?>).cast<Map<String, Object?>>();

/// Smallest signed difference between two angles in degrees, as arcseconds.
double angleDiffArcsec(double a, double b) => ((a - b + 540) % 360 - 180) * 3600;

/// Largest absolute value, for reporting worst-case error.
double maxAbs(Iterable<double> values) =>
    values.fold(0, (worst, v) => v.abs() > worst ? v.abs() : worst);

/// A core fixture location with its own date range, from manifest.json.
typedef FixtureLocation = ({String slug, double lat, double lon, String timezone});

List<FixtureLocation> coreLocations() {
  final manifest = jsonDecode(File('test/fixtures/core/manifest.json').readAsStringSync())
      as Map<String, Object?>;
  if (manifest['schema_version'] != supportedSchemaVersion) {
    throw StateError('core/manifest.json has schema ${manifest['schema_version']}; regenerate.');
  }
  return [
    for (final loc in (manifest['locations']! as List<Object?>).cast<Map<String, Object?>>())
      (
        slug: loc['slug']! as String,
        lat: (loc['lat']! as num).toDouble(),
        lon: (loc['lon']! as num).toDouble(),
        timezone: loc['timezone']! as String,
      ),
  ];
}

List<Map<String, Object?>> dayRows(String slug, String rule) =>
    (readCoreFixture('$slug/$rule/days.json.gz')['days']! as List<Object?>)
        .cast<Map<String, Object?>>();
