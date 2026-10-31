"""Version 5.4 workspace: goal-aware, privacy-scoped plans and manual completion."""
from datetime import datetime,timedelta,timezone
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from app.main import create_app
from app.learning_workspace import PlanRequest,make_plan,priorities,calendar_ics,summarise

A={'X-Owner-Token':'a'*64};B={'X-Owner-Token':'b'*64}
TODAY=datetime.now(timezone.utc).date().isoformat()

def test_schedule_is_bounded_and_not_a_grade():
    settings=PlanRequest(goal='balanced',days_per_week=4,minutes_per_day=30,start_date=TODAY)
    p=make_plan(settings,[],[])
    assert len(p['tasks'])==16
    assert len({t['date'] for t in p['tasks']})==16
    assert len([t for t in p['tasks'] if t['week']==3])==4
    assert {t['status'] for t in p['tasks']}=={'planned'}
    assert not p['provenance']['personalized']
    summary=summarise(p,[],[])
    assert summary['overview']['completion_percent']==0
    assert summary['priority_skills']==[]


def test_score_prioritization_excludes_demo_and_provisional():
    now=datetime.now(timezone.utc).timestamp()
    base={'status':'completed','created_at':now,'id':'a','plan':{'role':'Mechanical Engineer'},'setup':{'provider':'groq'},'retry_history':[]}
    valid={**base,'report':{'items':[{'name':'Structural analysis','score':1,'confidence':'medium'},{'name':'CAD Design','score':3}]}}
    demo={**base,'id':'b','setup':{'provider':'demo'},'report':{'items':[{'name':'Made up','score':0}]}}
    provisional={**base,'id':'c','report':{'provisional':True,'items':[{'name':'Bad score','score':0}]}}
    ranked,missed,progress=priorities([valid,demo,provisional],[])
    assert [x['name'] for x in ranked]==['Structural analysis','CAD Design']
    assert progress['scored_competency_observations']==2
    p=make_plan(PlanRequest(start_date=TODAY),[valid,demo,provisional],[])
    assert p['provenance']['personalized']
    assert any('Structural analysis' in t['title'] for t in p['tasks'])

@pytest.mark.parametrize('payload',[
 {'goal':'anything','days_per_week':4,'minutes_per_day':30,'start_date':TODAY},
 {'goal':'coding','days_per_week':1,'minutes_per_day':30,'start_date':TODAY},
 {'goal':'coding','days_per_week':4,'minutes_per_day':500,'start_date':TODAY},
 {'goal':'coding','days_per_week':4,'minutes_per_day':30,'start_date':'notadate'},
 {'goal':'coding','days_per_week':4,'minutes_per_day':30,'start_date':'2038-01-01'},
])
def test_invalid_planning_input_is_rejected(payload,tmp_path):
    with TestClient(create_app(tmp_path)) as c:
        assert c.post('/api/workspace/plan',headers=A,json=payload).status_code==422


def test_workspace_owner_isolation_completion_and_replacement(tmp_path):
    with TestClient(create_app(tmp_path)) as c:
        assert c.get('/api/workspace').status_code==401
        assert c.get('/api/workspace',headers=B).json()['plan'] is None
        r=c.post('/api/workspace/plan',headers=A,json={'goal':'engineering','start_date':TODAY,'days_per_week':3,'minutes_per_day':45})
        assert r.status_code==200,r.text
        plan=r.json()['plan']; assert len(plan['tasks'])==12
        assert all(x['minutes']==45 for x in plan['tasks'])
        first=plan['tasks'][0]
        assert c.get('/api/workspace',headers=B).json()['plan'] is None
        task_url=f"/api/workspace/plans/{plan['id']}/tasks/{first['id']}"
        assert c.patch(task_url,headers=B,json={'status':'completed'}).status_code==404
        assert c.patch(task_url,headers=A,json={'status':'unknown'}).status_code==422
        changed=c.patch(task_url,headers=A,json={'status':'completed'}).json()
        assert changed['overview']['completed']==1
        assert changed['overview']['completed_minutes']==45
        assert changed['overview']['scored_observations']==0
        assert changed['plan']['tasks'][0]['completed_at'] is not None
        again=c.patch(task_url,headers=A,json={'status':'planned'}).json()
        assert again['overview']['completed']==0
        assert again['plan']['tasks'][0]['completed_at'] is None
        ics=c.get('/api/workspace/calendar.ics',headers=A)
        assert ics.status_code==200 and 'BEGIN:VCALENDAR' in ics.text
        assert ics.text.count('BEGIN:VEVENT')==12
        assert 'Content-Disposition' in ics.headers
        private=c.get('/api/workspace/summary.json',headers=A).json()
        assert private['current_plan']['goal']=='engineering'
        assert private['practice_metrics']['completed_minutes']==0
        assert 'cv' not in str(private).lower().replace('candidate cvs','')
        newplan=c.post('/api/workspace/plan',headers=A,json={'start_date':TODAY,'goal':'coding'}).json()
        assert newplan['plan']['id']!=plan['id']
        assert c.patch(task_url,headers=A,json={'status':'completed'}).status_code==404
        assert c.delete('/api/workspace/plan',headers=B).json()['deleted'] is False
        assert c.delete('/api/workspace/plan',headers=A).json()['deleted'] is True
        assert c.get('/api/workspace/calendar.ics',headers=A).status_code==404


def test_practice_evidence_not_stored_as_candidate_code_and_privacy_delete(tmp_path):
    with TestClient(create_app(tmp_path)) as c:
        source='def solve(nums):\n    return sum(nums)'
        c.post('/api/practical/code',headers=A,json={'challenge_id':'sum_numbers','code':source}).raise_for_status()
        c.post('/api/practical/engineering',headers=A,json={'case_id':'enclosure_supports','claimed_result':0,'reasoning':'SECRET_CV_TEXT'}).raise_for_status()
        x=c.post('/api/workspace/plan',headers=A,json={'start_date':TODAY,'goal':'engineering'}).json()
        assert x['plan']['provenance']['personalized']
        assert x['overview']['practical_attempts']==2
        assert 'SECRET_CV_TEXT' not in str(x) and source not in str(x)
        assert c.get('/api/workspace',headers=B).json()['overview']['practical_attempts']==0
        assert c.post('/api/privacy/delete-all',headers=A,json={}).status_code==200
        assert c.get('/api/workspace',headers=A).json()['plan'] is None
        assert c.get('/api/practical/history',headers=A).json()['attempts']==[]


def test_retention_also_deletes_old_plans(tmp_path):
    from app.store import Store
    store=Store(tmp_path)
    p=make_plan(PlanRequest(start_date=TODAY),[],[])
    store.replace_plan('x',p)
    with store.connect() as c:
        c.execute('UPDATE learning_plans SET created_at=? WHERE owner=?',(datetime.now(timezone.utc).timestamp()-40*86400,'x'))
    store.purge_expired(30)
    assert store.load_plan('x') is None


def test_calendar_has_no_user_cv_and_escapes_untrusted_names():
    p=make_plan(PlanRequest(start_date=TODAY),[],[])
    p['tasks'][0]['title']='Study; control, new\\line\nInjected'
    ics=calendar_ics(p)
    assert 'SUMMARY:Study\\; control\\, new\\\\line\\nInjected' in ics
    assert 'BEGIN:VCALENDAR' in ics


def test_frontend_ids_and_navigation_preserved():
    from bs4 import BeautifulSoup
    from pathlib import Path
    static=Path(__file__).resolve().parents[1]/'app/static'
    html=(static/'index.html').read_text()
    soup=BeautifulSoup(html,'html.parser')
    assert soup.select_one('.nav[data-view="workspace"]') is not None
    for id in ('workspace-form','workspace-task-list','workspace-priorities','workspace-goal','workspace-calendar-export'):
        assert soup.select_one('#'+id)
    assert len(soup.select('.nav'))>=18
    assert '/static/workspace.js' in html
    assert all((static/f).exists() for f in ('app.js','practical.js','workspace.js'))

def test_private_summary_excludes_cv_and_answer_strings(tmp_path):
    with TestClient(create_app(tmp_path)) as c:
        r=c.get('/api/workspace/summary.json',headers=A)
        assert r.status_code==200
        assert 'attachment' in r.headers.get('content-disposition','')
        assert r.json()['current_plan'] is None
        assert not any(k in r.json() for k in ('cv','transcripts','source_code','answer'))
