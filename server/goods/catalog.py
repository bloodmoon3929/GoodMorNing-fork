"""Persistent public product candidates; private photos never enter this catalog."""
from contextlib import contextmanager
import hashlib
import json
import sqlite3
import time
import unicodedata
import uuid
from pathlib import Path
from urllib.parse import urlsplit
from .config import DATA, product_url

VERSION = '20261126_goods_catalog_v1'
DB = DATA / 'goodmorning.sqlite3'


@contextmanager
def connection():
    con = sqlite3.connect(DB, timeout=30)
    con.row_factory = sqlite3.Row
    con.execute('PRAGMA foreign_keys=ON')
    try:
        with con:
            yield con
    finally:
        con.close()


def initialize():
    DATA.mkdir(parents=True, exist_ok=True)
    with connection() as con:
        con.execute('PRAGMA journal_mode=WAL')
        # SQL is packaged source; no runtime/user text is interpolated.
        sql = Path(__file__).with_suffix('.sql').read_text(encoding='utf-8')
        try:
            con.executescript('BEGIN IMMEDIATE;\n' + sql)
            con.execute('INSERT OR IGNORE INTO schema_migrations VALUES(?,?)', (VERSION, time.time()))
            con.commit()
        except Exception:
            con.rollback()
            raise


def normalized(value):
    return ' '.join(unicodedata.normalize('NFKC', str(value)).casefold().split())


def digest(value):
    return hashlib.sha256(value.encode()).hexdigest()


def query_key(query):
    return digest(normalized(query))


def cached_sources(query, config_hash):
    with connection() as con:
        row = con.execute('SELECT * FROM catalog_query_cache WHERE query_hash=? AND config_hash=?',
                          (query_key(query), config_hash)).fetchone()
    return json.loads(row['sources']) if row and time.time() - row['checked_at'] < 900 else None


def record_collection(query, config_hash, products, sources, started_at):
    """Persist only public listing fields, never request headers/config/user images."""
    observed = time.time()
    key = query_key(query)
    by_source = {}
    for product in products:
        by_source.setdefault(product['source'], []).append(product)
    with connection() as con:
        for state in sources:
            source = state['source']
            job = uuid.uuid4().hex
            rows = by_source.pop(source, [])
            con.execute('INSERT INTO catalog_collect_jobs VALUES(?,?,?,?,?,?,?)',
                        (job, source, key, state['state'], len(rows), started_at, observed))
            for product in rows:
                url = product_url(product['url'])
                parts = urlsplit(url)
                origin = f'https://{parts.hostname}'
                mall = digest(source + '|' + origin)
                method = 'api' if source == '쿠팡' else 'crawl'
                con.execute('INSERT OR IGNORE INTO catalog_malls VALUES(?,?,?,?,?)',
                            (mall, source, origin, method, observed))
                external = str(product.get('id') or url)
                ident = 'offer-' + digest(mall + '|' + external)[:32]
                price = product.get('price')
                price = price if type(price) is int and price >= 0 else None
                previous = con.execute('SELECT price,shipping_fee,availability FROM catalog_offers WHERE id=?', (ident,)).fetchone()
                title = str(product['title'])[:300]
                con.execute('''INSERT INTO catalog_offers
                    (id,mall_id,external_id,title,title_search,url,image_url,price,affiliate,observed_at,created_at)
                    VALUES(?,?,?,?,?,?,?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET
                    title=excluded.title,title_search=excluded.title_search,url=excluded.url,
                    image_url=excluded.image_url,price=excluded.price,affiliate=excluded.affiliate,
                    observed_at=excluded.observed_at''',
                    (ident,mall,external,title,normalized(title),url,product.get('image_url'),price,
                     int(bool(product.get('affiliate'))),observed,observed))
                if previous is None or previous['price'] != price:
                    con.execute('INSERT INTO catalog_offer_history(offer_id,price,shipping_fee,availability,observed_at) VALUES(?,?,?,?,?)',
                                (ident,price,previous['shipping_fee'] if previous else None,
                                 previous['availability'] if previous else 'unknown',observed))
                payload = {k: product.get(k) for k in ('id','title','source','url','image_url','price','affiliate')}
                con.execute('INSERT INTO catalog_raw_listings(job_id,offer_id,payload,collected_at) VALUES(?,?,?,?)',
                            (job,ident,json.dumps(payload,ensure_ascii=False),observed))
                con.execute('INSERT INTO catalog_query_offers VALUES(?,?,?) ON CONFLICT(query_hash,offer_id) DO UPDATE SET seen_at=excluded.seen_at',
                            (key,ident,observed))
        con.execute('INSERT INTO catalog_query_cache VALUES(?,?,?,?) ON CONFLICT(query_hash,config_hash) DO UPDATE SET checked_at=excluded.checked_at,sources=excluded.sources',
                    (key,config_hash,observed,json.dumps(sources,ensure_ascii=False)))


def candidates(query, limit=32):
    # Previously found results survive a source outage. A bounded pool keeps CPU work predictable.
    words = normalized(query).split()[:8]
    escaped = [word.replace('\\','\\\\').replace('%','\\%').replace('_','\\_') for word in words]
    conditions = ' OR '.join("o.title_search LIKE ? ESCAPE '\\'" for _ in words) or '0'
    with connection() as con:
        rows = con.execute(f'''SELECT o.*, m.name AS source FROM catalog_offers o
            JOIN catalog_malls m ON m.id=o.mall_id
            LEFT JOIN catalog_query_offers q ON q.offer_id=o.id AND q.query_hash=?
            WHERE q.offer_id IS NOT NULL OR {conditions}
            ORDER BY (q.offer_id IS NOT NULL) DESC,o.observed_at DESC LIMIT ?''',
            [query_key(query), *['%'+word+'%' for word in escaped], limit]).fetchall()
    return [{'id':r['id'],'offer_id':r['id'],'variant_id':r['variant_id'],'title':r['title'],
             'url':r['url'],'source':r['source'],'image_url':r['image_url'],'price':r['price'],
             'affiliate':bool(r['affiliate']),'observed_at':int(r['observed_at']),
             'stale':time.time()-r['observed_at']>86400} for r in rows]


def image_record(offer_id):
    with connection() as con:
        row=con.execute('SELECT * FROM catalog_images WHERE offer_id=?',(offer_id,)).fetchone()
    return dict(row) if row else None


def record_image(offer_id, source_url, path, sha, width, height):
    with connection() as con:
        con.execute('''INSERT INTO catalog_images VALUES(?,?,?,?,?,?,?) ON CONFLICT(offer_id) DO UPDATE SET
          source_url=excluded.source_url,local_path=excluded.local_path,sha256=excluded.sha256,
          width=excluded.width,height=excluded.height,observed_at=excluded.observed_at''',
          (offer_id,source_url,path,sha,width,height,time.time()))


def vector(offer_id, kind, revision, content_hash):
    with connection() as con:
        row=con.execute('SELECT dimensions,vector FROM catalog_embeddings WHERE offer_id=? AND kind=? AND revision=? AND content_hash=?',
                        (offer_id,kind,revision,content_hash)).fetchone()
    return (row['dimensions'],row['vector']) if row else None


def record_vector(offer_id, kind, revision, content_hash, dimensions, value):
    with connection() as con:
        con.execute('''INSERT INTO catalog_embeddings(offer_id,kind,model,revision,content_hash,dimensions,vector,created_at)
          VALUES(?,?,?,?,?,?,?,?) ON CONFLICT(offer_id,kind,revision) DO UPDATE SET
          content_hash=excluded.content_hash,dimensions=excluded.dimensions,vector=excluded.vector,created_at=excluded.created_at''',
          (offer_id,kind,'google/embeddinggemma-2',revision,content_hash,dimensions,value,time.time()))


def link_asset(con, asset_id, owner, goods):
    if not goods or not goods.get('confirmed_by_user'): return
    # A personal choice never verifies or merges the shared product catalog.
    offer_id = goods.get('offer_id')
    offer=con.execute('SELECT id,variant_id FROM catalog_offers WHERE id=?',(offer_id,)).fetchone() if offer_id else None
    method=goods.get('match_method')
    if method not in ('manual','user_selected_recommendation'): return
    snapshot={k:goods[k] for k in ('title','url','source','affiliate','price','observed_at','match_method','confirmed_at') if k in goods}
    con.execute('''INSERT OR IGNORE INTO asset_product_links VALUES(?,?,?,?,?,?,?)''',
                (asset_id,owner,offer['id'] if offer else None,offer['variant_id'] if offer else None,
                 method,json.dumps(snapshot,ensure_ascii=False),goods.get('confirmed_at') or time.time()))


def backfill_links(con):
    for row in con.execute('''SELECT a.id,a.metadata,COALESCE(o.owner,'private') AS owner FROM assets a
      LEFT JOIN ownership o ON o.kind='asset' AND o.ident=a.id
      LEFT JOIN asset_product_links l ON l.asset_id=a.id WHERE l.asset_id IS NULL''').fetchall():
        link_asset(con,row['id'],row['owner'],json.loads(row['metadata']).get('goods'))
