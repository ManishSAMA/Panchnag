/// Delhi's day and Panchang section, and how a section line reads, for the
/// tests of Today's Panchang card and Full Panchang's section.
library;

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:jainpanchang/engine/day_reading.dart';
import 'package:jainpanchang/format/panchang_text.dart';
import 'package:jainpanchang/location/city_time.dart';
import 'package:panchang_engine/panchang_engine.dart';

PanchangDay delhiDay([CivilDate date = const CivilDate(2026, 10, 22)]) =>
    readDay(
      DayRequest(
        date: date,
        lat: 28.6139,
        lon: 77.2090,
        timezone: 'Asia/Kolkata',
      ),
    );

PanchangSection delhiSection([
  CivilDate date = const CivilDate(2026, 10, 22),
]) => readSection(
  SectionRequest(
    DayRequest(
      date: date,
      lat: 28.6139,
      lon: 77.2090,
      timezone: 'Asia/Kolkata',
    ),
  ),
);

/// The end of a section line as shown: the time, dated when off the day.
String shownEnd(DateTime utc, CivilDate day, Lang lang) => instantPhrase(
  roundDownToMinute(cityWall(utc, 'Asia/Kolkata')),
  day: day,
  lang: lang,
);

Finder line(String key) => find.byKey(Key(key));

String lineText(WidgetTester tester, String key) => tester
    .widget<RichText>(
      find.descendant(of: line(key), matching: find.byType(RichText)).first,
    )
    .text
    .toPlainText(includePlaceholders: false)
    // Section lines glue times together with non-breaking spaces.
    .replaceAll('\u00A0', ' ');
