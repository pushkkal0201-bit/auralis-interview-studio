"""No external API credentials used; requests are HTTP-mocked, never faked in user-facing live mode."""
import asyncio
import json

import httpx
import pytest
from fastapi.testclient import TestClient

from app.huggingface_provider import HuggingFaceProvider, HUGGINGFACE_MODELS
from app.main import create_app
from app.provider import ProviderError
from app.schemas import Decision

OWNER = {'X-Owner-Token': 'e' * 64}
CV = 'A student built a Python API using a SQL database, implemented test cases, and led a booking software project in college.'
JD = 'Backend internship requiring REST API knowledge, Python programming, SQL transactions, concurrency, debugging and testing.'


def decision_payload():
    return {
        'question': 'How do you make the booking operation atomic?',
        'competency_id': 'c1',
        'why': 'This job requires reliable concurrent booking logic.',
        'difficulty': 'applied',
        'difficulty_reason': 'The previous answer discussed availability, not atomicity.',
        'branch_id': '',
        'coaching': '',
        'decision_action': 'PROBE',
        'source_ref_id': ''
    }


def test_hf_models_are_open_weight_and_allowlisted():
    assert len(HUGGINGFACE_MODELS) == 2
    assert all(x.startswith('openai/gpt-oss-') for x in HUGGINGFACE_MODELS)
    p = HuggingFaceProvider(key='hf_dummy_token')
    with pytest.raises(ProviderError) as e:
        p._select_model('grok-4')
    assert e.value.status == 422


def test_hf_real_remote_endpoint_payload_is_schema_bound():
    captured = []
    def respond(req):
        assert req.url.host == 'router.huggingface.co'
        assert str(req.url.path) == '/v1/chat/completions'
        assert req.headers['Authorization'] == 'Bearer hf_dummy_token'
        request = json.loads(req.content)
        captured.append(request)
        return httpx.Response(200, json={'choices':[{'message':{'content':json.dumps(decision_payload())}}]})
    p = HuggingFaceProvider(key='hf_dummy_token', transport=httpx.MockTransport(respond))
    for model in HUGGINGFACE_MODELS:
        result = asyncio.run(p.generate('question', {'ai_model':model}, Decision))
        assert result.decision_action == 'PROBE'
    assert [x['model'] for x in captured] == list(HUGGINGFACE_MODELS)
    assert captured[0]['response_format']['type'] == 'json_schema'
    assert captured[1]['response_format']['type'] == 'json_object'
    assert all('hf_dummy_token' not in json.dumps(x) for x in captured)
    assert all('ai_model' not in x['messages'][1]['content'] for x in captured)


def test_hf_actual_model_probe_and_rate_limits():
    def respond(req):
        return httpx.Response(200, json={'choices':[{'message':{'content':'OK'}}]})
    p = HuggingFaceProvider(key='hf_dummy_token', transport=httpx.MockTransport(respond))
    result = asyncio.run(p.check_connection('openai/gpt-oss-120b:fireworks-ai'))
    assert result['connected'] is True
    bad = HuggingFaceProvider(key='hf_dummy_token', transport=httpx.MockTransport(
        lambda req: httpx.Response(429, headers={'retry-after':'8'})))
    with pytest.raises(ProviderError) as exc:
        asyncio.run(bad.generate('question', {'ai_model':'openai/gpt-oss-120b:fireworks-ai'}, Decision))
    assert exc.value.status == 429 and exc.value.retry_after == '8'


def test_hf_rejects_invalid_model_output_without_fallback():
    p = HuggingFaceProvider(key='hf_dummy_token', transport=httpx.MockTransport(
        lambda req: httpx.Response(200, json={'choices':[{'message':{'content':'{"question":"invalid"}'}}]})))
    with pytest.raises(ProviderError):
        asyncio.run(p.generate('question', {'ai_model':'openai/gpt-oss-120b:fireworks-ai'}, Decision))


def test_hf_consent_and_provider_model_pairing(tmp_path):
    with TestClient(create_app(tmp_path, hf_provider=HuggingFaceProvider(key=''))) as c:
        c.headers.update(OWNER)
        base = {'cv':CV,'jd':JD,'provider':'huggingface','ai_model':'openai/gpt-oss-120b:fireworks-ai'}
        assert c.post('/api/sessions',json=base).status_code==422
        assert c.post('/api/sessions',json={**base,'consent':True,'ai_model':'openai/gpt-oss-120b'}).status_code==422
        offline=c.post('/api/sessions',json={**base,'consent':True})
        assert offline.status_code==200
        assert offline.json()['plan_source']=='local_rubric_fallback'
        assert offline.json()['fallback_events'][0]['stage']=='plan'
        assert c.get('/api/live/check?provider=invalid').status_code==422
        assert c.get('/api/health').status_code==200
        assert 'huggingface_configured' in c.get('/api/health').json()
        assert 'value="huggingface"' in c.get('/').text


def test_hf_route_uses_correct_model_and_same_interview_controller(tmp_path):
    from app.demo import DemoProvider
    class FakeHF:
        model='hf/test';
        def __init__(self): self.models=[]
        def configured(self):return True
        async def check_connection(self,model=None):return {'connected':True,'model':model}
        async def generate(self,task,context,schema):
            self.models.append(context.get('ai_model'))
            if task == 'plan':
                return await DemoProvider().generate(task,context,schema)
            if task == 'question':
                return schema.model_validate(decision_payload())
            if task == 'report':
                items = []
                for comp in context['plan']['competencies']:
                    ids = [t['id'] for t in context['turns'] if t['question']['competency_id'] == comp['id']]
                    items.append({'competency_id':comp['id'],'status':'insufficient_evidence' if ids else 'not_assessed',
                                  'score':None,'feedback':'More direct evidence is required to assess this competency.',
                                  'evidence_ids':ids,'practice':'Explain your approach, tests, and trade-offs.'})
                return schema.model_validate({'summary':'Test-only assessment result from an injected fake model.',
                                               'items':items,'limitations':['Injected mock, not live inference.']})
            raise AssertionError(task)
    fake=FakeHF()
    with TestClient(create_app(tmp_path,hf_provider=fake)) as c:
        c.headers.update(OWNER)
        payload={'cv':CV,'jd':JD,'role':'Backend Engineer','provider':'huggingface','ai_model':'openai/gpt-oss-120b:fireworks-ai','consent':True}
        result = c.post('/api/sessions',json=payload)
        assert result.status_code == 200,result.text
        sid=result.json()['id']
        started=c.post(f'/api/sessions/{sid}/start')
        assert started.status_code == 200,started.text
        q=started.json()['current']
        ans=c.post(f'/api/sessions/{sid}/actions',json={'text':'Use a transaction with a unique constraint and retry handling.','expected_question_id':q['id'],'request_id':'uniqueRequestABC123'})
        assert ans.status_code == 200,ans.text
        finished=c.post(f'/api/sessions/{sid}/finish')
        assert finished.status_code == 200, finished.text
        assert finished.json()['status']=='completed'
        assert finished.json()['report']['demo'] is False
        assert len(fake.models) >= 4 and all(m=='openai/gpt-oss-120b:fireworks-ai' for m in fake.models)  # validated report may require a repair inference
