"""Version 5.3: practical lab, restricted parser, privacy, and regression checks."""
from pathlib import Path
import ast
import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from app.main import create_app
from app.practical_lab import CODING, CodingSubmission, EngineeringSubmission, catalog, evaluate_code, evaluate_engineering

OWNER_A={'X-Owner-Token':'e'*64}
OWNER_B={'X-Owner-Token':'f'*64}


@pytest.mark.parametrize('key,code',[
    ('sum_numbers','def solve(nums):\n    return sum(nums)'),
    ('reverse_text','def solve(text):\n    return text[::-1]'),
    ('palindrome','def solve(text):\n    return text == text[::-1]'),
    ('range_span','def solve(nums):\n    return max(nums) - min(nums)'),
    ('clamp','def solve(value, low, high):\n    return min(max(value, low), high)'),
])
def test_python_expressions_pass_public_and_edge_tests(key,code):
    out=evaluate_code(CodingSubmission(challenge_id=key,code=code))
    assert out['all_passed'] and out['passed']==5
    assert all('expected' not in x for x in out['tests'] if not x['public'])
    assert out['source']=='restricted_ast_test_runner'


@pytest.mark.parametrize('code',[
 'import os\ndef solve(nums):\n    return os.system("whoami")',
 'def solve(nums):\n    return __import__("os")',
 'def solve(nums):\n    return open("secret.txt")',
 'def solve(nums):\n    return nums.__class__',
 'def solve(nums):\n    while True: pass',
 'def solve(nums):\n    return [x for x in nums]',
 'def solve(nums):\n    return (lambda x:x)(1)',
 'def solve(nums):\n    return sum(nums) ** 100000',
 'def solve(nums):\n    return eval("1+1")',
 'def solve(nums):\n    return nums.sort()',
])
def test_forbidden_python_does_not_execute(code):
    try:
        out=evaluate_code(CodingSubmission(challenge_id='sum_numbers',code=code))
    except HTTPException as exc:
        assert exc.status_code==422
    else:
        assert not out['all_passed']
        assert any(t['status']=='error' for t in out['tests'])


def test_only_one_plain_function_and_correct_parameters():
    for src in ['def other(nums):\n    return sum(nums)',
                'def solve(nums, extra):\n    return sum(nums)',
                'def solve(nums=1):\n    return nums',
                'def solve(nums):\n    a = 1\n    return a']:
        with pytest.raises(HTTPException):
            evaluate_code(CodingSubmission(challenge_id='sum_numbers',code=src))


def test_wrong_code_fails_without_leaking_hidden_expected_values():
    out=evaluate_code(CodingSubmission(challenge_id='palindrome',code='def solve(text):\n    return False'))
    assert not out['all_passed']
    assert any(x['status']=='fail' for x in out['tests'])
    assert all('input' not in t and 'expected' not in t and 'actual' not in t for t in out['tests'] if not t['public'])


@pytest.mark.parametrize('case,answer',[
    ('enclosure_supports',441.45),
    ('bend_geometry',4.398229715),
    ('beam_deflection',1.3020833333),
])
def test_engineering_calculations(case,answer):
    result=evaluate_engineering(EngineeringSubmission(case_id=case,claimed_result=answer,reasoning='Assume stated limits.'))
    assert result['arithmetic_check']=='within_1_percent'
    assert result['reasoning_status']=='ungraded_manual_review'
    assert result['limitations']


def test_engineering_wrong_answer_and_no_reasoning():
    result=evaluate_engineering(EngineeringSubmission(case_id='enclosure_supports',claimed_result=150))
    assert result['arithmetic_check']=='outside_1_percent'
    assert result['reasoning_status']=='not_provided'


def test_owner_history_and_privacy_delete(tmp_path):
    with TestClient(create_app(tmp_path)) as c:
        assert c.get('/api/practical/catalog').status_code==401
        assert c.post('/api/practical/code',json={'challenge_id':'sum_numbers','code':'def solve(nums):\n return sum(nums)'}).status_code==401
        c.headers.update(OWNER_A)
        assert c.get('/api/health').json()['version']=='5.7.2'
        cat=c.get('/api/practical/catalog').json()
        assert len(cat['challenges'])>=5 and len(cat['engineering_cases'])>=3
        source='def solve(nums):\n    return sum(nums)'
        assert c.post('/api/practical/code',json={'challenge_id':'sum_numbers','code':source}).json()['all_passed']
        payload={'case_id':'enclosure_supports','claimed_result':441.45,'reasoning':'Dummy invented confidential note 123'}
        assert c.post('/api/practical/engineering',json=payload).status_code==200
        results=c.get('/api/practical/history').json()['attempts']
        assert len(results)==2 and results[0]['kind']=='engineering'
        assert source not in str(results) and payload['reasoning'] not in str(results)
        assert c.get('/api/practical/history',headers=OWNER_B).json()['attempts']==[]
        assert c.post('/api/privacy/delete-all',json={}).status_code==200
        assert c.get('/api/practical/history').json()['attempts']==[]


def test_bad_case_unknown_or_oversized(tmp_path):
    with TestClient(create_app(tmp_path)) as c:
        c.headers.update(OWNER_A)
        assert c.post('/api/practical/code',json={'challenge_id':'unknown','code':'def solve(x):\n return x'}).status_code==422
        assert c.post('/api/practical/code',json={'challenge_id':'sum_numbers','code':'a'*2501}).status_code==422
        assert c.post('/api/practical/engineering',json={'case_id':'wrong','claimed_result':42}).status_code==422
        assert c.post('/api/practical/engineering',json={'case_id':'enclosure_supports','claimed_result':'NaN'}).status_code==422
        assert c.post('/api/practical/engineering',json={'case_id':'enclosure_supports','claimed_result':3,'reasoning':'a'*2501}).status_code==422


def test_ui_navigation_and_non_executing_claim():
    root=Path(__file__).resolve().parents[1]/'app'/'static'
    html=(root/'index.html').read_text()
    js=(root/'practical.js').read_text()
    css=(root/'studio.css').read_text()
    for element in ('practical','practical-tab-code','practical-tab-engineering','practical-challenge','practical-source','practical-run','practical-code-result','practical-claimed','practical-engineering-run','practical-history-list'):
        assert 'id="'+element+'"' in html
    assert 'src="/static/practical.js"' in html
    assert "'practical'" not in js # view uses separate data-view handler
    assert 'innerHTML' not in js
    assert "'/api/practical/engineering'" in js and "'/api/practical/code'" in js
    assert '.practical-main' in css
