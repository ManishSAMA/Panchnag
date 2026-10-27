/// One background isolate that keeps the engine warm for the app's lifetime.
/// A fresh `Isolate.run` per read paid 50-240 ms each time to start an isolate
/// and load the time-zone database (plans/mobile-phase2-dart-engine.md, M4).
library;

import 'dart:async';
import 'dart:isolate';

import 'package:panchang_engine/panchang_engine.dart';

import 'day_reading.dart';

final class EngineWorker {
  EngineWorker._(this.isolate, this._requests, this._responses);

  final Isolate isolate;
  final SendPort _requests;
  final ReceivePort _responses;
  final Map<int, Completer<PanchangDay>> _pending = {};
  int _sent = 0;

  /// How many days have been asked for.
  int get reads => _sent;

  static Future<EngineWorker> spawn() async {
    final responses = ReceivePort();
    final ready = Completer<SendPort>();
    late final EngineWorker worker;
    responses.listen(
      (message) => switch (message) {
        final SendPort port => ready.complete(port),
        (final int id, final PanchangDay day) => worker._pending.remove(id)!.complete(day),
        (final int id, final RemoteError error) => worker._pending.remove(id)!.completeError(error),
        _ => throw StateError('Unexpected message from the engine worker: $message'),
      },
    );
    final isolate = await Isolate.spawn(_serve, responses.sendPort, debugName: 'panchang engine');
    worker = EngineWorker._(isolate, await ready.future, responses);
    return worker;
  }

  /// Fails with a [RemoteError] when the engine throws, as on a polar day.
  Future<PanchangDay> read(DayRequest request) {
    final id = _sent++;
    final answer = _pending[id] = Completer<PanchangDay>();
    _requests.send((id, request));
    return answer.future;
  }

  void close() {
    _responses.close();
    isolate.kill(priority: Isolate.immediate);
  }
}

void _serve(SendPort responses) {
  final requests = ReceivePort();
  responses.send(requests.sendPort);
  requests.listen((message) {
    final (int id, DayRequest request) = message as (int, DayRequest);
    try {
      responses.send((id, readDay(request)));
    } on Object catch (error, stack) {
      responses.send((id, RemoteError('$error', '$stack')));
    }
  });
}
