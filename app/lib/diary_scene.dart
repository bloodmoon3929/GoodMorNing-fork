import 'dart:js_interop';
import 'dart:ui_web' as ui_web;
import 'package:material_ui/material_ui.dart';
import 'package:web/web.dart' as web;
import 'api.dart';

class DiaryScene extends StatefulWidget {
  final Map<String, dynamic> diary;
  final List<Map<String, dynamic>> assets;
  final void Function(List<dynamic>) onChange;
  final void Function(String?) onSelect;
  final void Function(String) onError;
  final bool tilt;
  final String? selected;
  const DiaryScene({
    super.key,
    required this.diary,
    required this.assets,
    required this.onChange,
    required this.onSelect,
    required this.onError,
    required this.tilt,
    this.selected,
  });
  @override
  State<DiaryScene> createState() => DiarySceneState();
}

class DiarySceneState extends State<DiaryScene> {
  static int count = 0;
  late final String viewType;
  late final web.HTMLIFrameElement frame;
  late final JSFunction listener;
  bool ready = false;
  @override
  void initState() {
    super.initState();
    viewType = 'goodmorning-diary-${count++}';
    frame = web.HTMLIFrameElement()
      ..src = Api.staticUri('scene/index.html').toString()
      ..title = '입체 다이어리 편집'
      ..style.border = 'none'
      ..style.width = '100%'
      ..style.height = '100%';
    ui_web.platformViewRegistry.registerViewFactory(viewType, (_) => frame);
    listener = ((web.MessageEvent event) {
      if (!mounted ||
          event.origin != Uri.base.origin ||
          event.source != frame.contentWindow)
        return;
      final value = event.data.dartify();
      if (value is! Map || value['source'] != 'goodmorning-scene') return;
      switch (value['type']) {
        case 'ready':
          ready = true;
          sync();
        case 'change':
          widget.onChange(List<dynamic>.from(value['placements'] as List));
        case 'select':
          widget.onSelect(value['id'] as String?);
        case 'error':
          widget.onError(value['message'].toString());
      }
    }).toJS;
    web.window.addEventListener('message', listener);
  }

  void send(Map<String, dynamic> data) {
    if (ready)
      frame.contentWindow?.postMessage(
        {'source': 'goodmorning-app', ...data}.jsify(),
        Uri.base.origin.toJS,
      );
  }

  void sync() {
    send({
      'type': 'load',
      'data': {
        'diary': widget.diary,
        'assets': widget.assets
            .map(
              (a) => {
                ...a,
                'thumbnail': Api.uri(a['thumbnail']).toString(),
                'model': a['model'] == null
                    ? null
                    : Api.uri(a['model']).toString(),
              },
            )
            .toList(),
        'headers': Api.headers,
        'selected': widget.selected,
      },
    });
    send({'type': 'tilt', 'enabled': widget.tilt});
  }

  void exportImage() => send({'type': 'export'});
  @override
  void didUpdateWidget(covariant DiaryScene oldWidget) {
    super.didUpdateWidget(oldWidget);
    sync();
  }

  @override
  void dispose() {
    web.window.removeEventListener('message', listener);
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => HtmlElementView(viewType: viewType);
}
