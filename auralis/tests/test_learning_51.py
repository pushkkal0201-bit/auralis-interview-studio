"""Auralis 5.1: deterministic calculation, stored progress and repair regressions."""
import math
from pathlib import Path
from fastapi.testclient import TestClient
from app.main import create_app
from app.learning import progress_from_sessions
from app.technical_check import TechnicalCheckRequest, check_calculation
from test_flow import H, start, act


def test_load_gravity_equation():
    r=check_calculation(TechnicalCheckRequest(case='gravity_load',values={'mass_kg':180,'gravity_m_s2':9.81},claimed_result=1766))
    assert math.isclose(r['result'],1765.8)
    assert r['comparison']=='within_1_percent'
    assert r['unit']=='N'
    assert r['source']=='deterministic_formula'


def test_bend_allowance_formula():
    r=check_calculation(TechnicalCheckRequest(case='bend_allowance',values={'angle_deg':90,'inside_radius_mm':2,'thickness_mm':2,'k_factor':.4}))
    assert math.isclose(r['result'],4.398229715,abs_tol=1e-7)
    assert 'tooling' in r['interpretation']


def test_plate_stiffness_and_three_phase_current():
    r=check_calculation(TechnicalCheckRequest(case='plate_stiffness_ratio',values={'thickness_before_mm':2,'thickness_after_mm':3}))
    assert r['result']==3.375
    r=check_calculation(TechnicalCheckRequest(case='three_phase_current',values={'real_power_w':5e6,'line_voltage_v':11000,'power_factor':.9}))
    assert 290<r['result']<293
    assert 'not size protection' in r['interpretation'].lower()


def test_unsafe_cases_rejected_and_owner_required(tmp_path):
    with TestClient(create_app(tmp_path)) as c:
        good={'case':'gravity_load','values':{'mass_kg':180,'gravity_m_s2':9.81}}
        assert c.post('/api/technical/check',json=good).status_code==401
        c.headers.update(H)
        assert c.post('/api/technical/check',json=good).status_code==200
        assert c.post('/api/technical/check',json={'case':'gravity_load','values':{'mass_kg':180,'gravity_m_s2':0}}).status_code==422
        assert c.post('/api/technical/check',json={'case':'gravity_load','values':{'mass_kg':180,'gravity_m_s2':9.81,'extra':2}}).status_code==422
        assert c.post('/api/technical/check',json={'case':'gravity_load','values':{'mass_kg':1e100,'gravity_m_s2':9.81}}).status_code==422
        assert c.post('/api/technical/check',json={'case':'gravity_load','values':{'mass_kg':180,'gravity_m_s2':9.81},'claimed_result':'NaN'}).status_code==422
        assert c.post('/api/technical/check',json={'case':'eval','values':{'a':2,'b':2}}).status_code==422


def _session(sid,at,score,provider='groq',name='Mechanical Engineering Fundamentals',provisional=False):
    return {'id':sid,'created_at':at,'status':'completed','plan':{'role':'Mechanical Engineer','competencies':[{'id':'c1','requirement':'Stress and stiffness'}]},'setup':{'provider':provider},'retry_history':[],'report':{'items':[{'name':name,'competency_id':'c1','score':score}], 'ai_provider':provider,'ai_model':'openai/gpt-oss-120b','provisional':provisional,'demo':provider=='demo'}}


def test_progress_excludes_demo_offline_and_unscored():
    out=progress_from_sessions([_session('one',100,0),_session('two',200,3),_session('three',300,None),_session('four',400,4,'demo'),_session('five',500,4,provisional=True)])
    assert out['session_count']==5
    assert out['scored_competency_observations']==2
    skill=out['skills'][0]
    assert skill['latest_score']==3 and skill['earliest_score']==0
    assert skill['score_change']==3
    assert len(skill['points'])==2


def test_progress_isolation_deleted_session_and_repair_no_double_count(tmp_path):
    with TestClient(create_app(tmp_path)) as c:
        c.headers.update(H)
        s=start(c)
        s=act(c,s,'I would verify load paths in the engineering drawing.').json()
        s=c.post(f'/api/sessions/{s["id"]}/finish').json()
        r=c.get('/api/learning/progress').json()
        assert r['session_count']==1 and r['completed_count']==1
        assert r['skills']==[]  # Demo is not scored, even if it has an assessment.
        ans=next(t for t in s['turns'] if t['kind']=='answer')
        retry=c.post(f'/api/sessions/{s["id"]}/retry',json={'turn_id':ans['id'],'style':'repair'}).json()
        assert retry['retry']['question']==ans['question']['text']
        again=c.post(f'/api/sessions/{s["id"]}/retry/answer',json={'retry_id':retry['retry']['id'],'text':'Corrected answer with a realistic engineering load path.'})
        assert again.status_code==200
        r=c.get('/api/learning/progress').json()
        assert r['repair_attempt_count']==1 and r['skills']==[]
        assert c.get('/api/learning/progress',headers={'X-Owner-Token':'b'*64}).json()['session_count']==0
        assert c.delete(f'/api/sessions/{s["id"]}').status_code==200
        assert c.get('/api/learning/progress').json()['repair_attempt_count']==0


def test_progress_exact_competency_name_no_fuzzy_merges():
    r=progress_from_sessions([_session('1',100,1,name='Machine Design'),_session('2',200,3,name='Mechanical Design')])
    assert len(r['skills'])==2
    assert all(x['score_change'] is None for x in r['skills'])


def test_v51_browser_navigation_and_rendering_elements():
    root=Path(__file__).resolve().parents[1]/'app'/'static'
    html=(root/'index.html').read_text()
    js=(root/'app.js').read_text()
    css=(root/'studio.css').read_text()
    for ident in ['repair-workspace','repair-target','repair-original','repair-revised','repair-start','learning-content','calculation-fields','calculation-run','claimed-result']:
        assert f'id="{ident}"' in html
    assert "document.createTextNode(part)" in js
    assert 'renderRepairWorkspace' in js and 'loadLearningProgress' in js
    assert "'/api/learning/progress'" in js and "'/api/technical/check'" in js
    assert '@media(max-width:600px)' in css
    assert '.repair-workspace,.learning-section,.lab-shell' in css
