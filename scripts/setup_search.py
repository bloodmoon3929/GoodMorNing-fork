"""Download a fixed, public EmbeddingGemma 2 checkpoint. No photos are uploaded."""
import json
from pathlib import Path
from huggingface_hub import snapshot_download

ROOT=Path(__file__).resolve().parent.parent
REVISION='f9972ac22e696a105c482202646979e33e4b5a1e'
target=ROOT/'data/models/embeddinggemma-2'
snapshot_download('google/embeddinggemma-2',revision=REVISION,local_dir=target)
(target/'goodmorning-manifest.json').write_text(json.dumps({'model':'google/embeddinggemma-2','revision':REVISION}),encoding='utf-8')
print('EmbeddingGemma 2 model files are ready.')
