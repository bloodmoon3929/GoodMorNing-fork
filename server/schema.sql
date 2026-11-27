-- Application tables (PostgreSQL). Same columns and order as the former SQLite
-- tables; times are TIMESTAMPTZ and JSON documents are JSONB.
CREATE TABLE IF NOT EXISTS ownership(
 kind text NOT NULL, ident text NOT NULL, owner text NOT NULL, PRIMARY KEY(kind, ident));
CREATE TABLE IF NOT EXISTS assets(
 id text PRIMARY KEY, name text NOT NULL, kind text NOT NULL, engine text NOT NULL,
 created timestamptz NOT NULL, metadata jsonb NOT NULL);
CREATE TABLE IF NOT EXISTS jobs(
 id text PRIMARY KEY, name text NOT NULL, state text NOT NULL, progress integer NOT NULL,
 message text NOT NULL, asset_id text, created timestamptz NOT NULL);
CREATE TABLE IF NOT EXISTS diaries(
 id text PRIMARY KEY, body jsonb NOT NULL, updated timestamptz NOT NULL);
CREATE TABLE IF NOT EXISTS notebook_pages(
 owner text NOT NULL, page_key text NOT NULL, body jsonb NOT NULL, updated timestamptz NOT NULL,
 PRIMARY KEY(owner, page_key));
CREATE TABLE IF NOT EXISTS notebook_files(
 id text PRIMARY KEY, owner text NOT NULL, name text NOT NULL, mime text NOT NULL);
CREATE TABLE IF NOT EXISTS asset_trash(
 owner text NOT NULL, asset_id text NOT NULL, deleted_at timestamptz NOT NULL, PRIMARY KEY(owner, asset_id));
CREATE TABLE IF NOT EXISTS goods_searches(
 id text PRIMARY KEY, owner text NOT NULL, state text NOT NULL, body jsonb NOT NULL, created timestamptz NOT NULL);
