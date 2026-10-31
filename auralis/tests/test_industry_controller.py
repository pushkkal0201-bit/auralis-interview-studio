"""Evidence integrity, offline recovery, coverage, scoring, and privacy regression tests."""
import copy
import time
import uuid
from fastapi.testclient import TestClient
import pytest
from app.main import create_app
from app.demo import DemoProvider
from app.engine import validate_report
from app.policy import target_competency, coverage_summary
from app.provider import ProviderError
from app.schemas import Report
from test_flow import prepare, start, act, CV, JD, H


class ControlledProvider:
    model='openai/gpt-oss-120b'
    def __init__(self, question='valid'):
        self.question_mode=question
        self.calls=[]
        self.broken_report=False
    def configured(self):return True
    async def check_connection(self,requested_model=None):return {'connected':True,'model':requested_model or self.model}
    async def generate(self,task,context,schema):
        self.calls.append((task,copy.deepcopy(context)))
        if task=='plan':return await DemoProvider().generate(task,context,schema)
        if task=='question':
            if self.question_mode=='outage':raise ProviderError('Quota reached',429)
            target=context['mandatory_competency_id']
            if self.question_mode=='wrong':target='c3' if target!='c3' else 'c1'
            if self.question_mode=='repeated':q='How would you solve this problem safely?'
            else:
                prior=[t for t in context.get('turns',[]) if t.get('question',{}).get('competency_id')==target and t['kind']=='answer']
                skill=next(c for c in context['plan']['competencies'] if c['id']==target)
                q=(f'Explain your approach to {skill["name"]}: {skill["requirement"]}. What assumptions do you make?' if not prior
                   else f'For the competency {skill["name"]}, what can fail in production and how do you measure its impact?')
            return schema.model_validate(dict(question=q,competency_id=target,why='The role requires this concrete competency.',
                difficulty='applied',difficulty_reason='This tests practical design and verification.',
                decision_action='ADVANCE',source_ref_id='',branch_id='',coaching=''))
        if task=='report':
            if self.broken_report:raise ProviderError('Network problem',503)
            items=[]
            for c in context['plan']['competencies']:
                evidence=[t['id'] for t in context['turns'] if t['question']['competency_id']==c['id']]
                # Scenario has intentionally wrong answers; grading is supplied by the fake model,
                # not determined heuristically by the engine.
                items.append(dict(competency_id=c['id'],status='incorrect_reasoning' if evidence else 'not_assessed',
                                  score=0 if evidence else None,confidence='medium',
                                  evidence_ids=evidence[:8],initial_score=0 if evidence else None,latest_score=0 if evidence else None,feedback='Incorrect approach to concurrency; explicit recorded answer evidence.' if evidence else 'Not covered.',
                                  practice='Use a transaction and explain tests for simultaneous requests.'))
            return schema.model_validate(dict(summary='Practice report with rubric-aligned evidence.',items=items,
                                              limitations=['Model generated judgement, not an employment decision.']))
        raise AssertionError(task)


def fake_client(tmp_path,fake):
    c=TestClient(create_app(tmp_path,provider=fake));c.headers.update(H);return c


def test_target_rotates_on_two_attempts(tmp_path):
    with fake_client(tmp_path,ControlledProvider()) as c:
        s=prepare(c,provider='groq',ai_model='openai/gpt-oss-120b',consent=True)
        s=c.post(f"/api/sessions/{s['id']}/start").json()
        assert s['current']['competency_id']=='c1'
        s=act(c,s,text='wrong answer').json()
        assert s['current']['competency_id']=='c1'
        s=act(c,s,text='another wrong answer').json()
        assert s['current']['competency_id']=='c2'
        s=act(c,s,text='still wrong').json()
        assert s['current']['competency_id']=='c2'
        s=act(c,s,text='another wrong answer').json()
        assert s['current']['competency_id']=='c3'
        assert len(s['fallback_events'])==0


def test_rotation_when_clock_nearly_over(tmp_path):
    with fake_client(tmp_path,ControlledProvider()) as c:
        s=prepare(c,provider='groq',consent=True)
        s=c.post(f"/api/sessions/{s['id']}/start").json()
        owner=c.app.state.owner_hash('a'*64)
        stored=c.app.state.store.load(s['id'],owner)
        stored['deadline']=time.time()+190
        c.app.state.store.save(stored,owner)
        s=act(c,s).json()
        assert s['current']['competency_id']=='c2'


def test_provider_question_outage_keeps_answer_and_labels_fallback(tmp_path):
    fake=ControlledProvider()
    with fake_client(tmp_path,fake) as c:
        s=prepare(c,provider='groq',consent=True)
        s=c.post(f"/api/sessions/{s['id']}/start").json()
        fake.question_mode='outage'
        out=act(c,s,'Test answer to keep').json()
        assert out['current']['source']=='local_rubric_fallback'
        assert out['fallback_events'][0]['stage']=='question'
        assert out['turns'][0]['text']=='Test answer to keep'
        assert out['current']['competency_id']=='c1'


def test_invalid_model_competency_replaced_explicitly(tmp_path):
    fake=ControlledProvider(question='wrong')
    with fake_client(tmp_path,fake) as c:
        s=prepare(c,provider='groq',consent=True)
        out=c.post(f"/api/sessions/{s['id']}/start").json()
        assert out['current']['competency_id']=='c1'
        assert out['current']['source']=='local_rubric_fallback'
        assert len([x for x in fake.calls if x[0]=='question'])==2


def test_assessment_fallback_and_retry_upgrade(tmp_path):
    fake=ControlledProvider()
    with fake_client(tmp_path,fake) as c:
        s=prepare(c,provider='groq',consent=True)
        s=c.post(f"/api/sessions/{s['id']}/start").json()
        s=act(c,s,'I would ignore the database conflict.').json()
        fake.broken_report=True
        sid=s['id']
        result=c.post(f'/api/sessions/{sid}/finish')
        assert result.status_code==200,result.text
        report=result.json()['report']
        assert report['provisional'] is True
        assert all(item['score'] is None for item in report['items'])
        assert any(i['status']=='not_scored_provider_unavailable' for i in report['items'])
        assert result.json()['turns'][0]['text']=='I would ignore the database conflict.'
        fake.broken_report=False
        r=c.post(f'/api/sessions/{sid}/finish')
        assert r.status_code==200,r.text
        report=r.json()['report']
        assert report['provisional'] is False
        assessed=[i for i in report['items'] if i['evidence']]
        assert all(i['status']=='incorrect_reasoning' and i['score']==0 for i in assessed)
        assert report['coverage']['covered_count']==1
        assert report['coverage']['total_count']==3


def test_report_validator_rejects_wrong_score_status_and_false_unscored(tmp_path):
    with fake_client(tmp_path,ControlledProvider()) as c:
        s=prepare(c,provider='groq',consent=True)
        s=c.post(f"/api/sessions/{s['id']}/start").json()
        s=act(c,s).json()
        tid=s['turns'][0]['id']
        for status,score in [('incorrect_reasoning',None),('demonstrated',0),('partially_demonstrated',4),
                             ('insufficient_evidence',2),('not_assessed',None)]:
            items=[]
            for co in s['plan']['competencies']:
                assigned=co['id']==s['turns'][0]['question']['competency_id']
                items.append(dict(competency_id=co['id'],status=status if assigned else 'not_assessed',
                    score=score if assigned else None,evidence_ids=[tid] if assigned else [],
                    feedback='Insufficiently reasoned technical explanation.',practice='Review tests and assumptions.'))
            with pytest.raises(ProviderError):validate_report(Report.model_validate(dict(summary='Detailed feedback.',items=items,limitations=['Practice only.'])),s)


def test_wrong_answer_with_insufficient_status_is_rejected(tmp_path):
    with fake_client(tmp_path,ControlledProvider()) as c:
        s=prepare(c,provider='groq',consent=True)
        s=c.post(f"/api/sessions/{s['id']}/start").json()
        s=act(c,s,'A wrong answer').json()
        s=act(c,s,'Also a wrong answer').json()
        comp=s['turns'][0]['question']['competency_id']
        items=[]
        for co in s['plan']['competencies']:
            ids=[t['id'] for t in s['turns'] if t['question']['competency_id']==co['id']]
            items.append(dict(competency_id=co['id'],status='insufficient_evidence' if ids else 'not_assessed',
                score=None,evidence_ids=ids,feedback='Candidate misunderstood the technique, with factually incorrect explanations.',
                practice='Review fundamentals.'))
        with pytest.raises(ProviderError):validate_report(Report.model_validate(dict(summary='Practice feedback.',items=items,limitations=['Test.'])),s)


def test_end_time_finishes_without_generating_another_question(tmp_path):
    fake=ControlledProvider()
    with fake_client(tmp_path,fake) as c:
        s=prepare(c,provider='groq',consent=True)
        s=c.post(f"/api/sessions/{s['id']}/start").json()
        owner=c.app.state.owner_hash('a'*64)
        stored=c.app.state.store.load(s['id'],owner)
        stored['deadline']=time.time()+20
        c.app.state.store.save(stored,owner)
        before=len(fake.calls)
        out=act(c,s,'A considered answer').json()
        assert out['status']=='awaiting_report'
        assert len(fake.calls)==before
        assert len(out['turns'])==1


def test_delete_all_only_current_owner_and_retention(tmp_path,monkeypatch):
    with fake_client(tmp_path,ControlledProvider()) as c:
        own=prepare(c,provider='groq',consent=True)
        other_headers={'X-Owner-Token':'b'*64}
        other=c.post('/api/sessions',headers=other_headers,json=dict(cv=CV,jd=JD,provider='demo')).json()
        r=c.post('/api/privacy/delete-all')
        assert r.status_code==200 and r.json()['deleted']==1
        assert c.get('/api/sessions').json()==[]
        assert c.get(f"/api/sessions/{other['id']}",headers=other_headers).status_code==200
        assert c.post('/api/privacy/delete-all',headers=other_headers).json()['deleted']==1
        old=prepare(c,provider='groq',consent=True)
        owner=c.app.state.owner_hash('a'*64)
        rec=c.app.state.store.load(old['id'],owner)
        rec['created_at']=time.time()-32*86400
        c.app.state.store.save(rec,owner)
        assert c.app.state.store.purge_expired(30)==1
        assert c.get('/api/sessions').json()==[]
