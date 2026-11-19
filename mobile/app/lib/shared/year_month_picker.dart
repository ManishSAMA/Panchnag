import 'package:flutter/material.dart';

import '../features/today/today_state.dart';
import '../format/panchang_text.dart';
import '../l10n/app_localizations.dart';
import '../theme/navpad.dart';

typedef YearMonth = ({int year, int month});

/// A year the app covers ([firstDay] to [lastDay]); null when cancelled.
Future<int?> pickYear(BuildContext context, {required int selected}) => showDialog<int>(
  context: context,
  builder: (context) => _PickerDialog(
    title: AppLocalizations.of(context).pickYear,
    child: _YearGrid(selected: selected, onPicked: (year) => Navigator.of(context).pop(year)),
  ),
);

/// A year, then a month of it; null when cancelled.
Future<YearMonth?> pickYearMonth(BuildContext context, {required YearMonth selected}) =>
    showDialog<YearMonth>(context: context, builder: (context) => _YearMonthDialog(selected: selected));

class _YearMonthDialog extends StatefulWidget {
  const _YearMonthDialog({required this.selected});

  final YearMonth selected;

  @override
  State<_YearMonthDialog> createState() => _YearMonthDialogState();
}

class _YearMonthDialogState extends State<_YearMonthDialog> {
  int? _year;

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    final lang = langOf(context);
    final year = _year;
    if (year == null) {
      return _PickerDialog(
        title: l10n.pickYear,
        child: _YearGrid(selected: widget.selected.year, onPicked: (year) => setState(() => _year = year)),
      );
    }
    final current = year == widget.selected.year ? widget.selected.month : null;
    return _PickerDialog(
      title: '${l10n.pickMonth} · $year',
      onTitle: () => setState(() => _year = null),
      child: _ChoiceGrid(
        width: 112,
        choices: [
          for (var month = 1; month <= 12; month++)
            (key: 'month-$month', label: gregorianMonthName(month, lang), selected: month == current, value: month),
        ],
        onPicked: (month) => Navigator.of(context).pop((year: year, month: month)),
      ),
    );
  }
}

class _YearGrid extends StatelessWidget {
  const _YearGrid({required this.selected, required this.onPicked});

  final int selected;
  final ValueChanged<int> onPicked;

  @override
  Widget build(BuildContext context) => _ChoiceGrid(
    width: 84,
    choices: [
      for (var year = firstDay.year; year <= lastDay.year; year++)
        (key: 'year-$year', label: '$year', selected: year == selected, value: year),
    ],
    onPicked: onPicked,
  );
}

typedef _Choice = ({String key, String label, bool selected, int value});

/// Wrapped 48 dp buttons; the chosen one sits on the pill, as a selected chip does.
class _ChoiceGrid extends StatelessWidget {
  const _ChoiceGrid({required this.width, required this.choices, required this.onPicked});

  final double width;
  final List<_Choice> choices;
  final ValueChanged<int> onPicked;

  @override
  Widget build(BuildContext context) {
    final n = Theme.of(context).extension<Navpad>()!;
    return Wrap(
      alignment: WrapAlignment.center,
      spacing: 8,
      runSpacing: 8,
      children: [
        for (final c in choices)
          ConstrainedBox(
            constraints: BoxConstraints(minWidth: width),
            child: TextButton(
              key: Key(c.key),
              style: TextButton.styleFrom(
                minimumSize: const Size(48, 48),
                backgroundColor: c.selected ? n.pill : null,
                foregroundColor: n.ink,
                shape: const StadiumBorder(),
              ),
              onPressed: () => onPicked(c.value),
              child: Text(c.label, maxLines: 1, softWrap: false),
            ),
          ),
      ],
    );
  }
}

class _PickerDialog extends StatelessWidget {
  const _PickerDialog({required this.title, required this.child, this.onTitle});

  final String title;
  final Widget child;
  final VoidCallback? onTitle;

  @override
  Widget build(BuildContext context) {
    final text = Theme.of(context).textTheme;
    final heading = Text(title, style: text.titleLarge);
    return Dialog(
      child: ConstrainedBox(
        constraints: const BoxConstraints(maxWidth: 420),
        child: Padding(
          padding: const EdgeInsets.fromLTRB(20, 20, 20, 8),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              onTitle == null
                  ? heading
                  : Align(
                      alignment: AlignmentDirectional.centerStart,
                      child: TextButton.icon(
                        onPressed: onTitle,
                        icon: const Icon(Icons.arrow_back),
                        label: heading,
                      ),
                    ),
              const SizedBox(height: 16),
              Flexible(child: SingleChildScrollView(child: child)),
              Align(
                alignment: AlignmentDirectional.centerEnd,
                child: TextButton(
                  onPressed: () => Navigator.of(context).pop(),
                  child: Text(MaterialLocalizations.of(context).cancelButtonLabel),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
