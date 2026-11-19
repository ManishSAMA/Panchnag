import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:panchang_engine/panchang_engine.dart';

import '../features/today/today_state.dart';
import '../l10n/app_localizations.dart';
import '../location/city_time.dart';
import '../location/location_store.dart';

DateTime _local(CivilDate d) => DateTime(d.year, d.month, d.day);

/// Opens the phone's calendar on the date shown. A picked date goes to
/// [selectedDateProvider], so every screen with a date row follows it.
Future<void> pickDate(BuildContext context, WidgetRef ref) async {
  final city = ref.read(locationProvider)!;
  final picked = await showDatePicker(
    context: context,
    initialDate: _local(ref.read(selectedDateProvider)),
    firstDate: _local(firstDay),
    lastDate: _local(lastDay),
    currentDate: _local(todayIn(city.timezone, ref.read(clockProvider)())),
    helpText: AppLocalizations.of(context).pickDate,
  );
  if (picked == null) return;
  ref.read(selectedDateProvider.notifier).goTo(CivilDate(picked.year, picked.month, picked.day));
}

/// The calendar in the top bar of every screen that has a date row.
class DatePickerButton extends ConsumerWidget {
  const DatePickerButton({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) => IconButton(
    icon: const Icon(Icons.calendar_month_outlined),
    tooltip: AppLocalizations.of(context).pickDate,
    onPressed: () => pickDate(context, ref),
  );
}
