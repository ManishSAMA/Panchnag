import 'package:flutter_test/flutter_test.dart';
import 'package:jainpanchang/format/panchang_text.dart';
import 'package:panchang_engine/src/calendar/month.dart';
import 'package:panchang_engine/src/panchang/pachchakkhan.dart';
import 'package:panchang_engine/src/time/civil_day.dart';

DateTime wall(int hour, int minute, [int second = 0]) => DateTime(2026, 10, 22, hour, minute, second);

void main() {
  group('tithi names (Laghu booklet names; Purnima and Amavasya without paksha)', () {
    test('Hindi', () {
      expect(tithiName(1, Lang.hi), 'शुक्ल प्रतिपदा');
      expect(tithiName(11, Lang.hi), 'शुक्ल एकादशी');
      expect(tithiName(15, Lang.hi), 'पूर्णिमा');
      expect(tithiName(16, Lang.hi), 'कृष्ण प्रतिपदा');
      expect(tithiName(29, Lang.hi), 'कृष्ण चतुर्दशी');
      expect(tithiName(30, Lang.hi), 'अमावस्या');
    });

    test('English follows the Python engine', () {
      expect(tithiName(11, Lang.en), 'Shukla Ekadashi');
      expect(tithiName(15, Lang.en), 'Purnima');
      expect(tithiName(18, Lang.en), 'Krishna Tritiya');
      expect(tithiName(30, Lang.en), 'Amavasya');
    });

    test('every index has a distinct name in both languages', () {
      for (final lang in Lang.values) {
        expect({for (var i = 1; i <= 30; i++) tithiName(i, lang)}, hasLength(30));
      }
    });
  });

  group('month names', () {
    test('Hindi, with अधिक for an Adhik month', () {
      expect(monthName(const LunarMonth(index: 6, isAdhika: false), Lang.hi), 'आश्विन');
      expect(monthName(const LunarMonth(index: 8, isAdhika: false), Lang.hi), 'मार्गशीर्ष');
      expect(monthName(const LunarMonth(index: 4, isAdhika: true), Lang.hi), 'अधिक श्रावण');
    });

    test('English follows the engine', () {
      expect(monthName(const LunarMonth(index: 6, isAdhika: false), Lang.en), 'Ashwin');
      expect(monthName(const LunarMonth(index: 4, isAdhika: true), Lang.en), 'Adhika Shravana');
    });
  });

  test('nakshatra names follow the Python exports', () {
    expect(nakshatraName(1, Lang.hi), 'अश्विनी');
    expect(nakshatraName(24, Lang.hi), 'शतभिषा');
    expect(nakshatraName(25, Lang.hi), 'पूर्वा भाद्रपद');
    expect(nakshatraName(27, Lang.en), 'Revati');
    for (final lang in Lang.values) {
      expect({for (var i = 1; i <= 27; i++) nakshatraName(i, lang)}, hasLength(27));
    }
  });

  test('pachchakkhan names', () {
    expect(TimedPachchakkhan.values.map((p) => pachchakkhanName(p, Lang.hi)), [
      'नवकारसी',
      'पोरसी',
      'साढ़-पोरसी',
      'पुरिमड्ढ',
      'अवड्ढ',
    ]);
    expect(pachchakkhanName(TimedPachchakkhan.sadhPorsi, Lang.en), 'Sadh-Porsi');
  });

  group('clock times', () {
    test('Hindi period words: सुबह 4-12, दोपहर 12-4, शाम 4-7, रात 7-4', () {
      String period(int h, int m) => clockTime(wall(h, m), Lang.hi).period;

      expect([period(3, 59), period(4, 0), period(11, 59), period(12, 0)], ['रात', 'सुबह', 'सुबह', 'दोपहर']);
      expect([period(15, 59), period(16, 0), period(18, 59), period(19, 0)], ['दोपहर', 'शाम', 'शाम', 'रात']);
      expect(period(0, 0), 'रात');
    });

    test('12-hour clock with no leading zero', () {
      expect(clockTime(wall(0, 30), Lang.hi).time, '12:30');
      expect(clockTime(wall(6, 5), Lang.hi).time, '6:05');
      expect(clockTime(wall(12, 6), Lang.hi).time, '12:06');
      expect(clockTime(wall(14, 48), Lang.hi).time, '2:48');
    });

    test('English uses AM and PM', () {
      expect(clockTime(wall(0, 30), Lang.en).period, 'AM');
      expect(clockTime(wall(11, 59), Lang.en).period, 'AM');
      expect(clockTime(wall(12, 0), Lang.en).period, 'PM');
    });

    test('a phrase puts the Hindi period first and the English one last', () {
      expect(clockPhrase(wall(14, 48), Lang.hi), 'दोपहर 2:48');
      expect(clockPhrase(wall(14, 48), Lang.en), '2:48 PM');
    });

    test('seconds are dropped, not rounded', () {
      expect(clockTime(wall(14, 48, 59), Lang.hi).time, '2:48');
    });
  });

  group('rounding to the minute', () {
    test('up: a completion time is never shown early', () {
      expect(roundUpToMinute(wall(9, 15, 1)), wall(9, 16));
      expect(roundUpToMinute(DateTime(2026, 10, 22, 9, 15, 0, 1)), wall(9, 16));
      expect(roundUpToMinute(wall(9, 15)), wall(9, 15));
    });

    test('down: a deadline is never shown late', () {
      expect(roundDownToMinute(wall(17, 44, 59)), wall(17, 44));
      expect(roundDownToMinute(wall(17, 44)), wall(17, 44));
    });
  });

  test('durations count whole minutes, rounded up', () {
    expect(durationText(const Duration(minutes: 74), Lang.hi), '1 घं 14 मि');
    expect(durationText(const Duration(minutes: 46), Lang.hi), '46 मि');
    expect(durationText(const Duration(minutes: 120), Lang.hi), '2 घं');
    expect(durationText(const Duration(minutes: 45, seconds: 1), Lang.hi), '46 मि');
    expect(durationText(const Duration(seconds: 20), Lang.hi), '1 मि');
    expect(durationText(const Duration(minutes: 74), Lang.en), '1 h 14 min');
  });

  test('long dates', () {
    expect(longDate(const CivilDate(2026, 10, 22), Lang.hi), 'गुरुवार, 22 अक्टूबर 2026');
    expect(longDate(const CivilDate(2026, 10, 22), Lang.en), 'Thursday, 22 October 2026');
    expect(longDate(const CivilDate(2040, 12, 31), Lang.hi), 'सोमवार, 31 दिसंबर 2040');
  });

  test('short dates', () {
    expect(shortDate(const CivilDate(2026, 10, 18), Lang.hi), '18 अक्टूबर');
    expect(shortDate(const CivilDate(2026, 10, 18), Lang.en), '18 October');
  });

  test('samvat line', () {
    expect(samvatLine(viraNirvana: 2552, vikram: 2083, lang: Lang.hi), 'वीर नि. सं. 2552 · वि. सं. 2083');
    expect(samvatLine(viraNirvana: 2552, vikram: 2083, lang: Lang.en), 'VNS 2552 · VS 2083');
  });

  group('instants relative to the day shown', () {
    const day = CivilDate(2026, 10, 22);

    test('on the same day: just the clock', () {
      expect(instantPhrase(wall(14, 48), day: day, lang: Lang.hi), 'दोपहर 2:48');
    });

    test('on another day: the date as well, never a relative word', () {
      expect(instantPhrase(DateTime(2026, 10, 23, 1, 5), day: day, lang: Lang.hi), '23 अक्टूबर, रात 1:05');
      expect(instantPhrase(DateTime(2026, 10, 21, 18, 10), day: day, lang: Lang.en), '21 October, 6:10 PM');
    });

    test('a span dates both ends when either falls on another day', () {
      expect(spanPhrases(DateTime(2026, 10, 21, 9, 41), DateTime(2026, 10, 22, 7, 2), day: day, lang: Lang.en), (
        '21 October, 9:41 AM',
        '22 October, 7:02 AM',
      ));
      expect(spanPhrases(DateTime(2026, 10, 22, 7, 2), DateTime(2026, 10, 23, 1, 5), day: day, lang: Lang.hi), (
        '22 अक्टूबर, सुबह 7:02',
        '23 अक्टूबर, रात 1:05',
      ));
    });

    test('a span within the day shows just the clock', () {
      expect(spanPhrases(wall(7, 2), wall(9, 41), day: day, lang: Lang.hi), ('सुबह 7:02', 'सुबह 9:41'));
    });
  });
}
