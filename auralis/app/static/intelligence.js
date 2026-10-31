'use strict';
/* DOM-safe rendering with shared interview state and private API calls. */
(()=>{
 const by=id=>document.getElementById(id);
 const tx=(tag,value,cls)=>{const n=document.createElement(tag);if(value!==undefined)n.textContent=String(value);if(cls)n.className=cls;return n;};
 const box=(parent,...children)=>{parent.append(...children);return parent;};
 const err=(place,e)=>{place.replaceChildren(tx('p',e?.message||String(e),'intel-error'));};
 const btn=(label,action)=>{const b=tx('button',label);b.type='button';b.addEventListener('click',action);return b;};
 const runSafely=async(root,fn)=>{try{await fn()}catch(e){err(root,e)}};

 // LIVE REHEARSAL: controlled speech capture plus native question playback and local-only video preview.
 let liveSpeech=null,liveCamera=null,speechFinal='',lastQuestion='';
 const liveText=by('live-text'), liveCaption=by('live-caption');
 function stopLiveSpeech(){if(liveSpeech){const r=liveSpeech;liveSpeech=null;try{r.stop()}catch{}}by('live-mic').textContent='Start live captions';}
 function stopLiveCamera(){if(liveCamera){liveCamera.getTracks().forEach(t=>t.stop());liveCamera=null;}const v=by('live-camera');v.srcObject=null;}
 function liveRefresh(){
  if(currentView!=='live')return;
  const q=session?.current;const str=q?.text||'Create and start an interview from The brief first.';
  if(lastQuestion!==str){lastQuestion=str;by('live-question').textContent=str;if(q)liveText.value='';}
  by('live-source').textContent=q?`Practising: ${session?.plan?.competencies?.find(c=>c.id===q.competency_id)?.name||'Interview skills'}`:'No current interview turn.';
  by('live-status').textContent=session?`${session.status==='active'?'In progress':session.status==='completed'?'Completed':'Ready'} · ${session.plan?.role||'Interview practice'}`:'Create an interview from The brief to begin.';
 }
 by('live-read').onclick=()=>{if(session?.current)speak(session.current.text);else by('live-status').textContent='Begin an interview before using playback.'};
 by('live-interrupt').onclick=()=>{if('speechSynthesis'in window)speechSynthesis.cancel();by('live-caption').textContent='Playback interrupted.';};
 by('live-arena').onclick=()=>show('arena');
 by('open-live').onclick=()=>show('live');
 by('live-mic').onclick=()=>{
  if(liveSpeech){stopLiveSpeech();return;}
  if(!session?.current){liveCaption.textContent='Start an interview first.';return;}
  const Speech=window.SpeechRecognition||window.webkitSpeechRecognition;
  if(!Speech){liveCaption.textContent='Live captions are unavailable in this browser. Type your answer or use Practice room recording.';return;}
  if('speechSynthesis'in window)speechSynthesis.cancel();
  const r=new Speech();r.lang=session.setup?.language==='hi'?'hi-IN':'en-IN';r.continuous=true;r.interimResults=true;r.maxAlternatives=1;
  speechFinal=liveText.value.trim();liveSpeech=r;
  r.onresult=ev=>{let interim='';for(let i=ev.resultIndex;i<ev.results.length;i++){
    const value=ev.results[i][0].transcript;
    if(ev.results[i].isFinal)speechFinal+=(speechFinal?' ':'')+value.trim();else interim+=value;
  }liveText.value=(speechFinal+' '+interim).trim();liveCaption.textContent=interim?'Listening: '+interim:'Capturing speech. Review before sending.';};
  r.onerror=ev=>{liveCaption.textContent='Recognition unavailable: '+ev.error+'. Use typed input.';stopLiveSpeech()};
  r.onend=()=>{liveSpeech=null;by('live-mic').textContent='Start live captions';};
  try{r.start();by('live-mic').textContent='Stop live captions';liveCaption.textContent='Listening… Your browser may process microphone data through its speech service.';}
  catch(e){stopLiveSpeech();liveCaption.textContent=e.message;}
 };
 by('live-mic-stop').onclick=()=>{stopLiveSpeech();liveCaption.textContent='Microphone stopped. Review the text.'};
 by('live-submit').onclick=()=>{
  if(!session?.current){liveCaption.textContent='Start an interview first.';return;}
  if(liveSpeech){stopLiveSpeech();liveCaption.textContent='Microphone stopped. Review your final transcript, then submit again.';return;}
  if(!liveText.value.trim()){liveCaption.textContent='Enter an answer before sending.';return;}
  by('answer').value=liveText.value.trim();by('submit-answer').click();
  liveCaption.textContent='Answer sent. Your next question will appear after it is ready.';
 };
 by('live-camera-on').onclick=async()=>{try{
  if(liveCamera)return;if(!navigator.mediaDevices?.getUserMedia)throw Error('Camera capture unavailable.');
  liveCamera=await navigator.mediaDevices.getUserMedia({video:{width:{ideal:640},height:{ideal:480}},audio:false});by('live-camera').srcObject=liveCamera;
 }catch(e){stopLiveCamera();by('live-status').textContent='Camera could not be started. Check browser permissions and try again.';}};
 by('live-camera-off').onclick=stopLiveCamera;
 document.querySelectorAll('[data-view]').forEach(el=>el.addEventListener('click',()=>{if(el.dataset.view!=='live'){stopLiveSpeech();stopLiveCamera();}}));
 window.addEventListener('pagehide',()=>{stopLiveSpeech();stopLiveCamera();});
 setInterval(liveRefresh,900);

 // JOB MATCH: no auto-scored hiring claims, no persistence.
 by('match-copy').onclick=()=>{by('match-cv').value=by('cv').value;by('match-jd').value=by('jd').value;};
 by('match-form').onsubmit=ev=>{ev.preventDefault();runSafely(by('match-output'),async()=>{
  const cv=by('match-cv').value.trim(),jd=by('match-jd').value.trim();
  const result=await api('/api/intelligence/match',{method:'POST',body:{cv,jd}});
  const root=by('match-output');root.replaceChildren(tx('p',`${result.matched} of ${result.total} job requirements mentioned in your CV`,'intel-cap'));
  if(!result.items.length)root.append(tx('p','No controlled terms were detected. Add more explicit job requirements.'));
  result.items.forEach(item=>{
   const entry=tx('article',undefined,'intel-evidence-row');entry.append(tx('h3',item.requirement),tx('p','Job requirement · '+item.jd_excerpt,'intel-quote'));
   entry.append(tx('p',item.cv_excerpt?'CV evidence · '+item.cv_excerpt:'Not mentioned in the supplied CV',item.cv_excerpt?'intel-quote':'intel-muted'));
   entry.append(tx('small',item.verification));root.append(entry);
  });
  if(result.review_questions.length){const title=tx('h3','QUESTIONS TO PREPARE');root.append(title);result.review_questions.forEach(q=>root.append(tx('p',q,'intel-review-question')));}
  root.append(tx('p',result.limitations,'intel-muted'));
  (result.review_questions||[]).forEach(q=>{const b=btn('Save question to Question Bank',()=>runSafely(root,async()=>{await api('/api/question-bank',{method:'POST',body:{question:q,answer:'',competency:'CV job-match practice'}});b.disabled=true;b.textContent='Saved to your question bank';}));root.append(b);});
 });};

 // WHITEBOARD: SVG semantic nodes + PNG export with transient freehand overlay.
 const svgNS='http://www.w3.org/2000/svg';
 const svgNode=(tag,attrs)=>{const e=document.createElementNS(svgNS,tag);Object.entries(attrs).forEach(([k,v])=>e.setAttribute(k,String(v)));return e;};
 let nodes=[],edges=[],selected=[],dragId=null,pen=false,drawing=false,ix=0,iy=0;
 const graphic=by('board-graph'),ink=by('board-ink'),ctx=ink.getContext('2d');
 function coords(e){const r=graphic.getBoundingClientRect();return {x:Math.max(0,Math.min(1000,(e.clientX-r.left)/r.width*1000)),y:Math.max(0,Math.min(540,(e.clientY-r.top)/r.height*540))};}
 function drawBoard(){by('board-edges').replaceChildren();by('board-nodes').replaceChildren();
  edges.forEach(edge=>{const a=nodes.find(n=>n.id===edge.source),b=nodes.find(n=>n.id===edge.target);if(!a||!b)return;
   const line=svgNode('line',{x1:a.x,y1:a.y,x2:b.x,y2:b.y,stroke:'#858B67','stroke-width':2,'marker-end':'url(#board-arrow)'});by('board-edges').append(line);});
  nodes.forEach(n=>{const g=svgNode('g',{'data-id':n.id,tabindex:0,role:'button','aria-label':'Select or drag '+n.label});
   const rect=svgNode('rect',{x:n.x-80,y:n.y-23,width:160,height:46,rx:3,fill:selected.includes(n.id)?'#CDD6C2':'#F1EEE5',stroke:'#27332D','stroke-width':selected.includes(n.id)?3:1});
   const t=svgNode('text',{x:n.x,y:n.y+4,'text-anchor':'middle','font-family':'DM Sans, sans-serif','font-size':12,fill:'#27332D'});t.textContent=n.label.length>23?n.label.slice(0,21)+'…':n.label;
   g.append(rect,t);g.addEventListener('pointerdown',e=>{if(pen)return;e.preventDefault();if(!selected.includes(n.id))selected.push(n.id);selected=selected.slice(-2);dragId=n.id;drawBoard();});
   g.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();selected=[...selected,n.id].slice(-2);drawBoard();}});
   by('board-nodes').append(g);
  });
 }
 graphic.addEventListener('pointermove',e=>{if(!dragId)return;const n=nodes.find(n=>n.id===dragId);if(!n)return;const p=coords(e);n.x=Math.max(85,Math.min(915,p.x));n.y=Math.max(30,Math.min(510,p.y));drawBoard()});
 window.addEventListener('pointerup',()=>dragId=null);
 by('board-add').onclick=()=>{const label=by('board-label').value.trim();if(label.length<2){err(by('board-output'),'Enter a component label of at least 2 characters.');return;}if(nodes.length>=32){err(by('board-output'),'Maximum 32 nodes.');return;}const n={id:'n'+Date.now().toString(36)+nodes.length,label:label.slice(0,100),kind:'component',x:120+(nodes.length%5)*180,y:90+Math.floor(nodes.length/5)*75};nodes.push(n);selected=[n.id];by('board-label').value='';drawBoard();};
 by('board-connect').onclick=()=>{if(selected.length!==2){err(by('board-output'),'Select two different nodes on the canvas first.');return;}if(edges.length>=64){err(by('board-output'),'Maximum 64 connections.');return;}if(!edges.some(e=>e.source===selected[0]&&e.target===selected[1]))edges.push({source:selected[0],target:selected[1],label:''});selected=[];drawBoard();};
 by('board-clear').onclick=()=>{nodes=[];edges=[];selected=[];ctx.clearRect(0,0,ink.width,ink.height);drawBoard();by('board-output').replaceChildren();};
 by('board-pen').onclick=()=>{pen=!pen;ink.style.pointerEvents=pen?'auto':'none';by('board-pen').textContent=pen?'Stop pen':'Freehand pen';};
 function inkPoint(e){const r=ink.getBoundingClientRect();return {x:(e.clientX-r.left)/r.width*1000,y:(e.clientY-r.top)/r.height*540};}
 ink.addEventListener('pointerdown',e=>{if(!pen)return;drawing=true;ink.setPointerCapture(e.pointerId);const p=inkPoint(e);ix=p.x;iy=p.y;});
 ink.addEventListener('pointermove',e=>{if(!drawing)return;const p=inkPoint(e);ctx.strokeStyle='#27332D';ctx.lineWidth=2.5;ctx.lineCap='round';ctx.beginPath();ctx.moveTo(ix,iy);ctx.lineTo(p.x,p.y);ctx.stroke();ix=p.x;iy=p.y;});
 ink.addEventListener('pointerup',()=>drawing=false);
 function payload(){return {domain:by('board-domain').value,nodes,edges};}
 const renderBoardFeedback=result=>{const root=by('board-output');root.replaceChildren(tx('p',String(result.source||'diagram review').replaceAll('_',' ').toUpperCase(),'intel-cap'),tx('h2',result.question),tx('p',result.feedback));(result.observed_elements||[]).forEach(x=>root.append(tx('p','Included · '+x,'intel-quote')));root.append(tx('p',result.limitations,'intel-muted'));};
 by('board-review').onclick=()=>runSafely(by('board-output'),async()=>renderBoardFeedback(await api('/api/intelligence/whiteboard/review',{method:'POST',body:payload()})));
 by('board-ai').onclick=()=>runSafely(by('board-output'),async()=>{const result=await api('/api/intelligence/whiteboard/ai',{method:'POST',body:{...payload(),consent:by('board-consent').checked,model:'openai/gpt-oss-120b'}});renderBoardFeedback(result);});
 by('board-export').onclick=()=>{const raw=new XMLSerializer().serializeToString(graphic);const url='data:image/svg+xml;charset=utf-8,'+encodeURIComponent(raw);const img=new Image();img.onload=()=>{
  const c=document.createElement('canvas');c.width=1000;c.height=540;const dc=c.getContext('2d');dc.fillStyle='#E8EADC';dc.fillRect(0,0,1000,540);dc.drawImage(img,0,0);dc.drawImage(ink,0,0);
  c.toBlob(b=>{if(!b)return;const link=document.createElement('a');const u=URL.createObjectURL(b);link.href=u;link.download='auralis-whiteboard.png';link.click();setTimeout(()=>URL.revokeObjectURL(u),3000);},'image/png');};img.onerror=()=>{err(by('board-output'),'PNG export was blocked by your browser.');};img.src=url;};

 // EVIDENCE: all displayed citations anchored to actual saved answer turn IDs.
 async function refreshEvidenceChoices(){const select=by('evidence-session');const old=select.value;const sessions=await api('/api/sessions');select.replaceChildren(tx('option','Choose a completed interview'));select.firstChild.value='';(sessions||[]).filter(s=>s.status==='completed').forEach(s=>{const option=tx('option',`${s.role} · ${new Date(s.created_at*1000).toLocaleDateString()}`);option.value=s.id;select.append(option);});select.value=(old&&Array.from(select.options).some(o=>o.value===old))?old:((session?.status==='completed'&&session?.id)||'');}
 by('evidence-current').onclick=()=>runSafely(by('evidence-output'),async()=>{await refreshEvidenceChoices();if(session?.id)by('evidence-session').value=session.id;});
 by('evidence-session').addEventListener('focus',()=>runSafely(by('evidence-output'),refreshEvidenceChoices));
 document.querySelectorAll('[data-view="score-evidence"]').forEach(b=>b.addEventListener('click',()=>runSafely(by('evidence-output'),refreshEvidenceChoices)));
 async function loadEvidence(){const sid=by('evidence-session').value.trim();if(!sid)throw Error('Choose a completed interview to review its scores.');const report=await api('/api/intelligence/evidence/'+encodeURIComponent(sid));const root=by('evidence-output');root.replaceChildren(tx('p',report.role+' · '+report.items.length+' competency entries','intel-cap'));
  if(!report.items.length)root.append(tx('p','No scored assessment yet. Finish and assess your interview first.'));
  report.items.forEach(item=>{const entry=tx('article',undefined,'intel-evidence-row');entry.append(tx('h3',`${item.name||item.competency_id} · ${item.score===null||item.score===undefined?'UNSCORED':item.score+'/4'}`),tx('p',item.feedback||'No assessment feedback.'));
   entry.append(tx('p','To improve this score · '+item.score_gap,'intel-quote'));
   (item.criteria||[]).forEach(c=>entry.append(tx('small','Assessment criterion · '+c)));
   (item.citations||[]).forEach(c=>{const details=tx('details');details.append(tx('summary','Question · '+c.question),tx('blockquote',c.answer_excerpt));if(c.has_more)details.append(tx('p','Excerpt only. Review the complete replay for full context.','intel-muted'));entry.append(details);});
   const form=tx('form',undefined,'intel-dispute');const reason=tx('textarea');reason.required=true;reason.minLength=12;reason.maxLength=1200;reason.rows=2;reason.placeholder='Why does this score appear wrong? Cite the question or technical point.';
   const b=tx('button','Save private dispute note');b.type='submit';form.append(reason,b);form.onsubmit=e=>{e.preventDefault();runSafely(by('evidence-disputes'),async()=>{const d=await api('/api/intelligence/disputes/'+encodeURIComponent(sid),{method:'POST',body:{competency_id:item.competency_id,reason:reason.value}});reason.value='';await loadDisputes(sid);});};entry.append(form);root.append(entry);});
  root.append(tx('p',report.limitations,'intel-muted'));await loadDisputes(sid);
 }
 async function loadDisputes(sid){const res=await api('/api/intelligence/disputes/'+encodeURIComponent(sid));const root=by('evidence-disputes');root.replaceChildren(tx('h3','Saved review notes'));if(!res.notes.length)root.append(tx('p','No dispute notes recorded.','intel-muted'));res.notes.forEach(n=>root.append(tx('p',n.competency_id+': '+n.reason+' · Private note only','intel-quote')));}
 by('evidence-refresh').onclick=()=>runSafely(by('evidence-output'),loadEvidence);

 // Curated prereq map; practice outcome is self-report only.
 let mapData=null,activeTopic=null;
 async function loadMap(){const domain=by('knowledge-domain').value;mapData=await api('/api/intelligence/knowledge/'+domain);const root=by('knowledge-topics');root.replaceChildren();
  (mapData.assessment_signals||[]).forEach(signal=>root.append(tx('p',`Worth revisiting · ${signal.competency}: ${signal.score}/4 · provisional score`,'intel-quote')));
  mapData.topics.forEach((topic,i)=>{const entry=tx('article',undefined,'intel-topic');const num=tx('span',String(i+1).padStart(2,'0'),'intel-cap');const content=tx('div');content.append(tx('h3',topic.name),tx('p',topic.prerequisites.length?'PREREQUISITES / '+topic.prerequisites.map(id=>mapData.topics.find(n=>n.id===id)?.name||id).join(' · '):'FOUNDATION / NO PREREQUISITES','intel-muted'),tx('small',`${topic.attempts} practice record(s) · ${topic.latest.replaceAll('_',' ')}`));entry.append(num,content,btn('Practice ↗',()=>{activeTopic=topic;by('knowledge-question').replaceChildren(tx('p','PRACTICE QUESTION','intel-cap'),tx('h2',topic.question),tx('p','Explain your answer in a new scenario and check it against reliable course materials. Then record your own review.'));
   by('knowledge-question').append(btn('Needs more practice',()=>saveOutcome('needs_practice')),btn('I understand this',()=>saveOutcome('understood')));
   by('knowledge-question').scrollIntoView({block:'nearest',behavior:'smooth'});
  }));root.append(entry);});
 }
 async function saveOutcome(outcome){if(!activeTopic)return;await runSafely(by('knowledge-question'),async()=>{const r=await api('/api/intelligence/knowledge/practice',{method:'POST',body:{topic:activeTopic.id,domain:rDomain(),outcome}});mapData=r;await loadMap();by('knowledge-question').replaceChildren(tx('p','Practice marked '+outcome.replaceAll('_',' ')+'. No automatic mastery score was assigned.','intel-muted'));});}
 const rDomain=()=>by('knowledge-domain').value;
 by('knowledge-load').onclick=()=>runSafely(by('knowledge-topics'),loadMap);
 by('knowledge-domain').onchange=()=>{activeTopic=null;by('knowledge-question').replaceChildren();runSafely(by('knowledge-topics'),loadMap);};
 drawBoard();
})();
