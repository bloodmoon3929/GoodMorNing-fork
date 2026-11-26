"""Bundle the pinned prototype home and 3D viewers into Flutter's static web output.

Run before flutter build web, locally and in GitHub Actions. No user data is copied.
"""
from pathlib import Path
import base64
import json
import re
import shutil
import urllib.request

ROOT = Path(__file__).resolve().parent.parent
WEB = ROOT / 'app' / 'web'
REF = WEB / 'reference'
SOURCE = ROOT / 'prototype' / 'index.html'
REF.mkdir(parents=True, exist_ok=True)
html = SOURCE.read_text(encoding='utf-8')
css = re.search(r'<style>(.*?)</style>', html, re.S).group(1)
nav = re.search(r'<nav class="bottom-nav".*?</nav>', html, re.S).group(0)
previews = json.loads(re.search(r'<script id="rendered-previews" type="application/json">(.*?)</script>', html, re.S).group(1))
wordmark=previews['wordmark']
banner = re.search(r'<img class="brand-banner" src="(data:image/jpeg;base64,[^"]+)"',html).group(1)
(ROOT/'app/assets/brand-banner.jpg').write_bytes(base64.b64decode(banner.split(',',1)[1]))

# Original layout, safe geometry, colors, navigation icons, gestures, and home editing.
# Only relative resource URLs and cross-frame navigation are adapted.
html=html.replace('https://bloodmoon3929.github.io/goodmorning-3d/viewer/vendor/', '../scene/vendor/')
html=html.replace("const viewerBase = 'https://bloodmoon3929.github.io/goodmorning-3d/viewer/';", "const viewerBase = new URL('./upstream/viewer/', location.href).href;")
html=html.replace("const teamAssets = 'https://bloodmoon3929.github.io/goodmorning-3d/assets/';", "const teamAssets = new URL('./upstream/assets/', location.href).href;")
html=html.replace('location.href = diaryLink.href;', "parent.postMessage({source:'goodmorning-reference',tab:2},location.origin);")

# Bundle source typefaces; keep original fallbacks if a font is unavailable at build time.
for filename in ('Cafe24SsurroundAir.woff','Cafe24Ssurround.woff'):
    url='https://cdn.jsdelivr.net/gh/projectnoonnu/noonfonts_2105_2@1.0/'+filename
    target=REF/'fonts'/filename
    target.parent.mkdir(exist_ok=True)
    if not target.exists():
        urllib.request.urlretrieve(url,target)
    html=html.replace(url,'fonts/'+filename)
    css=css.replace(url,'fonts/'+filename)

bridge='''<script>
document.addEventListener('click',event=>{
  const link=event.target.closest('a[data-section], .topbar h1 a');
  if(!link || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
  const section=link.dataset.section||'home';
  if(section==='magnets' && !draft) return; // Source safe-opening animation navigates through its own bridge.
  event.preventDefault();event.stopImmediatePropagation();
  parent.postMessage({source:'goodmorning-reference',tab:section==='assets'?1:section==='magnets'?2:0},location.origin);
},true);
</script>'''
html=html.replace('</body>',bridge+'</body>')
(REF/'index.html').write_text(html,encoding='utf-8')
(REF/'source.css').write_text(css,encoding='utf-8')
nav=nav.replace('data-wordmark',f'src="{wordmark}"')
(REF/'nav.html').write_text('''<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><link rel="stylesheet" href="source.css"><style>html,body{height:100%;overflow:hidden}.bottom-nav{width:100%;position:absolute}</style></head><body>'''+nav+'''<script>
const tabs=['home','assets','magnets'];
document.querySelector('[data-section="'+tabs[Number(new URLSearchParams(location.search).get('tab'))||0]+'"]').setAttribute('aria-current','page');
document.addEventListener('click',event=>{const link=event.target.closest('a');if(!link)return;event.preventDefault();parent.postMessage({source:'goodmorning-reference',tab:tabs.indexOf(link.dataset.section)},location.origin);});
</script></body></html>''',encoding='utf-8')

shutil.copytree(ROOT/'server/scene',WEB/'scene',dirs_exist_ok=True)
shutil.copytree(ROOT/'sticker-engine/viewer/vendor',WEB/'scene/vendor',dirs_exist_ok=True)
for ident in ('pochita','2026_11_24_08_15','2026_11_24_08_16'):
    dest=REF/'upstream/assets'/ident
    dest.mkdir(parents=True,exist_ok=True)
    for filename in ('sticker.png','sticker.glb'):
        shutil.copy2(ROOT/'sticker-engine/assets'/ident/filename,dest/filename)
    dest=REF/'upstream/viewer/data'/ident
    dest.mkdir(parents=True,exist_ok=True)
    source=ROOT/'sticker-engine/viewer/data'/ident
    manifest=json.loads((source/'manifest.json').read_text(encoding='utf-8'))
    # These are pre-existing sample magnets, not the new photo generation pipeline.
    manifest['methods']=[method for method in manifest['methods'] if method['id']=='sam3d']
    (dest/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False),encoding='utf-8')
    shutil.copy2(source/'sam3d.splat',dest/'sam3d.splat')
print('Bundled original home, navigation, fonts, sample assets, and local diary renderer.')
