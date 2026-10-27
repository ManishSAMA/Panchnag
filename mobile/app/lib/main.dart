import 'package:flutter/widgets.dart';
import 'package:shared_preferences/shared_preferences.dart';

import 'app.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  runApp(JainPanchangApp(preferences: await SharedPreferences.getInstance()));
}
