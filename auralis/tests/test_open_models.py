"""Regression tests for one Groq key with session-scoped open-weight model selection."""
import asyncio
import json

import httpx
import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from app.provider import GroqProvider, ProviderError, SUPPORTED_OPEN_MODELS
from app.schemas import Decision

TOKEN = 'd' * 64
CV = 'B.Tech computer science student with Python backend API experience and a booking project using database queries and validation.'
JD = 'Backend engineering intern role requires Python, REST APIs, SQL transactions, concurrency handling, error recovery, and team communication.'


def test_open_weight_models_are_fixed_allowlist():
    assert set(SUPPORTED_OPEN_MODELS) == {
        'openai/gpt-oss-20b', 'openai/gpt-oss-120b', 'qwen/qwen3.8-27b'
    }
    with pytest.raises(ProviderError) as exc:
        GroqProvider(key='test')._select_model('grok-4')
    assert exc.value.status == 422


def test_groq_model_routing_sends_selected_id_not_secret():
    captured = []
    def respond(req):
        assert req.url.host == 'api.groq.com'
        body = json.loads(req.content)
        captured.append(body)
        data = {
            'question':'How do you prevent duplicate writes during concurrent requests?',
            'competency_id':'c1', 'why':'The job requires database concurrency.',
            'difficulty':'applied', 'difficulty_reason':'The answer mentioned checking availability.',
            'branch_id':'', 'coaching':'', 'decision_action':'PROBE',
            'source_ref_id':''
        }
        return httpx.Response(200,json={'choices':[{'message':{'content':json.dumps(data)}}]})
    p = GroqProvider(key='test_secret_key', transport=httpx.MockTransport(respond))
    for m in SUPPORTED_OPEN_MODELS:
        value = asyncio.run(p.generate('question',{'ai_model':m}, Decision))
        assert value.decision_action == 'PROBE'
    assert [r['model'] for r in captured] == list(SUPPORTED_OPEN_MODELS)
    assert all('test_secret_key' not in json.dumps(x) for x in captured)
    assert all('ai_model' not in x['messages'][1]['content'] for x in captured)
    assert 'reasoning_format' not in captured[-1]  # Qwen does not use GPT-OSS reasoning options


def test_selected_model_availability_checked_independently():
    def respond(req):
        return httpx.Response(200,json={'data':[{'id':'openai/gpt-oss-20b'}]})
    p=GroqProvider(key='test',transport=httpx.MockTransport(respond))
    out=asyncio.run(p.check_connection('openai/gpt-oss-20b'))
    assert out['connected'] is True and out['model']=='openai/gpt-oss-20b'
    with pytest.raises(ProviderError):
        asyncio.run(p.check_connection('qwen/qwen3.8-27b'))


def test_ui_and_api_allow_model_choice_but_no_grok_or_proprietary_gpt(tmp_path):
    with TestClient(create_app(tmp_path)) as client:
        client.headers.update({'X-Owner-Token':TOKEN})
        listing=client.get('/api/open-models')
        assert listing.status_code==200
        assert len(listing.json()['models']) == 5
        assert {m['provider'] for m in listing.json()['models']} == {'groq','huggingface'}
        page=client.get('/').text
        assert 'id="ai-model"' in page
        assert 'GPT-OSS 120B' in page
        assert 'Grok 4' not in page
        for fake in ['grok-4.7','gpt-6-luna','openai/gpt-4o']:
            response=client.post('/api/sessions',json={
                'cv':CV,'jd':JD,'provider':'demo','ai_model':fake
            })
            assert response.status_code == 422


def test_session_model_is_independent_in_scripted_mode(tmp_path):
    with TestClient(create_app(tmp_path)) as client:
        client.headers.update({'X-Owner-Token':TOKEN})
        for model in SUPPORTED_OPEN_MODELS:
            response=client.post('/api/sessions',json={
                'cv':CV,'jd':JD,'provider':'demo','ai_model':model
            })
            assert response.status_code == 200,response.text
            assert response.json()['setup']['ai_model'] == model


def test_controller_passes_each_sessions_model_without_shared_mutation(tmp_path):
    from app.engine import Engine
    from app.demo import DemoProvider
    from app.store import Store
    class CaptureProvider:
        model='openai/gpt-oss-20b'
        def __init__(self):self.seen=[]
        async def generate(self,task,ctx,schema):
            self.seen.append(ctx.get('ai_model'))
            return ctx.get('ai_model')
    p=CaptureProvider()
    e=Engine(Store(tmp_path),DemoProvider(),p)
    async def check():
        m1=await e.generate_for({'provider':'groq','ai_model':'openai/gpt-oss-120b'},'plan',{},object)
        m2=await e.generate_for({'provider':'groq','ai_model':'openai/gpt-oss-20b'},'plan',{},object)
        assert (m1,m2)==('openai/gpt-oss-120b','openai/gpt-oss-20b')
        assert p.model=='openai/gpt-oss-20b'
    asyncio.run(check())
