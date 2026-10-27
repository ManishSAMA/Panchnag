import 'package:panchang_engine/panchang_engine.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../features/today/today_state.dart';
import '../format/panchang_text.dart';
import '../l10n/app_localizations.dart';
import '../location/city_time.dart';

/// ‹ date ›, shared by every tab through [selectedDateProvider].
class DateNavigator extends ConsumerWidget {
  const DateNavigator({super.key, required this.date, required this.timezone});

  final CivilDate date;
  final String timezone;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l10n = AppLocalizations.of(context);
    final text = Theme.of(context).textTheme;
    final selected = ref.read(selectedDateProvider.notifier);
    final isToday = date == todayIn(timezone, currentTime(ref));
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 6),
      child: Row(
        children: [
          IconButton(
            icon: const Icon(Icons.chevron_left),
            tooltip: l10n.previousDay,
            onPressed: date.compareTo(firstDay) > 0 ? () => selected.shift(-1) : null,
          ),
          Expanded(
            child: Column(
              children: [
                Text(
                  longDate(date, langOf(context)),
                  textAlign: TextAlign.center,
                  style: text.bodyLarge!.copyWith(fontWeight: FontWeight.w600),
                ),
                if (isToday)
                  Text(
                    l10n.today,
                    style: text.bodyMedium!.copyWith(color: Theme.of(context).colorScheme.onSurfaceVariant),
                  )
                else
                  ActionChip(label: Text(l10n.today), onPressed: selected.goToday),
              ],
            ),
          ),
          IconButton(
            icon: const Icon(Icons.chevron_right),
            tooltip: l10n.nextDay,
            onPressed: date.compareTo(lastDay) < 0 ? () => selected.shift(1) : null,
          ),
        ],
      ),
    );
  }
}
