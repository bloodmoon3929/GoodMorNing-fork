"""Public server discovery address only. Never embed an access key in Pages."""
import json
import os
from pathlib import Path
from urllib.parse import urlsplit

address = os.getenv('GOODMORNING_GPU_URL', '').strip().rstrip('/')
if address:
    parsed = urlsplit(address)
    if parsed.scheme != 'https' or not parsed.netloc or parsed.username or parsed.password or parsed.path or parsed.query or parsed.fragment:
        raise ValueError('GPU_API_URL must be an HTTPS origin, without a key or path.')
target = Path(__file__).resolve().parent.parent / 'app/web/runtime-config.json'
target.write_text(json.dumps({'apiBase': address}), encoding='utf-8')
print('Wrote public GPU server discovery configuration (no credentials).')
