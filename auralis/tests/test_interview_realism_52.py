"""Auralis 5.2: interview-mode, backend-clock and transcript-based delivery tests."""
import math
import time
import uuid
from pathlib import Path
from fastapi.testclient import TestClient
from app.main import create_app
from app.interview_realism import interview_guidance, delivery_observation, delivery_summary
from test_flow import H, CV, JD


def _prepare(client, **extra):
    payload={'cv':CV,'jd':JD,'role':'Backend engineer','provider':'demo','mode':'interview',**extra}
    res=client.post('/api/sessions',json=payload)
    assert res.status_code==200,res.text
    return res.json()


def _start(client,session):
    res=client.post(f'/api/sessions/{session["id"]}/start')
    assert res.status_code==200,res.text
    return res.json()


def _act(client,session,text='Well, um, I would check one key assumption and test the failure.',**extra):
    return client.post(f'/api/sessions/{session["id"]}/actions',json={
        'kind':'answer','text':text,'expected_question_id':session['current']['id'],
        'request_id':str(uuid.uuid4()),**extra})


def test_modes_and_personas_are_per_session_and_save(tmp_path):
    with TestClient(create_app(tmp_path)) as c:
        c.headers.update(H)
        s=_prepare(c,interview_track='behavioral',interviewer_persona='hiring_manager',question_time_limit_seconds=90,adaptive_difficulty=False)
        s=_start(c,s)
        q=s['current']
        assert q['issued_at']>0 and q['time_limit_seconds']==90
        assert q['interview_track']=='behavioral' and q['interviewer_persona']=='hiring_manager'
        assert 'situation' in q['text'].lower()
        assert s['setup']['adaptive_difficulty'] is False
        assert c.get(f'/api/sessions/{s["id"]}').json()['setup']['interview_track']=='behavioral'
        history=c.get('/api/sessions').json()
        assert history[0]['id']==s['id']


def test_challenge_track_is_respectful_and_time_is_not_a_hard_rejection(tmp_path):
    with TestClient(create_app(tmp_path)) as c:
        c.headers.update(H)
        s=_start(c,_prepare(c,interview_track='pressure',interviewer_persona='panel',question_time_limit_seconds=60))
        assert 'priority decision first' in s['current']['text'].lower()
        # Modify the isolated test session timestamp to simulate elapsed question time without sleeping.
        store=c.app.state.store
        db_s=store.load(s['id'],c.app.state.owner_hash(H['X-Owner-Token']))
        db_s['current']['issued_at']=time.time()-65
        store.save(db_s,c.app.state.owner_hash(H['X-Owner-Token']))
        s2=_act(c,s).json()
        answer=s2['turns'][0]
        assert answer['over_question_limit'] is True
        assert answer['question_time_limit_seconds']==60
        assert answer['response_seconds']>=60
        assert s2['status']=='active'


def test_delivery_is_limited_to_voice_and_transcript_arithmetic(tmp_path):
    with TestClient(create_app(tmp_path)) as c:
        c.headers.update(H)
        s=_start(c,_prepare(c))
        text='Um, I would first check the load path, you know, and then run a static test.'
        s=_act(c,s,text,voice_duration_seconds=10,voice_source='browser_speech').json()
        d=s['turns'][0]['delivery']
        assert d['source']=='browser_speech'
        assert d['estimated_wpm']==round(60*d['transcript_word_count']/10,1)
        assert d['identified_fillers']==2
        assert 'NOT measured' in d['limitations']
        s=c.post(f'/api/sessions/{s["id"]}/finish').json()
        assert s['report']['delivery_summary']['samples']==1
        assert s['report']['delivery_summary']['filler_count']==2
        assert s['report']['delivery_summary']['mean_estimated_wpm']==d['estimated_wpm']
        assert 'audio' not in str(s['turns'][0]['delivery']).lower() or 'no audio' not in str(s['turns'][0]['delivery']).lower()


def test_typed_answers_have_no_delivery_and_bad_metadata_is_rejected(tmp_path):
    with TestClient(create_app(tmp_path)) as c:
        c.headers.update(H)
        s=_start(c,_prepare(c))
        base={'kind':'answer','text':'My answer','expected_question_id':s['current']['id'],'request_id':str(uuid.uuid4())}
        for patch in [{'voice_duration_seconds':10},{'voice_source':'browser_speech'},
                      {'voice_duration_seconds':1,'voice_source':'groq_transcription'},
                      {'voice_duration_seconds':121,'voice_source':'browser_speech'},
                      {'voice_duration_seconds':'NaN','voice_source':'browser_speech'},
                      {'voice_duration_seconds':10,'voice_source':'forged'}]:
            r=c.post(f'/api/sessions/{s["id"]}/actions',json={**base,**patch})
            assert r.status_code==422,(patch,r.text)
        typed=_act(c,s,'This is a typed response.').json()
        assert typed['turns'][0].get('delivery') is None
        assert typed['turns'][0]['over_question_limit'] is False


def test_reject_unknown_track_and_limit(tmp_path):
    with TestClient(create_app(tmp_path)) as c:
        c.headers.update(H)
        for extra in [{'interview_track':'mind_reader'},{'interviewer_persona':'intimidating'},
                      {'question_time_limit_seconds':1}, {'question_time_limit_seconds':3600}]:
            r=c.post('/api/sessions',json={'cv':CV,'jd':JD,**extra})
            assert r.status_code==422,(extra,r.text)


def test_legacy_session_default_guidance_and_no_voice():
    cfg=interview_guidance({'mode':'interview'})
    assert cfg['track']=='technical' and cfg['persona']=='supportive'
    assert delivery_summary([])['samples']==0
    assert delivery_observation('hello',None,'browser_speech') is None


def test_frontend_elements_and_submission_binding():
    root=Path(__file__).resolve().parents[1]/'app'/'static'
    html=(root/'index.html').read_text()
    js=(root/'app.js').read_text()
    for id in ['interview-track','interviewer-persona','question-limit','adaptive-difficulty',
               'question-countdown','voice-last','room-persona']:
        assert f'id="{id}"' in html
    for token in ['voice_duration_seconds','voiceEvidence','question_time_limit_seconds','renderArena','question-countdown']:
        assert token in js
    assert 'stopCapture(false);notify(' in js
    assert 'voiceEvidence=null' in js
