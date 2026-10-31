import time
from app.store import Store
from scripts.retention_maintenance import run_retention


def test_scheduled_retention_prunes_expired_local_sessions(tmp_path):
    store=Store(tmp_path)
    old={'id':'old','revision':0,'created_at':time.time()-90*86400}
    fresh={'id':'fresh','revision':0,'created_at':time.time()}
    store.create(old,'owner');store.create(fresh,'owner')
    result=run_retention(str(tmp_path),days=30)
    assert result['expired_sessions_deleted']==1
    assert store.load('old','owner') is None
    assert store.load('fresh','owner') is not None
