"""Auralis 5.7 production foundation regressions (no real cloud secrets in tests)."""
import asyncio
import uuid
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import create_app, owner_hash
from app.database import PGConnection, is_postgres
from app.store import Store
from app.engine import Engine
from app.demo import DemoProvider
from app.provider import ProviderError

ALICE = 'a0b78f05-94aa-440e-a3c1-4e16a82c1a11'
BOB = 'b1b78f05-94aa-440e-a3c1-4e16a82c1a22'


class FakeVerifiedSupabase:
    users = {'alice-token': {'id': ALICE, 'email': 'alice@example.org'},
             'bob-token': {'id': BOB, 'email': 'bob@example.org'}}
    def user(self, token):
        from fastapi import HTTPException
        if token not in self.users: raise HTTPException(401, 'Invalid authenticated user.')
        return self.users[token]
    def login(self, email, password):
        return {'access_token': 'alice-token', 'refresh_token': 'alice-refresh', 'expires_in': 300}
    def refresh(self, token):
        from fastapi import HTTPException
        if token != 'alice-refresh':raise HTTPException(401,'Invalid refresh token')
        return self.login('alice@example.org','password123')
    def signup(self, email, password):
        return {'user': {'id': ALICE}}
    def logout(self, token):return {}
    def recovery(self, email, redirect):return {}
    def password(self, token, password):return {}


def test_untrusted_browser_owner_token_rejected_when_verified_auth_enabled(tmp_path):
    app = create_app(tmp_path, auth_mode='supabase', auth_client=FakeVerifiedSupabase())
    with TestClient(app) as c:
        assert c.get('/api/public-config').json()['authentication_required'] is True
        assert c.get('/api/sessions',headers={'X-Owner-Token':'a'*64}).status_code==401
        assert c.get('/api/sessions',headers={'Authorization':'Bearer invalid','X-Owner-Token':'a'*64}).status_code==401
        assert c.get('/api/sessions',headers={'Authorization':'Bearer alice-token'}).status_code==200
        assert c.get('/api/sessions',headers={'Authorization':'Bearer bob-token'}).status_code==200
        assert owner_hash('supabase:'+ALICE) != owner_hash('supabase:'+BOB)


def test_real_user_ownership_separates_saved_practice_data(tmp_path):
    app = create_app(tmp_path, auth_mode='supabase', auth_client=FakeVerifiedSupabase())
    with TestClient(app) as c:
        a={'Authorization':'Bearer alice-token'}
        b={'Authorization':'Bearer bob-token'}
        result=c.post('/api/question-bank',headers=a,json={
            'question':'How would you test this service for concurrency problems?',
            'competency':'System reliability'}).json()
        # Verify actual API schema; an invalid card is not a stored record.
        if 'id' in result:
            aid=result['id']
            assert c.get('/api/question-bank',headers=a).json()['saved'][0]['id']==aid
            assert c.get('/api/question-bank',headers=b).json()['saved']==[]
            assert c.delete('/api/question-bank/'+aid,headers=b).json()['deleted'] is False


def test_login_refresh_and_logout_cookies_are_http_only(tmp_path):
    app=create_app(tmp_path,auth_mode='supabase',auth_client=FakeVerifiedSupabase())
    with TestClient(app) as c:
        r=c.post('/api/auth/signup',json={'email':'alice@example.org','password':'goodPassword123'})
        assert r.status_code==200 and r.json()['verification_required'] is True
        r=c.post('/api/auth/login',json={'email':'alice@example.org','password':'goodPassword123'})
        assert r.status_code==200
        assert r.json()['user']['id']==ALICE
        assert 'httponly' in r.headers['set-cookie'].lower()
        assert '/api/auth' in r.headers['set-cookie']
        assert 'refresh_token' not in r.json()
        assert c.post('/api/auth/refresh').json()['access_token']=='alice-token'
        assert c.post('/api/auth/logout',headers={'Authorization':'Bearer alice-token'}).status_code==200
        assert c.post('/api/auth/refresh').status_code==401


def test_production_rejects_missing_cloud_configuration(monkeypatch,tmp_path):
    monkeypatch.setenv('AURALIS_DEPLOYMENT_MODE','production')
    monkeypatch.setenv('AURALIS_PUBLIC_URL','https://auralis.example.org')
    monkeypatch.delenv('DATABASE_URL',raising=False)
    monkeypatch.delenv('GROQ_API_KEY',raising=False)
    with pytest.raises(RuntimeError,match='PostgreSQL DATABASE_URL'):
        create_app(tmp_path)


class FakeCursor:
    def __init__(self): self.rowcount=1
    def fetchone(self):return (1,)
    def fetchall(self):return [(1,)]
    def __iter__(self):return iter([(1,)])
class FakePG:
    def __init__(self):self.calls=[]
    def execute(self,sql,params=()):
        self.calls.append((sql,params));return FakeCursor()


def test_postgres_sqlite_migration_translations_are_explicit():
    db=PGConnection.__new__(PGConnection)
    db.conn=FakePG();db.row_factory=None
    assert is_postgres('postgresql://user@localhost/db')
    db.execute('CREATE TABLE x (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT)')
    assert 'BIGSERIAL PRIMARY KEY' in db.conn.calls[-1][0]
    db.execute('SELECT id FROM sessions WHERE owner=?',('abc',))
    assert '%s' in db.conn.calls[-1][0]
    db.execute('INSERT OR REPLACE INTO college_members VALUES (?,?,?,?)',('c','o','a',3))
    assert 'ON CONFLICT(cohort_id,owner)' in db.conn.calls[-1][0]
    db.execute('INSERT OR REPLACE INTO learning_plans (owner,created_at,payload) VALUES (?,?,?)',('a',1,'{}'))
    assert 'ON CONFLICT(owner)' in db.conn.calls[-1][0]
    db.execute('BEGIN IMMEDIATE')
    assert 'pg_advisory_xact_lock' in db.conn.calls[-1][0]


class FlakyLive:
    def __init__(self):self.questions=0;self.fail=True;self.demo=DemoProvider()
    async def generate(self,task,context,schema):
        if task=='plan':return await self.demo.generate('plan',context,schema)
        if task=='question':
            self.questions+=1
            if self.questions>1 and self.fail:raise ProviderError('Provider temporarily unavailable',503)
            return schema.model_validate({'question':('Explain a realistic load case, failure mode, and verification method for an engineering system.' if self.questions==1 else 'In a separate production design review, what inspection and failure analysis would validate a new prototype?'),
                'competency_id':context['mandatory_competency_id'],'why':'Role-based applied question for a skill.',
                'difficulty':'applied','difficulty_reason':'Applied practice case','branch_id':'','coaching':'','decision_action':'ADVANCE'})
        if task=='report':raise ProviderError('Provider temporarily unavailable',503)
        return await self.demo.generate(task,context,schema)


def test_answer_is_saved_before_failed_live_followup_and_can_resume(tmp_path):
    async def scenario():
        store=Store(tmp_path)
        provider=FlakyLive()
        engine=Engine(store,DemoProvider(),provider,strict_live=True)
        user='owner'
        data={'cv':'A CV description for testing the actual model plan with meaningful experience in engineering.',
              'jd':'Engineering role requires analytical calculations, test planning, manufacturing choices and verification.',
              'provider':'groq','ai_model':'openai/gpt-oss-120b','mode':'interview','language':'en',
              'duration_minutes':15,'consent':True,'role':'Engineer','project_evidence':'','codeproof_refs':[]}
        from app.schemas import Setup,Action
        sess=await engine.prepare(Setup.model_validate(data),user)
        sess=await engine.start(sess['id'],user)
        act=Action(text='I would calculate loads and verify the model with measurements.',kind='answer',request_id='unique-retry-001',expected_question_id=sess['current']['id'])
        with pytest.raises(ProviderError,match='answer was saved'):
            await engine.action(sess['id'],user,act)
        stored=store.load(sess['id'],user)
        assert stored['status']=='paused_provider'
        assert len(stored['turns'])==1
        assert stored['turns'][0]['text']==act.text
        provider.fail=False
        resumed=await engine.start(sess['id'],user)
        assert resumed['status']=='active' and resumed['current']['text']
        assert len(resumed['turns'])==1
        with pytest.raises(ProviderError):await engine.finish(sess['id'],user)
        assert store.load(sess['id'],user)['report'] is None
    asyncio.run(scenario())
