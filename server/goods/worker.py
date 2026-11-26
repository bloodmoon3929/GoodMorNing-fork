"""Loopback-only retrieval service in .venv-search, isolated from SAM 2."""
import base64
import hashlib
import hmac
import io
import json
import logging
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path
from contextlib import asynccontextmanager
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlsplit, urljoin
import httpx
import numpy as np
from PIL import Image
from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel, Field
from .config import ROOT, DATA, MODEL_REVISION, settings
from .coupang import search as coupang_search

log=logging.getLogger('goods-search')
cache=DATA/'goods-cache'; cache.mkdir(parents=True,exist_ok=True)
model=None; model_error=None
model_lock=threading.Lock(); search_lock=threading.Lock()
query_cache={}

def load_model():
    global model, model_error
    with model_lock:
        if model is not None: return model
        try:
            import torch
            from sentence_transformers import SentenceTransformer
            path=DATA/'models/embeddinggemma-2'
            device=settings().get('EMBEDDING_DEVICE','cpu')
            torch.set_num_threads(min(6,torch.get_num_threads()))
            model=SentenceTransformer(str(path),device=device,local_files_only=True,
                config_kwargs={'audio_config':None},model_kwargs={'dtype':torch.float32})
            model_error=None
            return model
        except Exception:
            model_error='EmbeddingGemma 2 모델을 준비하지 못했어요.'
            log.exception('EmbeddingGemma initialization failed')
            raise

def warmup():
    try: load_model()
    except Exception: pass

@asynccontextmanager
async def lifespan(app):
    threading.Thread(target=warmup,daemon=True).start()
    yield

app=FastAPI(lifespan=lifespan,docs_url=None,redoc_url=None,openapi_url=None)

@app.middleware('http')
async def authorize(request:Request,call_next):
    expected=(DATA/'access.key').read_text(encoding='utf-8').strip()
    token=request.headers.get('authorization','').removeprefix('Bearer ')
    if not hmac.compare_digest(token,expected):
        from fastapi.responses import JSONResponse
        return JSONResponse({'detail':'Unauthorized'},status_code=401)
    return await call_next(request)

@app.get('/health')
def health():
    config=settings()
    return {'status':'ok','model':'google/embeddinggemma-2','revision':MODEL_REVISION,
        'model_loaded':model is not None,'model_error':model_error,'device':config.get('EMBEDDING_DEVICE','cpu'),
        'coupang_configured':bool(config.get('COUPANG_ACCESS_KEY') and config.get('COUPANG_SECRET_KEY')),
        'naver':'api_retired_manual_links_only','official_shops':config.get('official_shops',True)}

class Search(BaseModel):
    query:str=Field(min_length=1,max_length=80)
    photo:str=Field(max_length=3_000_000)

def collect(query):
    config=settings()
    # Changing credentials/collection settings immediately invalidates cached configuration errors.
    fingerprint=hashlib.sha256(json.dumps(config,sort_keys=True).encode()).hexdigest()
    key=(query.casefold(),fingerprint)
    cached=query_cache.get(key)
    if cached and time.time()-cached[0] < 900: return cached[1],cached[2]
    products, state=coupang_search(query)
    states=[state,{'source':'네이버','state':'manual','message':'네이버 상품은 링크를 직접 입력해 연결할 수 있어요.'}]
    if config.get('official_shops',True):
        with tempfile.TemporaryDirectory(prefix='goods-',dir=cache) as folder:
            output=str(Path(folder)/'catalog.json')
            try:
                subprocess.run([sys.executable,'-m','server.goods.crawl',query,output],cwd=ROOT,
                    timeout=100,check=True,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE,
                    creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
                data=json.loads(Path(output).read_text(encoding='utf-8'))
                products.extend(data['products']);states.extend(data['sources'])
            except (subprocess.SubprocessError,OSError,ValueError,KeyError):
                states.append({'source':'공식 굿즈몰','state':'unavailable','message':'공식몰에 연결하지 못했어요. 잠시 후 다시 검색해 주세요.'})
    unique=list({p['id']:p for p in products}.values())[:32]
    if len(query_cache)>100: query_cache.clear()
    query_cache[key]=(time.time(),unique,states)
    return unique,states

def remote_image(url):
    if not url: return None
    domains=('coupangcdn.com','pstatic.net','pokemonstore.co.kr','daewonshop.com','cdn-nhncommerce.com','nhncommerce.com','shopby.co.kr')
    try:
        for _ in range(3):
            parsed=urlsplit(url);host=(parsed.hostname or '').lower()
            if parsed.scheme!='https' or parsed.username or parsed.password or parsed.port not in (None,443): return None
            if not any(host==d or host.endswith('.'+d) for d in domains): return None
            with httpx.stream('GET',url,timeout=8,follow_redirects=False,trust_env=False) as response:
                if response.status_code in (301,302,303,307,308):
                    url=urljoin(url,response.headers.get('location',''));continue
                if response.status_code!=200 or not response.headers.get('content-type','').startswith('image/'): return None
                content=bytearray()
                for chunk in response.iter_bytes():
                    content.extend(chunk)
                    if len(content)>5*1024*1024:return None
            image=Image.open(io.BytesIO(content))
            if image.width*image.height>24_000_000:return None
            image=image.convert('RGB');image.thumbnail((384,384))
            return image
    except (httpx.HTTPError,OSError,ValueError,Image.DecompressionBombError): pass
    return None

def embedding(value, identity=None):
    vector_file=cache/(hashlib.sha256((MODEL_REVISION+identity).encode()).hexdigest()+'.npy') if identity else None
    if vector_file and vector_file.exists(): return np.load(vector_file,allow_pickle=False)
    result=load_model().encode([value],normalize_embeddings=True,show_progress_bar=False,
        processing_kwargs={'image':{'max_soft_tokens':280}})[0].astype('float32')
    if vector_file: np.save(vector_file,result,allow_pickle=False)
    return result

@app.post('/search')
def search(body:Search):
    if not search_lock.acquire(blocking=False): raise HTTPException(429,'검색 중이에요. 잠시 후 다시 시도해 주세요.')
    try:
        try:
            raw=base64.b64decode(body.photo,validate=True);photo=Image.open(io.BytesIO(raw))
            if photo.width*photo.height>4_000_000:raise ValueError()
            photo=photo.convert('RGB')
        except (ValueError,OSError):raise HTTPException(422,'사진을 읽지 못했어요.')
        products,sources=collect(body.query)
        if not products:return {'items':[],'sources':sources,'ranking':'no_candidates'}
        try: query_vector=embedding({'image':photo})
        except Exception:raise HTTPException(503,'사진 비교 모델을 준비 중이에요. 잠시 후 다시 시도하거나 상품 링크를 직접 연결해 주세요.')
        ranked=[]
        with ThreadPoolExecutor(max_workers=4) as downloads:
            images=list(downloads.map(lambda item:remote_image(item.get('image_url')),products))
        for product,image in zip(products,images):
            item=dict(product)
            if image is not None:
                output=io.BytesIO();image.save(output,format='JPEG',quality=80);raw=output.getvalue()
                vector=embedding({'image':image},hashlib.sha256(raw).hexdigest())
                item['image_data']=base64.b64encode(raw).decode();item['basis']='image'
            else:
                vector=embedding(item['title'],'text:'+item['title']);item['basis']='text';item['image_data']=None
            item['similarity']=float(np.dot(query_vector,vector))
            item['retrieved_at']=int(time.time());item.pop('image_url',None)
            ranked.append(item)
        ranked.sort(key=lambda x:x['similarity'],reverse=True)
        return {'items':ranked[:8],'sources':sources,'ranking':'embeddinggemma-2','device':str(load_model().device)}
    finally: search_lock.release()
