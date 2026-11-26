import 'dart:math' as math;
import 'dart:typed_data';
import 'package:flutter/gestures.dart';
import 'package:material_ui/material_ui.dart';

/// Photo gestures are claimed on pointer-down so the parent can scroll only
/// when a gesture starts outside the image. Coordinates include the first touch.
class PhotoSelection extends StatefulWidget {
  final Uint8List bytes;
  final double ratio;
  final Rect? selection;
  final bool enabled;
  final ValueChanged<Rect> onChanged;
  const PhotoSelection({
    super.key,
    required this.bytes,
    required this.ratio,
    required this.selection,
    required this.enabled,
    required this.onChanged,
  });
  @override
  State<PhotoSelection> createState() => _PhotoSelectionState();
}

class _PhotoSelectionState extends State<PhotoSelection> {
  int? pointer;
  Offset? start;
  Rect? preview;
  @override
  Widget build(BuildContext context) => Center(
    child: SizedBox(
      width: math.min(430, 300 * widget.ratio),
      child: AspectRatio(
        aspectRatio: widget.ratio,
        child: LayoutBuilder(
          builder: (_, size) {
            Offset normalized(Offset p) => Offset(
              (p.dx / size.maxWidth).clamp(0, 1),
              (p.dy / size.maxHeight).clamp(0, 1),
            );
            final box = preview ?? widget.selection;
            return RawGestureDetector(
              behavior: HitTestBehavior.opaque,
              gestures: widget.enabled
                  ? {
                      EagerGestureRecognizer:
                          GestureRecognizerFactoryWithHandlers<
                            EagerGestureRecognizer
                          >(() => EagerGestureRecognizer(), (_) {}),
                    }
                  : {},
              child: Listener(
                behavior: HitTestBehavior.opaque,
                onPointerDown: (event) {
                  if (!widget.enabled || pointer != null) return;
                  FocusScope.of(context).unfocus();
                  setState(() {
                    pointer = event.pointer;
                    start = normalized(event.localPosition);
                    preview = Rect.fromPoints(start!, start!);
                  });
                },
                onPointerMove: (event) {
                  if (event.pointer != pointer || start == null) return;
                  setState(
                    () => preview = Rect.fromPoints(
                      start!,
                      normalized(event.localPosition),
                    ),
                  );
                },
                onPointerUp: (event) {
                  if (event.pointer != pointer || start == null) return;
                  final selected = Rect.fromPoints(
                    start!,
                    normalized(event.localPosition),
                  );
                  setState(() {
                    pointer = null;
                    start = null;
                    preview = null;
                  });
                  widget.onChanged(selected);
                },
                onPointerCancel: (event) {
                  if (event.pointer != pointer) return;
                  setState(() {
                    pointer = null;
                    start = null;
                    preview = null;
                  });
                },
                child: Stack(
                  fit: StackFit.expand,
                  children: [
                    Image.memory(
                      widget.bytes,
                      fit: BoxFit.fill,
                      gaplessPlayback: true,
                    ),
                    if (box != null && widget.enabled)
                      Positioned(
                        left: box.left * size.maxWidth,
                        top: box.top * size.maxHeight,
                        width: box.width * size.maxWidth,
                        height: box.height * size.maxHeight,
                        child: IgnorePointer(
                          child: DecoratedBox(
                            decoration: BoxDecoration(
                              color: const Color(0x1460bda0),
                              border: Border.all(
                                color: const Color(0xff62c2a4),
                                width: 2,
                              ),
                            ),
                          ),
                        ),
                      ),
                  ],
                ),
              ),
            );
          },
        ),
      ),
    ),
  );
}
