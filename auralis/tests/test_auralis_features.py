import asyncio
import io
import json
import zipfile

import httpx
import pytest
from fastapi.testclient import TestClient
from app.codeproof import CodeProofError, inspect_zip
from app.main import create_app
from app.provider import GroqProvider, ProviderError
from app.skill_loader import load_interviewer_skill

TOKEN='c'*64
H={'X-Owner-Token':TOKEN}


def zipped(mapping):
    b=io.BytesIO()
    with zipfile.ZipFile(b,'w',compression=zipfile.ZIP_DEFLATED) as z:
        for k,v in mapping.items():z.writestr(k,v)
    return b.getvalue()


def demo_code():
    return zipped({'demo-project/app/bookings.py':
        'def book_slot(slot):\n    if slot.available:\n        save_booking(slot)\n        slot.available = False\n',
        'demo-project/app/reporting.py':'def report():\n    return [1,2,3]\n'})


def test_codeproof_extracts_real_file_and_lines():
    result=inspect_zip(demo_code())
    assert result['source_files_scanned']==2
    assert any(r['path']=='app/bookings.py' and r['line_start']==1 and r['symbol']=='book_slot' for r in result['refs'])
    assert 'def book_slot' in result['evidence_text']
    assert all('runtime behavior not verified' in r['note'] for r in result['refs'])


def test_codeproof_rejects_zip_bomb_and_does_not_execute_code():
    with pytest.raises(CodeProofError):inspect_zip(zipped({'one.py':'x'*(1700*1024)}))
    with pytest.raises(CodeProofError):inspect_zip(zipped({'../evil.py':'def bad(): pass\n'}))
    marker={'called':False}
    result=inspect_zip(zipped({'demo/project.py':'raise RuntimeError("would only run if executed")\ndef safe():return 3\n'}))
    assert result['refs'] and marker['called'] is False


def test_codeproof_redacts_secret_like_assignments():
    result=inspect_zip(zipped({'demo/config.py':'def config():\n    api_key="SECRET_WOULD_LEAK"\n    return 1\n'}))
    assert 'SECRET_WOULD_LEAK' not in json.dumps(result)


def test_agent_skill_is_standards_metadata_plus_real_instructions():
    s=load_interviewer_skill()
    assert 'follow-up' in s.lower() and 'not assessed' in s.lower()


def test_codeproof_and_incident_http_routes(tmp_path):
    with TestClient(create_app(tmp_path)) as c:
        c.headers.update(H)
        r=c.post('/api/codeproof/zip',files={'file':('source.zip',demo_code(),'application/zip')})
        assert r.status_code==200,r.text
        assert r.json()['refs'][0]['id'].startswith('R')
        assert c.get('/api/incidents').json()['incidents'][0]['id']=='booking-race'
        assert c.post('/api/codeproof/zip',files={'file':('wrong.txt',b'bad')}).status_code==422
        for url in ['http://127.0.0.1/admin','https://github.com/owner/repo/../../private',
                    'https://github.com.evil.com/owner/repo']:
            assert c.post('/api/codeproof/github',json={'url':url}).status_code==422


def test_source_references_appear_in_xray_for_live_mock(tmp_path):
    # Use real controller and fake model for deterministic end-to-end verification.
    from app.schemas import Plan,Decision,Report
    class Fake:
        model='fake/test-model'
        def configured(self):return True
        async def generate(self,task,context,schema):
            if task=='plan':
                from app.demo import DemoProvider
                d=DemoProvider()
                return await d.generate(task,context,Plan)
            if task=='question':
                return Decision(question='Can two concurrent booking requests both pass this availability check?',
                       competency_id=context['plan']['competencies'][0]['id'],why='Source observation from book_slot at a specific path.',
                       difficulty='applied',difficulty_reason='Tests concurrency and atomicity.',decision_action='PROBE',source_ref_id='R01')
            if task=='report':
                raise AssertionError('Report not used in this test')
    cv='B.Tech student. Built Python FastAPI reservation API with database and validation. Worked on booking projects.'
    jd='Backend engineering intern: Python, API design, transactions, databases, debugging, and concurrency.'
    with TestClient(create_app(tmp_path,provider=Fake())) as c:
        c.headers.update(H)
        scanned=c.post('/api/codeproof/zip',files={'file':('source.zip',demo_code(),'application/zip')})
        assert scanned.status_code==200,scanned.text
        handle=scanned.json()['evidence_handle']
        body={'cv':cv,'jd':jd,'provider':'groq','consent':True,'codeproof_handle':handle,
              'project_evidence':scanned.json()['evidence_text']}
        res=c.post('/api/sessions',json=body)
        assert res.status_code==200,res.text
        sid=res.json()['id']
        result=c.post(f'/api/sessions/{sid}/start').json()
        assert result['current']['xray']['source']['path']=='app/bookings.py'
        assert result['current']['xray']['source']['line_start']==1
        assert result['current']['xray']['decision']=='START'
        assert result['current']['source_ref_id']=='R01'


def test_live_key_check_with_mock_transport():
    def fake(req):
        assert req.url.path.endswith('/models')
        return httpx.Response(200,json={'data':[{'id':'openai/gpt-oss-20b'}]})
    p=GroqProvider(key='test-key',transport=httpx.MockTransport(fake))
    assert asyncio.run(p.check_connection())['connected']
    p=GroqProvider(key='bad',transport=httpx.MockTransport(lambda r:httpx.Response(401)))
    with pytest.raises(ProviderError):asyncio.run(p.check_connection())
