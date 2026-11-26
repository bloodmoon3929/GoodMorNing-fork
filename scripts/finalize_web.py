"""Give executable bundles content-based URLs to avoid mixed cached releases."""
import hashlib
import json
import os
from pathlib import Path

root = Path(__file__).resolve().parent.parent / 'app/build/web'
main = (root / 'main.dart.js').read_bytes()
revision = hashlib.sha256(main).hexdigest()[:16]
main_name = f'main.{revision}.dart.js'
(root / main_name).write_bytes(main)
bootstrap = (root / 'flutter_bootstrap.js').read_text(encoding='utf-8')
bootstrap = bootstrap.replace('"main.dart.js"', json.dumps(main_name))
bootstrap_name = f'flutter_bootstrap.{hashlib.sha256(bootstrap.encode()).hexdigest()[:16]}.js'
(root / bootstrap_name).write_text(bootstrap, encoding='utf-8')
index = (root / 'index.html').read_text(encoding='utf-8')
index = index.replace("'flutter_bootstrap.js'", repr(bootstrap_name))
index = index.replace('<html lang="ko">', f'<html lang="ko" data-build="{revision}">')
(root / 'index.html').write_text(index, encoding='utf-8')
(root / 'build-info.json').write_text(json.dumps({'revision': revision, 'commit': os.getenv('GITHUB_SHA', 'local')}), encoding='utf-8')
print(f'Published immutable JavaScript bundles: {revision}')
