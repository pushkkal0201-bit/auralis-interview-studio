import time
import uuid
import pytest
from fastapi.testclient import TestClient
from app.main import create_app

CV = 'Alex built a booking API using Python and SQL. Implemented a database and tests for concurrent requests.'
JD = 'Backend developer. Python, SQL, transactions, API design, debugging and communication skills required.'
H = {'X-Owner-Token': 'a' * 64}

@pytest.fixture
def client(tmp_path):
    with TestClient(create_app(tmp_path)) as c:
        c.headers.update(H)
        yield c

def prepare(c, **kw):
    body = dict(cv=CV, jd=JD, role='Backend developer', mode='interview', language='en', duration_minutes=10, provider='demo', consent=False)
    body.update(kw)
    r=c.post('/api/sessions', json=body)
    assert r.status_code==200, r.text
    return r.json()

def start(c, **kw):
    s=prepare(c, **kw)
    r=c.post(f"/api/sessions/{s['id']}/start",json={})
    assert r.status_code==200,r.text
    return r.json()

def act(c,s,text='I use a database transaction with a unique constraint and an idempotency key.',kind='answer',rid=None):
    return c.post(f"/api/sessions/{s['id']}/actions",json={'text':text,'kind':kind,'request_id':rid or str(uuid.uuid4()),'expected_question_id':s['current']['id']})

def test_prepare_rubric_and_start(client):
    s=prepare(client)
    assert s['status']=='ready' and len(s['plan']['competencies'])>=3
    s=client.post(f"/api/sessions/{s['id']}/start",json={}).json()
    assert s['status']=='active' and s['current']['why'] and s['deadline']>time.time()

def test_answer_evolves_and_duplicate_request_is_idempotent(client):
    s=start(client); rid=str(uuid.uuid4())
    r=act(client,s,'I check if the booking exists.',rid=rid)
    assert r.status_code==200
    out=r.json(); assert out['current']['text']!=s['current']['text']
    duplicate=act(client,s,'I check if the booking exists.',rid=rid)
    assert duplicate.status_code==200
    assert len(duplicate.json()['turns'])==len(out['turns'])
    assert act(client,s).status_code==409

def test_clarification_keeps_question_and_facts(client):
    s=start(client)
    q=s['current']['id']
    out=act(client,s,'How many users are there?',kind='clarify').json()
    assert out['current']['id']==q and out['last_reply']
    assert out['plan']['scenario']['facts']==s['plan']['scenario']['facts']

def test_hint_requires_coaching_and_does_not_count_as_answer(client):
    s=start(client); assert act(client,s,'Hint please',kind='hint').status_code==409
    s=start(client,mode='coaching')
    out=act(client,s,'Hint please',kind='hint').json()
    assert out['current']['id']==s['current']['id']
    assert not [t for t in out['turns'] if t['kind']=='answer']

def test_finish_report_and_retry_preserve_original(client):
    s=start(client)
    s=act(client,s).json()
    r=client.post(f"/api/sessions/{s['id']}/finish",json={})
    assert r.status_code==200,r.text
    s=r.json(); assert s['status']=='completed'
    assert s['report']['demo'] is True
    assert all(i['score'] is None for i in s['report']['items'])
    answer=next(t for t in s['turns'] if t['kind']=='answer')
    q=client.post(f"/api/sessions/{s['id']}/retry",json={'turn_id':answer['id'],'style':'parallel'}).json()
    assert q['retry']['original_turn_id']==answer['id']
    r=client.post(f"/api/sessions/{s['id']}/retry/answer",json={'text':'I use transactions and test concurrent writes.','retry_id':q['retry']['id']})
    assert r.status_code==200,r.text
    assert r.json()['report']==s['report']
    assert r.json()['retry']['feedback']

def test_owner_isolation_and_delete(client):
    s=start(client)
    assert client.get(f"/api/sessions/{s['id']}",headers={'X-Owner-Token':'b'*64}).status_code==404
    assert client.get('/api/sessions',headers={'X-Owner-Token':'b'*64}).json()==[]
    assert client.delete(f"/api/sessions/{s['id']}").status_code==200
    assert client.get(f"/api/sessions/{s['id']}").status_code==404

def test_no_live_calls_without_key_or_consent(client):
    r=client.post('/api/sessions',json={'cv':CV,'jd':JD,'provider':'groq','consent':False})
    assert r.status_code==422

def test_empty_answer_rejected_and_end_is_terminal(client):
    s=start(client)
    assert act(client,s,'   ').status_code==422
    client.post(f"/api/sessions/{s['id']}/finish",json={})
    assert act(client,s).status_code==409

def test_cross_origin_rejected(client):
    r=client.post('/api/sessions',json={},headers={'Origin':'https://attacker.example'})
    assert r.status_code==403

def test_export_and_role_comparison(client):
    s=start(client)
    r=client.get(f"/api/sessions/{s['id']}/export")
    assert r.status_code==200 and r.json()['id']==s['id']
    r=client.post('/api/compare',json={'cv':CV,'jd_a':JD,'jd_b':'Technical support: customer incidents, networks and troubleshooting.','provider':'demo','consent':False})
    assert r.status_code==200,r.text
    assert r.json()['a']['competencies']!=r.json()['b']['competencies']
