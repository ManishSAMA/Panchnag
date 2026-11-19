import 'package:flutter/painting.dart';
import 'package:panchang_engine/panchang_engine.dart';

import '../l10n/app_localizations.dart';
import '../theme/navpad.dart';

/// Whether a time or a sign is good for beginning work.
enum Mark { good, plain, avoid }

/// The glyph and the word, so a mark never rests on colour.
String markText(AppLocalizations l10n, Mark mark) => switch (mark) {
  Mark.good => '✓ ${l10n.natureGood}',
  Mark.plain => '–',
  Mark.avoid => '✕ ${l10n.natureAvoid}',
};

/// ✓ green and ✕ red, so a person sees at once what to avoid; – stays quiet.
Color markColour(Navpad n, Mark mark) => switch (mark) {
  Mark.good => n.markGood,
  Mark.plain => n.ink2,
  Mark.avoid => n.markAvoid,
};

Mark markOfNature(ChoghadiyaNature nature) => switch (nature) {
  ChoghadiyaNature.auspicious => Mark.good,
  ChoghadiyaNature.neutral => Mark.plain,
  ChoghadiyaNature.inauspicious => Mark.avoid,
};
