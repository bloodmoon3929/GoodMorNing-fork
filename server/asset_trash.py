"""Reversible asset removal with server-side exact-name confirmation."""
from fastapi import Request, HTTPException
from pydantic import BaseModel, Field

class Confirmation(BaseModel):
    name: str = Field(min_length=1, max_length=60)

def initialize(con):
    con.execute('CREATE TABLE IF NOT EXISTS asset_trash(owner TEXT NOT NULL, asset_id TEXT NOT NULL, deleted_at TEXT NOT NULL, PRIMARY KEY(owner,asset_id))')

def hidden(con, owner, ident):
    return con.execute('SELECT 1 FROM asset_trash WHERE owner=? AND asset_id=?',(owner,ident)).fetchone() is not None

def register(app, connection, accessible, asset_dict, now, samples):
    @app.post('/api/assets/{ident}/trash')
    def trash(ident: str, confirmation: Confirmation, request: Request):
        with connection() as con:
            con.execute('BEGIN IMMEDIATE')
            row=con.execute('SELECT * FROM assets WHERE id=?',(ident,)).fetchone()
            if not row or not accessible(con,'asset',ident,request.state.owner):
                raise HTTPException(404,'에셋을 찾지 못했어요.')
            if ident in samples:
                raise HTTPException(403,'기본 샘플 에셋은 삭제할 수 없어요.')
            if confirmation.name != row['name']:
                raise HTTPException(422,'스티커 이름을 정확히 입력해야 삭제할 수 있어요.')
            con.execute('INSERT OR IGNORE INTO asset_trash VALUES(?,?,?)',(request.state.owner,ident,now()))
        return {'trashed':True,'id':ident}

    @app.get('/api/trash')
    def list_trash(request: Request):
        with connection() as con:
            rows=con.execute('SELECT a.*, t.deleted_at FROM assets a JOIN asset_trash t ON a.id=t.asset_id WHERE t.owner=? ORDER BY t.deleted_at DESC',(request.state.owner,)).fetchall()
            return [asset_dict(row) for row in rows if accessible(con,'asset',row['id'],request.state.owner)]

    @app.post('/api/trash/{ident}/restore')
    def restore(ident: str, request: Request):
        with connection() as con:
            row=con.execute('SELECT * FROM assets WHERE id=?',(ident,)).fetchone()
            if not row or not accessible(con,'asset',ident,request.state.owner):
                raise HTTPException(404,'에셋을 찾지 못했어요.')
            con.execute('DELETE FROM asset_trash WHERE owner=? AND asset_id=?',(request.state.owner,ident))
        return {'restored':True,'id':ident}
