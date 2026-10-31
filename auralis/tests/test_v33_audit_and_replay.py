"""3.3 regression cases from synthetic mechanical interview and PDF export review."""
from pathlib import Path
from fastapi.testclient import TestClient
from app.audit import (provider_failure_code, claim_provenance, score_gap_note,
                       fallback_record, cautious_claim_language)
from app.policy import is_repeated
from app.main import create_app
from app.provider import ProviderError
from test_industry_controller import ControlledProvider
from test_flow import prepare, act, H


FIRST_MATERIAL='Explain how material properties of 2 mm mild-steel sheet influence the design choices for a floor-mounted low-voltage switchgear enclosure, including considerations of strength, stiffness, and manufacturability.'
NEAR_MATERIAL='Explain how the material properties of 2 mm mild-steel sheet such as yield strength, Youngs modulus, and formability affect design choices for a floor-mounted low-voltage switchgear enclosure, specifically regarding wall thickness adequacy, stiffness, buckling resistance, and manufacturability considerations.'
FIRST_GDT='When generating the 2-D manufacturing drawings for the enclosure in Creo, which GD&T symbols would you apply to critical features such as the mating edges, mounting hole locations, and ventilation cutouts, and how would you justify the chosen tolerances to ensure proper fit and function while controlling cost?'
NEAR_GDT='When creating the 2-D manufacturing drawing for the enclosure in Creo, which datum feature hierarchy would you establish, and how would you apply the appropriate GD&T symbols to the critical mating edges, mounting hole patterns, and ventilation cutouts to balance functional tolerance needs with cost and manufacturability?'


def session_with_question(q,cid='c1'):
    return {'turns':[{'id':'t1','kind':'answer','question':{'text':q,'competency_id':cid}}]}


def test_mechanical_material_paraphrase_blocked():
    assert is_repeated(NEAR_MATERIAL,session_with_question(FIRST_MATERIAL),'c1')


def test_mechanical_gdt_paraphrase_blocked():
    assert is_repeated(NEAR_GDT,session_with_question(FIRST_GDT,'c2'),'c2')


def test_new_load_case_not_rejected_as_duplication():
    q='Given the internal equipment mass of 180 kg, how would you assess buckling and excessive deflection in the enclosure walls and verify the base-load path?'
    assert not is_repeated(q,session_with_question(FIRST_MATERIAL),'c1')


def test_distinct_competencies_are_allowed_similar_general_terms():
    assert not is_repeated(NEAR_MATERIAL,session_with_question(FIRST_MATERIAL,'c2'),'c1')


def test_error_categories_do_not_leak_provider_text():
    for status, code in [(429,'rate_limited'),(401,'authentication_or_permission'),(503,'provider_or_transport_unavailable'),(504,'timeout'),(422,'provider_output_invalid')]:
        error=ProviderError('secret gsk_123456789012345678901234567890',status)
        record=fallback_record('question','Live unavailable','c3',2,provider_failure_code(error))
        assert record['error_code']==code
        assert 'gsk_' not in str(record)
        assert record['attempt_count']==2


def test_synthetic_and_self_reported_provenance():
    synthetic=claim_provenance({'synthetic_data':True})
    unverified=claim_provenance({})
    assert synthetic['status']=='synthetic_test_data'
    assert 'fictional' in synthetic['label'].lower()
    assert unverified['status']=='self_reported_unverified'


def test_unsupported_employment_verification_is_normalized():
    text='Included a real-world project example with proven hands-on expertise and verified professional experience.'
    cautious=cautious_claim_language(text)
    assert 'real-world project' not in cautious
    assert 'proven hands-on' not in cautious
    assert 'unverified' in cautious.lower()


def test_missing_next_level_explanation_explicit_not_fabricated():
    assert 'did not specify' in score_gap_note({'score':3})
    assert score_gap_note({'score':3,'next_score_gap':'No actual FEA result was provided.'})=='No actual FEA result was provided.'
    assert 'Highest' in score_gap_note({'score':4})
    assert 'No score' in score_gap_note({'score':None})


def test_synthetic_flag_saved_and_report_claims_not_verified(tmp_path):
    fake=ControlledProvider()
    with TestClient(create_app(tmp_path,provider=fake)) as client:
        client.headers.update(H)
        setup=prepare(client,provider='groq',consent=True,synthetic_data=True)
        assert setup['setup']['synthetic_data'] is True
        sid=setup['id']
        session=client.post(f'/api/sessions/{sid}/start').json()
        assert session['current']['source']=='live_ai'
        assert session['current']['generation_attempts']==1
        assert session['current']['xray']['question_source']=='live_ai'
        session=act(client,session,'Fictional test answer: stress and strain are the same.').json()
        result=client.post(f'/api/sessions/{sid}/finish')
        assert result.status_code==200,result.text
        report=result.json()['report']
        assert report['claim_provenance']['status']=='synthetic_test_data'
        assert len(report['question_sources'])==1
        assert report['question_sources'][0]['source']=='live_ai'
        scored=[i for i in report['items'] if i['score'] is not None]
        assert scored and all('score_gap' in item for item in scored)


def test_rate_limit_fallback_visible_with_single_attempt(tmp_path):
    fake=ControlledProvider(question='outage')
    with TestClient(create_app(tmp_path,provider=fake)) as client:
        client.headers.update(H)
        session=prepare(client,provider='groq',consent=True)
        session=client.post(f'/api/sessions/{session["id"]}/start').json()
        assert session['current']['source']=='local_rubric_fallback'
        assert session['fallback_events'][0]['error_code']=='rate_limited'
        assert session['fallback_events'][0]['attempt_count']==1
        assert session['current']['xray']['generation_attempts']==1


def test_ui_has_both_export_modes_xray_and_markdown_safety():
    directory=Path(__file__).resolve().parents[1]/'app'/'static'
    js=(directory/'app.js').read_text()
    css=(directory/'style.css').read_text()
    html=(directory/'index.html').read_text()
    for fragment in ['claim_provenance','score_gap','replay-xray','answerDocument','report-method-details','print-compact','print-full']:
        assert fragment in js or fragment in css
    assert "document.createTextNode(part)" in js
    assert 'synthetic-data' in html
    assert 'body.print-full .report-replay .turn' in css
    assert 'break-inside:auto!important' in css
