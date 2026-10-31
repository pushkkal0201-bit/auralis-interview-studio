from playwright.sync_api import sync_playwright
import os
from pathlib import Path
import fitz

root=Path(__file__).resolve().parents[1]
output=root/'_print_qa_output'
output.mkdir(exist_ok=True)
longtext=('**Step 1: Verify the model**\nThe representative ANSYS setup includes a 2 mm wall, structural load path, and 180 kg of equipment.\n\n'
          'I would examine von Mises stress, deformation, mesh convergence, and possible corner singularities.\n'
          '- Test the brackets\n- Compare reaction force to approximately 1766 N\n- Verify prototype dimensions and safety bonds.\n\n')*5
turns=[]
items=[]
for j in range(12):
    qid=f'q_{j+1}'
    turns.append({'id':f'turn_{j+1}','kind':'answer','created_at':1793412000+j*60,'text':longtext,'question':{
        'id':qid,'text':f'Question {j+1}: Explain an engineering process and what evidence would validate it.',
        'competency_id':f'c{j%4+1}','why':f'Coverage controller selected competency c{j%4+1} for this specific question, based on test criteria.',
        'difficulty_reason':'Applied practice; difficulty is model-generated.','source':'live_ai','xray':{'decision':'PROBE'}}})
for i in range(4):
    cid=f'c{i+1}'
    items.append({'competency_id':cid,'name':['Mechanical Fundamentals','CAD and GD&T','Manufacturing and Materials','Structural Analysis'][i],
                  'score':3,'status':'demonstrated','confidence':'medium','feedback':'Demonstrates an appropriate engineering method and identifies testable assumptions.',
                  'score_gap':'The answer did not include an independently executed experiment or completed verified calculation.',
                  'practice':'Complete a real measured example and compare model results.',
                  'initial_score':0 if i==0 else 3,'latest_score':3,'improvement_note':'Later reasoning was more sound.',
                  'evidence':[{'turn_id':f'turn_{i+1}','quote':'**Step 1: Verify the model**\nEngineering answer with evidence examples.'}]})
fixture={'id':'session_fake','setup':{'provider':'groq','ai_model':'openai/gpt-oss-120b'},'plan':{'role':'Mechanical Design Engineer',
         'competencies':[{'id':f'c{i+1}','name':items[i]['name']} for i in range(4)]},'turns':turns,
         'report':{'demo':False,'provisional':False,'summary':'The candidate initially made errors but later corrected them across several technical competencies.',
                   'ai_provider':'groq','ai_model':'openai/gpt-oss-120b','evidence_policy':'Evidence sampled for long answers.',
                   'coverage':{'covered_count':4,'total_count':4,'coverage_percent':100,'unassessed_ids':[]},
                   'claim_provenance':{'status':'synthetic_test_data','label':'Fictional or synthetic test data. No real employment verified.'},
                   'fallback_events':[{'stage':'question','competency_id':'c3','reason':'Provider unavailable, local rubric used.','error_code':'rate_limited','attempt_count':1}],
                   'items':items,'limitations':['This is practice, not an externally validated certification.']}}
with sync_playwright() as p:
    chromium_path=os.getenv('AURALIS_CHROMIUM_PATH')
    browser=p.chromium.launch(headless=True,executable_path=chromium_path or None,args=['--no-sandbox'])
    page=browser.new_page(viewport={'width':1300,'height':900})
    page.goto(os.getenv('APP_URL','http://127.0.0.1:8765'),wait_until='networkidle')
    page.evaluate('(fixture)=>{session=fixture;renderReport();show("report");}',fixture)
    assert page.locator('#report-content').count()==1
    assert 'fictional' in page.locator('.claim-provenance').inner_text().lower()
    assert page.locator('.replay-xray').count()==12
    assert page.locator('.score-gap').count()==4
    page.screenshot(path=str(output/'report_web_preview.png'),full_page=True)
    page.evaluate("document.body.classList.add('print-compact')")
    compact=output/'compact_print_smoke.pdf'
    page.pdf(path=str(compact),format='A4',print_background=True)
    page.evaluate("document.body.classList.remove('print-compact');document.body.classList.add('print-full');document.querySelector('#full-replay').open=true")
    full=output/'full_replay_print_smoke.pdf'
    page.pdf(path=str(full),format='A4',print_background=True)
    browser.close()
for name in ['compact_print_smoke.pdf','full_replay_print_smoke.pdf']:
    pdf=fitz.open(output/name)
    txt='\n'.join(p.get_text() for p in pdf)
    print(name,len(pdf),'pages',len(txt),'text chars', 'X-RAY' in txt, 'raw markdown **' in txt)
    assert len(pdf)<28
    assert 'candidate' in txt.lower() or 'engineer' in txt.lower()
    if name.startswith('full'):
        assert 'INTERVIEW X-RAY' in txt
        assert 'Question 12:' in txt
    else:
        assert 'To reach the next rubric level' in txt
        assert 'Fictional or synthetic' in txt
