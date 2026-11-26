import json,time
from pathlib import Path
import httpx
import numpy as np
from PIL import Image

ROOT=Path(__file__).resolve().parent.parent
folder=ROOT/'sticker-engine/assets/pochita/sam3d_input'
photo=next(folder.glob('*.jpg'))
reference=np.asarray(Image.open(next(folder.glob('*mask*'))).convert('L'))>127
y,x=np.nonzero(reference)
box=[float(x.min()/reference.shape[1]),float(y.min()/reference.shape[0]),float(x.max()/reference.shape[1]),float(y.max()/reference.shape[0])]
with httpx.Client(base_url='http://127.0.0.1:8787',timeout=60) as client:
    response=client.post('/api/stickers',data={'name':'포치타 · 나의 첫 스티커','box':json.dumps(box)},files={'photo':('pochita.jpg',photo.read_bytes(),'image/jpeg')})
    response.raise_for_status();ident=response.json()['id'];start=time.monotonic()
    while time.monotonic()-start<120:
        job=client.get('/api/jobs/'+ident).json()
        if job['state'] in ('completed','failed'):break
        time.sleep(.3)
    assert job['state']=='completed',job
    info=client.get(f'/files/{ident}/sticker.json').json()
    assert info['segmentation']=='sam2.1-directml',info
    assert info['gaussians']['count']>100
    diary={'id':'first-photo-sticker','title':'오늘도 귀여운 하루','note':'내 사진으로 만든 첫 볼록 스티커!\n좋아하는 것들을 하나씩 모아 보기.','date':'2026-11-26','paper':'#fff9eb','placements':[
        {'id':'my-first-sticker','asset_id':ident,'x':.43,'y':.53,'size':.48,'rotation':-8},
        {'id':'rabbit','asset_id':'2026_11_24_08_16','x':.76,'y':.77,'size':.25,'rotation':14}]}
    client.put('/api/diaries/'+diary['id'],json=diary).raise_for_status()
    result={'job':job,'metadata':info,'seconds':time.monotonic()-start,'diary':diary['id']}
    out=ROOT/'data/verification';out.mkdir(parents=True,exist_ok=True)
    (out/'end-to-end.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False,indent=2))
