/// The Navpad building blocks from DESIGN.md "Components": bands, notes,
/// section headings and hairline list rows.
library;

import 'package:flutter/material.dart';

import '../theme/navpad.dart';

enum BandColour { red, yellow, green, navy }

/// A full-bleed colour band: title and sub-line left, value and chevron right.
class Band extends StatelessWidget {
  const Band({
    super.key,
    required this.colour,
    required this.title,
    required this.subtitle,
    required this.value,
    required this.onTap,
  });

  final BandColour colour;
  final String title, subtitle, value;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final n = Theme.of(context).extension<Navpad>()!;
    final (background, foreground, secondary) = switch (colour) {
      BandColour.red => (n.red, n.onRed, n.onRed2),
      BandColour.yellow => (n.yellow, n.onYellow, n.onYellow2),
      BandColour.green => (n.green, n.onGreen, n.onGreen2),
      BandColour.navy => (n.navy, n.onNavy, n.onNavy2),
    };
    final text = Theme.of(context).textTheme;
    final stacked = MediaQuery.textScalerOf(context).scale(1) >= 1.6;
    final valueText = Text(
      value,
      textAlign: TextAlign.end,
      style: text.labelLarge!.copyWith(color: foreground),
    );
    final label = Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      mainAxisSize: MainAxisSize.min,
      children: [
        Text(title, style: NavpadType.titleBand.copyWith(color: foreground)),
        Text(subtitle, style: text.labelMedium!.copyWith(color: secondary)),
        if (stacked) valueText,
      ],
    );
    return Material(
      color: background,
      child: InkWell(
        onTap: onTap,
        child: ConstrainedBox(
          constraints: const BoxConstraints(minHeight: 58),
          child: Padding(
            padding: const EdgeInsets.fromLTRB(18, 9, 12, 9),
            child: Row(
              children: [
                Expanded(child: label),
                if (!stacked) ...[const SizedBox(width: 12), Flexible(child: valueText)],
                Icon(Icons.chevron_right, size: 20, color: foreground),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

enum NoteIcon { info, alert }

/// The only bordered container: a surface box with an icon, a title and a body.
class Note extends StatelessWidget {
  const Note({super.key, required this.icon, required this.title, required this.body});

  final NoteIcon icon;
  final String title, body;

  @override
  Widget build(BuildContext context) {
    final n = Theme.of(context).extension<Navpad>()!;
    final text = Theme.of(context).textTheme;
    return Semantics(
      container: true,
      child: Container(
        margin: const EdgeInsets.symmetric(horizontal: 18),
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
        decoration: BoxDecoration(
          color: n.surface,
          border: Border.all(color: n.hair),
          borderRadius: BorderRadius.circular(8),
        ),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Icon(icon == NoteIcon.info ? Icons.info_outline : Icons.warning_amber_rounded, size: 22, color: n.ink),
            const SizedBox(width: 10),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(title, style: text.bodyLarge!.copyWith(fontWeight: FontWeight.w700)),
                  const SizedBox(height: 2),
                  Text(body, style: text.bodyMedium!.copyWith(color: n.ink2)),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

/// A section heading, 30 dp below what precedes it, with an optional link.
class SectionHeading extends StatelessWidget {
  const SectionHeading({super.key, required this.title, this.linkLabel, this.onLink});

  final String title;
  final String? linkLabel;
  final VoidCallback? onLink;

  @override
  Widget build(BuildContext context) {
    final text = Theme.of(context).textTheme;
    return Padding(
      padding: const EdgeInsets.fromLTRB(18, 30, 6, 6),
      child: Row(
        children: [
          Expanded(
            child: Semantics(header: true, child: Text(title, style: text.titleLarge)),
          ),
          if (linkLabel != null)
            TextButton(
              onPressed: onLink,
              style: TextButton.styleFrom(
                foregroundColor: Theme.of(context).colorScheme.onSurface,
                textStyle: text.labelLarge!.copyWith(decoration: TextDecoration.underline),
              ),
              child: Text(linkLabel!),
            ),
        ],
      ),
    );
  }
}

enum RowState { plain, done, next }

/// A hairline list row: a name (and sub-line) left, a time column right.
class TimeRow extends StatelessWidget {
  const TimeRow({
    super.key,
    required this.name,
    required this.time,
    this.subtitle,
    this.prefix,
    this.suffix,
    this.state = RowState.plain,
    this.semanticsLabel,
  });

  final String name, time;
  final String? subtitle, prefix, suffix, semanticsLabel;
  final RowState state;

  @override
  Widget build(BuildContext context) {
    final n = Theme.of(context).extension<Navpad>()!;
    final text = Theme.of(context).textTheme;
    final (background, ink, secondary) = switch (state) {
      RowState.plain => (n.ground, n.ink, n.ink2),
      RowState.done => (n.ground, n.ink3, n.ink3),
      RowState.next => (n.yellow, n.onYellow, n.onYellow2),
    };
    final small = text.labelMedium!.copyWith(color: secondary, fontSize: 15);
    final row = Container(
      constraints: const BoxConstraints(minHeight: 52),
      padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 8),
      decoration: BoxDecoration(
        color: background,
        border: Border(bottom: BorderSide(color: state == RowState.next ? n.yellow : n.hair)),
      ),
      child: Row(
        children: [
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(name, style: text.bodyLarge!.copyWith(color: ink)),
                if (subtitle != null) Text(subtitle!, style: text.labelMedium!.copyWith(color: secondary)),
              ],
            ),
          ),
          const SizedBox(width: 12),
          Flexible(
            child: Align(
              alignment: AlignmentDirectional.centerEnd,
              child: Wrap(
                alignment: WrapAlignment.end,
                crossAxisAlignment: WrapCrossAlignment.center,
                spacing: 6,
                children: [
                  if (state == RowState.done) Icon(Icons.check, size: 18, color: ink),
                  if (prefix != null) Text(prefix!, style: small),
                  Text(
                    time,
                    style: text.bodyLarge!.copyWith(
                      color: ink,
                      fontWeight: state == RowState.done ? FontWeight.w500 : FontWeight.w600,
                    ),
                  ),
                  if (suffix != null) Text(suffix!, style: small),
                ],
              ),
            ),
          ),
        ],
      ),
    );
    return semanticsLabel == null ? row : Semantics(label: semanticsLabel, excludeSemantics: true, child: row);
  }
}

/// A list's top hairline.
class ListTop extends StatelessWidget {
  const ListTop({super.key});

  @override
  Widget build(BuildContext context) =>
      Divider(height: 1, thickness: 1, color: Theme.of(context).extension<Navpad>()!.hair);
}
