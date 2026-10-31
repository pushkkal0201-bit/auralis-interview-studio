"""Non-destructive hosted configuration and dependency probe.

Usage:
  python -m scripts.cloud_preflight                 # no network, safe locally
  python -m scripts.cloud_preflight --live          # remote connectivity
  python -m scripts.cloud_preflight --live --inference   # one billable Groq generation

Never prints keys, database connection strings, passwords, or email addresses.
"""
import argparse
import os
from pathlib import Path
import sys
import httpx
from dotenv import load_dotenv
from urllib.parse import urlparse

load_dotenv(Path(__file__).resolve().parent.parent/'.env')


def config_checks():
    dsn=os.getenv('DATABASE_URL','')
    url=os.getenv('SUPABASE_URL','')
    public=os.getenv('AURALIS_PUBLIC_URL','')
    checks={
        'production mode':os.getenv('AURALIS_DEPLOYMENT_MODE','').lower()=='production',
        'PostgreSQL URL configured':dsn.startswith(('postgresql://','postgres://')),
        'Supabase HTTPS URL configured':url.startswith('https://') and url.endswith('.supabase.co'),
        'Supabase public key configured':bool(os.getenv('SUPABASE_PUBLISHABLE_KEY')),
        'Groq private key configured':bool(os.getenv('GROQ_API_KEY')),
        'public HTTPS URL configured':public.startswith('https://'),
        'instructor ID access list configured':bool(os.getenv('AURALIS_COLLEGE_INSTRUCTOR_IDS')),
    }
    return checks


def run(live=False,inference=False):
    checks=config_checks()
    for label,passed in checks.items():
        print(f"{'OK' if passed else 'CHECK'}  {label}")
    # Instructor list is optional. Without it there are no hosted instructor accounts.
    blocking=any(not v for k,v in checks.items() if k!='instructor ID access list configured')
    if not live:
        print('Offline configuration only. No remote systems or model generation tested.')
        return 1 if blocking else 0
    if blocking:
        print('Cannot run remote probes until required production configuration is complete.')
        return 1
    try:
        import psycopg
        with psycopg.connect(os.environ['DATABASE_URL'].replace('postgres://','postgresql://',1),connect_timeout=8) as db:
            db.execute('SELECT 1').fetchone()
            required=('sessions','source_evidence','college_cohorts','intelligence_disputes','ai_usage')
            with db.cursor() as cur:
                cur.execute('SELECT table_name FROM information_schema.tables WHERE table_schema=current_schema()')
                existing={name for (name,) in cur.fetchall()}
            missing=[x for x in required if x not in existing]
            if missing:
                print('CHECK  Database reachable but expected tables are missing: '+', '.join(missing))
                blocking=True
            else:print('OK  PostgreSQL connection and expected schema')
    except Exception:
        print('CHECK  PostgreSQL connection failed; inspect Render database credentials and network access.')
        blocking=True
    try:
        base=os.environ['SUPABASE_URL'].rstrip('/')
        key=os.environ['SUPABASE_PUBLISHABLE_KEY']
        with httpx.Client(timeout=12,follow_redirects=False) as client:
            resp=client.get(base+'/auth/v1/health',headers={'apikey':key})
        if resp.status_code==200:print('OK  Supabase Auth health endpoint (not a user-login test)')
        else:
            print(f'CHECK  Supabase Auth health returned HTTP {resp.status_code}; test signup separately.')
            blocking=True
    except (httpx.RequestError,ValueError):
        print('CHECK  Supabase Auth unreachable.')
        blocking=True
    try:
        model=os.getenv('GROQ_MODEL','openai/gpt-oss-120b')
        headers={'Authorization':'Bearer '+os.environ['GROQ_API_KEY']}
        with httpx.Client(timeout=20,follow_redirects=False) as client:
            resp=client.get('https://api.groq.com/openai/v1/models',headers=headers)
        if resp.status_code!=200:
            print(f'CHECK  Groq API model list HTTP {resp.status_code}')
            blocking=True
        elif model not in {x.get('id') for x in resp.json().get('data',[])}:
            print('CHECK  Selected Groq model is not listed for this account.')
            blocking=True
        else:
            print('OK  Groq key and selected model appear valid (generation not yet tested)')
            if inference:
                request={'model':model,'messages':[{'role':'user','content':'Return exactly the JSON object {"status":"ok"}.'}],
                         'response_format':{'type':'json_object'},'max_completion_tokens':120}
                if model.startswith('openai/gpt-oss-'):
                    request.update({'reasoning_format':'hidden','reasoning_effort':'low'})
                with httpx.Client(timeout=90,follow_redirects=False) as client:
                    actual=client.post('https://api.groq.com/openai/v1/chat/completions',headers=headers,json=request)
                if actual.status_code==200 and actual.json().get('choices'):
                    print('OK  Groq completed one real chat inference')
                else:
                    print(f'CHECK  Groq generation returned HTTP {actual.status_code}')
                    blocking=True
    except (httpx.RequestError,KeyError,ValueError):
        print('CHECK  Groq connection or response verification failed.')
        blocking=True
    print('Remote probe finished. Account isolation, backups, email delivery and concurrent interview recovery need separate acceptance tests.')
    return 1 if blocking else 0


if __name__=='__main__':
    parser=argparse.ArgumentParser(description='Verify production environment without printing secrets')
    parser.add_argument('--live',action='store_true',help='Contact your configured cloud services')
    parser.add_argument('--inference',action='store_true',help='Make one real, billable Groq request; requires --live')
    args=parser.parse_args()
    if args.inference and not args.live:parser.error('--inference requires --live')
    sys.exit(run(live=args.live,inference=args.inference))
