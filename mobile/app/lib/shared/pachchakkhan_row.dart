import 'package:flutter/widgets.dart';

import '../l10n/app_localizations.dart';
import 'navpad_widgets.dart';

/// A pachchakkhan row. [state] is null on a day other than today, where no row
/// is done or next and the screen reader hears only the name and time.
Widget pachchakkhanRow({
  required AppLocalizations l10n,
  required String name,
  required String time,
  required RowState? state,
  String? subtitle,
  String? prefix,
}) {
  final word = switch (state) {
    RowState.done => l10n.stateDone,
    RowState.next => l10n.stateNext,
    RowState.plain => l10n.stateLeft,
    null => null,
  };
  return TimeRow(
    name: name,
    subtitle: subtitle,
    time: time,
    prefix: prefix,
    state: state ?? RowState.plain,
    semanticsLabel: word == null ? '$name $time' : l10n.rowSemantics(name, time, word),
  );
}
