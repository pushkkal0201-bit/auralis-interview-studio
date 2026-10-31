"""Local SQLite or hosted PostgreSQL. Revision-checked session writes."""
import json
import sqlite3
from .database import connect as db_connect, is_postgres
import time
import os
from pathlib import Path

class Store:
    def __init__(self, directory):
        self.path = directory if is_postgres(directory) else str(Path(directory)/'auralis.sqlite3')
        if not is_postgres(self.path): Path(directory).mkdir(parents=True, exist_ok=True)
        with self.connect() as c:
            c.execute('PRAGMA journal_mode=WAL')
            c.execute('CREATE TABLE IF NOT EXISTS sessions (id TEXT PRIMARY KEY, owner TEXT NOT NULL, revision INTEGER NOT NULL, payload TEXT NOT NULL)')
            c.execute('CREATE TABLE IF NOT EXISTS source_evidence (id TEXT PRIMARY KEY, owner TEXT NOT NULL, created_at REAL NOT NULL, payload TEXT NOT NULL)')
            c.execute('CREATE TABLE IF NOT EXISTS practice_attempts (id INTEGER PRIMARY KEY AUTOINCREMENT, owner TEXT NOT NULL, created_at REAL NOT NULL, kind TEXT NOT NULL, challenge_id TEXT NOT NULL, passed INTEGER NOT NULL, total INTEGER NOT NULL)')
            c.execute('CREATE TABLE IF NOT EXISTS learning_plans (owner TEXT PRIMARY KEY, created_at REAL NOT NULL, payload TEXT NOT NULL)')
    def connect(self):
        return db_connect(self.path, timeout=10)
    def create(self, s, owner):
        with self.connect() as c:
            c.execute('INSERT INTO sessions VALUES (?,?,?,?)',(s['id'],owner,0,json.dumps(s)))
    def load(self, sid, owner):
        with self.connect() as c:
            row=c.execute('SELECT payload FROM sessions WHERE id=? AND owner=?',(sid,owner)).fetchone()
        return json.loads(row[0]) if row else None
    def save(self, s, owner):
        revision=s['revision']; s['revision']+=1
        with self.connect() as c:
            result=c.execute('UPDATE sessions SET revision=?,payload=? WHERE id=? AND owner=? AND revision=?',(s['revision'],json.dumps(s),s['id'],owner,revision))
            if result.rowcount != 1:
                raise RuntimeError('Session changed. Refresh before continuing.')
    def list(self, owner):
        with self.connect() as c:
            rows=c.execute(('SELECT payload FROM sessions WHERE owner=? ORDER BY (payload::jsonb->>\'created_at\')::double precision DESC LIMIT 100' if is_postgres(self.path) else 'SELECT payload FROM sessions WHERE owner=? ORDER BY rowid DESC LIMIT 100'),(owner,)).fetchall()
        return [json.loads(r[0]) for r in rows]
    def delete(self,sid,owner):
        with self.connect() as c:
            c.execute('DELETE FROM sessions WHERE id=? AND owner=?',(sid,owner))

    def save_source(self,source_id,owner,payload):
        with self.connect() as c:
            c.execute('INSERT INTO source_evidence (id,owner,created_at,payload) VALUES (?,?,?,?)',
                      (source_id,owner,time.time(),json.dumps(payload)))

    def load_source(self,source_id,owner):
        with self.connect() as c:
            row=c.execute('SELECT payload,created_at FROM source_evidence WHERE id=? AND owner=?',
                          (source_id,owner)).fetchone()
        if not row or time.time()-row[1] > 48*3600:
            return None
        return json.loads(row[0])

    def record_practice(self,owner,kind,challenge_id,passed,total):
        """Persist score metadata only; never submitted code or explanations."""
        with self.connect() as c:
            c.execute('INSERT INTO practice_attempts (owner,created_at,kind,challenge_id,passed,total) VALUES (?,?,?,?,?,?)',
                      (owner,time.time(),kind,challenge_id,int(passed),int(total)))
            c.execute('DELETE FROM practice_attempts WHERE owner=? AND id NOT IN (SELECT id FROM practice_attempts WHERE owner=? ORDER BY id DESC LIMIT 200)',(owner,owner))

    def list_practice(self,owner):
        with self.connect() as c:
            rows=c.execute('SELECT created_at,kind,challenge_id,passed,total FROM practice_attempts WHERE owner=? ORDER BY id DESC LIMIT 100',(owner,)).fetchall()
        return [{'created_at':r[0],'kind':r[1],'challenge_id':r[2],'passed':r[3],'total':r[4]} for r in rows]

    def load_plan(self, owner):
        with self.connect() as c:
            row=c.execute('SELECT payload FROM learning_plans WHERE owner=?',(owner,)).fetchone()
        return json.loads(row[0]) if row else None

    def replace_plan(self,owner,plan):
        # At most one current plan per owner; replacing it discards old checkboxes.
        with self.connect() as c:
            c.execute('INSERT OR REPLACE INTO learning_plans (owner,created_at,payload) VALUES (?,?,?)',
                      (owner,time.time(),json.dumps(plan)))

    def update_plan_task(self,owner,plan_id,task_id,status):
        # Atomic read/write stops simultaneous updates from silently undoing each other.
        with self.connect() as c:
            c.execute('BEGIN IMMEDIATE')
            row=c.execute('SELECT payload FROM learning_plans WHERE owner=?',(owner,)).fetchone()
            if not row: return None
            plan=json.loads(row[0])
            if plan['id']!=plan_id: return None
            matching=next((task for task in plan['tasks'] if task['id']==task_id),None)
            if not matching: return None
            matching['status']=status
            from datetime import datetime,timezone
            matching['completed_at']=datetime.now(timezone.utc).isoformat() if status=='completed' else None
            plan['revision']+=1
            c.execute('UPDATE learning_plans SET payload=? WHERE owner=?',(json.dumps(plan),owner))
            return plan

    def delete_plan(self,owner):
        with self.connect() as c:
            result=c.execute('DELETE FROM learning_plans WHERE owner=?',(owner,))
            return bool(result.rowcount)

    def delete_owner(self,owner):
        """Delete only sessions belonging to this browser's workspace."""
        with self.connect() as c:
            result=c.execute('DELETE FROM sessions WHERE owner=?',(owner,))
            c.execute('DELETE FROM source_evidence WHERE owner=?',(owner,))
            c.execute('DELETE FROM practice_attempts WHERE owner=?',(owner,))
            c.execute('DELETE FROM learning_plans WHERE owner=?',(owner,))
            return result.rowcount

    def purge_expired(self,days):
        """Automatic local retention, disabled if days=0."""
        if days<=0:
            # Disabling *session* retention does not disable short-lived source evidence expiry.
            with self.connect() as c:
                c.execute('DELETE FROM source_evidence WHERE created_at<?',(time.time()-48*3600,))
                # No session expiry policy when retention is disabled.
            return 0
        cutoff=time.time()-days*86400
        with self.connect() as c:
            rows=c.execute('SELECT id,payload FROM sessions').fetchall()
            stale=[]
            for sid,payload in rows:
                try:created=json.loads(payload).get('created_at',0)
                except (ValueError,TypeError):continue
                if isinstance(created,(float,int)) and created<cutoff:stale.append((sid,))
            if stale:c.executemany('DELETE FROM sessions WHERE id=?',stale)
            c.execute('DELETE FROM source_evidence WHERE created_at<?',(time.time()-48*3600,))
            c.execute('DELETE FROM practice_attempts WHERE created_at<?',(cutoff,))
            c.execute('DELETE FROM learning_plans WHERE created_at<?',(cutoff,))
            return len(stale)
