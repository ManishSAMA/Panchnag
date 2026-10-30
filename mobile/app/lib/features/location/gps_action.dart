import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../l10n/app_localizations.dart';
import '../../location/cities.dart';
import '../../location/gps.dart';
import '../../location/location_store.dart';
import '../../theme/navpad.dart';

/// "Find by GPS": one fix, saved as the location. A refusal or failure leaves
/// an inline note and the location as it was (mobile-ui-design.md §3.0).
class GpsAction extends ConsumerStatefulWidget {
  const GpsAction({super.key, this.onLocated});

  final VoidCallback? onLocated;

  @override
  ConsumerState<GpsAction> createState() => _GpsActionState();
}

class _GpsActionState extends ConsumerState<GpsAction> {
  bool _busy = false;
  GpsOutcome? _failure;

  Future<void> _locate() async {
    setState(() {
      _busy = true;
      _failure = null;
    });
    final outcome = await ref.read(gpsLocatorProvider)();
    if (!mounted) return;
    setState(() {
      _busy = false;
      _failure = outcome is GpsFix ? null : outcome;
    });
    if (outcome case GpsFix(:final lat, :final lon, :final timezone)) {
      await ref.read(locationProvider.notifier).choose(GpsPlace(lat: lat, lon: lon, timezone: timezone));
      widget.onLocated?.call();
    }
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    final note = switch (_failure) {
      GpsDenied() => l10n.gpsDenied,
      GpsOff() => l10n.gpsOff,
      GpsNoFix() => l10n.gpsNoFix,
      GpsFix() || null => null,
    };
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        FilledButton.tonalIcon(
          onPressed: _busy ? null : _locate,
          style: FilledButton.styleFrom(minimumSize: const Size(48, 48)),
          icon: _busy
              ? const SizedBox.square(dimension: 18, child: CircularProgressIndicator(strokeWidth: 2))
              : const Icon(Icons.my_location),
          label: Text(_busy ? l10n.findingLocation : l10n.findByGps),
        ),
        if (note != null) _InlineNote(text: note),
      ],
    );
  }
}

class _InlineNote extends StatelessWidget {
  const _InlineNote({required this.text});

  final String text;

  @override
  Widget build(BuildContext context) {
    final n = Theme.of(context).extension<Navpad>()!;
    return Semantics(
      liveRegion: true,
      child: Padding(
        padding: const EdgeInsets.only(top: 10),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Icon(Icons.info_outline, size: 20, color: n.ink2),
            const SizedBox(width: 8),
            Expanded(
              child: Text(text, style: Theme.of(context).textTheme.bodyMedium!.copyWith(color: n.ink2)),
            ),
          ],
        ),
      ),
    );
  }
}
