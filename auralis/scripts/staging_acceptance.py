"""Two-account HTTPS staging acceptance checks, using disposable verified users.

Never creates user identities or dumps secrets. Tests only tagged temporary data.
Opt in to model generation with --live-session; this uses paid provider capacity.
"""
import argparse
import os
import re
import secrets
import sys
from urllib.parse import urlsplit
import httpx

CONFIRM = 'I_CONFIRM_DISPOSABLE'


def require_settings():
    keys = ('AURALIS_STAGING_URL', 'AURALIS_TEST_A_EMAIL', 'AURALIS_TEST_A_PASSWORD',
            'AURALIS_TEST_B_EMAIL', 'AURALIS_TEST_B_PASSWORD')
    missing = [key for key in keys if not os.getenv(key)]
    if missing:
        raise ValueError('Missing staging settings: ' + ', '.join(missing))
    if os.getenv('AURALIS_TEST_ISOLATED_STAGING') != CONFIRM:
        raise ValueError('Set AURALIS_TEST_ISOLATED_STAGING=I_CONFIRM_DISPOSABLE for disposable staging only.')
    if os.getenv('AURALIS_STAGING_GATE_VERIFIED') != 'I_VERIFIED_ACCESS_GATE':
        raise ValueError('Set AURALIS_STAGING_GATE_VERIFIED=I_VERIFIED_ACCESS_GATE after checking real staging access control.')
    url = os.environ['AURALIS_STAGING_URL'].rstrip('/')
    parsed = urlsplit(url)
    if (parsed.scheme != 'https' or not parsed.hostname or parsed.username or parsed.password or
            parsed.port not in (None,443) or parsed.path or parsed.query or parsed.fragment):
        raise ValueError('AURALIS_STAGING_URL must be an exact HTTPS origin.')
    if os.environ['AURALIS_TEST_A_EMAIL'].casefold() == os.environ['AURALIS_TEST_B_EMAIL'].casefold():
        raise ValueError('Use two different verified Supabase test accounts.')
    return url


def expect(response, code, label, checks):
    if response.status_code != code:
        # Never echo response bodies: they can include owner-supplied CV or other private content.
        raise AssertionError(f'{label}: HTTP {response.status_code}, expected {code}')
    checks.append(label)
    print('PASS', label)
    return response


def run(live_session=False):
    base = require_settings()
    checks = []
    token_tag = secrets.token_hex(5)
    a_card = b_card = sid = None
    gateway_id=os.getenv('CF_ACCESS_CLIENT_ID','')
    gateway_secret=os.getenv('CF_ACCESS_CLIENT_SECRET','')
    if bool(gateway_id)!=bool(gateway_secret):
        raise ValueError('Configure BOTH Cloudflare Access service-token fields or neither.')
    gateway_headers=({'CF-Access-Client-Id':gateway_id,'CF-Access-Client-Secret':gateway_secret}
                     if gateway_id else {})
    with httpx.Client(base_url=base, timeout=60, follow_redirects=False,
                      headers=gateway_headers, trust_env=True) as alice, httpx.Client(base_url=base, timeout=60,
                      follow_redirects=False, headers=gateway_headers, trust_env=True) as bob:
        config = expect(alice.get('/api/public-config'), 200, 'public config', checks).json()
        assert config.get('authentication_required') is True and config.get('strict_live') is True, 'Not hosted-auth production mode'
        expect(alice.get('/api/ready'), 200, 'PostgreSQL-backed readiness', checks)
        health = expect(alice.get('/api/health'), 200, 'web server liveness', checks)
        assert health.headers.get('strict-transport-security'), 'Missing HSTS'
        assert health.headers.get('x-frame-options') == 'DENY', 'Missing frame denial'
        expect(alice.post('/api/auth/login', headers={'Origin':'http://'+urlsplit(base).netloc},
                          json={'email':'invalid@example.org','password':'invalidpass123'}),
               403, 'reject downgraded Origin', checks)
        for client, prefix in ((alice,'A'), (bob,'B')):
            email = os.environ[f'AURALIS_TEST_{prefix}_EMAIL']
            password = os.environ[f'AURALIS_TEST_{prefix}_PASSWORD']
            r = expect(client.post('/api/auth/login', json={'email':email,'password':password}),
                       200, f'{prefix} Supabase login', checks)
            assert r.json().get('access_token'), 'Missing access token'
            cookies = r.headers.get('set-cookie','').lower()
            assert all(x in cookies for x in ('httponly', 'secure', 'samesite=lax')), 'Refresh cookie flags missing'
            client.headers['Authorization'] = 'Bearer ' + r.json()['access_token']
            me = expect(client.get('/api/auth/me'), 200, f'{prefix} Supabase user verified', checks).json()
            assert me.get('email','').casefold() == email.casefold(), 'Account identity mismatch'
            if prefix == 'A': a_identity = me.get('id')
            else: assert me.get('id') != a_identity, 'Two accounts have identical Supabase user IDs'
            refresh = expect(client.post('/api/auth/refresh'), 200, f'{prefix} refresh cookie', checks).json()
            client.headers['Authorization'] = 'Bearer ' + refresh['access_token']
        try:
            content_a = f'Auralis staging-only question A {token_tag}: how does database row isolation work?'
            content_b = f'Auralis staging-only question B {token_tag}: how do safe backups work?'
            a_card = expect(alice.post('/api/question-bank', json={'question':content_a,'competency':'Security testing'}),
                            200, 'A creates owned record', checks).json()['id']
            b_card = expect(bob.post('/api/question-bank', json={'question':content_b,'competency':'Backup testing'}),
                            200, 'B creates owned record', checks).json()['id']
            list_a = expect(alice.get('/api/question-bank'), 200, 'A list records', checks).json()['saved']
            list_b = expect(bob.get('/api/question-bank'), 200, 'B list records', checks).json()['saved']
            assert a_card in [x['id'] for x in list_a] and b_card not in [x['id'] for x in list_a], 'A list leaked B record'
            assert b_card in [x['id'] for x in list_b] and a_card not in [x['id'] for x in list_b], 'B list leaked A record'
            checks.append('bidirectional stored-record isolation');print('PASS bidirectional stored-record isolation')
            expect(bob.post(f'/api/question-bank/{a_card}/practice', json={'status':'practiced'}),
                   404, 'B cannot modify A record', checks)
            r = expect(bob.delete(f'/api/question-bank/{a_card}'), 200,
                       'B delete A request safe', checks)
            assert r.json()['deleted'] is False, 'B deleted A record!'
            expect(bob.post('/api/college/cohorts',json={'name':'Unauthorized staging cohort'}),
                   403, 'non-instructor B forbidden from cohort creation', checks)
            if live_session:
                synthetic_cv = ('Synthetic staging candidate built a Python and PostgreSQL API with repeatable tests, '
                                'race-condition detection, schema migrations and encrypted backup checks for an internal pilot.')
                synthetic_jd = ('Backend software engineer responsible for Python APIs, secure database queries, '
                                'account isolation, operational reliability and disaster-recovery tests.')
                payload = {'cv':synthetic_cv,'jd':synthetic_jd,'role':'Backend engineer',
                           'provider':'groq','ai_model':os.getenv('GROQ_MODEL','openai/gpt-oss-120b'),
                           'consent':True,'synthetic_data':True}
                created = expect(alice.post('/api/sessions',json=payload,timeout=120),
                                 200, 'real Groq plan created and PostgreSQL-persisted', checks).json()
                sid = created['id']
                assert created.get('plan_source') == 'live_ai', 'No verified Groq live plan'
                expect(alice.get(f'/api/sessions/{sid}'), 200, 'A retrieves interview', checks)
                for method,path in (('get',f'/api/sessions/{sid}'), ('get',f'/api/sessions/{sid}/export'),
                                    ('delete',f'/api/sessions/{sid}'), ('post',f'/api/sessions/{sid}/finish'),
                                    ('post',f'/api/sessions/{sid}/start')):
                    expect(getattr(bob,method)(path),404,f'B blocked {method.upper()} A session',checks)
                expect(alice.get(f'/api/sessions/{sid}'),200,'A session intact after B attacks',checks)
        finally:
            # Only cleanup IDs created by this run. No deletion of other account data.
            if a_card:
                r=alice.delete(f'/api/question-bank/{a_card}')
                expect(r,200,'cleanup A test record',checks)
                assert r.json()['deleted'] is True
            if b_card:
                r=bob.delete(f'/api/question-bank/{b_card}')
                expect(r,200,'cleanup B test record',checks)
                assert r.json()['deleted'] is True
            if sid:
                expect(alice.delete(f'/api/sessions/{sid}'),200,'cleanup A synthetic interview',checks)
            for client,prefix in ((alice,'A'),(bob,'B')):
                r = client.post('/api/auth/logout')
                expect(r,200,f'{prefix} logout',checks)
                expect(client.post('/api/auth/refresh'),401,f'{prefix} refresh blocked after logout',checks)
    print(f'PASS: {len(checks)} accepted HTTP checks. This does NOT verify email delivery, token expiry, backups or full interviews.')
    return 0


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--live-session',action='store_true',help='Billable real Groq plan and session-isolation test')
    args=parser.parse_args()
    try: sys.exit(run(live_session=args.live_session))
    except (ValueError, AssertionError, httpx.HTTPError) as err:
        # Do not show HTTP response bodies or sensitive env values.
        print('FAIL', str(err) if isinstance(err,(ValueError,AssertionError)) else type(err).__name__)
        sys.exit(1)
