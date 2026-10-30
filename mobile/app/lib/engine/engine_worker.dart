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
  final Map<int, Completer<Object>> _pending = {};
  int _sent = 0;

  /// How many days and months have been asked for.
  int get reads => _sent;

  static Future<EngineWorker> spawn() async {
    final responses = ReceivePort();
    final ready = Completer<SendPort>();
    late final EngineWorker worker;
    responses.listen(
      (message) => switch (message) {
        final SendPort port => ready.complete(port),
        (final int id, final RemoteError error) => worker._pending.remove(id)!.completeError(error),
        (final int id, final Object answer) => worker._pending.remove(id)!.complete(answer),
        _ => throw StateError('Unexpected message from the engine worker: $message'),
      },
    );
    final isolate = await Isolate.spawn(_serve, responses.sendPort, debugName: 'panchang engine');
    worker = EngineWorker._(isolate, await ready.future, responses);
    return worker;
  }

  /// Fails with a [RemoteError] when the engine throws, as on a polar day.
  Future<PanchangDay> read(DayRequest request) => _ask(request);

  /// Fails with a [RemoteError] when the engine throws on any day of the month.
  Future<List<PanchangDay>> readMonth(MonthRequest request) => _ask(request);

  Future<T> _ask<T extends Object>(Object request) async {
    final id = _sent++;
    final answer = _pending[id] = Completer<Object>();
    _requests.send((id, request));
    return await answer.future as T;
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
    final (int id, Object request) = message as (int, Object);
    try {
      responses.send((
        id,
        switch (request) {
          final DayRequest day => readDay(day),
          final MonthRequest month => readMonth(month),
          _ => throw ArgumentError('Not an engine request: $request'),
        },
      ));
    } on Object catch (error, stack) {
      responses.send((id, RemoteError('$error', '$stack')));
    }
  });
}
