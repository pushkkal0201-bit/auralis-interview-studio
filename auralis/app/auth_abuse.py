"""Account-endpoint throttling shared across hosted workers.

Stores only SHA-256 digests of normalized identifiers, not email addresses,
passwords, tokens, IP addresses or request bodies. This supplements, rather
than replaces, Supabase and edge-level anti-abuse controls.
"""
from __future__ import annotations
import hashlib
import os
import time
from fastapi import HTTPException
from .database import connect, is_postgres

class AuthAttemptBudget:
    def __init__(self, path):
        self.path = path
        self.personal_cap = max(2, min(30, int(os.getenv('AURALIS_AUTH_ATTEMPTS_PER_15M', '8'))))
        self.global_cap = max(self.personal_cap, min(3000, int(os.getenv('AURALIS_AUTH_GLOBAL_PER_MINUTE', '90'))))
        with connect(self.path) as db:
            id_type = 'BIGSERIAL' if is_postgres(self.path) else 'INTEGER PRIMARY KEY AUTOINCREMENT'
            primary = 'BIGSERIAL PRIMARY KEY' if is_postgres(self.path) else id_type
            db.execute(f'CREATE TABLE IF NOT EXISTS auth_attempts (id {primary}, identity_hash TEXT NOT NULL, created_at DOUBLE PRECISION NOT NULL)')
            db.execute('CREATE INDEX IF NOT EXISTS auth_attempts_identity_time_idx ON auth_attempts(identity_hash, created_at)')
            db.execute('CREATE INDEX IF NOT EXISTS auth_attempts_time_idx ON auth_attempts(created_at)')

    def consume(self, operation: str, identity: str):
        # Never keep raw emails, passwords, or cookie tokens in the database.
        if operation not in {'login', 'signup', 'recover', 'refresh', 'password', 'delete'}:
            raise ValueError('Unsupported authentication operation')
        if not isinstance(identity, str) or not identity or len(identity) > 8192:
            raise HTTPException(400, 'Invalid account request.')
        key = hashlib.sha256((operation + ':' + identity.strip().casefold()).encode('utf-8')).hexdigest()
        now = time.time()
        with connect(self.path) as db:
            db.execute('BEGIN IMMEDIATE')
            db.execute('DELETE FROM auth_attempts WHERE created_at<?', (now - 900,))
            personal = db.execute('SELECT COUNT(*) FROM auth_attempts WHERE identity_hash=? AND created_at>=?', (key, now - 900)).fetchone()[0]
            global_recent = db.execute('SELECT COUNT(*) FROM auth_attempts WHERE created_at>=?', (now - 60,)).fetchone()[0]
            if personal >= self.personal_cap or global_recent >= self.global_cap:
                raise HTTPException(429, 'Too many account requests. Please try again later.', headers={'Retry-After': '60'})
            db.execute('INSERT INTO auth_attempts(identity_hash,created_at) VALUES(?,?)', (key, now))
