'use strict';
const $=id=>document.getElementById(id);
const el=(tag,text,cls)=>{const n=document.createElement(tag);if(text!==undefined)n.textContent=text;if(cls)n.className=cls;return n;};
let owner=localStorage.getItem('auralis-owner');
if(!owner){owner=Array.from(crypto.getRandomValues(new Uint8Array(32)),v=>v.toString(16).padStart(2,'0')).join('');localStorage.setItem('auralis-owner',owner);}
let session=null,working=false,recorder=null,stream=null,recognition=null,recordTarget='answer',recordTimer=null,pending=null,voices=[],currentView='setup',captureEpoch=0;
let codeproof=null,incidents=[],incidentEvidence='';
let voiceCaptureStart=0, voiceEvidence=null, voiceSource=null, voiceEligible=false;
const OPEN_MODEL_CHOICES = {
  groq: [
    ['openai/gpt-oss-120b','GPT-OSS 120B · Groq · advanced'],
    ['openai/gpt-oss-20b','GPT-OSS 20B · Groq · fast'],
    ['qwen/qwen3.8-27b','Qwen 3.8 27B · Groq']
  ],
  huggingface: [
    ['openai/gpt-oss-120b:fireworks-ai','GPT-OSS 120B · Hugging Face · structured'],
    ['openai/gpt-oss-20b:groq','GPT-OSS 20B · Hugging Face · routed']
  ]
};
function syncModelSelector(preferred){
 const provider=$('provider').value;
 const previous=preferred||$('ai-model').value;
 const choices=OPEN_MODEL_CHOICES[provider]||OPEN_MODEL_CHOICES.groq;
 $('ai-model').replaceChildren(...choices.map(([id,title])=>{const o=el('option',title);o.value=id;return o;}));
 $('ai-model').value=choices.some(c=>c[0]===previous)?previous:choices[0][0];
 $('model-choice').hidden=provider==='demo';
 $('provider-note').textContent=provider==='demo'?'Guided example uses prepared questions. It does not produce scored assessments.':
  provider==='groq'?'Uses Groq for questions and feedback. Voice recording is sent to Groq for transcription.':
  'Uses Hugging Face for questions and feedback. Dictation may use your browser’s speech provider.';
}

const sampleCV='Alex Morgan\nB.Tech Computer Science student. Built a booking API using Python, FastAPI and SQLite. Implemented booking validation, wrote unit tests, and worked with a team of three. Practised SQL, API design and debugging. Seeking a junior backend developer role.';
const sampleJD='Junior backend developer. Build Python REST APIs, design SQL schemas, handle concurrent booking requests and retries, write automated tests, and explain technical trade-offs. Work with product and QA teams. Familiarity with FastAPI is preferred.';
function notify(text,error=true){$('notice').hidden=!text;$('notice').textContent=text||'';if(error&&text)$('notice').scrollIntoView({behavior:matchMedia('(prefers-reduced-motion: reduce)').matches?'instant':'smooth',block:'nearest'});}
function setBusy(value){working=value;$('busy').hidden=!value;document.querySelectorAll('button').forEach(b=>b.disabled=value);if(!value)updateTimer();}
async function api(path,options={}){const headers={...authHeader(),...options.headers};if(options.body&&!(options.body instanceof FormData)){headers['Content-Type']='application/json';options.body=JSON.stringify(options.body);}let r;try{r=await fetch(path,{...options,headers});}catch{throw Error('Auralis could not connect. Check that the application is running, then try again.');}if(r.status===401&&window.auralisAuth?.enabled&&await window.auralisAuth.refresh()){
  r=await fetch(path,{...options,headers:{...headers,...authHeader()}});
 }let data;try{data=await r.json();}catch{throw Error('Something went wrong while loading this result. Please try again.');}if(!r.ok){let detail=data.detail;if(Array.isArray(detail))detail=detail.map(e=>e.msg).join('\n');throw Error(typeof detail==='string'&&!/traceback|exception|api[_ -]?key|token|uvicorn|sqlite|\/app\//i.test(detail)?detail:'We could not complete that request. Please try again.');}return data;}
async function run(fn){if(working)return;notify('');setBusy(true);try{await fn();}catch(e){notify(e.message);
 if(window.auralisAuth?.enabled&&session?.id&&/answer was saved/i.test(e.message)){
  try{keep(await api('/api/sessions/'+session.id));renderArena();show('arena');}catch{}
 }
}finally{setBusy(false);}}
function show(view){if(currentView!==view){stopCapture(true);speechSynthesis.cancel();}currentView=view;const activeLabel=document.querySelector(`.nav[data-view="${view}"] span:last-child`);if(activeLabel&&$('view-label'))$('view-label').textContent=activeLabel.textContent;document.querySelectorAll('.view').forEach(n=>n.hidden=n.id!==view);document.querySelectorAll('.nav').forEach(n=>n.classList.toggle('active',n.dataset.view===view));const activeSection=document.querySelector(`.nav[data-view="${view}"]`)?.closest('details.nav-collection');if(activeSection)activeSection.open=true;window.scrollTo({top:0,behavior:matchMedia('(prefers-reduced-motion: reduce)').matches?'instant':'smooth'});if(view==='history')run(async()=>{await loadHistory();await loadLearningProgress();});}
function setupData(){return {cv:$('cv').value.trim(),jd:$('jd').value.trim(),role:$('role').value.trim(),provider:$('provider').value,ai_model:$('ai-model').value,mode:$('mode').value,language:$('language').value,duration_minutes:Number($('duration').value),consent:$('consent').checked,synthetic_data:$('synthetic-data').checked,project_evidence:[$('evidence').value.trim(),codeproof?.evidence_text||'',incidentEvidence].filter(Boolean).join('\n\n').slice(0,12000),codeproof_refs:[],codeproof_handle:codeproof?.evidence_handle||'',incident_id:$('incident-select').value||'',interview_track:$('interview-track').value,interviewer_persona:$('interviewer-persona').value,question_time_limit_seconds:Number($('question-limit').value),adaptive_difficulty:$('adaptive-difficulty').checked};}
function keep(s){
 const changed=session?.id!==s.id;
 if(changed||session?.current?.id!==s.current?.id||session?.retry?.id!==s.retry?.id)stopCapture(true);
 session=s;localStorage.setItem('auralis-current',s.id);
 if(changed){pending=null;$('answer').value='';$('retry-answer').value='';$('interviewer-reply').hidden=true;renderArena();renderReport();}
 return s;
}
function skillNode(c){const n=el('div',undefined,'skill');n.append(el('h3',c.name),el('p',c.requirement));const ul=el('ul');c.criteria.forEach(x=>ul.append(el('li',x)));n.append(ul);return n;}
function renderCodeProof(result){
  codeproof=result;const box=$('codeproof-results');box.replaceChildren();
  const title=el('h3',`Project review · ${result.source_files_scanned} Python files inspected`);box.append(title);
  box.append(el('p','Static code observations only; Auralis cannot establish authorship, actual behavior or exploitability.','hint'));
  (result.refs||[]).slice(0,8).forEach(r=>{const d=el('details',undefined,'code-ref');d.append(el('summary',`${r.id} · ${r.path}:${r.line_start} · ${r.symbol}`));d.append(el('pre',r.snippet,'code-lines'));d.append(el('p',(r.indicators||[]).join(' · ')||'Function / class','hint'));box.append(d);});
  if(result.parse_errors?.length)box.append(el('p',`Some files could not be parsed: ${result.parse_errors.join(', ')}`,'hint'));
}
async function loadIncidents(){try{const res=await api('/api/incidents');incidents=res.incidents||[];const sel=$('incident-select');incidents.forEach(i=>{const opt=el('option',`${i.name} · ${i.domain}`);opt.value=i.id;sel.append(opt);});}catch(e){notify('Incident scenarios unavailable: '+e.message);}}
function chooseIncident(){const i=incidents.find(x=>x.id===$('incident-select').value);const container=$('incident-preview');container.replaceChildren();container.hidden=!i;incidentEvidence='';if(!i)return;
 container.append(el('h3',`${i.severity} · ${i.summary}`));const pre=el('pre',i.logs.join('\n'),'code-lines');container.append(pre,el('p',i.prompt,'hint'));
 incidentEvidence=`SYNTHETIC INCIDENT EXERCISE (not live telemetry). ${i.name}. ${i.summary}. Facts: ${i.facts.join(' ')} Logs: ${i.logs.join(' | ')} Candidate exercise: ${i.prompt}`;
}
function renderPlan(){if(!session)return;$('plan-preview').hidden=false;$('plan-title').textContent=session.plan.role;$('plan-summary').textContent=(session.plan_source==='local_rubric_fallback'?'A prepared interview outline is shown because live questions are unavailable.\n':'')+session.plan.summary;$('plan-skills').replaceChildren(...session.plan.competencies.map(skillNode));const d=$('plan-detail');d.replaceChildren(el('h3',session.plan.scenario.title),el('p',session.plan.scenario.situation));session.plan.claims.forEach(c=>d.append(el('p','CV claim: '+c.quote),el('p','Probe: '+c.probe)));$('start').hidden=session.status!=='ready';}
function speak(text){if(!('speechSynthesis'in window)){notify('Speech playback is unavailable in this browser.');return;}speechSynthesis.cancel();const u=new SpeechSynthesisUtterance(text);u.lang=(session?.setup.language||$('language').value)==='hi'?'hi-IN':'en-IN';const v=voices.find(v=>v.name===$('voice').value);if(v)u.voice=v;u.rate=.95;u.onerror=e=>{if(!['interrupted','canceled'].includes(e.error))notify('Voice playback failed. Choose another voice or use the question text.');};speechSynthesis.speak(u);}
function populateVoices(){if(!('speechSynthesis'in window))return;voices=speechSynthesis.getVoices();const prev=$('voice').value;$('voice').replaceChildren(el('option','System default'));$('voice').firstChild.value='';voices.forEach(v=>{const o=el('option',`${v.name} (${v.lang})`);o.value=v.name;$('voice').append(o);});if(voices.some(v=>v.name===prev))$('voice').value=prev;else{const preferred=voices.find(v=>/female|zira|samantha|aria|jenny|sonia|hazel|heera|neerja|susan|ava/i.test(v.name)&&/^en/i.test(v.lang));if(preferred)$('voice').value=preferred.name;}}
function renderArena(){
 if(session?.status==='paused_provider'){
  $('arena-empty').hidden=false;
  $('arena-body').hidden=true;
  $('arena-empty').replaceChildren(el('h2','Your answer is saved.'),el('p','The live interviewer is temporarily unavailable. Retry question generation when the connection is restored.'));
  const retry=el('button','Resume interview','primary');retry.onclick=()=>run(async()=>{keep(await api('/api/sessions/'+session.id+'/start',{method:'POST',body:{}}));renderArena();});
  $('arena-empty').append(retry);
  return;
 }
const s=session;$('arena-empty').hidden=!!s?.current;$('arena-body').hidden=!s?.current;if(!s?.current)return;$('session-role').textContent=s.plan.role;$('interviewer-name').textContent=(s.setup.interviewer_persona||'supportive').replaceAll('_',' ').replace(/(^|\s)\S/g,x=>x.toUpperCase())+' · Auralis';$('room-persona').textContent=`${(s.setup.interviewer_persona||'supportive').replaceAll('_',' ').toUpperCase()}  /  ${(s.setup.interview_track||'technical').replaceAll('_',' ').toUpperCase()}  /  ${(s.setup.question_time_limit_seconds||0)?s.setup.question_time_limit_seconds+'s per question':'no question clock'}`;$('mode-banner').textContent=s.setup.provider==='demo'?'Guided practice · prepared questions, without a score':s.current.source==='local_rubric_fallback'?'Prepared question · the adaptive service is temporarily unavailable':'Interview in progress · review your answer before sending';if(s.status==='awaiting_report')$('mode-banner').textContent+=' Interview completed. Click Finish & assess.';$('question').textContent=s.current.text;$('question-topic').textContent=(s.plan.competencies.find(c=>c.id===s.current.competency_id)?.name||'')+' · '+s.setup.mode;$('why').textContent=s.current.why;$('difficulty').textContent='';$('coach-note').hidden=!s.current.coaching;$('coach-note').textContent=s.current.coaching||'';$('interviewer-reply').hidden=!s.last_reply;$('interviewer-reply').textContent=s.last_reply||'';$('hint').hidden=s.setup.mode!=='coaching';const answers=s.turns.filter(t=>t.kind==='answer');$('turn-count').textContent=`${answers.length} answer${answers.length===1?'':'s'} recorded`;const counts=s.plan.competencies.map(c=>({c,number:answers.filter(t=>t.question.competency_id===c.id).length}));const covered=counts.filter(x=>x.number>0).length;$('coverage-progress').textContent=`${covered}/${counts.length} competencies have answer evidence · ${Math.round(100*covered/Math.max(1,counts.length))}% coverage`;$('coverage').replaceChildren(...counts.map(({c,number})=>{const n=el('div',c.name,'coverage-item');n.append(el('small',number+' answer(s) · '+(number?'evidence collected':'unassessed')));return n;}));$('scenario-facts').replaceChildren(el('p',s.plan.scenario.situation),...s.plan.scenario.facts.map(f=>el('p',f)),...s.branch_events.map(b=>el('p','New constraint: '+b.complication)));$('transcript').replaceChildren(...s.turns.map(t=>turnNode(t,false)));const voice=s.turns.filter(t=>t.kind==='answer'&&t.delivery).at(-1)?.delivery;const deliveryBox=$('voice-last');deliveryBox.replaceChildren(el('strong','Voice delivery · transcript only'));deliveryBox.append(el('p',voice?`${voice.estimated_wpm} estimated words/min · ${voice.transcript_word_count} transcript words · ${voice.identified_fillers} recognizable fillers. Not a confidence or skill score.`:'Use speech capture to see an estimated pace after submitting. Pauses and vocal confidence are not measured.')); 
 const x=s.current.xray||{};$('xray-summary').replaceChildren(el('span',`Practice focus: ${s.plan.competencies.find(c=>c.id===s.current.competency_id)?.name||"Interview reasoning"}`,'xray-pill'));
 const source=$('xray-source');source.replaceChildren();if(x.source){source.append(el('p',`Project reference · ${x.source.path}:${x.source.line_start}-${x.source.line_end}`,'source-path'),el('pre',x.source.snippet,'code-lines'));}else source.append(el('p','This question is based on the role and skills being practised.','hint'));
 updateTimer();}
function updateTimer(){if(!session?.current||!session.deadline)return;const left=Math.max(0,Math.ceil(session.deadline-Date.now()/1000));$('timer').textContent=`${String(Math.floor(left/60)).padStart(2,'0')}:${String(left%60).padStart(2,'0')}`;const qLimit=session.current.time_limit_seconds||0;
 const qClock=$('question-countdown');
 if(qClock){if(qLimit&&session.current.issued_at){const qLeft=Math.ceil(qLimit-(Date.now()/1000-session.current.issued_at));qClock.textContent=qLeft>0?`QUESTION · ${Math.floor(qLeft/60)}:${String(qLeft%60).padStart(2,'0')} left`:'QUESTION · TIME ELAPSED (answer still accepted)';qClock.classList.toggle('expired',qLeft<=0);}else{qClock.textContent='UNTIMED QUESTION';qClock.classList.remove('expired');}}
 const ended=session.status!=='active'||left===0;['record','submit-answer','clarify','hint','skip'].forEach(id=>$(id).disabled=working||ended);if(ended&&(recorder||recognition)&&recordTarget==='answer')stopCapture(true);if(left===0&&session.status==='active')$('mic-status').textContent='Time is up. Finish the interview to generate feedback.';}
// Safe text-only Markdown rendering for user-supplied answer transcripts.
// Never inject HTML from a candidate answer into the report or replay.
function formatInline(parent,source){
 const chunks=String(source).split(/(\*\*[^*\n]+\*\*)/g);
 chunks.forEach(part=>{if(part.startsWith('**')&&part.endsWith('**')&&part.length>4){parent.append(el('strong',part.slice(2,-2)));}else if(part)parent.append(document.createTextNode(part));});
}
function answerDocument(text){
 const wrapper=el('div',undefined,'answer-document');let list=null;
 const lines=String(text||'').replace(/\r\n/g,'\n').split('\n');
 for(const line of lines){const value=line.trim();if(!value){list=null;continue;}
  if(/^[-*]\s+/.test(value)){if(!list){list=el('ul');wrapper.append(list);}const item=el('li');formatInline(item,value.replace(/^[-*]\s+/,''));list.append(item);continue;}
  list=null;const title=value.match(/^#{1,4}\s+(.+)/);
  const n=el(title?'h4':'p');formatInline(n,title?title[1]:value);wrapper.append(n);
 }
 return wrapper;
}
function turnNode(t,withButtons){const n=el('div',undefined,'turn');n.id='evidence-'+t.id;n.append(el('span',t.kind+' · '+new Date(t.created_at*1000).toLocaleTimeString(),'meta'),el('p',t.question.text),answerDocument(t.text));if(t.reply)n.append(el('p',t.reply));if(t.kind==='answer'&&(t.question_time_limit_seconds||t.delivery)){const d=t.delivery;n.append(el('p',`Response time: ${Math.round(t.response_seconds||0)}s${t.over_question_limit?' · over suggested time':''}${d?' · Voice: '+d.estimated_wpm+' estimated WPM, '+d.identified_fillers+' recognizable fillers':''}`,'delivery-record'));}if(withButtons&&t.kind==='answer'){const a=el('div',undefined,'actions no-print');const replay=el('button','Replay question');replay.onclick=()=>speak(t.question.text);const repair=el('button','Repair this answer');repair.onclick=()=>startRetry(t.id,'repair');const retry=el('button','Try a new scenario');retry.onclick=()=>startRetry(t.id,'parallel');a.append(replay,repair,retry);n.append(a);
 const rationale=el('div',undefined,'replay-xray');rationale.append(el('h4','Why this question came up'),el('p',t.question.why||'No controller rationale recorded.'),el('p',t.question.difficulty_reason||''),el('p',t.question.revisit?'This topic returns to check whether your reasoning has improved.':'This question explores an area of the role.'));n.append(rationale);}return n;}
function renderReport(){const s=session;if(!s?.report){$('report-content').replaceChildren(el('p','Complete an interview to see your feedback.','panel'));$('retry-panel').hidden=true;$('repair-workspace').hidden=true;return;}const root=$('report-content');root.replaceChildren();const head=el('div',undefined,'report-summary');head.append(el('p',s.report.provisional?'ASSESSMENT UNAVAILABLE · ANSWERS SAVED':s.report.demo?'GUIDED EXAMPLE · UNSCORED':'YOUR INTERVIEW REVIEW','eyebrow'),el('h2',s.plan.role),el('p',s.report.summary));root.append(head);root.append(el('p','Automated practice feedback. Review important conclusions carefully.','report-provenance'));const provenance=s.report.claim_provenance||{status:'self_reported_unverified',label:'CV and project claims are unverified. No hands-on experience or authorship was independently validated.'};const sourceDetails=el('details',undefined,'report-method-details');sourceDetails.append(el('summary','Assessment method and source information'),el('p',`Interview service: ${s.report.ai_provider||s.setup.provider} · ${s.report.ai_model||s.setup.ai_model||'guided example'}`),el('p',s.report.evidence_policy||'Assessment uses recorded answer excerpts.'),el('p',provenance.label));root.append(sourceDetails);$('retry-report').hidden=!s.report.provisional;const delivery=s.report.delivery_summary;if(delivery?.samples){const note=el('div',undefined,'panel report-delivery');note.append(el('h3','Voice delivery notes'),el('p',`${delivery.samples} voice-recorded answers · ${delivery.mean_estimated_wpm} average estimated WPM · ${delivery.filler_count} recognizable filler terms.`),el('p',delivery.note,'hint'));root.append(note);}const cov=s.report.coverage;if(cov){const coverage=el('div',undefined,'panel report-coverage');coverage.append(el('h3',`Interview coverage: ${cov.covered_count}/${cov.total_count} competencies (${cov.coverage_percent}%)`));const missing=cov.unassessed_ids.map(id=>s.plan.competencies.find(c=>c.id===id)?.name||id);coverage.append(el('p',missing.length?'Unassessed: '+missing.join(', '):'Every planned competency has recorded answers; this does not establish correct performance or hands-on skill.'));root.append(coverage);}if(s.report.fallback_events?.length){const log=el('details',undefined,'report-method-details');log.append(el('summary','Question preparation notes'),el('p','Some questions used prepared practice material when live questions were not available.'));s.report.fallback_events.forEach(f=>log.append(el('p',`${f.stage==='question'?'A practice question':f.stage==='plan'?'The interview plan':'An assessment step'} used an alternative method.`)));root.append(log);}
 const map=el('div',undefined,'panel skill-dna');map.append(el('h2','Skill DNA · What was actually assessed'));
 s.report.items.forEach(i=>{const row=el('div',undefined,'dna-row');row.append(el('strong',i.name));const bar=el('div',undefined,'dna-bar');const fill=el('div',undefined,'dna-fill');fill.style.width=i.score===null?'0%':`${i.score/4*100}%`;bar.append(fill);const inspect=el('button',i.score===null?i.status.replaceAll('_',' ').toUpperCase():`${i.score}/4 · ${i.status.replaceAll('_',' ')} ↗`,'intel-score-button');inspect.type='button';inspect.setAttribute('aria-label','Inspect scoring evidence for '+i.name);inspect.onclick=()=>{show('score-evidence');$('evidence-session').value=s.id;$('evidence-refresh').click();};row.append(bar,inspect);map.append(row);});root.append(map);
 s.report.items.forEach(i=>{const n=el('article',undefined,'panel report-item');const header=el('header');const title=el('div');title.append(el('h2',i.name),el('p',i.status.replaceAll('_',' '),'assessment-status'));header.append(title,el('span',i.score===null?'Unscored':`${i.score} / 4`,'score'));n.append(header,el('p',i.feedback),el('p','To reach the next rubric level: '+(i.score_gap||'Not specified by this assessment. Manual review recommended.'),'score-gap'),el('p','Next practice: '+i.practice),el('p','Feedback certainty: '+(i.confidence||'limited'),'hint'));if(i.initial_score!==null&&i.initial_score!==undefined&&i.latest_score!==null&&i.latest_score!==undefined){n.append(el('p',`Change across your answers: first ${i.initial_score}/4 → latest ${i.latest_score}/4. ${i.improvement_note||''}`,'trajectory'));}i.evidence.forEach(e=>{const q=el('div',undefined,'evidence');const go=el('a','View complete answer in replay','replay-link');go.href='#evidence-'+e.turn_id;go.onclick=()=>{const replayPanel=$('full-replay');if(replayPanel)replayPanel.open=true;};q.append(el('small','FROM YOUR ANSWER'),answerDocument(e.quote),go);n.append(q);});root.append(n);});const limits=el('details',undefined,'report-method-details');limits.append(el('summary','How to interpret your scores'));s.report.limitations.forEach(l=>limits.append(el('p',String(l).replace(/AI-generated|model-generated/gi,'automated'))));limits.append(el('p','This is an automated practice assessment and may be wrong. It is not a hiring evaluation. Score guide: 0 incorrect reasoning, 1 fragmentary, 2 partial, 3 sound, 4 sound with trade-offs and verification. Insufficient evidence is not scored.','hint'));root.append(limits);const replay=el('details',undefined,'panel report-replay');replay.id='full-replay';replay.append(el('summary','Full interview replay, complete answers and answer repair'));const full=el('div');s.turns.forEach(t=>full.append(turnNode(t,true)));replay.append(full);root.append(replay);renderRetry();renderRepairWorkspace();}
function renderRetry(){const r=session?.retry;$('retry-panel').hidden=!r;if(!r)return;$('retry-question').textContent=r.question;$('retry-criteria').textContent='Same rubric: '+r.competency.criteria.join(' ');$('retry-hints').textContent=r.hints.slice(0,r.hints_used).join(' ');$('retry-feedback').hidden=!r.feedback;$('retry-feedback').textContent=r.feedback?r.feedback.comparison+'\n\nNext step: '+r.feedback.next_step:'';$('retry-answer').value=r.answer||'';$('retry-submit').hidden=!!r.feedback;$('retry-hint').hidden=!!r.feedback;$('retry-record').hidden=!!r.feedback;$('retry-grade').hidden=r.feedback_source!=='unscored_offline_fallback';}
async function startRetry(turn,style){stopCapture(true);await run(async()=>{keep(await api(`/api/sessions/${session.id}/retry`,{method:'POST',body:{turn_id:turn,style}}));renderRetry();renderRepairWorkspace();$('retry-panel').scrollIntoView({behavior:matchMedia('(prefers-reduced-motion: reduce)').matches?'instant':'smooth'});});}
async function loadHistory(){const list=await api('/api/sessions');$('history-list').replaceChildren();if(!list.length){$('history-list').append(el('p','No saved interviews yet.','panel'));return;}list.forEach(s=>{const n=el('div',undefined,'panel history-row'),info=el('div');info.append(el('h2',s.role),el('p',`${new Date(s.created_at*1000).toLocaleString()} · ${s.status.replaceAll('_',' ')} · ${s.answers} answers`));const actions=el('div',undefined,'actions'),open=el('button','Open session'),del=el('button','Delete session');open.onclick=()=>run(async()=>{keep(await api('/api/sessions/'+s.id));restoreFields();renderPlan();renderArena();renderReport();show(session.status==='ready'?'setup':session.status==='completed'?'report':'arena');});del.onclick=()=>{if(confirm('Delete this session and its saved CV, transcript and feedback?'))run(async()=>{await api('/api/sessions/'+s.id,{method:'DELETE'});if(session?.id===s.id){session=null;localStorage.removeItem('auralis-current');$('arena-body').hidden=true;$('arena-empty').hidden=false;$('plan-preview').hidden=true;$('report-content').replaceChildren(el('p','Complete an interview to see your feedback.','panel'));$('retry-panel').hidden=true;}await loadHistory();});};actions.append(open,del);n.append(info,actions);$('history-list').append(n);});}
function restoreFields(){if(!session)return;for(const k of ['cv','jd','role','provider','mode','language'])$(k).value=session.setup[k];syncModelSelector(session.setup.ai_model||'openai/gpt-oss-20b');$('duration').value=String(session.setup.duration_minutes);$('interview-track').value=session.setup.interview_track||'technical';$('interviewer-persona').value=session.setup.interviewer_persona||'supportive';$('question-limit').value=String(session.setup.question_time_limit_seconds||0);$('adaptive-difficulty').checked=session.setup.adaptive_difficulty!==false;$('evidence').value=session.setup.project_evidence;codeproof=null;incidentEvidence='';$('incident-select').value=session.setup.incident_id||'';chooseIncident();$('consent').checked=session.setup.consent;$('synthetic-data').checked=!!session.setup.synthetic_data;}
function recorderUI(active){$('record').hidden=active&&recordTarget==='answer';$('stop-record').hidden=!(active&&recordTarget==='answer');$('retry-record').hidden=(active&&recordTarget==='retry-answer')||!!session?.retry?.feedback;$('retry-stop').hidden=!(active&&recordTarget==='retry-answer');$('mic-status').textContent=active?'Listening… click Done speaking when finished.':'Your microphone is off';}
function stopCapture(discard=false){
 if(!discard&&voiceEligible&&voiceCaptureStart&&recordTarget==='answer'&&voiceSource==='browser_speech'){
   const duration=(performance.now()-voiceCaptureStart)/1000;
   if(duration>=2&&duration<=120&&$('answer').value.trim())voiceEvidence={seconds:duration,source:'browser_speech',transcript:$('answer').value.trim(),question_id:session?.current?.id};
 }
 if(discard){voiceEvidence=null;voiceEligible=false;}
 voiceCaptureStart=0;
 if(discard)captureEpoch++;
 clearTimeout(recordTimer);
 const oldRecorder=recorder;recorder=null;
 const oldRecognition=recognition;recognition=null;
 if(oldRecorder&&oldRecorder.state!=='inactive')oldRecorder.stop();
 if(oldRecognition)oldRecognition.stop();
 if(stream){stream.getTracks().forEach(t=>t.stop());stream=null;}
 recorderUI(false);
}
async function capture(target){
 if(working)return;
 if(!session){notify('Start an interview first.');return;}
 stopCapture(true);speechSynthesis.cancel();recordTarget=target;notify('');voiceEligible=target==='answer'&&!$(target).value.trim();voiceCaptureStart=performance.now();voiceSource=session.setup.provider==='groq'?'groq_transcription':'browser_speech';
 const startAt=voiceCaptureStart;const epoch=captureEpoch,sid=session.id,view=currentView;
 const questionId=target==='answer'?session.current?.id:session.retry?.id;
 const valid=()=>captureEpoch===epoch&&session?.id===sid&&currentView===view&&(target==='answer'?session.current?.id:session.retry?.id)===questionId;
 if(session.setup.provider==='demo'||session.setup.provider==='huggingface'){
  const SR=window.SpeechRecognition||window.webkitSpeechRecognition;
  if(!SR){notify('Browser speech recognition is unavailable. You may type your answer or use Groq for audio transcription.');return;}
  if(!sessionStorage.getItem('browser-speech-consent')){if(!confirm('Browser speech recognition may transmit audio to the browser vendor. Continue?'))return;sessionStorage.setItem('browser-speech-consent','yes');}
  const rec=new SR();recognition=rec;rec.lang=session.setup.language==='hi'?'hi-IN':'en-IN';rec.continuous=true;rec.interimResults=true;const base=$(target).value;
  rec.onresult=e=>{if(!valid())return;let words='';for(let i=0;i<e.results.length;i++)words+=e.results[i][0].transcript+' ';$(target).value=(base+' '+words).trim();};
  rec.onerror=e=>{if(valid())notify('Browser speech recognition: '+e.error+'. Type an answer or use live Groq transcription.');};
  rec.onend=()=>{if(recognition===rec)recognition=null;if(valid()){if(target==='answer'&&voiceEligible&&voiceCaptureStart){const duration=(performance.now()-voiceCaptureStart)/1000;if(duration>=2&&duration<=120&&$('answer').value.trim())voiceEvidence={seconds:duration,source:'browser_speech',transcript:$('answer').value.trim(),question_id:questionId};voiceCaptureStart=0;}recorderUI(false);clearTimeout(recordTimer);}};
  try{rec.start();recorderUI(true);recordTimer=setTimeout(()=>stopCapture(false),120000);}catch(e){recognition=null;notify('Could not start speech recognition. '+e.message);}return;
 }
 try{
  if(!navigator.mediaDevices?.getUserMedia)throw Error('Microphone access requires localhost or HTTPS.');
  const acquired=await navigator.mediaDevices.getUserMedia({audio:{echoCancellation:true,noiseSuppression:true}});
  if(!valid()){acquired.getTracks().forEach(t=>t.stop());return;}
  stream=acquired;
  const mime=['audio/webm;codecs=opus','audio/webm','audio/mp4'].find(t=>MediaRecorder.isTypeSupported(t));
  const chunks=[];let bytes=0;let recordingBegan=0;const rec=new MediaRecorder(acquired,mime?{mimeType:mime}:{});recorder=rec;
  rec.ondataavailable=e=>{if(e.data.size&&valid()){chunks.push(e.data);bytes+=e.data.size;if(bytes>9*1024*1024)stopCapture(false);}};
  rec.onstop=()=>{
   acquired.getTracks().forEach(t=>t.stop());if(stream===acquired)stream=null;if(recorder===rec)recorder=null;
   if(!valid())return;
   clearTimeout(recordTimer);recorderUI(false);
   if(!chunks.length)return;
   const capturedSeconds=(performance.now()-recordingBegan)/1000;
   const blob=new Blob(chunks,{type:rec.mimeType});
   run(async()=>{const form=new FormData();form.append('file',blob,rec.mimeType.includes('mp4')?'answer.m4a':'answer.webm');const result=await api('/api/transcribe/'+sid,{method:'POST',body:form});if(valid()){ $(target).value=result.text;const d=capturedSeconds;if(target==='answer'&&voiceEligible&&d>=2&&d<=120)voiceEvidence={seconds:d,source:'groq_transcription',transcript:result.text.trim(),question_id:questionId};}});
  };
  rec.start(500);recordingBegan=performance.now();recorderUI(true);recordTimer=setTimeout(()=>stopCapture(false),120000);
 }catch(e){if(valid()){stopCapture(true);notify('Microphone unavailable: '+e.message+' You can type your answer instead.');}}
}
function download(name,obj){const url=URL.createObjectURL(new Blob([JSON.stringify(obj,null,2)],{type:'application/json'}));const a=document.createElement('a');a.href=url;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);}
async function submit(kind){if(recorder||recognition){stopCapture(false);notify('Recording ended. Review the recognized transcript, then submit again.',false);return;}const text=kind==='skip'?'Skipped this question.':$('answer').value.trim();if(!text){notify('Speak or type an answer first.');return;}const voice=(kind==='answer'&&voiceEvidence&&voiceEvidence.question_id===session.current.id&&voiceEvidence.transcript===text)?{voice_duration_seconds:Math.round(voiceEvidence.seconds*10)/10,voice_source:voiceEvidence.source}:{};const signature=session.id+session.current.id+kind+text;if(!pending||pending.signature!==signature)pending={signature,id:crypto.randomUUID()};await run(async()=>{keep(await api(`/api/sessions/${session.id}/actions`,{method:'POST',body:{text,kind,request_id:pending.id,expected_question_id:session.current.id,...voice}}));pending=null;voiceEvidence=null;$('answer').value='';renderArena();if($('auto-speak').checked)speak(session.last_reply||session.current.text);});}

// Auralis 5.1: Evidence-first answer repair. Existing persisted retry state is reused.
function renderRepairWorkspace(){
 const root=$('repair-workspace'),s=session;
 const answers=s?.turns?.filter(t=>t.kind==='answer')||[];
 root.hidden=!s?.report||!answers.length;
 if(root.hidden)return;
 const sel=$('repair-target'),previous=sel.value;
 sel.replaceChildren(...answers.map((t,i)=>{
  const skill=s.plan.competencies.find(c=>c.id===t.question.competency_id)?.name||'General';
  const o=el('option',`${String(i+1).padStart(2,'0')} / ${skill} / ${t.question.text.slice(0,68)}`);
  o.value=t.id;return o;
 }));
 // Prefer currently active retry, then the first recorded answer for visible improvement.
 sel.value=answers.some(t=>t.id===previous)?previous:(s.retry?.original_turn_id||answers[0].id);
 if(!answers.some(t=>t.id===sel.value))sel.value=answers[0].id;
 showRepairSelection();
}
function showRepairSelection(){
 const t=session?.turns?.find(t=>t.id===$('repair-target').value&&t.kind==='answer');
 if(!t)return;
 const c=session.plan.competencies.find(x=>x.id===t.question.competency_id);
 const item=session.report?.items?.find(x=>x.competency_id===t.question.competency_id);
 const guide=$('repair-guide');guide.replaceChildren();
 guide.append(el('p','RUBRIC / '+(c?.name||'Interview answer'),'section-index'));
 const list=el('ol');(c?.criteria||[]).forEach(v=>list.append(el('li',v)));guide.append(list);
 if(item){guide.append(el('p','Assessment: '+item.feedback),el('p','Next-score gap: '+(item.score_gap||'Not specified by the assessor.')));}
 $('repair-original').replaceChildren(answerDocument(t.text));
 const r=[...(session.retry_history||[])].reverse().find(r=>r.original_turn_id===t.id && r.answer);
 $('repair-revised').replaceChildren();
 if(r){$('repair-revised').append(answerDocument(r.answer));$('repair-revised').append(el('p',r.feedback_source==='unscored_offline_fallback'?'AI feedback unavailable: this retry has not been graded.':r.feedback?.comparison||'Retry saved.','repair-result-note'));}
 else $('repair-revised').append(el('p','No revised answer recorded yet. Choose “Repair selected answer” to try again.','hint'));
 $('repair-start').disabled=(session.retry_history||[]).length>=10;
}

// The progress view uses existing owner-scoped stored assessments, never locally invented grades.
async function loadLearningProgress(){
 const root=$('learning-content');root.replaceChildren(el('p','Loading progress…','hint'));
 const data=await api('/api/learning/progress');root.replaceChildren();
 const stats=el('div',undefined,'learning-stats');
 [['Sessions',data.session_count],['Completed',data.completed_count],['Scored observations',data.scored_competency_observations],['Answer repairs',data.repair_attempt_count]].forEach(([label,val])=>{
  const n=el('div',undefined,'learning-stat');n.append(el('strong',String(val)),el('span',label));stats.append(n);
 });root.append(stats);
 if(!data.skills.length)root.append(el('p','No graded competency history yet. Finish a live assessed interview, then return here. Demo and offline results are deliberately excluded.','learning-empty'));
 data.skills.forEach(skill=>{
  const card=el('article',undefined,'learning-skill');
  const head=el('div',undefined,'learning-skill-head');head.append(el('h3',skill.name),el('span',`${skill.session_count} observation${skill.session_count===1?'':'s'}`,'hint'));card.append(head);
  const graph=el('div',undefined,'learning-graph');graph.setAttribute('role','img');
  graph.setAttribute('aria-label',skill.name+' scores in chronological order: '+skill.points.map(p=>p.score+'/4').join(', '));
  skill.points.forEach((point,i)=>{
    const bar=el('div',undefined,'learning-bar');bar.style.height=`${Math.max(4,(point.score/4)*100)}%`;
    bar.title=`${point.date} · ${point.role} · ${point.score}/4 · ${point.provider}`;
    const label=el('span',`${point.score}/4`);bar.append(label);graph.append(bar);
  });card.append(graph);
  card.append(el('p','Latest: '+skill.latest_score+'/4 · '+(skill.score_change===null?'One scored assessment; no change measurable':`Change from first: ${skill.score_change>0?'+':''}${skill.score_change} points`)+' · Cross-session comparison is indicative only.','hint'));
  root.append(card);
 });
 const disclaimer=el('div',undefined,'learning-limitations');data.limitations.forEach(line=>disclaimer.append(el('p',line)));root.append(disclaimer);
}

const CALCULATIONS={
 gravity_load:{label:'Equipment gravitational load',fields:[['mass_kg','Mass (kg)',180],['gravity_m_s2','Gravity (m/s²)',9.81]]},
 bend_allowance:{label:'Bend allowance',fields:[['angle_deg','Bend angle (degrees)',90],['inside_radius_mm','Inside radius (mm)',2],['thickness_mm','Sheet thickness (mm)',2],['k_factor','K-factor',0.4]]},
 plate_stiffness_ratio:{label:'Plate stiffness ratio',fields:[['thickness_before_mm','Original thickness (mm)',2],['thickness_after_mm','New thickness (mm)',3]]},
 three_phase_current:{label:'Three-phase current',fields:[['real_power_w','Real power (W)',5000000],['line_voltage_v','Line voltage (V)',11000],['power_factor','Power factor',0.9]]}
};
function renderCalculationFields(){
 const spec=CALCULATIONS[$('calculation-case').value],root=$('calculation-fields');root.replaceChildren();
 spec.fields.forEach(([key,label,initial])=>{
  const node=el('div');const l=el('label',label);l.htmlFor='calc-'+key;
  const inp=el('input');inp.type='number';inp.step='any';inp.id='calc-'+key;inp.value=initial;node.append(l,inp);root.append(node);
 });$('calculation-result').replaceChildren(el('p','Enter assumptions and click Check calculation.','hint'));
}
async function checkTechnicalCalculation(){
 const spec=CALCULATIONS[$('calculation-case').value],values={};
 for(const [key] of spec.fields){const raw=$('calc-'+key).value;if(!raw.trim())throw Error('Enter each numeric assumption.');values[key]=Number(raw);if(!Number.isFinite(values[key]))throw Error('Enter finite numbers only.');}
 const raw=$('claimed-result').value.trim();
 const claimed_result=raw===''?null:Number(raw);
 if(claimed_result!==null&&!Number.isFinite(claimed_result))throw Error('Enter a valid claimed answer.');
 const data=await api('/api/technical/check',{method:'POST',body:{case:$('calculation-case').value,values,claimed_result}});
 const root=$('calculation-result');root.replaceChildren(el('p','DETERMINISTIC CHECK / '+data.name.toUpperCase(),'section-index'),el('h2',`${data.result.toLocaleString(undefined,{maximumFractionDigits:6})} ${data.unit}`),el('p',data.formula,'formula'));
 if(data.comparison!=='not_supplied')root.append(el('p',(data.comparison==='within_1_percent'?'Within 1% of the formula result.':'Different from the formula result.')+' Relative difference: '+data.relative_error_percent+'%.','calculation-comparison'));
 root.append(el('p',data.interpretation),el('p',data.warning,'hint'));
}
$('repair-target').onchange=showRepairSelection;
$('repair-start').onclick=()=>startRetry($('repair-target').value,'repair');
$('calculation-case').onchange=renderCalculationFields;
$('calculation-run').onclick=()=>run(checkTechnicalCalculation);
renderCalculationFields();
$('inspect-zip').onclick=()=>run(async()=>{const file=$('repo-file').files[0];if(!file)throw Error('Choose a source-only Python ZIP.');const form=new FormData();form.append('file',file);renderCodeProof(await api('/api/codeproof/zip',{method:'POST',body:form}));});
$('inspect-github').onclick=()=>run(async()=>{const url=$('repo-url').value.trim();if(!url)throw Error('Paste a public GitHub repository URL.');renderCodeProof(await api('/api/codeproof/github',{method:'POST',body:{url}}));});
$('incident-select').onchange=chooseIncident;
document.querySelectorAll('[data-view]').forEach(b=>b.onclick=()=>show(b.dataset.view));
$('sample').onclick=()=>{$('cv').value=sampleCV;$('jd').value=sampleJD;$('role').value='Junior backend developer';$('synthetic-data').checked=true;};
$('check-live').onclick=()=>run(async()=>{if($('provider').value==='demo')throw Error('Choose Groq or Hugging Face to test a real model.');const out=await api('/api/live/check?provider='+encodeURIComponent($('provider').value)+'&model='+encodeURIComponent($('ai-model').value));notify(out.message,false);$('connection').textContent=($('provider').value==='groq'?'Groq':'Hugging Face')+' model checked · '+out.model;});
$('provider').onchange=()=>syncModelSelector();
$('setup-form').onsubmit=e=>{e.preventDefault();run(async()=>{keep(await api('/api/sessions',{method:'POST',body:setupData()}));renderPlan();$('plan-preview').scrollIntoView({behavior:matchMedia('(prefers-reduced-motion: reduce)').matches?'instant':'smooth'});});};
$('cv-file').onchange=()=>run(async()=>{const f=$('cv-file').files[0];if(!f)return;const form=new FormData();form.append('file',f);$('cv').value=(await api('/api/documents',{method:'POST',body:form})).text;});
$('rea-file').onchange=()=>run(async()=>{const f=$('rea-file').files[0];if(!f)return;const form=new FormData();form.append('file',f);$('evidence').value=(await api('/api/evidence',{method:'POST',body:form})).text;});
$('start').onclick=()=>run(async()=>{keep(await api(`/api/sessions/${session.id}/start`,{method:'POST',body:{}}));renderArena();show('arena');if($('auto-speak').checked)speak(session.current.text);});
$('submit-answer').onclick=()=>submit('answer');$('clarify').onclick=()=>submit('clarify');$('skip').onclick=()=>submit('skip');$('hint').onclick=()=>{$('answer').value='Please give me a hint.';submit('hint');};
$('finish').onclick=()=>{stopCapture(true);run(async()=>{keep(await api(`/api/sessions/${session.id}/finish`,{method:'POST',body:{}}));renderReport();show('report');});};
$('record').onclick=()=>capture('answer');$('stop-record').onclick=()=>stopCapture(false);$('retry-record').onclick=()=>capture('retry-answer');$('retry-stop').onclick=()=>stopCapture(false);
$('speak-question').onclick=()=>speak(session.current.text);$('mute').onclick=()=>speechSynthesis.cancel();$('retry-speak').onclick=()=>speak(session.retry.question);
$('retry-hint').onclick=()=>run(async()=>{const answer=$('retry-answer').value;keep(await api(`/api/sessions/${session.id}/retry/hint`,{method:'POST',body:{}}));renderRetry();$('retry-answer').value=answer;speak(session.retry.hints[session.retry.hints_used-1]);});
$('retry-submit').onclick=()=>run(async()=>{keep(await api(`/api/sessions/${session.id}/retry/answer`,{method:'POST',body:{retry_id:session.retry.id,text:$('retry-answer').value.trim()}}));renderRetry();renderRepairWorkspace();});
$('retry-grade').onclick=()=>run(async()=>{keep(await api(`/api/sessions/${session.id}/retry/regrade`,{method:'POST',body:{}}));renderRetry();renderRepairWorkspace();});
$('compare-button').onclick=()=>run(async()=>{const data=setupData();const result=await api('/api/compare',{method:'POST',body:{cv:data.cv,jd_a:data.jd,jd_b:$('jd-b').value.trim(),provider:data.provider,ai_model:data.ai_model,consent:data.consent}});const root=$('compare-results');root.replaceChildren();if(result.demo)root.append(el('p','This comparison uses prepared practice material. For custom comparisons, choose an adaptive interview.','banner comparison-note'));if(Object.values(result.sources||{}).some(s=>s==='local_rubric_fallback'))root.append(el('p','A prepared role outline is shown because the live comparison was unavailable.','banner comparison-note'));['a','b'].forEach(k=>{const p=result[k],n=el('div',undefined,'panel');n.append(el('p',k==='a'?'ROLE A':'ROLE B','eyebrow'),el('h2',p.role),el('p',p.summary));p.competencies.forEach(c=>n.append(skillNode(c)));p.claims.forEach(c=>n.append(el('p','Project probe: '+c.probe)));root.append(n);});});
$('export').onclick=()=>run(async()=>{if(!session)throw Error('Open a session first.');download('Auralis-'+session.id+'.json',await api(`/api/sessions/${session.id}/export`));});
$('retry-report').onclick=()=>run(async()=>{if(!session?.report?.provisional)throw Error('This report is already fully generated.');keep(await api(`/api/sessions/${session.id}/finish`,{method:'POST',body:{}}));renderReport();if(session.report.provisional)notify('The assessment is not available right now. Your answers have been saved.',false);});
$('delete-all').onclick=()=>{if(!confirm('Permanently delete all interviews, CVs, assessments, practical attempts and the study plan from your Auralis account?'))return;run(async()=>{const result=await api('/api/privacy/delete-all',{method:'POST',body:{}});session=null;localStorage.removeItem('auralis-current');$('plan-preview').hidden=true;$('arena-body').hidden=true;$('arena-empty').hidden=false;renderReport();await loadHistory();notify(`Deleted ${result.deleted} interview session(s).`,false);});};
$('print').onclick=()=>{if(!session?.report){notify('Generate a report first.');return;}document.body.classList.remove('print-full');document.body.classList.add('print-compact');window.addEventListener('afterprint',()=>document.body.classList.remove('print-compact'),{once:true});window.print();};
$('print-full').onclick=()=>{if(!session?.report){notify('Generate a report first.');return;}document.body.classList.remove('print-compact');document.body.classList.add('print-full');const section=$('full-replay');const wasOpen=section.open;section.open=true;const cleanup=()=>{section.open=wasOpen;document.body.classList.remove('print-full');};window.addEventListener('afterprint',cleanup,{once:true});window.print();};
window.addEventListener('beforeunload',()=>{stopCapture(true);speechSynthesis.cancel();});
setInterval(updateTimer,1000);populateVoices();loadIncidents();if('speechSynthesis'in window)speechSynthesis.onvoiceschanged=populateVoices;
async function auralisInitialize(){await window.auralisAuth.ready;if(window.auralisAuth.enabled&&!window.auralisAuth.token)return;
 if(window.auralisAuth.enabled){
  for(const opt of [...$('provider').options])if(opt.value!=='groq')opt.remove();
  $('provider').value='groq';syncModelSelector('openai/gpt-oss-120b');
 }
 try{const h=await api('/api/health');$('connection').textContent=h.groq_configured&&h.huggingface_configured?'Both interview providers are configured':h.groq_configured?'Groq is configured':h.huggingface_configured?'Hugging Face is configured':'Guided example is available';const sid=localStorage.getItem('auralis-current');if(sid){try{keep(await api('/api/sessions/'+sid));restoreFields();renderPlan();renderArena();renderReport();}catch{localStorage.removeItem('auralis-current');}}}catch(e){$('connection').textContent='Connection unavailable';notify(e.message);}}
window.auralisOnLogin=auralisInitialize;auralisInitialize();

$('interview-track').addEventListener('change',()=>{if($('interview-track').value==='pressure'&&$('question-limit').value==='0')$('question-limit').value='90';});
$('provider').onchange();
