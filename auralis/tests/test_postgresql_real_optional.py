"""Optional real PostgreSQL smoke test.

Only runs against an explicitly designated disposable database. It creates
schema objects and may change schema: NEVER point at a live customer database.
Example: AURALIS_TEST_DATABASE_URL=postgresql://... and
AURALIS_TEST_ISOLATED_DATABASE=I_CONFIRM_DISPOSABLE, pytest this file.
"""
import os
import uuid
import pytest

url=os.getenv('AURALIS_TEST_DATABASE_URL','')
confirmation=os.getenv('AURALIS_TEST_ISOLATED_DATABASE','')
pytestmark=pytest.mark.skipif(
    not url.startswith(('postgresql://','postgres://')) or confirmation!='I_CONFIRM_DISPOSABLE',
    reason='Requires isolated PostgreSQL URL and explicit disposable-database confirmation')


def test_full_schema_and_owner_persistence():
    from app.store import Store
    from app import career_suite as cs, intelligence56 as intel
    from app.database import connect
    store=Store(url)
    cs.init_tables(url)
    intel.init_tables(url)
    user='smoke_'+str(uuid.uuid4()); other='smoke_'+str(uuid.uuid4())
    sid='smoke_'+str(uuid.uuid4())
    session={'id':sid,'revision':0,'created_at':1500000000.0,'setup':{'provider':'groq'}}
    try:
        store.create(session,user)
        assert store.load(sid,user)['id']==sid
        assert store.load(sid,other) is None
        session['revision']=0
        session['status']='ready'
        store.save(session,user)
        assert store.load(sid,user)['status']=='ready'
        assert any(x['id']==sid for x in store.list(user))
        assert not any(x['id']==sid for x in store.list(other))
        assert store.delete_plan(user) is False
        with connect(url) as db:assert db.execute('SELECT 1').fetchone()[0]==1
    finally:
        store.delete_owner(user)
