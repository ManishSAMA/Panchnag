/// Words for the Muhurat section: residences, the day's yoga names in Hindi,
/// and which nitya yogas are inauspicious.
library;

import 'package:panchang_engine/panchang_engine.dart';

import 'panchang_text.dart';

/// A time phrase held on one line, so a wrap never strands "सुबह", "AM",
/// "तक" or a date's month: only a span's dash may break.
String glued(String phrase) => phrase.replaceAll(' ', ' ');

/// A window of [day], from wall-clock readings: [allDay] when it runs from
/// sunrise to the next sunrise, the bare clock range when both ends fall on
/// [day], else the start as read on [day] and the end with its date, so a
/// window past midnight never looks like a minute long.
String dayWindowText({
  required DateTime start,
  required DateTime end,
  required ({DateTime sunrise, DateTime nextSunrise})? bounds,
  required CivilDate day,
  required Lang lang,
  required String allDay,
}) {
  if (bounds != null && start == bounds.sunrise && end == bounds.nextSunrise) return allDay;
  final onDay = CivilDate(end.year, end.month, end.day) == day && CivilDate(start.year, start.month, start.day) == day;
  if (onDay) return glued(clockRange(start, end, lang));
  return '${glued(instantPhrase(start, day: day, lang: lang))} – ${glued(instantPhrase(end, day: day, lang: lang))}';
}

String agniVaasName(AgniVaas vaas, Lang lang) => switch ((vaas, lang)) {
  (AgniVaas.prithvi, Lang.hi) => 'पृथ्वी',
  (AgniVaas.aakash, Lang.hi) => 'आकाश',
  (AgniVaas.patal, Lang.hi) => 'पाताल',
  (AgniVaas.prithvi, Lang.en) => 'Earth',
  (AgniVaas.aakash, Lang.en) => 'Sky',
  (AgniVaas.patal, Lang.en) => 'Underworld',
};

/// Where Bhadra stays: only on Earth does it harm the work begun.
String bhadraResidenceText(BhadraResidence residence, Lang lang) => switch ((residence, lang)) {
  (BhadraResidence.earth, Lang.hi) => 'पृथ्वी पर',
  (BhadraResidence.heaven, Lang.hi) => 'स्वर्ग में',
  (BhadraResidence.underworld, Lang.hi) => 'पाताल में',
  (BhadraResidence.earth, Lang.en) => 'on Earth',
  (BhadraResidence.heaven, Lang.en) => 'in Heaven',
  (BhadraResidence.underworld, Lang.en) => 'in Patal',
};

/// The nine inauspicious nitya yogas: Vishkambha, Atiganda, Shula, Ganda,
/// Vyaghata, Vajra, Vyatipata, Parigha and Vaidhriti (1-based).
const _inauspiciousNitya = {1, 6, 9, 10, 13, 15, 17, 19, 27};

bool nityaYogaIsAuspicious(int index) => !_inauspiciousNitya.contains(index);

/// A day yoga's name as the engine spells it (after yoga_rules.py), in Hindi
/// or as given. The rules spell some yogas two ways (Dainika "Shrivatsa",
/// Aanandadi "Shreevatsa"); both read the same in Hindi.
String dayYogaName(String name, Lang lang) {
  if (lang == Lang.en) return name;
  if (RegExp(r'^Ravi Yoga \((.+)\)$').firstMatch(name) case final m?) {
    return '${_yogaHi['Ravi Yoga']} (${dayYogaName(m[1]!, lang)})';
  }
  return _yogaHi[name] ?? name;
}

const _yogaHi = {
  'Adham Tithi': 'अधम तिथि',
  'Amrit': 'अमृत',
  'Amrut': 'अमृत',
  'Amrit Siddhi': 'अमृत सिद्धि',
  'Anand': 'आनंद',
  'Chara': 'चर',
  'Chatra': 'छत्र',
  'Chhatra': 'छत्र',
  'Dagdha Tithi': 'दग्ध तिथि',
  'Dagdha Yoga': 'दग्ध योग',
  'Dhumra': 'धूम्र',
  'Dhwaja': 'ध्वज',
  'Dhwanksh': 'ध्वांक्ष',
  'Dhwanksha': 'ध्वांक्ष',
  'Dusht Tithi': 'दुष्ट तिथि',
  'Dwipushkar': 'द्विपुष्कर',
  'Gad': 'गद',
  'Gada': 'गद',
  'Guru Pushya Amrit': 'गुरु पुष्य अमृत',
  'Hutashan Tithi': 'हुताशन तिथि',
  'Jwalamukhi': 'ज्वालामुखी',
  'Kaal': 'काल',
  'Kaal Dand': 'कालदंड',
  'Kaan': 'काण',
  'Kaan Yoga': 'काण योग',
  'Krakach Tithi': 'क्रकच तिथि',
  'Kumar Yog': 'कुमार योग',
  'Kumar Yog (Tyajya)': 'कुमार योग (त्याज्य)',
  'Lumbak': 'लुम्बक',
  'Manas': 'मानस',
  'Matanga': 'मातंग',
  'Mitra': 'मित्र',
  'Mrityu': 'मृत्यु',
  'Mrityu Yoga Nakshatra': 'मृत्यु योग (नक्षत्र)',
  'Mrityu Yoga Tithi': 'मृत्यु योग (तिथि)',
  'Mudgar': 'मुद्गर',
  'Mudgar Yog': 'मुद्गर योग',
  'Musal': 'मूसल',
  'Musal Yoga': 'मूसल योग',
  'Padma': 'पद्म',
  'Prajapati': 'प्रजापति',
  'Raj Yog': 'राज योग',
  'Rakshas Yoga': 'राक्षस योग',
  'Rakshasa': 'राक्षस',
  'Ravi Pushya Amrit': 'रवि पुष्य अमृत',
  'Ravi Yoga': 'रवि योग',
  'Sarvartha Siddhi': 'सर्वार्थ सिद्धि',
  'Saumya': 'सौम्य',
  'Soumya': 'सौम्य',
  'Shreevatsa': 'श्रीवत्स',
  'Shrivatsa': 'श्रीवत्स',
  'Shubh': 'शुभ',
  'Shubha': 'शुभ',
  'Siddhi': 'सिद्धि',
  'Siddhi Yoga': 'सिद्धि योग',
  'Siddhi Yoga Tithi': 'सिद्धि योग (तिथि)',
  'Sthir Yog': 'स्थिर योग',
  'Sthira': 'स्थिर',
  'Tripushkar': 'त्रिपुष्कर',
  'Utpat': 'उत्पात',
  'Utpat Nakshatra': 'उत्पात (नक्षत्र)',
  'Vajra': 'वज्र',
  'Vajra Yog': 'वज्र योग',
  'Varjit Tithi Nakshatra': 'वर्जित तिथि-नक्षत्र',
  'Vishakhya Tithi': 'विषाख्य तिथि',
  'Vriddhi': 'वृद्धि',
  'Yam Ghant': 'यमघंट',
};
