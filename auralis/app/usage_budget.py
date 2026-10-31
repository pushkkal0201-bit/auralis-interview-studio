"""Live-model rate budgeting.

Local mode: process-wide best-effort cap. Hosted mode: transactionally shared
PostgreSQL counters, for per-account and global limits across workers.
Every attempted provider call is charged before the network request is sent.
This is an availability/cost guard, not a subscription or fraud prevention system.
"""
import os
import time
from collections import deque
from .provider import ProviderError
from .database import connect, is_postgres


class UsageBudget:
    def __init__(self, database_path=None):
        self.minute=deque()
        self.hour=deque()
        self.minute_cap=max(2,min(120,int(os.getenv('AURALIS_MAX_CALLS_PER_MINUTE','15'))))
        self.hour_cap=max(5,min(1000,int(os.getenv('AURALIS_MAX_CALLS_PER_HOUR','90'))))
        self.global_minute_cap=max(self.minute_cap,min(2000,int(os.getenv('AURALIS_GLOBAL_CALLS_PER_MINUTE','60'))))
        self.global_hour_cap=max(self.hour_cap,min(10000,int(os.getenv('AURALIS_GLOBAL_CALLS_PER_HOUR','500'))))
        self.database_path=database_path
        if database_path:
            with connect(database_path) as db:
                db.execute('CREATE TABLE IF NOT EXISTS ai_usage (id BIGSERIAL PRIMARY KEY, owner TEXT NOT NULL, created_at DOUBLE PRECISION NOT NULL)') if is_postgres(database_path) else db.execute('CREATE TABLE IF NOT EXISTS ai_usage (id INTEGER PRIMARY KEY AUTOINCREMENT, owner TEXT NOT NULL, created_at REAL NOT NULL)')
                db.execute('CREATE INDEX IF NOT EXISTS ai_usage_owner_time_idx ON ai_usage(owner,created_at)')
                db.execute('CREATE INDEX IF NOT EXISTS ai_usage_time_idx ON ai_usage(created_at)')

    def consume(self, owner=None):
        if self.database_path:
            if not isinstance(owner,str) or not owner or len(owner)>160:
                raise ProviderError('Account identity required for hosted AI requests.',401)
            now=time.time()
            with connect(self.database_path) as db:
                db.execute('BEGIN IMMEDIATE')  # PG advisory transaction lock
                db.execute('DELETE FROM ai_usage WHERE created_at<?',(now-3600,))
                personal_minute=db.execute('SELECT COUNT(*) FROM ai_usage WHERE owner=? AND created_at>=?',(owner,now-60)).fetchone()[0]
                personal_hour=db.execute('SELECT COUNT(*) FROM ai_usage WHERE owner=? AND created_at>=?',(owner,now-3600)).fetchone()[0]
                global_minute=db.execute('SELECT COUNT(*) FROM ai_usage WHERE created_at>=?',(now-60,)).fetchone()[0]
                global_hour=db.execute('SELECT COUNT(*) FROM ai_usage WHERE created_at>=?',(now-3600,)).fetchone()[0]
                if (personal_minute>=self.minute_cap or personal_hour>=self.hour_cap or
                    global_minute>=self.global_minute_cap or global_hour>=self.global_hour_cap):
                    raise ProviderError('Live interview request limit reached. Your saved progress is safe. Try again later.',429,60)
                db.execute('INSERT INTO ai_usage(owner,created_at) VALUES(?,?)',(owner,now))
            return
        now=time.monotonic()
        while self.minute and self.minute[0]<=now-60:self.minute.popleft()
        while self.hour and self.hour[0]<=now-3600:self.hour.popleft()
        if len(self.minute)>=self.minute_cap or len(self.hour)>=self.hour_cap:
            raise ProviderError('Live-AI request budget reached. Your session is safe; retry later.',429,60)
        self.minute.append(now)
        self.hour.append(now)

    def stats(self):
        # No usage details are disclosed from the hosted service.
        if self.database_path:return {'mode':'shared_database'}
        return {'minute_remaining':max(0,self.minute_cap-len(self.minute)),
                'hour_remaining':max(0,self.hour_cap-len(self.hour))}
