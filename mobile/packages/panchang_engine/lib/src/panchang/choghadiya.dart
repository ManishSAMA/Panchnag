/// Choghadiya: day and night each split into eight equal slots, named from a
/// seven-name cycle that starts at the weekday's slot (Python `choghadiya_service`).
library;

enum ChoghadiyaNature { auspicious, neutral, inauspicious }

enum Choghadiya {
  udveg(ChoghadiyaNature.inauspicious),
  char(ChoghadiyaNature.neutral),
  labh(ChoghadiyaNature.auspicious),
  amrit(ChoghadiyaNature.auspicious),
  kaal(ChoghadiyaNature.inauspicious),
  shubh(ChoghadiyaNature.auspicious),
  rog(ChoghadiyaNature.inauspicious);

  const Choghadiya(this.nature);

  final ChoghadiyaNature nature;
}

const _dayOrder = [
  Choghadiya.udveg, Choghadiya.char, Choghadiya.labh, Choghadiya.amrit, //
  Choghadiya.kaal, Choghadiya.shubh, Choghadiya.rog,
];
const _nightOrder = [
  Choghadiya.shubh, Choghadiya.amrit, Choghadiya.char, Choghadiya.rog, //
  Choghadiya.kaal, Choghadiya.labh, Choghadiya.udveg,
];

/// Where each vara (0 = Sunday) starts in the day and night orders.
const _dayStart = [0, 3, 6, 2, 5, 1, 4];
const _nightStart = [0, 2, 4, 6, 5, 3, 1];

/// Julian Days (UT).
typedef ChoghadiyaSlot = ({Choghadiya name, double start, double end, bool isNight});

List<ChoghadiyaSlot> choghadiyaSlots({
  required double sunrise,
  required double sunset,
  required double nextSunrise,
  required int vara,
}) {
  List<ChoghadiyaSlot> half(double start, double end, List<Choghadiya> order, int first, {required bool isNight}) {
    final length = (end - start) / 8;
    return [
      for (var i = 0; i < 8; i++)
        (name: order[(first + i) % 7], start: start + i * length, end: start + (i + 1) * length, isNight: isNight),
    ];
  }

  return [
    ...half(sunrise, sunset, _dayOrder, _dayStart[vara], isNight: false),
    ...half(sunset, nextSunrise, _nightOrder, _nightStart[vara], isNight: true),
  ];
}
