'use strict';
// This file deliberately uses Auralis's existing owner-scoped api() and run() helpers.
// DOM-only rendering: untrusted text is rendered through textContent only.
let practicalCatalog=null;
const practicalText=(tag,content,className)=>{const node=document.createElement(tag);if(content!==undefined)node.textContent=String(content);if(className)node.className=className;return node;};
const practicalClear=id=>$(id).replaceChildren();
function practicalSwitch(to){
 const code=to==='code';
 $('practical-code-panel').hidden=!code;
 $('practical-engineering-panel').hidden=code;
 $('practical-tab-code').classList.toggle('selected',code);
 $('practical-tab-engineering').classList.toggle('selected',!code);
 $('practical-tab-code').setAttribute('aria-pressed',String(code));
 $('practical-tab-engineering').setAttribute('aria-pressed',String(!code));
}
function practicalDescription(){
 if(!practicalCatalog)return;
 const c=practicalCatalog.challenges.find(v=>v.id===$('practical-challenge').value);
 if(!c)return;
 $('practical-code-title').textContent=c.title;
 $('practical-code-description').textContent=c.description;
 $('practical-source').value=c.starter;
 $('practical-hint').textContent=c.hint;
 const root=$('practical-examples');root.replaceChildren(practicalText('p','PUBLIC EXAMPLES','section-index'));
 c.examples.forEach(v=>{
   const n=practicalText('p',`Input ${JSON.stringify(v.input)}  →  ${JSON.stringify(v.expected)}`,'practical-example');root.append(n);
 });
 $('practical-code-result').replaceChildren(practicalText('h2','Ready for a test.'),practicalText('p','Submit a return expression and inspect both the example tests and hidden edge cases.'));
}
function practicalEngineeringDescription(){
 if(!practicalCatalog)return;
 const c=practicalCatalog.engineering_cases.find(v=>v.id===$('practical-engineering-case').value);
 if(!c)return;
 $('practical-engineering-title').textContent=c.title;
 $('practical-engineering-description').textContent=c.scenario;
 $('practical-claimed').value='';
 $('practical-engineering-result').replaceChildren(practicalText('h2','Ready to verify.'),practicalText('p','Enter a result with the stated units.'));
}
async function practicalLoad(){
 if(!practicalCatalog){
   practicalCatalog=await api('/api/practical/catalog');
   const c=$('practical-challenge'),e=$('practical-engineering-case');
   c.replaceChildren(...practicalCatalog.challenges.map(x=>{const n=practicalText('option',x.title);n.value=x.id;return n;}));
   e.replaceChildren(...practicalCatalog.engineering_cases.map(x=>{const n=practicalText('option',x.title);n.value=x.id;return n;}));
   practicalDescription();practicalEngineeringDescription();
 }
 await practicalHistory();
}
async function practicalHistory(){
 const result=await api('/api/practical/history');
 const root=$('practical-history-list');root.replaceChildren();
 if(!result.attempts?.length){root.append(practicalText('p','No attempts recorded. Your first result will appear here.'));return;}
 result.attempts.slice(0,12).forEach(item=>{
   const n=practicalText('div',undefined,'practical-history-row');
   n.append(practicalText('span',item.kind==='coding'?'PYTHON':'ENGINEERING','practical-history-kind'),
       practicalText('strong',item.challenge_id.replaceAll('_',' ')),
       practicalText('span',`${item.passed} / ${item.total} verified`),
       practicalText('time',new Date(item.created_at*1000).toLocaleDateString()));
   root.append(n);
 });
}
async function practicalRunCode(){
 const result=await api('/api/practical/code',{method:'POST',body:{challenge_id:$('practical-challenge').value,code:$('practical-source').value}});
 const root=$('practical-code-result');root.replaceChildren();
 root.append(practicalText('h2',`${result.passed} / ${result.total} tests passed.`),
             practicalText('p',result.all_passed?'All provided test cases passed.':'Review the cases below and revise your function.'));
 const list=practicalText('div',undefined,'practical-tests');
 result.tests.forEach(t=>{
   const n=practicalText('div',undefined,'practical-test');
   n.append(practicalText('span',`TEST ${String(t.test).padStart(2,'0')} / ${t.public?'EXAMPLE':'EDGE CASE'}`,'section-index'),
     practicalText('strong',t.status==='pass'?'PASS':t.status==='fail'?'NOT YET':'UNSUPPORTED','practical-test-'+t.status));
   if(t.public){n.append(practicalText('p',`Expected: ${JSON.stringify(t.expected)} · Received: ${JSON.stringify(t.actual)}`));}
   if(t.message){n.append(practicalText('p',t.message));}
   list.append(n);
 });
 root.append(list,practicalText('p',result.limitations,'hint'));
 await practicalHistory();
}
async function practicalRunEngineering(){
 const raw=$('practical-claimed').value;
 if(raw.trim()==='')throw Error('Enter a numerical result before verifying the scenario.');
 const result=await api('/api/practical/engineering',{method:'POST',body:{case_id:$('practical-engineering-case').value,claimed_result:Number(raw),reasoning:$('practical-reasoning').value}});
 const root=$('practical-engineering-result');root.replaceChildren();
 root.append(practicalText('h2',result.arithmetic_check==='within_1_percent'?'Arithmetic matches.':'Check the calculation.'),
    practicalText('p',`Reference: ${result.expected} ${result.unit}`,'practical-figure'),
    practicalText('p',`Submitted: ${result.claimed_result} ${result.unit} · Relative difference ${result.relative_error_percent}%`),
    practicalText('p',result.formula,'practical-math'),
    practicalText('h3','Assumptions to inspect'),practicalText('p',result.assumptions),
    practicalText('p',result.reasoning_status==='ungraded_manual_review'?'Your reasoning remains ungraded and is not saved.':'No reasoning submitted.','hint'),
    practicalText('p',result.limitations,'hint'));
 await practicalHistory();
}
$('practical-tab-code').onclick=()=>practicalSwitch('code');
$('practical-tab-engineering').onclick=()=>practicalSwitch('engineering');
$('practical-challenge').onchange=practicalDescription;
$('practical-engineering-case').onchange=practicalEngineeringDescription;
$('practical-reset').onclick=practicalDescription;
$('practical-run').onclick=()=>run(practicalRunCode);
$('practical-engineering-run').onclick=()=>run(practicalRunEngineering);
document.querySelector('.nav[data-view="practical"]').addEventListener('click',()=>run(practicalLoad));
