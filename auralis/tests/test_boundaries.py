import io
import json
import time
import uuid
import httpx
import pytest
from docx import Document
from app.documents import extract_document, normalize_evidence
from app.provider import GroqProvider, ProviderError
from app.schemas import Decision, Report
from app.engine import validate_report
from test_flow import client, start, prepare, act, CV, JD


def test_text_and_docx_extract():
    assert extract_document('cv.txt',b'Python developer with projects')=='Python developer with projects'
    d=Document(); d.add_paragraph('My Python booking project'); b=io.BytesIO(); d.save(b)
    assert 'Python booking' in extract_document('cv.docx',b.getvalue())

def test_bad_documents_and_large_text_rejected():
    with pytest.raises(ValueError):extract_document('cv.exe',b'bad')
    with pytest.raises(ValueError):extract_document('cv.pdf',b'not a PDF')
    with pytest.raises(ValueError):extract_document('cv.txt',b'x'*25001)

def test_upload_api(client):
    r=client.post('/api/documents',files={'file':('cv.txt',CV.encode(),'text/plain')})
    assert r.status_code==200 and r.json()['text']==CV
    assert client.post('/api/documents',files={'file':('a.exe',b'bad')}).status_code==422

def test_evidence_is_bounded_and_retains_paths(client):
    r=client.post('/api/evidence',files={'file':('rea.json',json.dumps({'modules':[{'path':'src/db.js','imports':['sqlite']}]}).encode(),'application/json')})
    assert r.status_code==200 and 'src/db.js' in r.json()['text']
    with pytest.raises(ValueError):normalize_evidence(b'{')

def test_expired_session_does_not_record_answer(client):
    s=start(client); owner=client.app.state.owner_hash('a'*64)
    original=client.app.state.store.load(s['id'],owner);original['deadline']=time.time()-1;client.app.state.store.save(original,owner)
    assert act(client,s).status_code==409
    assert client.get('/api/sessions/'+s['id']).json()['turns']==[]

def test_provider_failure_rolls_back_answer(client):
    s=start(client)
    async def fail(*a):raise ProviderError('Unavailable',503)
    client.app.state.engine.demo.generate=fail
    assert act(client,s).status_code==503
    actual=client.get('/api/sessions/'+s['id']).json()
    assert actual['turns']==[] and actual['current']==s['current']

def test_fake_evidence_cannot_be_reported(client):
    s=start(client);s=act(client,s).json()
    items=[dict(competency_id=c['id'],status='demonstrated',score=4,feedback='Strong answer with supporting evidence.',evidence_ids=['invented'],practice='Try a new scenario.') for c in s['plan']['competencies']]
    report=Report(summary='Good work in this interview.',items=items,limitations=['Practice guidance only.'])
    with pytest.raises(ProviderError):validate_report(report,s)

def test_no_evidence_means_unassessed_not_zero(client):
    s=start(client)
    report=Report(summary='Practice feedback.',items=[dict(competency_id=c['id'],status='demonstrated',score=4,feedback='Strong answer.',evidence_ids=[],practice='Try a scenario.') for c in s['plan']['competencies']],limitations=['Practice only.'])
    out=validate_report(report,s)
    assert all(i['score'] is None and i['status']=='not_assessed' for i in out['items'])

def test_groq_error_and_shape_handling():
    import asyncio
    provider=GroqProvider(key='test',transport=httpx.MockTransport(lambda r:httpx.Response(429,headers={'retry-after':'12'})))
    with pytest.raises(ProviderError) as e:asyncio.run(provider.generate('question',{},Decision))
    assert e.value.status==429 and e.value.retry_after=='12'
    provider=GroqProvider(key='test',transport=httpx.MockTransport(lambda r:httpx.Response(200,json={'choices':[{'message':{'content':'{"question":"bad"}'}}]})))
    with pytest.raises(ProviderError):asyncio.run(provider.generate('question',{},Decision))

def test_live_request_shape_and_transcription():
    import asyncio
    decision={'question':'How would you test concurrent writes?','competency_id':'c1','why':'The job requires concurrency.','difficulty':'applied','difficulty_reason':'The previous answer named a transaction.','branch_id':'','coaching':''}
    def transport(req):
        if req.url.path.endswith('transcriptions'):return httpx.Response(200,json={'text':'I use a transaction.'})
        body=json.loads(req.content)
        assert body['model']=='openai/gpt-oss-20b' and body['response_format']['type']=='json_object'
        return httpx.Response(200,json={'choices':[{'message':{'content':json.dumps(decision)}}]})
    p=GroqProvider(key='test',transport=httpx.MockTransport(transport))
    assert asyncio.run(p.generate('question',{},Decision)).competency_id=='c1'
    assert asyncio.run(p.transcribe(b'audio','answer.webm','audio/webm','en'))=='I use a transaction.'

def test_compare_live_without_consent_is_validation_error(client):
    r=client.post('/api/compare',json={'cv':CV,'jd_a':JD,'jd_b':JD,'provider':'groq','consent':False})
    assert r.status_code==422

def test_model_context_is_bounded_and_report_excerpts_labelled(client):
    s=start(client)
    for n in range(12):
        s['turns'].append({'id':f'turn_{n}','kind':'answer','text':'x'*8000,'question':s['current'],'created_at':time.time()})
    s['setup']['provider']='groq'
    ctx=client.app.state.engine.context(s,assessment=True)
    assert len(json.dumps(ctx))<24000
    assert all(t['excerpted'] for t in ctx['turns'])
    assert len(ctx['turns'])==12
