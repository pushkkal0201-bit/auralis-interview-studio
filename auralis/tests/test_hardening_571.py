"""Shared-usage and authenticated-production boundaries; no cloud secrets needed."""
import os
import uuid
import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from app.main import create_app
from app.usage_budget import UsageBudget
from app.provider import ProviderError

ALICE='a0b78f05-94aa-440e-a3c1-4e16a82c1a11'
BOB='b1b78f05-94aa-440e-a3c1-4e16a82c1a22'

class FakeAuth:
    def user(self,token):
        if token=='alice':return {'id':ALICE,'email':'alice@example.org'}
        if token=='bob':return {'id':BOB,'email':'bob@example.org'}
        raise HTTPException(401,'Invalid user')


def test_shared_quota_separates_accounts_and_enforces_global_limit(tmp_path,monkeypatch):
    monkeypatch.setenv('AURALIS_MAX_CALLS_PER_MINUTE','2')
    monkeypatch.setenv('AURALIS_MAX_CALLS_PER_HOUR','5')
    monkeypatch.setenv('AURALIS_GLOBAL_CALLS_PER_MINUTE','3')
    monkeypatch.setenv('AURALIS_GLOBAL_CALLS_PER_HOUR','5')
    db=str(tmp_path/'quota.db')
    # Different server objects use the same underlying usage table.
    one=UsageBudget(db);other=UsageBudget(db)
    one.consume('alice');one.consume('alice')
    with pytest.raises(ProviderError,match='limit reached'):other.consume('alice')
    other.consume('bob')
    with pytest.raises(ProviderError,match='limit reached'):one.consume('bob')


def test_shared_quota_rejects_missing_owner_before_recording(tmp_path):
    quota=UsageBudget(str(tmp_path/'quota.db'))
    with pytest.raises(ProviderError,match='identity required'):quota.consume()
    with pytest.raises(ProviderError,match='identity required'):quota.consume('')


def production_config(monkeypatch):
    monkeypatch.setenv('AURALIS_DEPLOYMENT_MODE','production')
    monkeypatch.setenv('AURALIS_PUBLIC_URL','https://auralis.example.org')
    monkeypatch.setenv('DATABASE_URL','postgresql://ignored.example.org/test')
    monkeypatch.setenv('GROQ_API_KEY','fake-test-key')
    monkeypatch.setenv('AURALIS_COLLEGE_INSTRUCTOR_IDS',ALICE)


def test_instructor_permissions_require_explicit_allowlist_in_hosted_mode(tmp_path,monkeypatch):
    production_config(monkeypatch)
    app=create_app(tmp_path,auth_mode='supabase',auth_client=FakeAuth())
    with TestClient(app) as c:
        a={'Authorization':'Bearer alice'};b={'Authorization':'Bearer bob'}
        assert c.get('/api/ready').json()=={'status':'ready'}
        assert c.get('/api/public-config').json()['college_instructor_invite_required']
        assert c.post('/api/college/cohorts',json={'name':'Engineering cohort'},headers=b).status_code==403
        result=c.post('/api/college/cohorts',json={'name':'Engineering cohort'},headers=a)
        assert result.status_code==200,result.text
        cid=result.json()['id'];invite=result.json()['invite']
        assert c.post(f'/api/college/cohorts/{cid}/assignments',headers=b,json={'title':'Buckling analysis','instructions':'Calculate stress and explain limitations'}).status_code==403
        assert c.post(f'/api/college/cohorts/{cid}/assignments',headers=a,json={'title':'Buckling analysis','instructions':'Calculate stress and explain limitations'}).status_code==200
        join=c.post('/api/college/join',headers=b,json={'invite':invite,'display_name':'Student B'})
        assert join.status_code==200,join.text
        view=c.get('/api/college',headers=b).json()
        assert len(view['joined'])==1
        assert len(view['managed'])==0
        assert c.get('/api/sessions',headers=b).status_code==200
        assert c.get('/api/sessions',headers=a).status_code==200


def test_production_college_defaults_to_no_instructor(tmp_path,monkeypatch):
    production_config(monkeypatch)
    monkeypatch.delenv('AURALIS_COLLEGE_INSTRUCTOR_IDS')
    app=create_app(tmp_path,auth_mode='supabase',auth_client=FakeAuth())
    with TestClient(app) as c:
        assert c.post('/api/college/cohorts',json={'name':'Engineering cohort'},headers={'Authorization':'Bearer alice'}).status_code==403


def test_production_rejects_bad_instructor_identifiers(tmp_path,monkeypatch):
    production_config(monkeypatch)
    monkeypatch.setenv('AURALIS_COLLEGE_INSTRUCTOR_IDS','alice@university.edu')
    with pytest.raises(RuntimeError,match='invalid Supabase UUID'):
        create_app(tmp_path,auth_mode='supabase',auth_client=FakeAuth())


def test_readiness_distinguishes_database_outage_from_process_liveness(tmp_path,monkeypatch):
    app=create_app(tmp_path)
    app.state.store.path=str(tmp_path/'db_is_now_gone'/'missing.sqlite3')
    with TestClient(app) as c:
        assert c.get('/api/health').status_code==200
        r=c.get('/api/ready')
        assert r.status_code==503
        assert r.json()=={'status':'unavailable'}
        assert 'traceback' not in r.text.lower()

class DeletingAuth(FakeAuth):
    def __init__(self):self.deleted=[]
    def login(self,email,password):
        if email!='alice@example.org' or password!='correct-password':
            raise HTTPException(400,'Invalid credentials')
        return {'access_token':'alice'}
    def admin_delete_user(self,uid):
        self.deleted.append(uid)
        return True


def test_account_removal_requires_fresh_password_and_deletes_only_self(tmp_path,monkeypatch):
    production_config(monkeypatch)
    monkeypatch.setenv('SUPABASE_SERVICE_ROLE_KEY','test-secret-not-a-real-key')
    auth=DeletingAuth()
    app=create_app(tmp_path,auth_mode='supabase',auth_client=auth)
    alice={'Authorization':'Bearer alice'}
    bob={'Authorization':'Bearer bob'}
    with TestClient(app) as c:
        a=c.post('/api/question-bank',headers=alice,json={'question':'How do you diagnose a failing industrial pump?','competency':'Mechanical engineering'})
        assert a.status_code==200
        b=c.post('/api/question-bank',headers=bob,json={'question':'How do you verify a software API deployment?','competency':'Software engineering'})
        assert b.status_code==200
        denied=c.post('/api/auth/delete-account',headers=alice,json={'password':'incorrect-password','confirmation':'DELETE MY ACCOUNT'})
        assert denied.status_code==400
        assert len(c.get('/api/question-bank',headers=alice).json()['saved'])==1
        invalid=c.post('/api/auth/delete-account',headers=alice,json={'password':'correct-password','confirmation':'DELETE'})
        assert invalid.status_code==422
        deleted=c.post('/api/auth/delete-account',headers=alice,json={'password':'correct-password','confirmation':'DELETE MY ACCOUNT'})
        assert deleted.status_code==200,deleted.text
        assert auth.deleted==[ALICE]
        assert c.get('/api/question-bank',headers=alice).json()['saved']==[]
        assert len(c.get('/api/question-bank',headers=bob).json()['saved'])==1


def test_account_removal_disabled_without_private_admin_key(tmp_path,monkeypatch):
    production_config(monkeypatch)
    monkeypatch.delenv('SUPABASE_SERVICE_ROLE_KEY',raising=False)
    app=create_app(tmp_path,auth_mode='supabase',auth_client=DeletingAuth())
    with TestClient(app) as c:
        r=c.post('/api/auth/delete-account',headers={'Authorization':'Bearer alice'},json={'password':'correct-password','confirmation':'DELETE MY ACCOUNT'})
        assert r.status_code==503
        assert 'not configured' in r.text


def test_shared_quota_is_atomic_under_parallel_requests(tmp_path,monkeypatch):
    from concurrent.futures import ThreadPoolExecutor
    monkeypatch.setenv('AURALIS_MAX_CALLS_PER_MINUTE','4')
    monkeypatch.setenv('AURALIS_MAX_CALLS_PER_HOUR','8')
    monkeypatch.setenv('AURALIS_GLOBAL_CALLS_PER_MINUTE','12')
    db=str(tmp_path/'concurrent.db')
    shared=UsageBudget(db)
    def try_request(_):
        try:
            shared.consume('alice')
            return True
        except ProviderError as err:
            assert err.status==429
            return False
    with ThreadPoolExecutor(max_workers=8) as pool:
        results=list(pool.map(try_request,range(15)))
    assert sum(results)==4
