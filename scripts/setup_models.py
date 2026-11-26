from pathlib import Path
from urllib.request import urlretrieve, urlopen
import json
import hashlib

root = Path(__file__).resolve().parent.parent
dest = root / 'data' / 'models' / 'sam2'
dest.mkdir(parents=True, exist_ok=True)
revision = '814a066640debee5a91e70aa401fb8e17e030503'
base = f'https://huggingface.co/onnx-community/sam2.1-hiera-tiny-ONNX/resolve/{revision}/'
files = ['onnx/vision_encoder.onnx', 'onnx/vision_encoder.onnx_data',
         'onnx/prompt_encoder_mask_decoder.onnx', 'onnx/prompt_encoder_mask_decoder.onnx_data', 'preprocessor_config.json']
manifest = {'repository': 'onnx-community/sam2.1-hiera-tiny-ONNX', 'revision': revision, 'files': {}}
for file in files:
    path = dest / Path(file).name
    if not path.exists():
        print(f'Downloading {file}', flush=True)
        partial = path.with_suffix(path.suffix + '.part')
        urlretrieve(base + file, partial)
        partial.replace(path)
    manifest['files'][path.name] = {'bytes': path.stat().st_size, 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}
(dest / 'manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
print(json.dumps(manifest, indent=2))

