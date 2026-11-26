import 'dart:js_interop';
import 'dart:ui_web' as ui_web;
import 'package:material_ui/material_ui.dart';
import 'package:web/web.dart' as web;
import 'api.dart';

/// Original prototype's CSS safe and navigation, embedded in the Flutter app.
class ReferenceView extends StatefulWidget {
  final bool navigationOnly;
  final int tab;
  final ValueChanged<int> onNavigate;
  const ReferenceView({
    super.key,
    this.navigationOnly = false,
    this.tab = 0,
    required this.onNavigate,
  });
  @override
  State<ReferenceView> createState() => _ReferenceViewState();
}

class _ReferenceViewState extends State<ReferenceView> {
  static int count = 0;
  late final String viewType;
  late final web.HTMLIFrameElement frame;
  late final JSFunction listener;
  @override
  void initState() {
    super.initState();
    viewType = 'reference-${count++}';
    frame = web.HTMLIFrameElement()
      ..src = Api.staticUri(
        widget.navigationOnly
            ? 'reference/nav.html?tab=${widget.tab}'
            : 'reference/index.html?home',
      ).toString()
      ..title = (widget.navigationOnly ? '굿모닝 메뉴' : '내 금고')
      ..style.border = 'none'
      ..style.width = '100%'
      ..style.height = '100%';
    ui_web.platformViewRegistry.registerViewFactory(viewType, (_) => frame);
    listener = ((web.MessageEvent event) {
      if (event.origin != Uri.base.origin ||
          event.source != frame.contentWindow)
        return;
      final data = event.data.dartify();
      if (data is Map &&
          data['source'] == 'goodmorning-reference' &&
          data['tab'] is int) {
        final tab = data['tab'] as int;
        if (tab >= 0 && tab <= 2) widget.onNavigate(tab);
      }
    }).toJS;
    web.window.addEventListener('message', listener);
  }

  @override
  void didUpdateWidget(covariant ReferenceView oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (widget.navigationOnly && oldWidget.tab != widget.tab)
      frame.src = Api.staticUri(
        'reference/nav.html?tab=${widget.tab}',
      ).toString();
  }

  @override
  void dispose() {
    web.window.removeEventListener('message', listener);
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => HtmlElementView(viewType: viewType);
}
