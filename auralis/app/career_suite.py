"""Auralis 5.5 offline campus, bilingual, question bank, college pilot and reliability drills.

Explicitly local-first: teacher/students sharing one machine may use different browser profiles.
No cloud authentication or real role identity is asserted. No student CV, transcript or
free-form college response is exposed to college owners.
"""
from __future__ import annotations
import hashlib, json, math, re, secrets, sqlite3, time
from .database import connect as db_connect
from datetime import datetime, timezone, timedelta
from difflib import SequenceMatcher
from pydantic import BaseModel, ConfigDict, Field
from typing import Literal
from fastapi import HTTPException

class Strict(BaseModel):model_config=ConfigDict(extra='forbid',str_strip_whitespace=True)
class PlacementCreate(Strict):role: str=Field(default='Software Engineer',min_length=3,max_length=100)
class PlacementAnswer(Strict):answer: str=Field(min_length=1,max_length=3200)
class CoachInput(Strict):text: str=Field(min_length=10,max_length=2500);language: Literal['en','hi','hinglish']='en';domain: Literal['general','software','mechanical','electrical']='general'
class ReviewCreate(Strict):question: str=Field(min_length=12,max_length=500);answer: str=Field(default='',max_length=2400);competency: str=Field(default='General reasoning',max_length=80)
class ReviewStatus(Strict):status:Literal['due','practiced']='practiced';answer: str=Field(default='',max_length=2400)
class CollegeCreate(Strict):name:str=Field(min_length=3,max_length=90)
class CollegeJoin(Strict):invite: str=Field(pattern=r'^[a-f0-9]{40}$');display_name:str=Field(min_length=2,max_length=60)
class CollegeAssignment(Strict):title:str=Field(min_length=5,max_length=120);type:Literal['coding','engineering','interview','aptitude']='interview';instructions:str=Field(min_length=12,max_length=700);target_role:str=Field(default='General',max_length=80)
class CollegeMark(Strict):completed:bool
class CollegeMentorNote(Strict):note:str=Field(min_length=5,max_length=400)

# Five successive stages, fixed published prompt bank to prevent invented question origin.
APTITUDE=[
 {'q':'A test has 40 questions and 75% were answered correctly. How many were correct?','options':['20','25','30','35'],'correct':2,'why':'0.75 × 40 = 30.'},
 {'q':'Complete the sequence: 2, 6, 12, 20, 30, ?','options':['36','40','42','44'],'correct':2,'why':'Differences are 4, 6, 8, 10, then 12.'},
 {'q':'An item costs ₹800 after a 20% discount. What was its original price?','options':['₹960','₹1,000','₹1,200','₹640'],'correct':1,'why':'800 / 0.8 = 1,000.'},
 {'q':'A team completes a task in 6 days with 4 equally productive people. How long with 8 people?','options':['2 days','3 days','4 days','12 days'],'correct':1,'why':'24 person-days / 8 people = 3 days, assuming linear productivity.'},
 {'q':'In the word ENGINEER, how many distinct vowels appear?','options':['1','2','3','4'],'correct':1,'why':'E and I are the distinct vowels.'},
]
STAGE=['aptitude','coding','group_discussion','technical','hr']
STAGE_DATA={
 'aptitude':{'name':'Aptitude screening','question':'Answer the multiple-choice aptitude question.','type':'objective'},
 'coding':{'name':'Coding / practical round','question':'Implement a function that reverses a string. Use def solve(text): return ... (the restricted Python expression evaluator checks the result).','type':'verified'},
 'group_discussion':{'name':'Group discussion practice','question':'Discuss: Should employers prioritize demonstrable skills over degrees? Give an opening position, respond to a different viewpoint, and summarize.','type':'self_review','panel_views':['Participant A: A degree gives useful foundational knowledge.','Participant B: Project work gives stronger evidence of applied skill.','Moderator: Build a balanced position and acknowledge the counterargument.']},
 'technical':{'name':'Technical interview','question':'Explain a difficult technical problem you solved. State the assumptions, steps taken, verification, and trade-offs.','type':'self_review'},
 'hr':{'name':'HR / behavioral interview','question':'Describe a time your plan failed. What did you change, how did you communicate, and what did you learn?','type':'self_review'}
}

def _utc():return datetime.now(timezone.utc).isoformat()
def _id(prefix):return prefix+secrets.token_hex(12)

def placement_public(p):
    stage=STAGE[min(len(p['answers']),4)] if len(p['answers'])<5 else None
    question=STAGE_DATA[stage].copy() if stage else None
    if stage=='aptitude':
        n=len(p.get('aptitude_answers',[]))
        question.update({'question':APTITUDE[n]['q'],'options':APTITUDE[n]['options'],'question_number':n+1,'question_total':len(APTITUDE)})
    return {'id':p['id'],'role':p['role'],'current_stage':stage,'round':len(p['answers'])+1 if stage else 5,
            'stages':[{'id':x,**STAGE_DATA[x],'status':'completed' if i<len(p['answers']) else ('current' if i==len(p['answers']) else 'locked')} for i,x in enumerate(STAGE)],
            'question':question,'results':p['answers'],'complete':stage is None,'aptitude_progress':len(p.get('aptitude_answers',[])),
            'limitations':'Scripted placement simulation. Only aptitude and restricted coding are automatically checked. GD, technical and HR responses are self-review, not objectively scored.'}

def placement_submit(p,answer):
    n=len(p['answers'])
    if n>=5:raise HTTPException(409,'Placement is already complete.')
    stage=STAGE[n]
    result={'stage':stage,'submitted_at':_utc(),'status':'recorded','scored':False}
    if stage=='aptitude':
        raw=answer.strip(); napt=len(p.get('aptitude_answers',[]));correct=APTITUDE[napt]['correct']
        try:choice=int(raw)
        except ValueError:raise HTTPException(422,'Choose a numbered aptitude option, 0 to 3.')
        if not 0<=choice<4:raise HTTPException(422,'Choose one of the four aptitude options, 0 to 3.')
        p.setdefault('aptitude_answers',[]).append({'correct':choice==correct,'feedback':APTITUDE[napt]['why']})
        if len(p['aptitude_answers'])<len(APTITUDE):return placement_public(p)
        result.update({'scored':True,'passed':sum(int(a['correct']) for a in p['aptitude_answers']),
                       'total':len(APTITUDE),'feedback':'Five deterministic aptitude questions checked. Answer explanations: '+' '.join(a['feedback'] for a in p['aptitude_answers'])})
    elif stage=='coding':
        from .practical_lab import CodingSubmission,evaluate_code
        response=evaluate_code(CodingSubmission(challenge_id='reverse_text',code=answer))
        result.update({'scored':True,'passed':response['passed'],'total':response['total'],'feedback':'Validated by restricted test cases; no arbitrary Python execution.'})
    else:result.update({'feedback':'Response recorded for private self-review. No AI or human evaluator assessed this response.'})
    p['answers'].append(result)
    return placement_public(p)

TERMS={
 'general':[('assumption','धारणा','Something taken as given, to be checked.'),('evidence','प्रमाण','Information supporting a conclusion.'),('trade-off','समझौता','Gaining one benefit while sacrificing another.')],
 'software':[('time complexity','समय जटिलता','How algorithmic work grows with input size.'),('test case','परीक्षण उदाहरण','Input and expected outcome used to check behavior.')],
 'mechanical':[('yield strength','प्रवाह सीमा','Stress where permanent deformation begins.'),('buckling','बकलिंग','Instability under compression.')],
 'electrical':[('power factor','शक्ति गुणांक','Real power divided by apparent power.'),('load flow','लोड फ्लो','Calculation of network voltages and power flows.')]
}
HINDI_HINT='उत्तर में समस्या, आपके कदम, परिणाम और जाँच को स्पष्ट रूप से बताइए।'
MIX_HINT='Problem ko define kijiye, steps batayiye, result aur verification explain kijiye.'

def coach(payload:CoachInput):
    text=payload.text.strip();tokens=re.findall(r"[\w\u0900-\u097F]+",text.lower())
    matches=[]
    for en,hi,meaning in TERMS['general']+TERMS.get(payload.domain,[]):
        if en in text.lower() or hi in text:matches.append({'english':en,'hindi':hi,'explanation':meaning})
    filler=[w for w in ('um','uh','basically','actually','matlab') if re.search(r'\b'+re.escape(w)+r'\b',text.lower())]
    has_number=bool(re.search(r'\b\d+(?:\.\d+)?\b',text))
    suggestion=('State the situation, explain your own action, describe the outcome, then say how you verified it.' if payload.language=='en' else HINDI_HINT if payload.language=='hi' else MIX_HINT)
    translations=[
      {'english':'I checked the assumptions.','hindi':'मैंने मान्यताओं की जाँच की।','hinglish':'Maine assumptions verify kiye.'},
      {'english':'I tested the result with another example.','hindi':'मैंने परिणाम को एक अन्य उदाहरण से जाँचा।','hinglish':'Maine result ko doosre example se test kiya.'},
      {'english':'I would explain the trade-off before deciding.','hindi':'निर्णय से पहले मैं लाभ और सीमाएँ समझाऊँगा।','hinglish':'Decision se pehle main trade-offs explain karunga.'},
    ]
    return {'language':payload.language,'domain':payload.domain,'observed_words':len(tokens),'matched_terms':matches,'phrase_examples':translations,
            'filler_terms':filler,'mentions_quantity':has_number,'structure_hint':suggestion,
            'terminology_tip':'Keep technical terms precise. It is acceptable to use English terminology within Hindi answers.',
            'limitations':'Local terminology and curated phrase translation examples only. No free-text translation or assessment of accent, identity, fluency or employability. Original answer is not saved.'}

# A 1,3,7,14,30 day spaced-practice sequence; new prompts rotate by cue, not LLM.
VARIANTS=[
 'Explain the underlying principle using a different example and one counterexample.',
 'Solve a related scenario with changed assumptions. Show how you would verify the result.',
 'Teach the concept to a beginner, then point out a common mistake.',
 'Apply the same concept to a new case without using your original answer.',
 'Write a compact explanation with conditions under which your approach would fail.'
]
GAPS=(1,3,7,14,30)

def new_review(data:ReviewCreate):
    return {'id':_id('rev_'),'question':data.question,'competency':data.competency,'created_at':_utc(),
            'next_due':_utc(),'attempts':0,'status':'due','variant':VARIANTS[0],
            'source':'candidate_marked_for_review','note':'Self-selected mistake, not a verified AI finding.'}

def practice_review(item):
    attempt=item['attempts']+1;days=GAPS[min(attempt-1,len(GAPS)-1)]
    item.update({'attempts':attempt,'status':'scheduled','last_practiced':_utc(),
                 'next_due':(datetime.now(timezone.utc)+timedelta(days=days)).isoformat(),
                 'variant':VARIANTS[attempt%len(VARIANTS)]})
    return item

def normalize_question(q):
    words=re.findall(r'\w+',q.lower())
    stop={'the','a','an','how','what','why','would','you','to','of','in','and','for','explain','describe','could','please','with','your'}
    return ' '.join(x for x in words if x not in stop)

def repeated_questions(questions):
    out=[]
    for i in range(len(questions)):
        for j in range(i):
            a,b=normalize_question(questions[i]),normalize_question(questions[j])
            if not a or not b:continue
            ratio=SequenceMatcher(None,a,b).ratio()
            ta,tb=set(a.split()),set(b.split())
            overlap=len(ta&tb)/max(1,len(ta|tb))
            if ratio>=.78 or overlap>=.72:out.append({'first':j+1,'second':i+1,'similarity':round(max(ratio,overlap),2),'issue':'Possible near-duplicate question'})
    return out[:20]

FIXTURES=[
 {'id':'wrong_strength','category':'contradictory_reasoning','input':'Youngs modulus is identical to yield strength.','expected':'incorrect'},
 {'id':'valid_current','category':'numeric_consistency','input':'5 MW at 415V PF .9 ≈ 7730 A.','expected':'approximately_7730_A'},
 {'id':'repeat_question','category':'question_repetition','input':'Explain sheet bending stiffness / Describe sheet bending stiffness','expected':'duplicate_warning'},
 {'id':'unverified_experience','category':'unsupported_claim','input':'My fictional role has 10 years experience','expected':'unverified_claim'},
 {'id':'conflicting_scores','category':'score_consistency','input':'status not assessed but score 4','expected':'contradiction_warning'}
]

def _status_score_inconsistent(item):
    return (item.get('status') in ('not_assessed','insufficient_evidence','not_scored_provider_unavailable')
            and item.get('score') is not None)

def _unverified_experience_claim(feedback):
    return any(phrase in str(feedback).lower() for phrase in
               ('verified professional experience','confirmed prior employment','proven years of experience','real-world project experience'))

def reliability_fixture():
    current=5_000_000/(math.sqrt(3)*415*.9)
    checks=[
      {'id':'wrong_strength','passed':bool(re.search(r'young.?s modulus.*yield strength', FIXTURES[0]['input'].lower())),
       'details':'Fixture encodes the known false equivalence between stiffness and strength; human technical review still needed.'},
      {'id':'valid_current','passed':abs(current-7730)<10,
       'details':f'Independent numeric reference: {current:.1f} A at 415 V, 0.9 PF.'},
      {'id':'repeat_question','passed':bool(repeated_questions(['Explain sheet bending stiffness','Describe sheet bending stiffness'])),
       'details':'Similarity test flags a near-duplicate question.'},
      {'id':'unverified_experience','passed':_unverified_experience_claim('This is verified professional experience'),
       'details':'Fixture demonstrates an unsupported-experience claim phrase that should be flagged.'},
      {'id':'conflicting_scores','passed':_status_score_inconsistent({'status':'not_assessed','score':4}),
       'details':'An unassessed status with a numeric score is inconsistent.'}
    ]
    return {'fixtures':checks,'passed':sum(x['passed'] for x in checks),'total':len(checks),
            'limitations':'Limited deterministic diagnostics, not a statistical accuracy benchmark. No live Groq requests and no certification of an AI assessment.'}

def reliability_session(session):
    questions=[t.get('question',{}).get('text','') for t in session.get('turns',[]) if t.get('kind')=='answer']
    items=session.get('report',{}).get('items',[]) if isinstance(session.get('report'),dict) else []
    issues=[]
    for d in repeated_questions(questions):issues.append({'category':'question_repetition','severity':'review','detail':f"Answers {d['first']} and {d['second']} followed near-duplicate prompts; similarity {d['similarity']}."})
    for i,item in enumerate(items):
        score=item.get('score');status=item.get('status','')
        if _status_score_inconsistent(item):
            issues.append({'category':'score_consistency','severity':'warning','detail':f'Rubric item {i+1} has {status} but numeric score {score}.'})
        if score is not None and not item.get('evidence_ids'):
            issues.append({'category':'evidence_provenance','severity':'review','detail':f'Rubric item {i+1} has a score without evidence IDs.'})
    if any(_unverified_experience_claim(item.get('feedback','')) for item in items):
        issues.append({'category':'unsupported_claim','severity':'review','detail':'Feedback appears to assert verified career experience that this practice tool cannot establish.'})
    if session.get('setup',{}).get('synthetic_data'):
        issues.append({'category':'synthetic_data','severity':'info','detail':'CV/project experience in this session was provided as fictional data; do not treat it as verified.'})
    return {'session_id':session['id'],'questions_reviewed':len(questions),'rubric_items_reviewed':len(items),'issues':issues[:40],
            'limitations':'Heuristic audit only. Cannot prove the absence of hallucinations or verify the engineering correctness of arbitrary answers.'}

# College pilot persists only metadata, brief assignments, pseudonyms, and completion flags.
# Never gives institute owners access to sessions, transcripts, CVs or personal learner history.
def init_tables(path):
    with db_connect(path,timeout=10) as db:
        db.execute('CREATE TABLE IF NOT EXISTS college_cohorts (id TEXT PRIMARY KEY, owner TEXT NOT NULL, name TEXT NOT NULL, invite_hash TEXT NOT NULL UNIQUE, created REAL NOT NULL)')
        db.execute('CREATE TABLE IF NOT EXISTS college_members (cohort_id TEXT NOT NULL, owner TEXT NOT NULL, display_name TEXT NOT NULL, joined REAL NOT NULL, PRIMARY KEY(cohort_id,owner))')
        db.execute("CREATE TABLE IF NOT EXISTS college_assignments (id TEXT PRIMARY KEY, cohort_id TEXT NOT NULL, title TEXT NOT NULL, kind TEXT NOT NULL, instructions TEXT NOT NULL, created REAL NOT NULL, target_role TEXT NOT NULL DEFAULT 'General', mentor_note TEXT NOT NULL DEFAULT '')")
        cols={r[1] for r in db.execute('PRAGMA table_info(college_assignments)')}
        if 'target_role' not in cols:db.execute("ALTER TABLE college_assignments ADD COLUMN target_role TEXT NOT NULL DEFAULT 'General'")
        if 'mentor_note' not in cols:db.execute("ALTER TABLE college_assignments ADD COLUMN mentor_note TEXT NOT NULL DEFAULT ''")
        db.execute('CREATE TABLE IF NOT EXISTS college_completions (assignment_id TEXT NOT NULL, student TEXT NOT NULL, completed INTEGER NOT NULL, PRIMARY KEY(assignment_id,student))')
        db.execute('CREATE TABLE IF NOT EXISTS placement_simulations (id TEXT PRIMARY KEY, owner TEXT NOT NULL, payload TEXT NOT NULL, created REAL NOT NULL)')
        db.execute('CREATE TABLE IF NOT EXISTS review_cards (id TEXT PRIMARY KEY, owner TEXT NOT NULL, payload TEXT NOT NULL, created REAL NOT NULL)')

def db_read(path,sql,params=()):
    with db_connect(path,timeout=10) as db:
        db.row_factory=sqlite3.Row
        return [dict(row) for row in db.execute(sql,params).fetchall()]
def db_exec(path,sql,params=()):
    with db_connect(path,timeout=10) as db:return db.execute(sql,params).rowcount

def create_college(path,owner,name):
    existing=db_read(path,'SELECT id FROM college_cohorts WHERE owner=?',(owner,))
    if len(existing)>=3:raise HTTPException(409,'This local workspace already has the maximum of three cohorts.')
    code=secrets.token_hex(20)
    cid=_id('col_');db_exec(path,'INSERT INTO college_cohorts VALUES (?,?,?,?,?)',(cid,owner,name,hashlib.sha256(code.encode()).hexdigest(),time.time()))
    return {'id':cid,'name':name,'invite':code,'limitations':'LOCAL PILOT: invite code is a bearer secret. No verified college accounts or production authentication.'}

def join_college(path,owner,payload):
    digest=hashlib.sha256(payload.invite.encode()).hexdigest()
    row=db_read(path,'SELECT id,name FROM college_cohorts WHERE invite_hash=?',(digest,))
    if not row:raise HTTPException(404,'Invite not found.')
    c=row[0]
    institute=db_read(path,'SELECT owner FROM college_cohorts WHERE id=?',(c['id'],))[0]
    if institute['owner']==owner:raise HTTPException(409,'Open a different browser profile to join as a learner.')
    enrolled=db_read(path,'SELECT COUNT(*) AS n FROM college_members WHERE cohort_id=?',(c['id'],))[0]['n']
    if enrolled>=60:raise HTTPException(409,'Local college pilot cohort is full.')
    db_exec(path,'INSERT OR REPLACE INTO college_members VALUES (?,?,?,?)',(c['id'],owner,payload.display_name,time.time()))
    return {'joined':True,'cohort':c,'privacy':'Instructor sees only cohort totals and pseudonym membership, never CVs, transcripts, or interview answers.'}

def add_assignment(path,owner,cid,payload):
    if not db_read(path,'SELECT id FROM college_cohorts WHERE id=? AND owner=?',(cid,owner)):raise HTTPException(404,'Cohort not found.')
    if len(db_read(path,'SELECT id FROM college_assignments WHERE cohort_id=?',(cid,)))>=30:raise HTTPException(409,'Maximum 30 assignments per cohort.')
    aid=_id('asg_');db_exec(path,'INSERT INTO college_assignments (id,cohort_id,title,kind,instructions,created,target_role) VALUES (?,?,?,?,?,?,?)',(aid,cid,payload.title,payload.type,payload.instructions,time.time(),payload.target_role))
    return {'id':aid,'title':payload.title,'type':payload.type,'instructions':payload.instructions,'target_role':payload.target_role}

def college_view(path,owner):
    managed=db_read(path,'SELECT id,name,created FROM college_cohorts WHERE owner=? ORDER BY created DESC',(owner,))
    memberships=db_read(path,'SELECT m.cohort_id,c.name,m.display_name FROM college_members m JOIN college_cohorts c ON c.id=m.cohort_id WHERE m.owner=?',(owner,))
    for c in managed:
        c['students']=db_read(path,'SELECT COUNT(*) AS n FROM college_members WHERE cohort_id=?',(c['id'],))[0]['n']
        c['assignments']=db_read(path,'SELECT a.id,a.title,a.kind AS type,a.instructions,a.target_role,a.mentor_note,COUNT(CASE WHEN p.completed=1 THEN 1 END) AS completed FROM college_assignments a LEFT JOIN college_completions p ON p.assignment_id=a.id WHERE a.cohort_id=? GROUP BY a.id ORDER BY a.created DESC',(c['id'],))
    for m in memberships:
        m['assignments']=db_read(path,'SELECT a.id,a.title,a.kind AS type,a.instructions,a.target_role,a.mentor_note,COALESCE(p.completed,0) AS completed FROM college_assignments a LEFT JOIN college_completions p ON p.assignment_id=a.id AND p.student=? WHERE a.cohort_id=? ORDER BY a.created DESC',(owner,m['cohort_id']))
    return {'managed':managed,'joined':memberships,'limitations':'Local demonstration only. Assignment completion is self-reported, not an exam result. Teacher views are aggregate. No public hosting or verified college identity.'}

def mentor_college(path,owner,aid,note):
    allowed=db_read(path,'SELECT a.id FROM college_assignments a JOIN college_cohorts c ON c.id=a.cohort_id WHERE a.id=? AND c.owner=?',(aid,owner))
    if not allowed:raise HTTPException(404,'Assignment not found in your cohort.')
    db_exec(path,'UPDATE college_assignments SET mentor_note=? WHERE id=?',(note,aid))
    return {'saved':True,'scope':'all_students_in_cohort','student_responses_visible':False}

def mark_college(path,owner,aid,completed):
    member=db_read(path,'SELECT 1 FROM college_assignments a JOIN college_members m ON m.cohort_id=a.cohort_id WHERE a.id=? AND m.owner=?',(aid,owner))
    if not member:raise HTTPException(404,'Assignment not found in your enrolled cohort.')
    db_exec(path,'INSERT OR REPLACE INTO college_completions VALUES (?,?,?)',(aid,owner,int(completed)))
    return {'recorded':True,'completed':completed,'graded':False}

def remove_my_data(path,owner):
    own=db_read(path,'SELECT id FROM college_cohorts WHERE owner=?',(owner,));ids=[r['id'] for r in own]
    with db_connect(path,timeout=10) as db:
        db.execute('DELETE FROM placement_simulations WHERE owner=?',(owner,))
        db.execute('DELETE FROM review_cards WHERE owner=?',(owner,))
        db.execute('DELETE FROM college_completions WHERE student=?',(owner,))
        db.execute('DELETE FROM college_members WHERE owner=?',(owner,))
        for cid in ids:
            db.execute('DELETE FROM college_completions WHERE assignment_id IN (SELECT id FROM college_assignments WHERE cohort_id=?)',(cid,))
            db.execute('DELETE FROM college_assignments WHERE cohort_id=?',(cid,))
            db.execute('DELETE FROM college_members WHERE cohort_id=?',(cid,))
            db.execute('DELETE FROM college_cohorts WHERE id=?',(cid,))


def purge_expired(path,days):
    """Respect the same explicit local-retention setting as existing session storage."""
    if days<=0:return
    cutoff=time.time()-days*86400
    with db_connect(path,timeout=10) as db:
        db.execute('DELETE FROM placement_simulations WHERE created<?',(cutoff,))
        db.execute('DELETE FROM review_cards WHERE created<?',(cutoff,))
        ids=[row[0] for row in db.execute('SELECT id FROM college_cohorts WHERE created<?',(cutoff,)).fetchall()]
        for cid in ids:
            db.execute('DELETE FROM college_completions WHERE assignment_id IN (SELECT id FROM college_assignments WHERE cohort_id=?)',(cid,))
            db.execute('DELETE FROM college_assignments WHERE cohort_id=?',(cid,))
            db.execute('DELETE FROM college_members WHERE cohort_id=?',(cid,))
            db.execute('DELETE FROM college_cohorts WHERE id=?',(cid,))
