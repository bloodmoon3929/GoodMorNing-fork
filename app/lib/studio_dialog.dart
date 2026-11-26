import 'package:material_ui/material_ui.dart';
import 'package:web/web.dart' as web;

int _openDialogs = 0;

/// Embedded HTML viewers must not receive touches through a Flutter modal.
Future<T?> showStudioDialog<T>({
  required BuildContext context,
  required WidgetBuilder builder,
}) async {
  if (web.document.getElementById('goodmorning-dialog-pointer-style') == null) {
    final style = web.HTMLStyleElement()
      ..id = 'goodmorning-dialog-pointer-style'
      ..textContent =
          'html.goodmorning-dialog-open iframe { pointer-events: none !important; }';
    web.document.head?.append(style);
  }
  _openDialogs++;
  web.document.documentElement?.classList.add('goodmorning-dialog-open');
  try {
    return await showDialog<T>(
      context: context,
      useRootNavigator: true,
      builder: builder,
    );
  } finally {
    // Keep the underlying viewers blocked during the closing animation too.
    await Future<void>.delayed(const Duration(milliseconds: 300));
    if (--_openDialogs == 0)
      web.document.documentElement?.classList.remove('goodmorning-dialog-open');
  }
}
