"""Database adapter for legacy Auralis queries. PostgreSQL is required in hosted mode.

The app retains SQLite only for local development. No automatic bulk migration:
A reviewed, separate import is required for existing SQLite accounts.
"""
import re
import sqlite3


def is_postgres(path):
    return str(path).startswith(('postgresql://', 'postgres://'))


class PGCursor:
    def __init__(self, cursor): self.cursor = cursor
    @property
    def rowcount(self): return self.cursor.rowcount
    def fetchone(self): return self.cursor.fetchone()
    def fetchall(self): return self.cursor.fetchall()
    def __iter__(self): return iter(self.cursor)


class PGConnection:
    def __init__(self, dsn):
        try:
            import psycopg
        except ImportError as e:
            raise RuntimeError('PostgreSQL mode requires psycopg[binary]. Install requirements.txt.') from e
        self.conn = psycopg.connect(dsn.replace('postgres://','postgresql://',1),connect_timeout=8)
        self.row_factory = None
    def __enter__(self): self.conn.__enter__(); return self
    def __exit__(self,*args): return self.conn.__exit__(*args)
    def execute(self, sql, params=()):
        sql=sql.strip()
        if sql.upper().startswith('PRAGMA JOURNAL_MODE='):
            return PGCursor(self.conn.execute('SELECT 1'))
        match=re.fullmatch(r'PRAGMA\s+table_info\(([a-z_]+)\)',sql,re.I)
        if match:
            return PGCursor(self.conn.execute('SELECT ordinal_position-1,column_name FROM information_schema.columns WHERE table_schema=current_schema() AND table_name=%s ORDER BY ordinal_position',(match.group(1),)))
        if sql.upper() == 'BEGIN IMMEDIATE':
            # Coarse transaction lock preserves SQLite's serialized update assumption.
            return PGCursor(self.conn.execute("SELECT pg_advisory_xact_lock(hashtext('auralis_transaction'))"))
        sql=re.sub(r'INTEGER PRIMARY KEY AUTOINCREMENT','BIGSERIAL PRIMARY KEY',sql,flags=re.I)
        if sql.startswith('INSERT OR REPLACE INTO learning_plans'):
            sql=sql.replace('INSERT OR REPLACE INTO','INSERT INTO',1)+ ' ON CONFLICT(owner) DO UPDATE SET created_at=excluded.created_at,payload=excluded.payload'
        elif sql.startswith('INSERT OR REPLACE INTO college_members'):
            sql=sql.replace('INSERT OR REPLACE INTO','INSERT INTO',1)+' ON CONFLICT(cohort_id,owner) DO UPDATE SET display_name=excluded.display_name,joined=excluded.joined'
        elif sql.startswith('INSERT OR REPLACE INTO college_completions'):
            sql=sql.replace('INSERT OR REPLACE INTO','INSERT INTO',1)+' ON CONFLICT(assignment_id,student) DO UPDATE SET completed=excluded.completed'
        if 'INSERT OR REPLACE' in sql.upper():
            raise RuntimeError('Unsupported SQLite UPSERT on PostgreSQL: query needs explicit conflict target')
        sql=sql.replace('?', '%s')
        if self.row_factory is sqlite3.Row:
            from psycopg.rows import dict_row
            return PGCursor(self.conn.cursor(row_factory=dict_row).execute(sql,params))
        return PGCursor(self.conn.execute(sql,params))
    def executemany(self, sql, rows):
        cursor=self.conn.cursor()
        cursor.executemany(sql.replace('?','%s'),rows)
        return PGCursor(cursor)


def connect(path,timeout=10):
    if is_postgres(path): return PGConnection(path)
    return sqlite3.connect(path,timeout=timeout)
