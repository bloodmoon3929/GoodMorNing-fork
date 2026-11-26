-- Additive SQLite migration. Private user data remains in existing tables.
CREATE TABLE IF NOT EXISTS schema_migrations(version TEXT PRIMARY KEY, applied_at REAL NOT NULL);
CREATE TABLE IF NOT EXISTS catalog_products(
 id TEXT PRIMARY KEY, name TEXT NOT NULL, maker TEXT, description TEXT,
 state TEXT NOT NULL DEFAULT 'unverified' CHECK(state IN ('unverified','verified','retired')),
 created_at REAL NOT NULL, updated_at REAL NOT NULL);
CREATE TABLE IF NOT EXISTS catalog_variants(
 id TEXT PRIMARY KEY, product_id TEXT NOT NULL REFERENCES catalog_products(id),
 name TEXT NOT NULL, attrs TEXT NOT NULL DEFAULT '{}', barcode TEXT UNIQUE,
 created_at REAL NOT NULL);
CREATE TABLE IF NOT EXISTS catalog_malls(
 id TEXT PRIMARY KEY, name TEXT NOT NULL, origin TEXT NOT NULL,
 method TEXT NOT NULL CHECK(method IN ('api','crawl')), created_at REAL NOT NULL);
CREATE TABLE IF NOT EXISTS catalog_offers(
 id TEXT PRIMARY KEY, mall_id TEXT NOT NULL REFERENCES catalog_malls(id),
 external_id TEXT NOT NULL, variant_id TEXT REFERENCES catalog_variants(id),
 title TEXT NOT NULL, title_search TEXT NOT NULL, url TEXT NOT NULL, image_url TEXT,
 price INTEGER CHECK(price IS NULL OR price >= 0), currency TEXT NOT NULL DEFAULT 'KRW',
 shipping_fee INTEGER CHECK(shipping_fee IS NULL OR shipping_fee >= 0),
 availability TEXT NOT NULL DEFAULT 'unknown' CHECK(availability IN ('unknown','available','sold_out')),
 affiliate INTEGER NOT NULL DEFAULT 0 CHECK(affiliate IN (0,1)),
 observed_at REAL NOT NULL, created_at REAL NOT NULL, UNIQUE(mall_id,external_id));
CREATE INDEX IF NOT EXISTS catalog_offers_recent ON catalog_offers(observed_at DESC);
CREATE INDEX IF NOT EXISTS catalog_offers_variant ON catalog_offers(variant_id);
CREATE TABLE IF NOT EXISTS catalog_offer_history(
 id INTEGER PRIMARY KEY, offer_id TEXT NOT NULL REFERENCES catalog_offers(id),
 price INTEGER, shipping_fee INTEGER, availability TEXT NOT NULL, observed_at REAL NOT NULL);
CREATE INDEX IF NOT EXISTS catalog_history_offer ON catalog_offer_history(offer_id,observed_at DESC);
CREATE TABLE IF NOT EXISTS catalog_collect_jobs(
 id TEXT PRIMARY KEY, source TEXT NOT NULL, query_hash TEXT NOT NULL,
 state TEXT NOT NULL, item_count INTEGER NOT NULL, started_at REAL NOT NULL, finished_at REAL NOT NULL);
CREATE TABLE IF NOT EXISTS catalog_raw_listings(
 id INTEGER PRIMARY KEY, job_id TEXT NOT NULL REFERENCES catalog_collect_jobs(id),
 offer_id TEXT NOT NULL REFERENCES catalog_offers(id), payload TEXT NOT NULL,
 match_state TEXT NOT NULL DEFAULT 'pending' CHECK(match_state IN ('pending','matched','review','rejected')),
 collected_at REAL NOT NULL);
CREATE TABLE IF NOT EXISTS catalog_query_cache(
 query_hash TEXT NOT NULL, config_hash TEXT NOT NULL, checked_at REAL NOT NULL,
 sources TEXT NOT NULL, PRIMARY KEY(query_hash,config_hash));
CREATE TABLE IF NOT EXISTS catalog_query_offers(
 query_hash TEXT NOT NULL, offer_id TEXT NOT NULL REFERENCES catalog_offers(id),
 seen_at REAL NOT NULL, PRIMARY KEY(query_hash,offer_id));
CREATE TABLE IF NOT EXISTS catalog_images(
 offer_id TEXT PRIMARY KEY REFERENCES catalog_offers(id), source_url TEXT NOT NULL,
 local_path TEXT NOT NULL, sha256 TEXT NOT NULL, width INTEGER NOT NULL, height INTEGER NOT NULL,
 observed_at REAL NOT NULL);
CREATE TABLE IF NOT EXISTS catalog_embeddings(
 offer_id TEXT NOT NULL REFERENCES catalog_offers(id), kind TEXT NOT NULL CHECK(kind IN ('image','text')),
 model TEXT NOT NULL, revision TEXT NOT NULL, content_hash TEXT NOT NULL,
 dimensions INTEGER NOT NULL CHECK(dimensions > 0), dtype TEXT NOT NULL DEFAULT 'float32-le',
 vector BLOB NOT NULL CHECK(length(vector)=dimensions*4), created_at REAL NOT NULL,
 PRIMARY KEY(offer_id,kind,revision));
CREATE TABLE IF NOT EXISTS asset_product_links(
 asset_id TEXT PRIMARY KEY REFERENCES assets(id), owner TEXT NOT NULL,
 offer_id TEXT REFERENCES catalog_offers(id), variant_id TEXT REFERENCES catalog_variants(id),
 method TEXT NOT NULL CHECK(method IN ('manual','user_selected_recommendation')),
 snapshot TEXT NOT NULL, confirmed_at REAL NOT NULL);
CREATE INDEX IF NOT EXISTS asset_product_links_owner ON asset_product_links(owner);
