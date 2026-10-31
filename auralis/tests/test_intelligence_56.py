"""5.6 verification: owner scope, exact answer provenance, no fabricated skill claims."""
import json
from pathlib import Path
from fastapi.testclient import TestClient
from app.main import create_app, owner_hash
from app.intelligence56 import MatchRequest, match_cv,WhiteboardRequest,whiteboard_observe

A={'X-Owner-Token':'a'*64}; B={'X-Owner-Token':'b'*64}

def sample_report(sid='interview56'):
    return {'id':sid,'created_at':99,'revision':0,'setup':{'provider':'groq'},'plan':{
        'role':'Mechanical Design Engineer', 'competencies':[{'id':'c1','name':'Mechanical Engineering Fundamentals','criteria':['Understand strength and stiffness']}]
    },'turns':[{'id':'turn1','kind':'answer','text':'Young modulus is elastic stiffness and not the yield strength.','question':{'text':'Distinguish modulus and yield strength','competency_id':'c1'}}],
    'report':{'provisional':False,'demo':False,'items':[{'competency_id':'c1','name':'Mechanical Engineering Fundamentals','score':2,'status':'partially_demonstrated','feedback':'Good basics, but no verification example','score_gap':'Provide a load case and validation data','evidence_ids':['turn1']} ]}}

def test_match_is_unverified_not_hiring_score(tmp_path):
    with TestClient(create_app(tmp_path)) as c:
        content={'cv':'Experienced engineer. Used PTC Creo to design 2 mm sheet metal enclosures and checked brackets.',
                 'jd':'Role requires CAD experience with Creo and FEA using ANSYS and sheet metal fabrication.'}
        assert c.post('/api/intelligence/match',json=content).status_code==401
        res=c.post('/api/intelligence/match',headers=A,json=content)
        assert res.status_code==200,res.text
        data=res.json(); assert data['total']>0 and data['matched']>0
        assert any(it['status']=='mentioned_in_cv_unverified' for it in data['items'])
        assert any(it['status']=='not_found_in_cv' for it in data['items'])
        assert 'hiring' in data['limitations'].lower()
        assert content['cv'] not in str(c.get('/api/sessions',headers=A).json())
        assert c.get('/api/health').json()['version']=='5.7.2'

def test_board_structure_rejects_invalid_edges_and_no_data_retention(tmp_path):
    with TestClient(create_app(tmp_path)) as c:
        body={'domain':'mechanical','nodes':[{'id':'a','label':'Base frame','x':100,'y':100},{'id':'b','label':'Support bracket','x':300,'y':100}],
              'edges':[{'source':'a','target':'b','label':'transfers load'}]}
        r=c.post('/api/intelligence/whiteboard/review',json=body,headers=A)
        assert r.status_code==200,r.text
        data=r.json(); assert data['source']=='deterministic_diagram_review'
        assert 'Freehand pixels' in data['limitations']
        assert 'Base frame' in data['observed_elements'][0]
        assert c.post('/api/intelligence/whiteboard/review',json={**body,'edges':[{'source':'a','target':'absent'}]},headers=A).status_code==422
        assert c.post('/api/intelligence/whiteboard/ai',json={**body,'consent':False},headers=A).status_code==422
        assert c.get('/api/sessions',headers=A).json()==[]

def test_evidence_dispute_owner_and_deletion(tmp_path):
    app=create_app(tmp_path)
    app.state.store.create(sample_report(),owner_hash(A['X-Owner-Token']))
    with TestClient(app) as c:
        assert c.get('/api/intelligence/evidence/interview56',headers=B).status_code==404
        data=c.get('/api/intelligence/evidence/interview56',headers=A).json()
        item=data['items'][0]; assert item['score']==2 and 'validation' in item['score_gap']
        assert item['citations'][0]['turn_id']=='turn1'
        assert item['citations'][0]['answer_excerpt']=='Young modulus is elastic stiffness and not the yield strength.'
        assert c.post('/api/intelligence/disputes/interview56',headers=A,json={'competency_id':'wrong','reason':'The score misread the evidence.'}).status_code==422
        result=c.post('/api/intelligence/disputes/interview56',headers=A,json={'competency_id':'c1','reason':'The submitted calculation was correctly evaluated.'})
        assert result.status_code==200,result.text
        assert result.json()['status']=='recorded_for_your_review'
        assert c.get('/api/intelligence/disputes/interview56',headers=B).status_code==404
        assert len(c.get('/api/intelligence/disputes/interview56',headers=A).json()['notes'])==1
        assert c.delete('/api/sessions/interview56',headers=A).status_code==200
        assert c.get('/api/intelligence/evidence/interview56',headers=A).status_code==404
        with app.state.store.connect() as db:
            assert db.execute('SELECT COUNT(*) FROM intelligence_disputes').fetchone()[0]==0

def test_knowledge_map_practice_spaced_variant_and_owner_scope(tmp_path):
    with TestClient(create_app(tmp_path)) as c:
        r=c.get('/api/intelligence/knowledge/mechanical',headers=A)
        assert r.status_code==200,r.text
        data=r.json();assert len(data['topics'])==5
        assert data['topics'][2]['prerequisites']==['mechanical-0','mechanical-1']
        original=data['topics'][2]['question']
        r=c.post('/api/intelligence/knowledge/practice',headers=A,json={'domain':'mechanical','topic':'mechanical-2','outcome':'needs_practice'})
        assert r.status_code==200 and r.json()['topics'][2]['attempts']==1
        assert r.json()['topics'][2]['question']!=original
        assert c.get('/api/intelligence/knowledge/mechanical',headers=B).json()['topics'][2]['attempts']==0
        assert c.post('/api/intelligence/knowledge/practice',headers=A,json={'domain':'mechanical','topic':'software-2','outcome':'understood'}).status_code==422
        assert c.get('/api/intelligence/knowledge/invalid',headers=A).status_code==404
        c.post('/api/privacy/delete-all',headers=A)
        assert c.get('/api/intelligence/knowledge/mechanical',headers=A).json()['topics'][2]['attempts']==0

def test_knowledge_low_score_signals_are_only_provisional(tmp_path):
    app=create_app(tmp_path)
    app.state.store.create(sample_report(),owner_hash(A['X-Owner-Token']))
    with TestClient(app) as c:
        r=c.get('/api/intelligence/knowledge/mechanical',headers=A).json()
        assert r['assessment_signals'][0]['score']==2
        assert c.get('/api/intelligence/knowledge/mechanical',headers=B).json()['assessment_signals']==[]

def test_frontend_present_and_source_preserved():
    p=Path(__file__).resolve().parents[1]/'app/static'
    h=(p/'index.html').read_text()
    from bs4 import BeautifulSoup
    s=BeautifulSoup(h,'html.parser')
    ids=[i.get('id') for i in s.select('[id]')]
    assert len(ids)==len(set(ids))
    for view in ('live','match','whiteboard','score-evidence','knowledge'):
        assert s.select_one('#'+view)
        assert s.select_one(f'.nav[data-view="{view}"]')
    js=(p/'intelligence.js').read_text()
    assert 'innerHTML' not in js
    assert 'eval(' not in js
    assert '/static/intelligence.js' in h

class DiagramGroqFixture:
    model='openai/gpt-oss-120b'
    def configured(self):return True
    async def _post(self,path,**kwargs):
        assert path=='chat/completions'
        content=kwargs['json']['messages'][1]['content']
        # Only structured labels and links, never bitmap, are sent.
        assert 'nodes' in content and 'edges' in content
        return {'choices':[{'message':{'content':json.dumps({
            'observed_elements':['API and database components labeled'],
            'question':'How would you keep the API available if the database connection fails?',
            'feedback':'You described an API-to-database relationship; explain request retries and error handling.',
            'limitations':'Text labels alone do not prove the drawing is technically valid.'})}}]}

def test_whiteboard_groq_path_explicit_consent_and_model_provenance(tmp_path):
    body={'domain':'software','nodes':[{'id':'x','label':'API Server','x':100,'y':100}],
          'edges':[],'consent':True,'model':'openai/gpt-oss-120b'}
    with TestClient(create_app(tmp_path,provider=DiagramGroqFixture())) as c:
        r=c.post('/api/intelligence/whiteboard/ai',headers=A,json=body)
        assert r.status_code==200,r.text
        result=r.json()
        assert result['source']=='groq_ai_provisional'
        assert 'freehand pixels were not interpreted' in result['limitations'].lower()
        assert 'database connection fails' in result['question']
