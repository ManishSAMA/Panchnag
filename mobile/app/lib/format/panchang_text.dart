/// Display text for panchang values. Pure functions over plain values, so the
/// screens only lay text out (mobile-ui-design.md §4). Hindi names follow the
/// Python exports (`hindi_export.py`, `laghu_panchang.py`, `hindi_calendar_pdf.py`),
/// English names the Python engine (`panchang.py`).
library;

import 'package:panchang_engine/panchang_engine.dart';
import 'package:flutter/widgets.dart';

enum Lang { hi, en }

Lang langOf(BuildContext context) => Localizations.localeOf(context).languageCode == 'en' ? Lang.en : Lang.hi;

const _tithiHi = [
  'प्रतिपदा', 'द्वितीया', 'तृतीया', 'चतुर्थी', 'पंचमी', 'षष्ठी', 'सप्तमी', 'अष्टमी', //
  'नवमी', 'दशमी', 'एकादशी', 'द्वादशी', 'त्रयोदशी', 'चतुर्दशी',
];
const _tithiEn = [
  'Pratipada', 'Dwitiya', 'Tritiya', 'Chaturthi', 'Panchami', 'Shashthi', 'Saptami', 'Ashtami', //
  'Navami', 'Dashami', 'Ekadashi', 'Dwadashi', 'Trayodashi', 'Chaturdashi',
];

/// [index] is 1-30: Shukla 1-15 (15 is Purnima), Krishna 16-30 (30 is Amavasya).
String tithiName(int index, Lang lang) {
  if (index == 15) return lang == Lang.hi ? 'पूर्णिमा' : 'Purnima';
  if (index == 30) return lang == Lang.hi ? 'अमावस्या' : 'Amavasya';
  final shukla = index < 15;
  final name = (lang == Lang.hi ? _tithiHi : _tithiEn)[(index - 1) % 15];
  final paksha = switch (lang) {
    Lang.hi => shukla ? 'शुक्ल' : 'कृष्ण',
    Lang.en => shukla ? 'Shukla' : 'Krishna',
  };
  return '$paksha $name';
}

const _monthsHi = [
  'चैत्र', 'वैशाख', 'ज्येष्ठ', 'आषाढ़', 'श्रावण', 'भाद्रपद', //
  'आश्विन', 'कार्तिक', 'मार्गशीर्ष', 'पौष', 'माघ', 'फाल्गुन',
];

String monthName(LunarMonth month, Lang lang) => switch (lang) {
  Lang.hi => month.isAdhika ? 'अधिक ${_monthsHi[month.index]}' : _monthsHi[month.index],
  Lang.en => month.name,
};

const _nakshatraHi = [
  'अश्विनी', 'भरणी', 'कृत्तिका', 'रोहिणी', 'मृगशिरा', 'आर्द्रा', 'पुनर्वसु', 'पुष्य', //
  'आश्लेषा', 'मघा', 'पूर्वा फाल्गुनी', 'उत्तरा फाल्गुनी', 'हस्त', 'चित्रा', 'स्वाति',
  'विशाखा', 'अनुराधा', 'ज्येष्ठा', 'मूल', 'पूर्वाषाढ़ा', 'उत्तराषाढ़ा', 'श्रवण',
  'धनिष्ठा', 'शतभिषा', 'पूर्वा भाद्रपद', 'उत्तरा भाद्रपद', 'रेवती',
];
const _nakshatraEn = [
  'Ashwini', 'Bharani', 'Krittika', 'Rohini', 'Mrigashirsha', 'Ardra', 'Punarvasu', 'Pushya', //
  'Ashlesha', 'Magha', 'Purva Phalguni', 'Uttara Phalguni', 'Hasta', 'Chitra', 'Swati',
  'Vishakha', 'Anuradha', 'Jyeshtha', 'Mula', 'Purva Ashadha', 'Uttara Ashadha', 'Shravana',
  'Dhanishta', 'Shatabhisha', 'Purva Bhadrapada', 'Uttara Bhadrapada', 'Revati',
];

String nakshatraName(int index, Lang lang) => (lang == Lang.hi ? _nakshatraHi : _nakshatraEn)[index - 1];

String pachchakkhanName(TimedPachchakkhan kind, Lang lang) => switch ((kind, lang)) {
  (TimedPachchakkhan.navkarsi, Lang.hi) => 'नवकारसी',
  (TimedPachchakkhan.porsi, Lang.hi) => 'पोरसी',
  (TimedPachchakkhan.sadhPorsi, Lang.hi) => 'साढ़-पोरसी',
  (TimedPachchakkhan.purimaddh, Lang.hi) => 'पुरिमड्ढ',
  (TimedPachchakkhan.avaddh, Lang.hi) => 'अवड्ढ',
  (TimedPachchakkhan.navkarsi, Lang.en) => 'Navkarsi',
  (TimedPachchakkhan.porsi, Lang.en) => 'Porsi',
  (TimedPachchakkhan.sadhPorsi, Lang.en) => 'Sadh-Porsi',
  (TimedPachchakkhan.purimaddh, Lang.en) => 'Purimaddh',
  (TimedPachchakkhan.avaddh, Lang.en) => 'Avaddh',
};

/// The Hindi day parts: सुबह from 4, दोपहर from 12, शाम from 16, रात from 19.
String _hindiPeriod(int hour) => switch (hour) {
  >= 4 && < 12 => 'सुबह',
  >= 12 && < 16 => 'दोपहर',
  >= 16 && < 19 => 'शाम',
  _ => 'रात',
};

/// A wall-clock reading as a 12-hour time and its period word.
({String period, String time}) clockTime(DateTime wall, Lang lang) {
  final hour12 = wall.hour % 12 == 0 ? 12 : wall.hour % 12;
  final time = '$hour12:${wall.minute.toString().padLeft(2, '0')}';
  final period = switch (lang) {
    Lang.hi => _hindiPeriod(wall.hour),
    Lang.en => wall.hour < 12 ? 'AM' : 'PM',
  };
  return (period: period, time: time);
}

String clockPhrase(DateTime wall, Lang lang) {
  final (:period, :time) = clockTime(wall, lang);
  return lang == Lang.hi ? '$period $time' : '$time $period';
}

DateTime _toMinute(DateTime t) => DateTime(t.year, t.month, t.day, t.hour, t.minute);

DateTime roundDownToMinute(DateTime t) => _toMinute(t);

DateTime roundUpToMinute(DateTime t) {
  final down = _toMinute(t);
  return down == t ? t : down.add(const Duration(minutes: 1));
}

String durationText(Duration d, Lang lang) {
  final minutes = (d.inMicroseconds / Duration.microsecondsPerMinute).ceil();
  final (h, m) = (minutes ~/ 60, minutes % 60);
  final (hu, mu) = lang == Lang.hi ? ('घं', 'मि') : ('h', 'min');
  if (h == 0) return '$m $mu';
  if (m == 0) return '$h $hu';
  return '$h $hu $m $mu';
}

String countdownClock(Duration d) {
  final seconds = (d.inMicroseconds / Duration.microsecondsPerSecond).ceil();
  final (h, m, s) = (seconds ~/ 3600, seconds ~/ 60 % 60, seconds % 60);
  String two(int v) => v.toString().padLeft(2, '0');
  return h == 0 ? '$m:${two(s)}' : '$h:${two(m)}:${two(s)}';
}

const _weekdaysHi = ['सोमवार', 'मंगलवार', 'बुधवार', 'गुरुवार', 'शुक्रवार', 'शनिवार', 'रविवार'];
const _weekdaysEn = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];
const _gregorianHi = [
  'जनवरी', 'फरवरी', 'मार्च', 'अप्रैल', 'मई', 'जून', //
  'जुलाई', 'अगस्त', 'सितंबर', 'अक्टूबर', 'नवंबर', 'दिसंबर',
];
const _gregorianEn = [
  'January', 'February', 'March', 'April', 'May', 'June', //
  'July', 'August', 'September', 'October', 'November', 'December',
];

String shortDate(CivilDate date, Lang lang) =>
    '${date.day} ${(lang == Lang.hi ? _gregorianHi : _gregorianEn)[date.month - 1]}';

String longDate(CivilDate date, Lang lang) {
  final weekday = DateTime.utc(date.year, date.month, date.day).weekday;
  return '${(lang == Lang.hi ? _weekdaysHi : _weekdaysEn)[weekday - 1]}, ${shortDate(date, lang)} ${date.year}';
}

String samvatLine({required int viraNirvana, required int vikram, required Lang lang}) => switch (lang) {
  Lang.hi => 'वीर नि. सं. $viraNirvana · वि. सं. $vikram',
  Lang.en => 'VNS $viraNirvana · VS $vikram',
};

/// A wall-clock instant as read on [day]: the clock alone on that day,
/// otherwise with its date ("कल" would mean both yesterday and tomorrow).
String instantPhrase(DateTime wall, {required CivilDate day, required Lang lang}) =>
    _dateOf(wall) == day ? clockPhrase(wall, lang) : _dated(wall, lang);

/// Both ends of a span: dated together when either falls off [day], so a
/// reader never has to guess which day an undated end belongs to.
(String, String) spanPhrases(DateTime start, DateTime end, {required CivilDate day, required Lang lang}) =>
    _dateOf(start) == day && _dateOf(end) == day
    ? (clockPhrase(start, lang), clockPhrase(end, lang))
    : (_dated(start, lang), _dated(end, lang));

CivilDate _dateOf(DateTime wall) => CivilDate(wall.year, wall.month, wall.day);

String _dated(DateTime wall, Lang lang) => '${shortDate(_dateOf(wall), lang)}, ${clockPhrase(wall, lang)}';
