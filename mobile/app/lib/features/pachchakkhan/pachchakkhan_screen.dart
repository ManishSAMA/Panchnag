import 'package:flutter/material.dart';

import '../../l10n/app_localizations.dart';

class PachchakkhanScreen extends StatelessWidget {
  const PachchakkhanScreen({super.key});

  @override
  Widget build(BuildContext context) =>
      Scaffold(appBar: AppBar(title: Text(AppLocalizations.of(context).tabPachchakkhan)));
}
