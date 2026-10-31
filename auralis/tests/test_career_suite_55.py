"""Auralis 5.5: controlled campus, language, revision, college privacy, reliability."""
import re
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from app.main import create_app
from app.career_suite import coach,CoachInput, repeated_questions, reliability_fixture
A={'X-Owner-Token':'1'*64};B={'X-Owner-Token':'2'*64};C={'X-Owner-Token':'3'*64}

def test_campus_five_rounds_and_scoring_boundaries(tmp_path):
    with TestClient(create_app(tmp_path)) as c:
        assert c.post('/api/campus',json={'role':'Software'}).status_code==401
        new=c.post('/api/campus',headers=A,json={'role':'Software Engineer'}).json()
        sid=new['id']
        assert new['current_stage']=='aptitude'
        assert c.get('/api/campus',headers=B).json()['simulations']==[]
        assert c.get(f'/api/campus/{sid}',headers=B).status_code==404
        assert c.post(f'/api/campus/{sid}/submit',headers=A,json={'answer':'4'}).status_code==422
        p=c.post(f'/api/campus/{sid}/submit',headers=A,json={'answer':'2'}).json()
        for i in range(1,5):
            assert p['current_stage']=='aptitude'
            p=c.post(f'/api/campus/{sid}/submit',headers=A,json={'answer':str([2,1,1,1][i-1])}).json()
        assert p['results'][0]['scored'] and p['results'][0]['passed']==5
        assert p['current_stage']=='coding'
        wrong_code='import os\ndef solve(text):\n return os.system("whoami")'
        assert c.post(f'/api/campus/{sid}/submit',headers=A,json={'answer':wrong_code}).status_code==422
        good_code='def solve(text):\n    return text[::-1]'
        p=c.post(f'/api/campus/{sid}/submit',headers=A,json={'answer':good_code}).json()
        assert p['results'][1]['scored'] and p['results'][1]['passed']==5
        for _ in range(3):
            p=c.post(f'/api/campus/{sid}/submit',headers=A,json={'answer':'Context, steps taken, result and lesson learnt.'}).json()
            assert p['results'][-1]['scored'] is False
        assert p['complete'] and len(p['results'])==5
        assert good_code not in str(p)
        assert c.post(f'/api/campus/{sid}/submit',headers=A,json={'answer':'try again'}).status_code==409
        assert c.delete(f'/api/campus/{sid}',headers=B).json()['deleted'] is False
        assert c.delete(f'/api/campus/{sid}',headers=A).json()['deleted'] is True


def test_language_no_translation_or_sensitive_score_claims():
    r=coach(CoachInput(text='I checked yield strength and verified the design under load',language='hinglish',domain='mechanical'))
    assert r['matched_terms'][0]['english']=='yield strength'
    assert r['language']=='hinglish'
    assert 'accent' in r['limitations'] and 'not saved' in r['limitations']
    assert 'identity' in r['limitations']


def test_question_bank_owner_isolation_schedule_and_auto_hints(tmp_path):
    with TestClient(create_app(tmp_path)) as c:
        x=c.post('/api/question-bank',headers=A,json={'question':'Explain the implications of buckling for a steel panel','answer':'','competency':'Mechanical'}).json()
        assert x['attempts']==0
        assert len(c.get('/api/question-bank',headers=B).json()['saved'])==0
        r=c.post(f"/api/question-bank/{x['id']}/practice",headers=A,json={'status':'practiced','answer':'I changed my explanation'}).json()
        assert r['attempts']==1 and r['variant']
        assert 'I changed my explanation' not in str(c.get('/api/question-bank',headers=A).json())
        assert c.post(f"/api/question-bank/{x['id']}/practice",headers=B,json={'status':'practiced'}).status_code==404
        assert c.delete(f"/api/question-bank/{x['id']}",headers=A).json()['deleted']
        assert not c.get('/api/question-bank',headers=A).json()['saved']


def test_college_cohort_invites_isolation_and_aggregate_only(tmp_path):
    with TestClient(create_app(tmp_path)) as c:
        r=c.post('/api/college/cohorts',headers=A,json={'name':'Campus Placement - Batch A'});assert r.status_code==200,r.text
        invite=r.json()['invite'];cid=r.json()['id']
        assert len(invite)==40
        assert invite not in str(c.get('/api/college',headers=A).json())
        assert c.post('/api/college/join',headers=A,json={'invite':invite,'display_name':'Instructor'}).status_code==409
        assert c.post('/api/college/join',headers=B,json={'invite':'0'*40,'display_name':'Learner'}).status_code==404
        assert c.post('/api/college/join',headers=B,json={'invite':invite,'display_name':'Learner B'}).status_code==200
        assert c.post('/api/college/join',headers=C,json={'invite':invite,'display_name':'Learner C'}).status_code==200
        d=c.post(f'/api/college/cohorts/{cid}/assignments',headers=B,json={'title':'Mock technical interview','type':'interview','instructions':'Describe a project and explain the tradeoffs you made.'})
        assert d.status_code==404
        a=c.post(f'/api/college/cohorts/{cid}/assignments',headers=A,json={'title':'Mock technical interview','type':'interview','instructions':'Describe a project and explain the tradeoffs you made.','target_role':'Mechanical Design Engineer'}).json()
        assert a['target_role']=='Mechanical Design Engineer'
        assert c.patch(f"/api/college/assignments/{a['id']}/mentor",headers=B,json={'note':'Review the load assumptions.'}).status_code==404
        assert c.patch(f"/api/college/assignments/{a['id']}/mentor",headers=A,json={'note':'Review the load assumptions.'}).status_code==200
        learner=c.get('/api/college',headers=B).json()
        assert learner['joined'][0]['assignments'][0]['mentor_note']=='Review the load assumptions.'
        assert c.patch(f"/api/college/assignments/{a['id']}",headers=C,json={'completed':True}).status_code==200
        data=c.get('/api/college',headers=A).json()
        assert data['managed'][0]['students']==2
        assert data['managed'][0]['assignments'][0]['completed']==1
        assert 'Learner C' not in str(data) and 'private transcript' not in str(data)
        assert c.patch(f"/api/college/assignments/{a['id']}",headers=A,json={'completed':True}).status_code==404
        assert c.post('/api/privacy/delete-all',headers=A).status_code==200
        assert not c.get('/api/college',headers=B).json()['joined']


def test_reliability_and_owner_scope(tmp_path):
    assert repeated_questions(['Explain sheet bending stiffness','Describe sheet bending stiffness'])
    assert not repeated_questions(['How do you verify weld strength','Describe conflict resolution in a team'])
    with TestClient(create_app(tmp_path)) as c:
        fixtures=c.get('/api/reliability/fixtures',headers=A).json()
        assert fixtures['total']==5 and fixtures['passed']==5
        assert 'not' in fixtures['limitations'].lower()
        assert c.get('/api/reliability/audit/unknown',headers=A).status_code==404


def test_new_navigation_and_scripts_responsive():
    static=Path(__file__).resolve().parents[1]/'app'/'static'
    html=(static/'index.html').read_text()
    assert html.count('class="nav"')>=12
    for view in ['campus','bilingual','bank','college','reliability']:
        assert f'id="{view}"' in html
        assert f'data-view="{view}"' in html
    assert '/static/career.js' in html and '/static/career.css' in html
    assert 'innerHTML' not in (static/'career.js').read_text() or 'frm.innerHTML=\'\'' in (static/'career.js').read_text()
