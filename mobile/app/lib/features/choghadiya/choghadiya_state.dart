import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:panchang_engine/panchang_engine.dart';

import '../../engine/day_reading.dart';
import '../../location/cities.dart';
import '../../location/city_time.dart';
import '../today/today_state.dart';

/// The slot running at an instant, the one after it and how far it has run.
typedef LiveChoghadiya = ({int index, ChoghadiyaPeriod slot, ChoghadiyaPeriod? next, Duration remaining, double progress});

/// The slot of [day] holding [now], or null outside its sunrise-to-next-sunrise
/// span. Slots are half-open, so a boundary instant belongs to the later slot.
/// [following] is the next day, which supplies the slot after the last night slot.
LiveChoghadiya? liveChoghadiya(PanchangDay day, DateTime now, {PanchangDay? following}) {
  final slots = day.choghadiya;
  final index = slots.indexWhere((s) => !now.isBefore(s.start) && now.isBefore(s.end));
  if (index < 0) return null;
  final slot = slots[index];
  return (
    index: index,
    slot: slot,
    next: index + 1 < slots.length ? slots[index + 1] : following?.choghadiya.first,
    remaining: slot.end.difference(now),
    progress: now.difference(slot.start).inMicroseconds / slot.end.difference(slot.start).inMicroseconds,
  );
}

/// The day whose slots the Choghadiya screen and band show for [date], or null
/// while it loads. Follow the sun: before today's sunrise, yesterday's night is
/// still running, so the shown day is yesterday and [date] is the one after it.
typedef ChoghadiyaReading = ({PanchangDay day, PanchangDay? following, bool beforeSunrise});

ChoghadiyaReading? watchChoghadiya(WidgetRef ref, {required PresetCity city, required CivilDate date, required DateTime now}) {
  DayRequest on(CivilDate d) => DayRequest(date: d, lat: city.lat, lon: city.lon, timezone: city.timezone);
  final selected = ref.watch(dayReadingProvider(on(date))).value;
  if (selected == null) return null;
  if (date != todayIn(city.timezone, now) || !now.isBefore(selected.sunrise)) {
    return (day: selected, following: null, beforeSunrise: false);
  }
  final before = DateTime.utc(date.year, date.month, date.day - 1);
  final yesterday = ref.watch(dayReadingProvider(on(CivilDate(before.year, before.month, before.day)))).value;
  return yesterday == null ? null : (day: yesterday, following: selected, beforeSunrise: true);
}
