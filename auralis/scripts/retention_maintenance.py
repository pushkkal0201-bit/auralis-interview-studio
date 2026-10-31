"""One-shot retention cleanup for a managed scheduled job.

Run with the same DATABASE_URL / AURALIS_DATA_DIR and AURALIS_RETENTION_DAYS
as the web service. No provider credentials are needed and no inference occurs.
"""
import os
import time
from pathlib import Path
from app.database import is_postgres
from app.store import Store
from app import career_suite, intelligence56
from app.auth_abuse import AuthAttemptBudget
from app.usage_budget import UsageBudget


def run_retention(store_path=None, days=None):
    production = os.getenv('AURALIS_DEPLOYMENT_MODE', 'local').lower() == 'production'
    configured = os.getenv('DATABASE_URL', '') if production else os.getenv('AURALIS_DATA_DIR', str(Path(__file__).resolve().parents[1] / '.data'))
    target = store_path or configured
    if production and not is_postgres(target):
        raise RuntimeError('Hosted maintenance requires a PostgreSQL DATABASE_URL.')
    retention = int(days if days is not None else os.getenv('AURALIS_RETENTION_DAYS', '30'))
    if retention < 1 or retention > 365:
        raise ValueError('Scheduled session retention must be between 1 and 365 days.')
    store = Store(target)
    career_suite.init_tables(store.path)
    intelligence56.init_tables(store.path)
    cleared = store.purge_expired(retention)
    career_suite.purge_expired(store.path, retention)
    intelligence56.purge_expired(store.path, retention)
    # Cleanup must not rely on new login / inference traffic.
    AuthAttemptBudget(store.path)
    UsageBudget(store.path)
    now = time.time()
    with store.connect() as db:
        db.execute('DELETE FROM auth_attempts WHERE created_at<?', (now - 900,))
        db.execute('DELETE FROM ai_usage WHERE created_at<?', (now - 3600,))
    return {'expired_sessions_deleted': cleared, 'retention_days': retention}

if __name__ == '__main__':
    result = run_retention()
    print('Retention maintenance finished; expired sessions removed:', result['expired_sessions_deleted'])
