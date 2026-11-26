import importlib
import io
import json
import struct
import time

import numpy as np
import pytest
from fastapi.testclient import TestClient
from PIL import Image, ImageDraw


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv('GOODMORNING_DATA',str(tmp_path))
    from server import app as module
    module = importlib.reload(module)
    with TestClient(module.app) as client:
        yield client, tmp_path


def photo():
    image=Image.new('RGBA',(200,240),(0,0,0,0))
    draw=ImageDraw.Draw(image);draw.ellipse((35,35,165,205),fill=(230,155,95,255));draw.ellipse((70,90,82,106),fill='black')
    out=io.BytesIO();image.save(out,'PNG');return out.getvalue()


def test_photo_to_gaussian_glb_and_saved_diary(client):
    c,data=client
    job=c.post('/api/stickers',data={'name':'test sticker'},files={'photo':('rabbit.png',photo(),'image/png')})
    assert job.status_code==202,job.text
    ident=job.json()['id']
    for _ in range(100):
        state=c.get('/api/jobs/'+ident).json()
        if state['state'] in ('completed','failed'):break
        time.sleep(.05)
    assert state['state']=='completed',state
    glb=c.get(f'/files/{ident}/sticker.glb').content
    assert struct.unpack('<4sII',glb[:12])==(b'glTF',2,len(glb))
    length=struct.unpack('<I',glb[12:16])[0]
    manifest=json.loads(glb[20:20+length])
    assert manifest['materials'][0]['extensions']['KHR_materials_clearcoat']['clearcoatFactor']==1
    assert c.get(f'/files/{ident}/sticker.ply').content.startswith(b'ply\n')
    metadata=c.get(f'/files/{ident}/sticker.json').json()
    assert metadata['gaussians']['count']>100
    assert metadata['max_height_mm']>0
    diary={'id':'persistent','title':'나의 기록','note':'hello','date':'2026-11-26','paper':'#fff9eb','placements':[
        {'id':'placed','asset_id':ident,'x':.4,'y':.6,'size':.25,'rotation':12}]}
    assert c.put('/api/diaries/persistent',json=diary).status_code==200
    assert next(d for d in c.get('/api/diaries').json() if d['id']=='persistent')==diary
    assert (data/'goodmorning.sqlite3').exists()
    # A fresh SQLite reader verifies persistence outside the request context.
    import sqlite3
    with sqlite3.connect(data/'goodmorning.sqlite3') as db:
        assert json.loads(db.execute("select body from diaries where id='persistent'").fetchone()[0])==diary


def test_reject_invalid_upload_and_geometry(client):
    c,_=client
    assert c.post('/api/stickers',data={'name':'bad'},files={'photo':('fake.png',b'not an image','image/png')}).status_code==400
    assert c.post('/api/stickers',data={'name':'bad','box':'[0,0,0,0]'},files={'photo':('a.png',photo(),'image/png')}).status_code==422
    assert c.get('/files/anything/source.png').status_code==404
    assert c.get('/api/unknown').status_code==404


def test_origin_and_unknown_asset_rejected(client):
    c,_=client
    assert c.post('/api/stickers',headers={'Origin':'https://unrelated.invalid'},data={'name':'bad'},files={'photo':('a.png',photo(),'image/png')}).status_code==403
    diary={'id':'bad','title':'bad','date':'2026-11-26','placements':[{'id':'x','asset_id':'missing','x':.5,'y':.5,'size':.2,'rotation':0}]}
    assert c.put('/api/diaries/bad',json=diary).status_code==422


def test_remote_access_key_required(client):
    c,data=client
    remote={'Host':'preview.trycloudflare.com','cf-ray':'test'}
    assert c.get('/api/assets',headers=remote).status_code==401
    assert c.post('/auth/login',headers=remote,json={'key':'wrong'}).status_code==403
    key=(data/'access.key').read_text()
    assert c.post('/auth/login',headers=remote,json={'key':key}).status_code==200
    assert c.get('/api/assets',headers=remote).status_code==200
