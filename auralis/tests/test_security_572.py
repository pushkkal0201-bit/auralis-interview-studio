"""No live network or account: synthetic test principals only."""
import os
from uuid import UUID
from fastapi import HTTPException
from fastapi.testclient import TestClient
from app.main import create_app, owner_hash
from app.auth_abuse import AuthAttemptBudget

ALICE='a0b78f05-94aa-440e-a3c1-4e16a82c1a11'

class Auth:
    def user(self, token):
        if token == 'alice': return {'id': ALICE, 'email': 'alice@example.org'}
        raise HTTPException(401, 'Invalid token')
    def login(self, email, password):
        return {'access_token': 'alice', 'refresh_token': 'test-refresh', 'expires_in': 300}
    def signup(self, email, password):
        return {'user': {'id': ALICE}}
    def refresh(self, token):
        return self.login('alice@example.org','dummy')
    def recovery(self, email, redirect): return {}
    def logout(self, token): return {}


def test_account_budget_is_shared_and_never_stores_plain_email(tmp_path, monkeypatch):
    monkeypatch.setenv('AURALIS_AUTH_ATTEMPTS_PER_15M', '2')
    monkeypatch.setenv('AURALIS_AUTH_GLOBAL_PER_MINUTE', '20')
    path=str(tmp_path/'security.sqlite3')
    a=AuthAttemptBudget(path);b=AuthAttemptBudget(path)
    a.consume('login', 'ALICE@example.org')
    b.consume('login', 'alice@example.org')
    from pytest import raises
    with raises(HTTPException) as err:a.consume('login', 'alice@example.org')
    assert err.value.status_code==429
    assert err.value.headers['Retry-After']=='60'
    from app.database import connect
    with connect(path) as db:
        values=db.execute('SELECT identity_hash FROM auth_attempts').fetchall()
    assert len(values)==2
    assert all(len(v[0])==64 and '@' not in v[0] for v in values)
    a.consume('recover','alice@example.org')  # Separate endpoint budget.


def test_auth_login_throttled_before_upstream(tmp_path,monkeypatch):
    monkeypatch.setenv('AURALIS_AUTH_ATTEMPTS_PER_15M','2')
    monkeypatch.setenv('AURALIS_PUBLIC_URL','https://auralis.example.org')
    app=create_app(tmp_path,auth_mode='supabase',auth_client=Auth())
    with TestClient(app) as client:
        for _ in range(2):
            assert client.post('/api/auth/login',json={'email':'alice@example.org','password':'aTestPassword123'}).status_code==200
        denied=client.post('/api/auth/login',json={'email':'alice@example.org','password':'aTestPassword123'})
        assert denied.status_code==429 and denied.headers['retry-after']=='60'
        assert client.post('/api/auth/recover',json={'email':'alice@example.org'}).status_code==200


def test_strict_origin_scheme_and_fetch_metadata(tmp_path,monkeypatch):
    monkeypatch.setenv('AURALIS_DEPLOYMENT_MODE','production')
    monkeypatch.setenv('DATABASE_URL','postgresql://dummy.invalid/test')
    monkeypatch.setenv('GROQ_API_KEY','not-a-real-key')
    monkeypatch.setenv('AURALIS_PUBLIC_URL','https://auralis.example.org')
    monkeypatch.setenv('AURALIS_EXTRA_HOSTS','auralis.example.org')
    app=create_app(tmp_path,auth_mode='supabase',auth_client=Auth())
    with TestClient(app,base_url='https://auralis.example.org') as client:
        payload={'email':'alice@example.org','password':'aTestPassword123'}
        assert client.post('/api/auth/login',json=payload,headers={'Origin':'http://auralis.example.org'}).status_code==403
        assert client.post('/api/auth/login',json=payload,headers={'Origin':'https://auralis.example.org'}).status_code==200
        assert client.post('/api/auth/login',json=payload,headers={'Sec-Fetch-Site':'cross-site'}).status_code==403
        assert client.post('/api/auth/login',json=payload,headers={'Sec-Fetch-Site':'same-site'}).status_code==403
        ok=client.get('/api/health')
        assert ok.headers['strict-transport-security']=='max-age=31536000'
        assert ok.headers['x-frame-options']=='DENY'
        assert 'microphone=' in ok.headers['permissions-policy']


def test_unsupported_model_probe_does_not_charge_quota(tmp_path):
    app=create_app(tmp_path,auth_mode='supabase',auth_client=Auth())
    with TestClient(app) as client:
        r=client.get('/api/live/check?provider=unknown',headers={'Authorization':'Bearer alice'})
        assert r.status_code==422
        with app.state.store.connect() as db:
            rows=db.execute('SELECT COUNT(*) FROM ai_usage').fetchone()[0] if app.state.engine.strict_live else 0
        assert rows==0


def test_delete_all_also_clears_ai_usage_in_production(tmp_path, monkeypatch):
    monkeypatch.setenv('AURALIS_DEPLOYMENT_MODE','production')
    monkeypatch.setenv('DATABASE_URL','postgresql://dummy.invalid/test')
    monkeypatch.setenv('GROQ_API_KEY','not-a-real-key')
    monkeypatch.setenv('AURALIS_PUBLIC_URL','https://auralis.example.org')
    app=create_app(tmp_path,auth_mode='supabase',auth_client=Auth())
    key=owner_hash('supabase:'+ALICE)
    with app.state.store.connect() as db:
        db.execute('INSERT INTO ai_usage(owner,created_at) VALUES(?,?)',(key,1234.0))
    with TestClient(app) as client:
        r=client.post('/api/privacy/delete-all',headers={'Authorization':'Bearer alice'})
        assert r.status_code==200
    with app.state.store.connect() as db:
        assert db.execute('SELECT COUNT(*) FROM ai_usage WHERE owner=?',(key,)).fetchone()[0]==0

def test_host_configuration_rejects_wildcards(tmp_path,monkeypatch):
    import pytest
    monkeypatch.setenv('AURALIS_DEPLOYMENT_MODE','production')
    monkeypatch.setenv('AURALIS_PUBLIC_URL','https://auralis.example.org')
    monkeypatch.setenv('DATABASE_URL','postgresql://dummy.invalid/test')
    monkeypatch.setenv('GROQ_API_KEY','test-key')
    monkeypatch.setenv('AURALIS_EXTRA_HOSTS','*')
    with pytest.raises(RuntimeError,match='wildcards'):
        create_app(tmp_path,auth_mode='supabase',auth_client=Auth())


def test_public_url_rejects_credentials_and_path(tmp_path,monkeypatch):
    import pytest
    monkeypatch.setenv('AURALIS_DEPLOYMENT_MODE','production')
    monkeypatch.setenv('DATABASE_URL','postgresql://dummy.invalid/test')
    monkeypatch.setenv('GROQ_API_KEY','test-key')
    for url in ('http://auralis.example.org','https://alice:secret@auralis.example.org',
                'https://auralis.example.org/app','https://auralis.example.org/?token=x'):
        monkeypatch.setenv('AURALIS_PUBLIC_URL',url)
        with pytest.raises(RuntimeError,match='exact HTTPS'):
            create_app(tmp_path,auth_mode='supabase',auth_client=Auth())
