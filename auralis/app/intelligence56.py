"""Auralis 5.6: explicit evidence boundaries, private diagram coaching and practice map.

No CV or diagram persisted; no automated verifier of skills, hiring suitability or claimed work.
"""
from __future__ import annotations
import json, re, secrets, sqlite3, time
from .database import connect as db_connect
from datetime import datetime, timezone
from pydantic import BaseModel, Field, ConfigDict, model_validator
from typing import Literal
from fastapi import HTTPException

class Strict(BaseModel):
    model_config=ConfigDict(extra='forbid',str_strip_whitespace=True)
class MatchRequest(Strict):
    cv:str=Field(min_length=40,max_length=24000)
    jd:str=Field(min_length=30,max_length=16000)
class Node(Strict):
    id:str=Field(pattern=r'^[a-zA-Z0-9_-]{1,24}$')
    label:str=Field(min_length=2,max_length=100)
    kind:Literal['process','decision','data','system','component']='component'
    x:float=Field(ge=0,le=2000)
    y:float=Field(ge=0,le=1200)
class Edge(Strict):
    source:str=Field(pattern=r'^[a-zA-Z0-9_-]{1,24}$')
    target:str=Field(pattern=r'^[a-zA-Z0-9_-]{1,24}$')
    label:str=Field(default='',max_length=90)
class WhiteboardRequest(Strict):
    domain:Literal['software','mechanical','electrical','general']='software'
    nodes:list[Node]=Field(min_length=1,max_length=32)
    edges:list[Edge]=Field(default_factory=list,max_length=64)
    @model_validator(mode='after')
    def validate_graph(self):
        ids=[n.id for n in self.nodes]
        if len(ids)!=len(set(ids)):raise ValueError('Diagram node identifiers must be unique.')
        for e in self.edges:
            if e.source not in ids or e.target not in ids or e.source==e.target:
                raise ValueError('Every connection must reference two different existing nodes.')
        return self
class WhiteboardAIRequest(WhiteboardRequest):
    consent:bool=False
    model:Literal['openai/gpt-oss-120b','openai/gpt-oss-20b']='openai/gpt-oss-120b'
class DiagramFeedback(Strict):
    observed_elements:list[str]=Field(min_length=1,max_length=6)
    question:str=Field(min_length=15,max_length=450)
    feedback:str=Field(min_length=20,max_length=850)
    limitations:str=Field(min_length=20,max_length=350)
class Dispute(Strict):
    competency_id:str=Field(min_length=1,max_length=80)
    reason:str=Field(min_length=12,max_length=1200)
class Practice(Strict):
    topic:str=Field(min_length=1,max_length=65)
    domain:Literal['software','mechanical','electrical','general']='software'
    outcome:Literal['needs_practice','understood']='needs_practice'

SKILLS={
 'software':[
  ('Variables and data structures',[], 'Explain the distinction between a list and a dictionary using an inventory example.'),
  ('Complexity analysis',[0],'Compare the complexity of linear search and binary search on sorted data.'),
  ('API contracts',[0],'Design a response and error contract for a booking API.'),
  ('Concurrency',[2],'Explain how two users booking the last available seat could cause a race condition.'),
  ('Validation and tests',[1,2],'Propose boundary tests for an endpoint that changes inventory.')],
 'mechanical':[
  ('Material properties',[],'Distinguish yield strength from Young\'s modulus for a steel enclosure.'),
  ('Load paths',[0],'Trace the 180 kg equipment weight from the brackets into a base frame.'),
  ('Panel buckling',[0,1],'Explain how a reinforcement affects a thin panel\'s buckling risk.'),
  ('Finite element analysis',[1,2],'Describe realistic constraints and a mesh convergence check.'),
  ('Prototype verification',[3],'Name two physical tests that could reveal a flawed static model.')],
 'electrical':[
  ('Electrical fundamentals',[],'Distinguish active, reactive and apparent power.'),
  ('Three-phase calculations',[0],'Compute current at a specified three-phase power, voltage and power factor.'),
  ('Fault analysis',[0,1],'Explain the assumptions needed before performing short-circuit analysis.'),
  ('Protection coordination',[2],'Compare two time-current curves and identify selective tripping risks.'),
  ('Validation and safety',[3],'State what would need to be checked before implementing a relay setting.')],
 'general':[
  ('Problem framing',[],'State the given constraints, unknowns and acceptance criterion.'),
  ('Evidence and assumptions',[0],'Separate a stated fact from an unverified assumption.'),
  ('Trade-off reasoning',[1],'Choose between two solutions and justify the compromise.'),
  ('Testing strategy',[2],'Design a test that could disprove your proposed solution.'),
  ('Communication',[3],'Explain your decision to someone outside your field.')]
}
DOMAIN_HINT={'software':'Consider APIs, data flow, failure modes and trust boundaries.',
 'mechanical':'Consider mechanical loads, fabrication tolerances and physical verification.',
 'electrical':'Consider protective bonding, load calculations, fault conditions and independent verification.',
 'general':'Consider assumptions, evidence and a falsifiable test.'}

def _sentences(text):
    parts=re.split(r'(?<=[.!?])\s+|\n+',text)
    return [p.strip(' -•\t')[:350] for p in parts if len(p.strip())>=12]

def _keywords(text):
    return set(re.findall(r'[a-z][a-z0-9+.#-]{2,}',text.lower()))

STOP=set('with from this that which have were will and the for are can would into using their years skills strong experience knowledge able required ability preferred role company position responsibilities provide through including projects based working software engineering engineer design technical quality relevant candidate'.split())
PHRASES={
 'software':['python','java','javascript','fastapi','react','sql','postgresql','database','api','docker','kubernetes','unit testing','system design','machine learning','git','redis'],
 'mechanical':['creo','solidworks','ansys','autocad','gd&t','sheet metal','welding','fea','tolerance','buckling','manufacturing','cad','thermal','fatigue'],
 'electrical':['etap','autocad electrical','iec','relay coordination','power factor','load flow','short circuit','arc flash','switchgear','protection','single line','electrical'],
 'general':['communication','leadership','teamwork','documentation','testing','analysis','project management','customer']}

def match_cv(payload:MatchRequest):
    cv,jd=payload.cv,payload.jd
    sentences=_sentences(cv)
    jd_sentences=_sentences(jd)
    vocab=[]
    for phrases in PHRASES.values():
        for phrase in phrases:
            if re.search(r'(?<![a-z0-9])'+re.escape(phrase)+r'(?![a-z0-9])',jd,re.I) and phrase not in vocab:
                vocab.append(phrase)
    # JD keywords from free form, limited and explicitly heuristic, not AI.
    if len(vocab)<3:
        ranked=[k for k in _keywords(jd)-STOP if len(k)>=5]
        vocab+=sorted(ranked,key=lambda k:(-sum(k in s.lower() for s in jd_sentences),k))[:5]
    results=[]
    for term in vocab[:16]:
        supporting=next((line for line in sentences if re.search(r'(?<![a-z0-9])'+re.escape(term)+r'(?![a-z0-9])',line,re.I)),None)
        requirement=next((line for line in jd_sentences if term in line.lower()),term)
        results.append({'requirement':term,'jd_excerpt':requirement[:260],'cv_excerpt':supporting[:260] if supporting else None,
                        'status':'mentioned_in_cv_unverified' if supporting else 'not_found_in_cv',
                        'verification':'This is a self-reported claim, not independently verified.' if supporting else 'Not found does not prove a skill is absent.'})
    return {'items':results,'matched':sum(bool(r['cv_excerpt']) for r in results),'total':len(results),
            'review_questions':[f'Your role requests {r["requirement"]}. What project or result demonstrates it?' for r in results if not r['cv_excerpt']][:5],
            'method':'Deterministic phrase matching, not a validated ATS score. No CV/JD data stored by this endpoint.',
            'limitations':'Mentioned is not verified; absent in a CV is not absent in a person. Do not use for automated hiring.'}

def whiteboard_observe(payload:WhiteboardRequest):
    names=[n.label for n in payload.nodes]
    disconnected=[n.label for n in payload.nodes if len(payload.nodes)>1 and not any(e.source==n.id or e.target==n.id for e in payload.edges)]
    observations=[f'{len(names)} labeled elements: '+', '.join(names[:5])]
    if payload.edges:observations.append(f'{len(payload.edges)} explicit connections')
    if disconnected:observations.append('No connection for: '+', '.join(disconnected[:4]))
    if len(names)==1:question=f'What components connect to {names[0]}, and how would you verify that relationship?'
    elif disconnected:question=f'How is {disconnected[0]} connected to the rest of the design, and which direction does information or load flow?'
    else:question=f'What happens if {names[0]} fails, and what observation would validate your diagram?'
    return {'observed_elements':observations,'question':question,
            'feedback':f'Your diagram has {len(names)} named elements and {len(payload.edges)} directed connection(s). '+DOMAIN_HINT[payload.domain]+(' Review isolated elements and missing links.' if disconnected else ' Explain each connection and its validation evidence.'),
            'limitations':'Only structured labeled nodes and edges were inspected. Freehand pixels, drawing correctness, circuit safety and physical feasibility were not checked.',
            'source':'deterministic_diagram_review'}

def evidence_bundle(session):
    report=session.get('report') or {}; turns={t.get('id'):t for t in session.get('turns',[]) if t.get('kind')=='answer'}
    rows=[]
    for item in report.get('items',[]):
        citations=[]
        for tid in item.get('evidence_ids',[])[:8]:
            t=turns.get(tid)
            if t and t.get('question',{}).get('competency_id')==item.get('competency_id'):
                answer=t.get('text','')
                citations.append({'turn_id':tid,'question':t.get('question',{}).get('text','')[:350],
                                  'answer_excerpt':answer[:700], 'has_more':len(answer)>700,
                                  'evidence_scope':'Source response excerpt, NOT proof the model reasoning is correct.'})
        rows.append({'competency_id':item.get('competency_id'),'name':item.get('name'),
                     'score':item.get('score'),'status':item.get('status'), 'feedback':item.get('feedback',''),
                     'score_gap':item.get('score_gap','') or item.get('next_score_gap','') or 'No defensible next-score explanation supplied.',
                     'criteria': next((c.get('criteria',[]) for c in session.get('plan',{}).get('competencies',[]) if c.get('id')==item.get('competency_id')),[]),
                     'citations':citations})
    return {'session_id':session['id'],'role':session.get('plan',{}).get('role','Unknown'),
            'items':rows,'provisional':report.get('provisional',True),
            'limitations':'Evidence is directly linked to saved answer turns. AI judgments and score-gap explanations remain provisional. Disputes are private notes, not automatic regrading.'}

def knowledge_map(domain, practice=None, signals=None):
    skills=SKILLS[domain];stats=practice or {}
    prompts=[]
    for i,(name,prereqs,question) in enumerate(skills):
        record=stats.get(f'{domain}-{i}',{});attempts=record.get('attempts',0)
        # Transfer scenarios are curated prompt changes, not guaranteed equivalent calibrated items.
        variants=[question,
                  f'Transfer scenario: use a different numerical or operational example to explain {name.lower()}. State assumptions and verify the result.',
                  f'Failure analysis: identify a plausible incorrect claim about {name.lower()}, correct it, and propose a test that could reveal the mistake.']
        prompts.append({'id':f'{domain}-{i}','name':name,'prerequisites':[f'{domain}-{j}' for j in prereqs],
                        'question':variants[attempts%len(variants)],'attempts':attempts,
                        'latest':record.get('latest','not_practiced')})
    return {'domain':domain,'topics':prompts,'assessment_signals':signals or [],
            'limitations':'Prerequisites and practice variants are curated study prompts, not calibrated equivalent assessments. Completion is self-reported, not demonstrated mastery. Low score signals are provisional model judgments.'}

def signals_from_sessions(sessions,domain):
    keys={'mechanical':('mechanical','buckling','structural','manufacturing','cad'),
          'software':('software','backend','python','coding','api','database'),
          'electrical':('electrical','power system','coordination','protection'),
          'general':('communication','behavioral','reasoning')}
    signals=[]
    for s in sessions[:50]:
        report=s.get('report') or {}
        if report.get('demo') or report.get('provisional') or s.get('setup',{}).get('provider')=='demo':continue
        for item in report.get('items',[]):
            score=item.get('score');name=item.get('name','')
            if isinstance(score,int) and score<=2 and any(k in name.lower() for k in keys[domain]):
                signals.append({'competency':name,'score':score,'note':'Provisional low score in a completed interview; review prerequisite topics and retest with new questions.'})
    # De-duplicate by competency; keep at most three signals, and avoid exposing answers.
    return list({s['competency']:s for s in signals}.values())[:3]


def init_tables(path):
    with db_connect(path,timeout=10) as db:
        db.execute('CREATE TABLE IF NOT EXISTS intelligence_disputes (id TEXT PRIMARY KEY, owner TEXT NOT NULL, session_id TEXT NOT NULL, competency TEXT NOT NULL, reason TEXT NOT NULL, created REAL NOT NULL)')
        db.execute('CREATE TABLE IF NOT EXISTS intelligence_practice (owner TEXT NOT NULL, topic TEXT NOT NULL, attempts INTEGER NOT NULL, latest TEXT NOT NULL, updated REAL NOT NULL, PRIMARY KEY(owner,topic))')

def save_dispute(path,owner,sid,payload:Dispute):
    did='dis_'+secrets.token_hex(12)
    with db_connect(path,timeout=10) as db:
        if db.execute('SELECT COUNT(*) FROM intelligence_disputes WHERE owner=?',(owner,)).fetchone()[0]>=75:
            raise HTTPException(409,'Limit of 75 saved disputes reached. Clear old notes first.')
        db.execute('INSERT INTO intelligence_disputes VALUES (?,?,?,?,?,?)',(did,owner,sid,payload.competency_id,payload.reason,time.time()))
    return {'id':did,'status':'recorded_for_your_review','message':'Private note saved. No human review or score adjustment is implied.'}

def list_disputes(path,owner,sid):
    with db_connect(path,timeout=10) as db:
        return [{'id':row[0],'competency_id':row[1],'reason':row[2],'created_at':row[3],'status':'recorded_for_your_review'} for row in db.execute('SELECT id,competency,reason,created FROM intelligence_disputes WHERE owner=? AND session_id=? ORDER BY created DESC',(owner,sid))]

def practice(path,owner,payload:Practice):
    valid={f'{payload.domain}-{i}' for i in range(len(SKILLS[payload.domain]))}
    if payload.topic not in valid:raise HTTPException(422,'Unknown topic for the requested domain.')
    with db_connect(path,timeout=10) as db:
        db.execute('INSERT INTO intelligence_practice VALUES (?,?,?,?,?) ON CONFLICT(owner,topic) DO UPDATE SET attempts=attempts+1,latest=excluded.latest,updated=excluded.updated',(owner,payload.topic,1,payload.outcome,time.time()))
    return knowledge_map(payload.domain,practice_stats(path,owner,payload.domain))

def practice_stats(path,owner,domain):
    with db_connect(path,timeout=10) as db:
        return {r[0]:{'attempts':r[1],'latest':r[2]} for r in db.execute('SELECT topic,attempts,latest FROM intelligence_practice WHERE owner=? AND topic LIKE ?', (owner,domain+'-%'))}

def remove_owner(path,owner):
    with db_connect(path,timeout=10) as db:
        db.execute('DELETE FROM intelligence_disputes WHERE owner=?',(owner,))
        db.execute('DELETE FROM intelligence_practice WHERE owner=?',(owner,))

def delete_session_notes(path,owner,sid):
    with db_connect(path,timeout=10) as db:db.execute('DELETE FROM intelligence_disputes WHERE owner=? AND session_id=?',(owner,sid))

def purge_expired(path,days):
    if days<=0:return
    with db_connect(path,timeout=10) as db:
        db.execute('DELETE FROM intelligence_disputes WHERE created<?',(time.time()-days*86400,))
        db.execute('DELETE FROM intelligence_practice WHERE updated<?',(time.time()-days*86400,))
