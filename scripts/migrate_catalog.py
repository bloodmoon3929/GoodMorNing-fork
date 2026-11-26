"""Back up the local DB, rehearse additive migration, then optionally apply it.
Stop both application servers before --apply. Never prints database row contents.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sqlite3
import sys
import tempfile
from datetime import datetime, timezone

ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT))
from server.goods import catalog

LEGACY=('assets','ownership','jobs','diaries','notebook_pages','notebook_files','asset_trash','goods_searches')

def fingerprints(path):
    result={}
    con=sqlite3.connect(path)
    try:
        tables={r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        for table in LEGACY:
            if table not in tables:continue
            rows=sorted(hashlib.sha256(repr(tuple(row)).encode()).digest() for row in con.execute('SELECT * FROM '+table))
            result[table]=(len(rows),hashlib.sha256(b''.join(rows)).hexdigest())
    finally:con.close()
    return result

def verify(path, before):
    if fingerprints(path)!=before:raise RuntimeError('Existing application data changed; stop migration.')
    con=sqlite3.connect(path)
    try:
        if con.execute('PRAGMA integrity_check').fetchone()[0]!='ok':raise RuntimeError('Database integrity check failed.')
        if con.execute('PRAGMA foreign_key_check').fetchall():raise RuntimeError('Foreign key validation failed.')
    finally:con.close()

def apply(path):
    original=catalog.DB
    try:
        catalog.DB=path
        catalog.initialize()
        with catalog.connection() as con:catalog.backfill_links(con)
    finally:catalog.DB=original

def copy_database(source,target):
    src=sqlite3.connect(source);dst=sqlite3.connect(target)
    try:src.backup(dst)
    finally:dst.close();src.close()

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--apply',action='store_true')
    args=parser.parse_args()
    source=catalog.DB
    if not source.is_file():raise RuntimeError('Existing local database not found.')
    if args.apply:
        con=sqlite3.connect(source)
        try:
            busy=con.execute("SELECT COUNT(*) FROM jobs WHERE state IN ('queued','running')").fetchone()[0]
            busy+=con.execute("SELECT COUNT(*) FROM goods_searches WHERE state='running'").fetchone()[0]
            if busy:raise RuntimeError('Active jobs found; wait for them before migration.')
        finally:con.close()
    backups=source.parent/'backups';backups.mkdir(exist_ok=True)
    stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    backup=backups/f'before-catalog-{stamp}.sqlite3'
    copy_database(source,backup)
    before=fingerprints(backup)
    with tempfile.TemporaryDirectory(prefix='catalog-rehearsal-',dir=backups) as folder:
        copy=Path(folder)/'rehearsal.sqlite3'
        copy_database(backup,copy)
        apply(copy);verify(copy,before)
        apply(copy);verify(copy,before)
    if args.apply:
        if fingerprints(source)!=before:raise RuntimeError('Database changed after backup; stop both servers and retry.')
        apply(source);verify(source,before)
    print(json.dumps({'migration':catalog.VERSION,'applied':args.apply,
                      'legacy_tables_preserved':len(before),'integrity':'ok','repeat_migration':'ok',
                      'backup':str(backup)},ensure_ascii=False))

if __name__=='__main__':main()
