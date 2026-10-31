'use strict';
/* Auralis 5.4 workspace. Uses existing owner-token API client, no third-party UI libs. */
let workspaceState = null;
let workspaceWeek = 1;
const workspaceText=(tag,text,cls)=>{const n=document.createElement(tag);if(text!==undefined)n.textContent=text;if(cls)n.className=cls;return n;};
function workspaceLocalDate(){const d=new Date();return [d.getFullYear(),String(d.getMonth()+1).padStart(2,'0'),String(d.getDate()).padStart(2,'0')].join('-');}
$('workspace-start').value=workspaceLocalDate();
function workspaceRender(data){
  workspaceState=data;
  const root=$('workspace-metrics');root.replaceChildren();
  [['Interviews',data.overview.completed_interviews],['Practical attempts',data.overview.practical_attempts],['Planned sessions',data.overview.planned],['Completed',data.overview.completed]].forEach(([heading,count])=>{
    const item=workspaceText('div',undefined,'workspace-metric');item.append(workspaceText('strong',String(count)),workspaceText('span',heading));root.append(item);
  });
  const priorities=$('workspace-priorities');priorities.replaceChildren();
  if(!data.priority_skills.length&&!data.practice_gaps.length){
    priorities.append(workspaceText('p','No scored evidence yet. Start with a baseline plan, then complete a live assessed interview or practical exercise. Demo results are not treated as grades.','workspace-evidence-note'));
  }else{
    data.priority_skills.slice(0,4).forEach((v,i)=>{
      const item=workspaceText('div',undefined,'workspace-evidence-row');
      const left=workspaceText('div');left.append(workspaceText('small','STORED AI RUBRIC / '+String(i+1).padStart(2,'0')),workspaceText('strong',v.name));
      item.append(left,workspaceText('span',`${v.score}/4${v.score_change===null?'':(' · Δ '+(v.score_change>0?'+':'')+v.score_change)}`));priorities.append(item);
    });
    data.practice_gaps.slice(0,3).forEach(v=>{
      const item=workspaceText('div',undefined,'workspace-evidence-row');const left=workspaceText('div');left.append(workspaceText('small','INCOMPLETE PRACTICE TESTS'),workspaceText('strong',v.id.replaceAll('_',' ')));item.append(left,workspaceText('span',`${v.not_full} incomplete`));priorities.append(item);
    });
  }
  const p=data.plan;
  $('workspace-calendar-export').disabled=!p;
  $('workspace-clear').disabled=!p;
  const weeks=$('workspace-weeks');weeks.replaceChildren();
  if(p){
    for(let w=1;w<=4;w++){
      const button=workspaceText('button',`WEEK ${String(w).padStart(2,'0')}`,'workspace-week'+(w===workspaceWeek?' selected':''));
      button.type='button';button.setAttribute('aria-pressed',String(workspaceWeek===w));
      button.onclick=()=>{workspaceWeek=w;workspaceRender(workspaceState);};weeks.append(button);
    }
  }
  const list=$('workspace-task-list');list.replaceChildren();
  if(!p){list.append(workspaceText('p','Create a schedule to see your practice sessions here.','workspace-empty'));}
  else{
    const count= p.tasks.filter(t=>t.week===workspaceWeek&&t.status==='completed').length;
    list.append(workspaceText('p',`${count} of ${p.tasks.filter(t=>t.week===workspaceWeek).length} marked complete · ${p.days_per_week} practice days per week · ${p.minutes_per_day} min each`,'workspace-week-caption'));
    p.tasks.filter(t=>t.week===workspaceWeek).forEach((t,i)=>{
      const row=workspaceText('article',undefined,'workspace-task'+(t.status==='completed'?' complete':''));
      const date=workspaceText('time',new Date(t.date+'T12:00:00').toLocaleDateString(undefined,{weekday:'short',month:'short',day:'numeric'}));date.dateTime=t.date;
      const title=workspaceText('h3',t.title);const content=workspaceText('div',undefined,'workspace-task-copy');
      content.append(workspaceText('small',`${t.kind.toUpperCase()} · ${t.minutes} MIN · ${t.source.replaceAll('_',' ')}`),title,workspaceText('p',t.description));
      const controls=workspaceText('div',undefined,'workspace-task-controls');
      const select=workspaceText('select');select.setAttribute('aria-label',`Status for ${t.title}`);
      [['planned','Planned'],['completed','Completed'],['skipped','Skipped']].forEach(([value,label])=>{const option=workspaceText('option',label);option.value=value;select.append(option);});
      select.value=t.status;
      select.onchange=()=>run(async()=>{const updated=await api(`/api/workspace/plans/${encodeURIComponent(p.id)}/tasks/${encodeURIComponent(t.id)}`,{method:'PATCH',body:{status:select.value}});workspaceRender(updated);});
      controls.append(select);row.append(date,content,controls);list.append(row);
    });
    list.append(workspaceText('p',`${data.overview.completed_minutes} self-reported practice minutes across this plan. A completed checkbox does not raise your Skill DNA score.`,'workspace-postscript'));
  }
  const lim=$('workspace-limitations');lim.textContent=data.limitations.join(' ');
  $('workspace-plan-hint').textContent=p?`Current plan started ${p.start_date}. ${p.provenance.note} Creating another plan replaces these checkboxes, not your saved interviews.`:'Creating a plan generates a private calendar. You can replace or delete the schedule at any time.';
}
async function workspaceLoad(){workspaceRender(await api('/api/workspace'));}
$('workspace-form').onsubmit=e=>{e.preventDefault();run(async()=>{
  if(workspaceState?.plan&&!confirm('Replace the current plan and its completion checkboxes? Saved interviews and practical results will stay.'))return;
  const data=await api('/api/workspace/plan',{method:'POST',body:{goal:$('workspace-goal').value,days_per_week:Number($('workspace-days').value),minutes_per_day:Number($('workspace-minutes').value),start_date:$('workspace-start').value}});
  workspaceWeek=1;workspaceRender(data);
 });};
$('workspace-clear').onclick=()=>{if(!confirm('Delete your current study plan and completed checkboxes? Interview and practical history will remain.'))return;run(async()=>{await api('/api/workspace/plan',{method:'DELETE'});workspaceWeek=1;await workspaceLoad();});};
$('workspace-calendar-export').onclick=()=>run(async()=>{
  const response=await fetch('/api/workspace/calendar.ics',{headers:authHeader()});
  if(!response.ok)throw Error('Calendar export failed. Reopen the workspace and try again.');
  const blob=await response.blob();const url=URL.createObjectURL(blob);const a=document.createElement('a');a.href=url;a.download='auralis-practice.ics';document.body.append(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),1000);
});
document.querySelector('.nav[data-view="workspace"]').addEventListener('click',()=>run(workspaceLoad));

$('workspace-summary-export').onclick=()=>run(async()=>{
  const response=await fetch('/api/workspace/summary.json',{headers:authHeader()});
  if(!response.ok)throw Error('Could not export progress.');
  const blob=await response.blob();const url=URL.createObjectURL(blob);const a=document.createElement('a');a.href=url;a.download='auralis-private-progress.json';document.body.append(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),1000);
});
