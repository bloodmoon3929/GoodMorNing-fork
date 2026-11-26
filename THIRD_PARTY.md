# Sources and notices

- UI reference and wordmark: https://github.com/mokma18/goodmorning-prototype-demo (pinned submodule `prototype`).
- Sticker geometry: https://github.com/bloodmoon3929/goodmorning-3d, `pipeline/sticker.py`. The CPU map, mesh and GLB functions are copied into `server/vendor/sticker_geometry.py`; its header identifies the source commit. The original CUDA rendering and SAM 3D inference paths are not used for new uploaded photos.
- Three.js and its addons: upstream goodmorning-3d `viewer/vendor`, MIT. The license is retained in `server/scene/vendor/LICENSE-three.txt`.
- Spark: upstream viewer vendor, MIT. Its license is retained alongside it; diary rendering uses the GLB surface.
- SAM 2.1: https://github.com/facebookresearch/sam2 (Apache-2.0).
- SAM 2.1 ONNX conversion: https://huggingface.co/onnx-community/sam2.1-hiera-tiny-ONNX, revision `814a066640debee5a91e70aa401fb8e17e030503`. Model weights are downloaded locally and are not committed.
- Flutter / Dart packages: see `app/pubspec.lock` and the Flutter dependency licenses exposed by their respective packages.
- Python runtime packages: see `server/requirements-windows-lock.txt`.

This repository does not replace or relicense the upstream projects. Their notices and applicable license terms remain with their components. Refer to the linked source repositories for terms covering original artwork, examples and model weights.
