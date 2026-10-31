"""Regressions derived from the user's 45-page electrical-interview report.
No network/API secrets; faults are checked using synthetic session evidence.
"""
import math
import pytest
from fastapi.testclient import TestClient
from app.assessment_integrity import evidence_excerpt,build_assessment_turns,contradicted_electrical_criticism
from app.main import create_app
from app.provider import ProviderError
from app.schemas import Report
from app.engine import validate_report
from test_industry_controller import ControlledProvider
from test_flow import prepare,act,H


def test_long_answer_retains_late_corrections_and_numbered_calculations():
    original=('Preliminary model setup. '+('Busbars, transformers, and cables must be modeled. '*22) +
             '\n\nFor the new 5 MW feeder at 11 kV and 0.9 PF, current is 292 A. '+
             'At 415 V it becomes approximately 7,730 A; a 630 A MCCB cannot feed it directly.\n\n' +
             ('We need to validate devices, manufacturer curves and equipment ratings. '*18) +
             '\n\nFinally, the engineer must review protection and arc-flash exposure before commissioning.')
    e,short=evidence_excerpt(original,1700)
    assert short
    assert '292 A' in e and '7,730 A' in e
    assert 'before commissioning' in e
    assert 'Busbars' in e
    assert len(e)<1900


def test_build_assessment_context_preserves_all_chronological_answers():
    turns=[{'id':'turn'+str(i),'kind':'answer', 'text':'A'*2000+f'\n\nLater correction number {i} and important conclusion.',
            'question':{'text':'What is your method?','competency_id':'c1'}} for i in range(10)]
    out=build_assessment_turns(turns)
    assert len(out)==10
    assert sum(len(t['text']) for t in out)<19000
    assert out[-1]['id']=='turn9'
    assert 'Later correction number 9' in out[-1]['text']
    assert all(t['excerpted'] for t in out)


def test_electrical_false_accusation_is_flagged():
    ans=('A 5 MW load at 415 V and 0.9 PF draws approximately 7,730 A. '
         'At 11 kV and 0.9 PF, it draws 292 A; a low voltage MCCB would not be suitable for 11 kV.')
    assert contradicted_electrical_criticism({'feedback':'Unrealistic current calculations indicate confusion.'},[ans])
    assert contradicted_electrical_criticism({'feedback':'Confusion between low- and medium-voltage devices.'},[ans])
    assert not contradicted_electrical_criticism({'feedback':'Good answer, needs actual ETAP measurements.'},[ans])


def test_validator_rejects_later_score_contradiction_and_wrong_current(tmp_path):
    with TestClient(create_app(tmp_path,provider=ControlledProvider())) as c:
        c.headers.update(H)
        s=prepare(c,provider='groq',consent=True)
        s=c.post('/api/sessions/'+s['id']+'/start').json()
        s=act(c,s,('A 5 MW load at 415 V and 0.9 power factor draws about 7,730 A. '
                   'At 11 kV and 0.9 PF, it draws 292 A; a 630 A low voltage MCCB would not be suitable for 11 kV.')).json()
        answer=s['turns'][0];cid=answer['question']['competency_id']
        def make(**changes):
            items=[]
            for comp in s['plan']['competencies']:
                if comp['id']==cid:
                    row={'competency_id':cid,'status':'incorrect_reasoning','score':0,
                         'evidence_ids':[answer['id']],'feedback':'Unrealistic current calculations.',
                         'practice':'Practice verifying voltage and current calculations.'}
                    row.update(changes)
                else:
                    row={'competency_id':comp['id'],'status':'not_assessed','score':None,
                         'evidence_ids':[],'feedback':'Not tested in this session.',
                         'practice':'Try another question.'}
                items.append(row)
            return Report.model_validate({'summary':'Practice assessment.','items':items,'limitations':['Practice only.']})
        with pytest.raises(ProviderError,match='Numerical claims'):
            validate_report(make(),s)
        with pytest.raises(ProviderError,match='later-answer'):
            validate_report(make(feedback='Needs further justification.',initial_score=0,latest_score=3),s)


def test_local_plan_preserves_workflow_on_outage(tmp_path):
    class Offline(ControlledProvider):
        async def generate(self,task,context,schema):
            raise ProviderError('Outage',503)
    with TestClient(create_app(tmp_path,provider=Offline())) as c:
        c.headers.update(H)
        s=prepare(c,provider='groq',consent=True)
        assert s['plan_source']=='local_rubric_fallback'
        assert len(s['plan']['competencies'])>=3
        assert s['fallback_events'][0]['stage']=='plan'
        s=c.post('/api/sessions/'+s['id']+'/start').json()
        assert s['current']['source']=='local_rubric_fallback'
        s=act(c,s,'My decision would be to verify the design.').json()
        final=c.post('/api/sessions/'+s['id']+'/finish').json()
        assert final['report']['provisional']
        assert all(item['score'] is None for item in final['report']['items'])


def test_model_call_budget_process_wide_and_no_provider_charge_on_rejection(tmp_path,monkeypatch):
    monkeypatch.setenv('AURALIS_MAX_CALLS_PER_MINUTE','2')
    from app.usage_budget import UsageBudget
    budget=UsageBudget()
    budget.consume();budget.consume()
    with pytest.raises(ProviderError,match='budget reached'):
        budget.consume()
    assert budget.stats()['minute_remaining']==0


def test_controller_rationale_does_not_falsely_claim_unassessed(tmp_path):
    with TestClient(create_app(tmp_path,provider=ControlledProvider())) as c:
        c.headers.update(H)
        s=prepare(c,provider='groq',consent=True)
        s=c.post('/api/sessions/'+s['id']+'/start').json()
        assert '0 prior recorded answer' in s['current']['why']
        s=act(c,s,'Answer to first question.').json()
        assert '1 prior recorded answer' in s['current']['why']
        assert 'has not been assessed yet' not in s['current']['why']

def test_scoring_zero_after_later_correct_power_triangle_is_blocked():
    from app.assessment_integrity import contradicted_power_factor_criticism
    wrong='Active power uses sine; reactive power uses cosine. Capacitors generate active power.'
    right='P = √3 × VL × IL × cosφ. Q = √3 × VL × IL × sinφ. S² = P² + Q².'
    assert contradicted_power_factor_criticism({'score':0},[wrong,right])
    assert not contradicted_power_factor_criticism({'score':0},[wrong,'Still incorrect.'])


def test_source_scan_redacts_common_token_patterns():
    from app.codeproof import _redact
    assert 'gsk_' not in _redact("print('gsk_ABCDEFGHIJKLMNOPQRSTUVWXYZ123456')")
    assert 'hf_' not in _redact("AUTH = 'Bearer hf_ABCDEFGHIJKLMNOPQRSTUVWXYZ123456'")
    assert 'AKIA' not in _redact("token = 'AKIAABCDEFGHIJKLMNOP'")

def test_codeproof_citations_require_server_bound_evidence(tmp_path):
    from app.main import create_app
    from app.codeproof import inspect_zip
    from test_auralis_features import demo_code
    from test_flow import CV,JD
    with TestClient(create_app(tmp_path,provider=ControlledProvider())) as c:
        c.headers.update(H)
        fake={'id':'R01','path':'fake/credentials.py','symbol':'forged','line_start':1,'line_end':100}
        r=c.post('/api/sessions',json={'cv':CV,'jd':JD,'provider':'groq','consent':True,'codeproof_refs':[fake]})
        assert r.status_code==200
        assert r.json()['setup']['codeproof_refs']==[]
        token=c.post('/api/codeproof/zip',files={'file':('source.zip',demo_code(),'application/zip')}).json()['evidence_handle']
        other=c.post('/api/sessions',headers={'X-Owner-Token':'b'*64},json={'cv':CV,'jd':JD,'provider':'groq','consent':True,'codeproof_handle':token})
        assert other.status_code==422
        good=c.post('/api/sessions',json={'cv':CV,'jd':JD,'provider':'groq','consent':True,'codeproof_handle':token})
        assert good.status_code==200,good.text
        assert good.json()['setup']['codeproof_source_verified'] is True
        assert good.json()['setup']['codeproof_refs'][0]['id']=='R01'

def test_compare_and_retry_feedback_work_offline(tmp_path):
    from test_flow import CV,JD
    class Offline(ControlledProvider):
        async def generate(self,task,context,schema):
            if task in ('plan','question','retry_question','retry_feedback'):
                raise ProviderError('Unreachable',503)
            return await super().generate(task,context,schema)
    with TestClient(create_app(tmp_path,provider=Offline())) as c:
        c.headers.update(H)
        pair=c.post('/api/compare',json={'cv':CV,'jd_a':JD,'jd_b':'Electrical power systems, circuit breakers, load flow analysis, compliance documentation.', 'provider':'groq','consent':True})
        assert pair.status_code==200
        assert set(pair.json()['sources'].values())=={'local_rubric_fallback'}
        s=prepare(c,provider='groq',consent=True)
        s=c.post('/api/sessions/'+s['id']+'/start').json()
        s=act(c,s,'I would analyze loads and verify assumptions.').json()
        s=c.post('/api/sessions/'+s['id']+'/finish').json()
        tid=next(t for t in s['turns'] if t['kind']=='answer')['id']
        r=c.post('/api/sessions/'+s['id']+'/retry',json={'turn_id':tid,'style':'parallel'})
        assert r.status_code==200,r.text
        s=r.json();assert s['retry']['feedback'] is None
        r=c.post('/api/sessions/'+s['id']+'/retry/answer',json={'retry_id':s['retry']['id'],'text':'I will verify a secondary scenario.'})
        assert r.status_code==200,r.text
        assert r.json()['retry']['feedback_source']=='unscored_offline_fallback'
        regrade=c.post('/api/sessions/'+s['id']+'/retry/regrade')
        assert regrade.status_code==503
        assert c.get('/api/sessions/'+s['id']).json()['retry']['answer']=='I will verify a secondary scenario.'

def test_disabling_session_retention_does_not_disable_source_expiry(tmp_path):
    from app.store import Store
    store=Store(tmp_path)
    store.save_source('src_old','ownerA',{'refs':[]})
    with store.connect() as conn:
        conn.execute('UPDATE source_evidence SET created_at=? WHERE id=?',(0,'src_old'))
    store.purge_expired(0)
    assert store.load_source('src_old','ownerA') is None
    with store.connect() as conn:
        assert conn.execute('SELECT count(*) FROM source_evidence').fetchone()[0]==0
