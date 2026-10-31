'use strict';
/* Campus 5.5. All text from candidates/teachers is rendered via textContent. */
(()=>{
const id=x=>document.getElementById(x);
const make=(tag,txt,cls)=>{const e=document.createElement(tag);if(txt!==undefined)e.textContent=txt;if(cls)e.className=cls;return e;};
const wipe=x=>{const e=id(x);e.replaceChildren();return e;};
const row=(root,title,detail,meta)=>{const e=make('article',undefined,'suite-entry');if(meta)e.append(make('small',meta));e.append(make('h3',title),make('p',detail));root.append(e);return e;};
const action=(text,fn,secondary=false)=>{const b=make('button',text,secondary?'secondary':'');b.type='button';b.onclick=()=>run(fn);return b;};
const navigate=(view,fn)=>document.querySelector(`.nav[data-view="${view}"]`)?.addEventListener('click',()=>run(fn));
let placementId=localStorage.getItem('auralis-55-campus')||'';
function campusRender(p){
 placementId=p.id;localStorage.setItem('auralis-55-campus',p.id);
 const stages=wipe('campus-stages');p.stages.forEach((s,i)=>{const d=make('div',undefined,'suite-stage '+s.status);d.append(make('small',`${String(i+1).padStart(2,'0')} / ${s.status.toUpperCase()}`),make('strong',s.name));stages.append(d);});
 const q=wipe('campus-question'),ledger=wipe('campus-results');p.results.forEach((s,i)=>row(ledger,p.stages[i].name,s.feedback,s.scored?`${s.passed}/${s.total} CHECKED`:'UNSCORED / SELF-REVIEW'));
 id('campus-answer-form').hidden=p.complete;
 if(p.complete){q.append(make('h2','Placement practice complete'),make('p','You finished all five rounds. Objective checks and self-review stages are shown separately.'));return;}
 const meta=`ROUND ${p.round}/5 · ${p.question.type}${p.question.question_total?' · APTITUDE '+p.question.question_number+'/'+p.question.question_total:''}`;
 q.append(make('small',meta.toUpperCase()),make('h2',p.question.name),make('p',p.question.question));
 (p.question.panel_views||[]).forEach(v=>q.append(make('p',v,'suite-muted')));
 const options=wipe('campus-options');const apt=p.current_stage==='aptitude';options.hidden=!apt;id('campus-answer').hidden=apt;id('campus-answer-label').textContent=apt?'Choose an answer':'Your response';id('campus-answer').value='';
 id('campus-answer').placeholder=p.current_stage==='coding'?'def solve(text):\n    return text[::-1]':'Explain your position, actions, evidence and verification.';
 if(apt)p.question.options.forEach((text,i)=>{const label=make('label',undefined,'suite-option'),input=make('input');input.type='radio';input.name='placement-choice';input.value=String(i);label.append(input,make('span',`${i+1}. ${text}`));options.append(label);});
}
async function campusLoad(){let p=placementId?await api(`/api/campus/${encodeURIComponent(placementId)}`).catch(()=>null):null;if(!p){const a=await api('/api/campus');p=a.simulations[0];}if(p)campusRender(p);}
id('campus-create').onsubmit=e=>{e.preventDefault();run(async()=>campusRender(await api('/api/campus',{method:'POST',body:{role:id('campus-role').value}})));};
id('campus-answer-form').onsubmit=e=>{e.preventDefault();run(async()=>{const answer=id('campus-options').hidden?id('campus-answer').value.trim():id('campus-options').querySelector('input:checked')?.value;if(answer===undefined||answer==='')throw Error('Select an option or enter your response.');campusRender(await api(`/api/campus/${placementId}/submit`,{method:'POST',body:{answer}}));});};
navigate('campus',campusLoad);

id('bilingual-form').onsubmit=e=>{e.preventDefault();run(async()=>{
 const out=await api('/api/bilingual/coach',{method:'POST',body:{text:id('bilingual-text').value,language:id('bilingual-lang').value,domain:id('bilingual-domain').value}}),root=wipe('bilingual-results');
 root.append(make('small','LOCAL LANGUAGE NOTEBOOK'),make('h2','Speak with clarity.'));
 row(root,'Answer structure',out.structure_hint,`${out.observed_words} WORDS`);
 if(out.matched_terms.length)out.matched_terms.forEach(v=>row(root,`${v.english} / ${v.hindi}`,v.explanation,'TERM MATCH'));
 else row(root,'Terminology','No terms from the selected glossary were found.');
 const phrases=row(root,'Useful translated phrases','Curated examples only, not automatic translation of your answer.');
 (out.phrase_examples||[]).forEach(v=>phrases.append(make('p',`${v.english} · ${v.hindi} · ${v.hinglish}`,'suite-muted')));
 if(out.filler_terms.length)row(root,'Possible filler words',out.filler_terms.join(', '));root.append(make('p',out.limitations,'suite-muted'));
 });};

async function bankLoad(){const data=await api('/api/question-bank'),saved=wipe('bank-saved'),auto=wipe('bank-suggested');saved.append(make('h2','Your review cards'));
 if(!data.saved.length)saved.append(make('p','No saved cards yet. Add one or save a suggested question.','suite-muted'));
 data.saved.forEach(c=>{const e=row(saved,c.question,`${c.competency} · ${c.attempts} attempts · next due ${new Date(c.next_due).toLocaleDateString()}`,c.source.replaceAll('_',' ').toUpperCase());e.append(make('p',c.variant));const buttons=make('div',undefined,'suite-actions');buttons.append(action('Mark practiced ↗',async()=>{await api(`/api/question-bank/${c.id}/practice`,{method:'POST',body:{status:'practiced'}});await bankLoad();}),action('Delete',async()=>{if(!confirm('Delete this question card?'))return;await api(`/api/question-bank/${c.id}`,{method:'DELETE'});await bankLoad();},true));e.append(buttons);});
 auto.append(make('p','Candidate prompts from lower-scored LIVE interviews. AI grades are provisional.','suite-muted'));
 if(!data.suggested.length)auto.append(make('p','No low-scored live questions to suggest.','suite-muted'));
 data.suggested.forEach(c=>row(auto,c.question,c.competency,'SUGGESTED · NOT VERIFIED').append(action('Save for later ↗',async()=>{await api('/api/question-bank',{method:'POST',body:{question:c.question,competency:c.competency}});await bankLoad();})));
}
id('bank-create').onsubmit=e=>{e.preventDefault();run(async()=>{await api('/api/question-bank',{method:'POST',body:{question:id('bank-question').value,competency:id('bank-competency').value||'General reasoning'}});id('bank-question').value='';await bankLoad();});};
navigate('bank',bankLoad);

async function collegeLoad(){const data=await api('/api/college'),managed=wipe('college-managed'),joined=wipe('college-joined');managed.append(make('h2','Instructor cohorts'));
 if(!data.managed.length)managed.append(make('p','No cohorts created for this account.','suite-muted'));
 data.managed.forEach(c=>{const section=row(managed,c.name,`${c.students} students · ${c.assignments.length} assignments`,'INSTRUCTOR · AGGREGATE ONLY');
  c.assignments.forEach(a=>{const e=row(section,a.title,`${a.target_role} · ${a.type} · ${a.completed} marked complete`,a.instructions);if(a.mentor_note)e.append(make('p','Mentor guidance: '+a.mentor_note));
   const mentor=make('form',undefined,'suite-form'),input=make('input');input.maxLength=400;input.required=true;input.setAttribute('aria-label','Mentor note for '+a.title);input.placeholder='Guidance for all students in this cohort';const submit=make('button','Publish mentor note');submit.type='submit';mentor.append(input,submit);mentor.onsubmit=event=>{event.preventDefault();run(async()=>{await api(`/api/college/assignments/${a.id}/mentor`,{method:'PATCH',body:{note:input.value}});await collegeLoad();});};e.append(mentor);
  });
  const form=make('form',undefined,'suite-form');
  const title=make('input'),type=make('select'),role=make('input'),detail=make('textarea');
  title.required=true;title.maxLength=120;title.placeholder='Assignment title';title.setAttribute('aria-label','Assignment title');
  ['interview','aptitude','coding','engineering'].forEach(name=>{const option=make('option',name);option.value=name;type.append(option);});type.setAttribute('aria-label','Assignment type');
  role.maxLength=80;role.value='General';role.setAttribute('aria-label','Target role');
  detail.required=true;detail.maxLength=700;detail.rows=3;detail.placeholder='Practice instructions (at least 12 characters)';detail.setAttribute('aria-label','Practice instructions');
  const submit=make('button','Create assignment ↗');submit.type='submit';form.append(title,type,role,detail,submit);
  form.onsubmit=e=>{e.preventDefault();run(async()=>{await api(`/api/college/cohorts/${c.id}/assignments`,{method:'POST',body:{title:title.value,type:type.value,target_role:role.value,instructions:detail.value}});await collegeLoad();});};section.append(form);
 });
 joined.append(make('h2','Student assignments'));
 if(!data.joined.length)joined.append(make('p','Join a class with a one-time invitation code.','suite-muted'));
 data.joined.forEach(c=>{const section=row(joined,c.name,'Your pseudonym: '+c.display_name,'STUDENT CHECKLIST');
  c.assignments.forEach(a=>{const e=row(section,a.title,`${a.target_role} · ${a.instructions}`,a.completed?'COMPLETED':'OPEN');if(a.mentor_note)e.append(make('p','Mentor note: '+a.mentor_note));e.append(action(a.completed?'Undo completion':'Mark complete ↗',async()=>{await api(`/api/college/assignments/${a.id}`,{method:'PATCH',body:{completed:!a.completed}});await collegeLoad();}));});
 });
}
id('college-create').onsubmit=e=>{e.preventDefault();run(async()=>{const c=await api('/api/college/cohorts',{method:'POST',body:{name:id('college-name').value}}),box=id('college-invite-result');box.hidden=false;box.replaceChildren(make('strong','Copy the one-time invite code'),make('code',c.invite),make('p','Keep it private. This code is shown only at creation.'));box.append(action('Copy invite',async()=>{await navigator.clipboard.writeText(c.invite);}));await collegeLoad();});};
id('college-join').onsubmit=e=>{e.preventDefault();run(async()=>{await api('/api/college/join',{method:'POST',body:{invite:id('college-invite').value,display_name:id('college-student-name').value}});id('college-invite').value='';await collegeLoad();});};
navigate('college',collegeLoad);

id('reliability-run').onclick=()=>run(async()=>{const r=await api('/api/reliability/fixtures'),root=wipe('reliability-fixtures');root.append(make('h2',`${r.passed}/${r.total} deterministic fixtures passed`));r.fixtures.forEach(f=>row(root,f.id.replaceAll('_',' '),f.details,f.passed?'PASS':'REVIEW'));root.append(make('p',r.limitations,'suite-muted'));});
async function reliabilityLoad(){const sessions=await api('/api/sessions'),sel=id('reliability-session');sel.replaceChildren();sessions.filter(s=>s.status==='completed').forEach(s=>{const o=make('option',`${s.role} / ${s.id.slice(0,10)}`);o.value=s.id;sel.append(o);});if(!sel.options.length){const o=make('option','No completed interview available');o.value='';sel.append(o);}}
id('reliability-audit').onclick=()=>run(async()=>{const sid=id('reliability-session').value;if(!sid)throw Error('Complete an interview before auditing its feedback.');const r=await api(`/api/reliability/audit/${encodeURIComponent(sid)}`),root=wipe('reliability-report');root.append(make('h2',`${r.issues.length} review flags`),make('p',`${r.questions_reviewed} questions / ${r.rubric_items_reviewed} rubric items.`));r.issues.forEach(i=>row(root,i.category.replaceAll('_',' '),i.detail,i.severity.toUpperCase()));root.append(make('p',r.limitations,'suite-muted'));});
navigate('reliability',reliabilityLoad);
})();
