"""Staging tooling and isolation regression; NO external credentials/services.

The SQLite backup check is explicitly NOT proof of PostgreSQL PITR.
"""
import sqlite3
from fastapi import HTTPException
from fastapi.testclient import TestClient
import pytest
from app.main import create_app
from app.store import Store
from scripts.staging_acceptance import require_settings
from scripts.verify_restored_database import run as verify_restored_database

A = 'a0b78f05-94aa-440e-a3c1-4e16a82c1a11'
B = 'b1b78f05-94aa-440e-a3c1-4e16a82c1a22'
CV = 'Synthetic engineer implemented Python database transactions, rate limits, backups, and multi-user API isolation.'
JD = 'Backend developer: Python, database transactions, concurrency, security, recovery and testing skills.'


class FakeAuth:
    def user(self, token):
        if token == 'a': return {'id': A, 'email': 'a@example.org'}
        if token == 'b': return {'id': B, 'email': 'b@example.org'}
        raise HTTPException(401, 'Invalid login')


def test_account_abuse_across_session_endpoints_and_restart(tmp_path):
    app = create_app(tmp_path, auth_mode='supabase', auth_client=FakeAuth())
    ah = {'Authorization':'Bearer a'}
    bh = {'Authorization':'Bearer b'}
    with TestClient(app) as client:
        create = client.post('/api/sessions',headers=ah,
                             json={'cv':CV,'jd':JD,'provider':'demo','consent':False})
        assert create.status_code == 200, create.text
        sid=create.json()['id']
        assert sid in [s['id'] for s in client.get('/api/sessions',headers=ah).json()]
        assert sid not in [s['id'] for s in client.get('/api/sessions',headers=bh).json()]
        for method,path in [('get',f'/api/sessions/{sid}'),('get',f'/api/sessions/{sid}/export'),
                            ('post',f'/api/sessions/{sid}/start'),('post',f'/api/sessions/{sid}/finish'),
                            ('delete',f'/api/sessions/{sid}')]:
            assert getattr(client,method)(path,headers=bh).status_code==404
        assert client.get(f'/api/sessions/{sid}',headers=ah).status_code==200
    # Recreate an independent app against the same persistent store, like a server restart.
    restarted=create_app(tmp_path,auth_mode='supabase',auth_client=FakeAuth())
    with TestClient(restarted) as client:
        assert client.get(f'/api/sessions/{sid}',headers=ah).status_code==200
        assert client.get(f'/api/sessions/{sid}',headers=bh).status_code==404


def test_sqlite_backup_and_restore_local_only(tmp_path):
    source=tmp_path/'source'; recovered=tmp_path/'restored'
    source_store=Store(source)
    source_store.create({'id':'synthetic_1','revision':0,'created_at':1760000000.0},'owner_a')
    recovered.mkdir()
    with sqlite3.connect(source_store.path) as src,sqlite3.connect(str(recovered/'auralis.sqlite3')) as dest:
        src.backup(dest)
    restored_store=Store(recovered)
    assert restored_store.load('synthetic_1','owner_a')['id']=='synthetic_1'
    assert restored_store.load('synthetic_1','owner_b') is None


def test_staging_harness_requires_disposable_confirmation(monkeypatch):
    for k in ['AURALIS_STAGING_URL','AURALIS_TEST_A_EMAIL','AURALIS_TEST_A_PASSWORD',
              'AURALIS_TEST_B_EMAIL','AURALIS_TEST_B_PASSWORD']:
        monkeypatch.setenv(k, 'https://testing.example.org' if k.endswith('URL') else k+'-test')
    monkeypatch.delenv('AURALIS_TEST_ISOLATED_STAGING',raising=False)
    with pytest.raises(ValueError,match='I_CONFIRM_DISPOSABLE'):
        require_settings()


def test_restore_verifier_is_opt_in(monkeypatch):
    monkeypatch.delenv('AURALIS_RESTORE_VALIDATION',raising=False)
    with pytest.raises(ValueError,match='I_CONFIRM_READ_ONLY'):
        verify_restored_database()
