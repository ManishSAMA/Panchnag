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

/// A Month cell's tithi: the paksha initial and the day within the paksha.
String tithiShort(int index, Lang lang) {
  if (index == 15) return lang == Lang.hi ? 'पूर्णिमा' : 'Purnima';
  if (index == 30) return lang == Lang.hi ? 'अमावस' : 'Amavas';
  final shukla = index < 15;
  final paksha = switch (lang) {
    Lang.hi => shukla ? 'शु' : 'कृ',
    Lang.en => shukla ? 'S' : 'K',
  };
  return '$paksha ${(index - 1) % 15 + 1}';
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

/// The Rashis (0 = Mesha) a nakshatra's four padas fall in: one, or two when
/// a sign boundary splits it. A pada is 3°20′, a ninth of a Rashi.
List<int> nakshatraRashis(int nakshatra) {
  final (first, last) = ((4 * (nakshatra - 1)) ~/ 9, (4 * nakshatra - 1) ~/ 9);
  return first == last ? [first] : [first, last];
}

const _yogaHi = [
  'विष्कुम्भ', 'प्रीति', 'आयुष्मान', 'सौभाग्य', 'शोभन', 'अतिगण्ड', 'सुकर्मा', 'धृति', 'शूल', //
  'गण्ड', 'वृद्धि', 'ध्रुव', 'व्याघात', 'हर्षण', 'वज्र', 'सिद्धि', 'व्यतीपात', 'वरीयान', //
  'परिघ', 'शिव', 'सिद्ध', 'साध्य', 'शुभ', 'शुक्ल', 'ब्रह्म', 'इन्द्र', 'वैधृति',
];
const _yogaEn = [
  'Vishkumbha', 'Priti', 'Ayushman', 'Saubhagya', 'Shobhana', 'Atiganda', 'Sukarma', 'Dhriti', 'Shula', //
  'Ganda', 'Vriddhi', 'Dhruva', 'Vyaghata', 'Harshana', 'Vajra', 'Siddhi', 'Vyatipata', 'Variyana', //
  'Parigha', 'Shiva', 'Siddha', 'Sadhya', 'Shubha', 'Shukla', 'Brahma', 'Indra', 'Vaidhriti',
];

/// [index] is 1-27, from Vishkumbha.
String yogaName(int index, Lang lang) => (lang == Lang.hi ? _yogaHi : _yogaEn)[index - 1];

const _movableKaranaHi = ['बव', 'बालव', 'कौलव', 'तैतिल', 'गर', 'वणिज', 'विष्टि (भद्रा)'];
const _movableKaranaEn = ['Bava', 'Balava', 'Kaulava', 'Taitila', 'Garaja', 'Vanija', 'Vishti (Bhadra)'];
const _fixedKaranaHi = {1: 'किंस्तुघ्न', 58: 'शकुनि', 59: 'चतुष्पद', 60: 'नाग'};
const _fixedKaranaEn = {1: 'Kimstughna', 58: 'Shakuni', 59: 'Chatushpada', 60: 'Naga'};

/// [index] is 1-60 within the lunar month: Kimstughna, the seven movable
/// karanas eight times over, then Shakuni, Chatushpada and Naga.
String karanaName(int index, Lang lang) =>
    (lang == Lang.hi ? _fixedKaranaHi : _fixedKaranaEn)[index] ??
    (lang == Lang.hi ? _movableKaranaHi : _movableKaranaEn)[(index - 2) % 7];

const _rashiHi = ['मेष', 'वृषभ', 'मिथुन', 'कर्क', 'सिंह', 'कन्या', 'तुला', 'वृश्चिक', 'धनु', 'मकर', 'कुंभ', 'मीन'];
const _rashiEn = [
  'Mesha (Aries)', 'Vrishabha (Taurus)', 'Mithuna (Gemini)', 'Karka (Cancer)', 'Simha (Leo)', 'Kanya (Virgo)', //
  'Tula (Libra)', 'Vrishchika (Scorpio)', 'Dhanu (Sagittarius)', 'Makara (Capricorn)', 'Kumbha (Aquarius)', //
  'Meena (Pisces)',
];

/// [index] is 0-11, from Mesha.
String rashiName(int index, Lang lang) => (lang == Lang.hi ? _rashiHi : _rashiEn)[index];

/// The paksha of a tithi (1-30).
String pakshaName(int tithi, Lang lang) => switch (lang) {
  Lang.hi => tithi <= 15 ? 'शुक्ल' : 'कृष्ण',
  Lang.en => tithi <= 15 ? 'Shukla' : 'Krishna',
};

/// The Rashi the Sun is in and the day of its stay: "तुला 21 गते".
String gataText(Gata gata, Lang lang) => switch (lang) {
  Lang.hi => '${rashiName(gata.rashi, lang)} ${gata.day} गते',
  Lang.en => '${rashiName(gata.rashi, lang)}, day ${gata.day}',
};

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

const _choghadiyaHi = {
  Choghadiya.udveg: 'उद्वेग',
  Choghadiya.char: 'चर',
  Choghadiya.labh: 'लाभ',
  Choghadiya.amrit: 'अमृत',
  Choghadiya.kaal: 'काल',
  Choghadiya.shubh: 'शुभ',
  Choghadiya.rog: 'रोग',
};

/// English follows the Python engine's spelling.
String choghadiyaName(Choghadiya slot, Lang lang) => switch (lang) {
  Lang.hi => _choghadiyaHi[slot]!,
  Lang.en => '${slot.name[0].toUpperCase()}${slot.name.substring(1)}',
};

/// Quality is never shown by colour alone (DESIGN.md, the Not-By-Colour-Alone Rule).
String natureGlyph(ChoghadiyaNature nature) => switch (nature) {
  ChoghadiyaNature.auspicious => '✓',
  ChoghadiyaNature.neutral => '–',
  ChoghadiyaNature.inauspicious => '✕',
};

/// Two wall-clock readings as one span; the period word appears once when both share it.
String clockRange(DateTime start, DateTime end, Lang lang) {
  final (from, to) = (clockTime(start, lang), clockTime(end, lang));
  return switch (lang) {
    Lang.hi when from.period == to.period => '${from.period} ${from.time}–${to.time}',
    Lang.hi => '${from.period} ${from.time}–${to.period} ${to.time}',
    Lang.en when from.period == to.period => '${from.time}–${to.time} ${to.period}',
    Lang.en => '${from.time} ${from.period}–${to.time} ${to.period}',
  };
}

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

const _varaShortHi = ['रवि', 'सोम', 'मंगल', 'बुध', 'गुरु', 'शुक्र', 'शनि'];
const _varaShortEn = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];

/// The Month grid's column heading; [vara] 0 is Sunday, as in the engine.
String varaShort(int vara, Lang lang) => (lang == Lang.hi ? _varaShortHi : _varaShortEn)[vara];

String monthTitle(int year, int month, Lang lang) =>
    '${(lang == Lang.hi ? _gregorianHi : _gregorianEn)[month - 1]} $year';

/// The Month header's subtitle: the lunar months of its days, each once, and
/// the VS, as a range when it turns over within the month.
String monthSpanLine({required List<LunarMonth> months, required List<int> vikrams, required Lang lang}) {
  final names = [
    for (final (i, month) in months.indexed)
      if (i == 0 || months[i - 1] != month) monthName(month, lang),
  ];
  final (first, last) = (vikrams.first, vikrams.last);
  final vs = first == last ? '$first' : '$first–$last';
  return '${names.join(' – ')} · ${lang == Lang.hi ? 'वि. सं.' : 'VS'} $vs';
}

/// Where [at] falls in [day]'s daylight: 0 at sunrise, 1 at sunset.
double dayFraction(DateTime at, PanchangDay day) =>
    at.difference(day.sunrise).inSeconds / day.sunset.difference(day.sunrise).inSeconds;

String gregorianMonthName(int month, Lang lang) => (lang == Lang.hi ? _gregorianHi : _gregorianEn)[month - 1];

String weekdayName(CivilDate date, Lang lang) =>
    (lang == Lang.hi ? _weekdaysHi : _weekdaysEn)[DateTime.utc(date.year, date.month, date.day).weekday - 1];

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
