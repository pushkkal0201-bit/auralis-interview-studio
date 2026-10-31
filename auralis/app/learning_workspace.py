"""Auralis 5.4: deterministic, owner-private practice planning.

The planner offers suggestions from stored evidence only; it never fabricates a grade
or interprets a completion checkbox as mastery. No LLM, network or scheduling daemon.
"""
from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from collections import defaultdict
from pydantic import BaseModel, Field, field_validator
from typing import Literal
from uuid import uuid4

from .learning import progress_from_sessions

Goal = Literal['balanced', 'interview', 'coding', 'engineering']
Status = Literal['planned', 'completed', 'skipped']

class PlanRequest(BaseModel):
    goal: Goal = 'balanced'
    days_per_week: int = Field(default=4, ge=2, le=7)
    minutes_per_day: int = Field(default=30, ge=15, le=120)
    start_date: date

    @field_validator('start_date')
    @classmethod
    def sensible_start_date(cls, value):
        today = datetime.now(timezone.utc).date()
        if value < today - timedelta(days=2) or value > today + timedelta(days=60):
            raise ValueError('Start within two days of today or the next 60 days.')
        return value

class TaskChange(BaseModel):
    status: Status


def priorities(sessions, practice):
    """Score-derived priorities are only suggestions, never verified skill judgments."""
    progress=progress_from_sessions(sessions)
    ranked=[]
    for skill in progress['skills']:
        if not skill['points']:
            continue
        item=skill['points'][-1]
        ranked.append({
            'id':skill['id'], 'name':skill['name'][:90],
            'score':skill['latest_score'],
            'score_change':skill['score_change'],
            'observations':skill['session_count'],
            'role':str(item.get('role','Interview'))[:90],
            'source':'ai_rubric',
            'reason':f"Last stored AI rubric score: {skill['latest_score']}/4. This is provisional practice feedback.",
        })
    ranked.sort(key=lambda r:(r['score'],r['name'].lower()))
    # Repeated wrong attempts are a signal for more practice, not a new grade.
    count=defaultdict(lambda:[0,0])
    for attempt in practice:
        if attempt.get('kind') not in ('coding','engineering'):continue
        key=(attempt['kind'],attempt.get('challenge_id',''))
        count[key][0]+=1
        count[key][1]+=int(attempt.get('passed',0)==attempt.get('total',-1) and attempt.get('total',0)>0)
    challenges=[]
    for (kind, name),(tries,perfect) in count.items():
        if perfect < tries:
            challenges.append({'kind':kind,'id':name[:70],'attempts':tries,'not_full':tries-perfect})
    challenges.sort(key=lambda c:(-c['not_full'],c['kind'],c['id']))
    return ranked[:6],challenges[:6],progress


def make_plan(pref:PlanRequest,sessions,practice):
    scored,missed,progress=priorities(sessions,practice)
    # Exact evidence references only, never pretend a task is personalized if no evidence.
    tasks=[]
    slots=[(i*7)//pref.days_per_week for i in range(pref.days_per_week)]
    kinds={
        'balanced':['review','coding','engineering','recall'],
        'interview':['review','recall','review','coding'],
        'coding':['coding','coding','review','recall'],
        'engineering':['engineering','engineering','review','recall'],
    }[pref.goal]
    for week in range(4):
        for day_index,offset in enumerate(slots):
            n=len(tasks)
            due=pref.start_date+timedelta(days=7*week+offset)
            kind=kinds[n%len(kinds)]
            source='baseline'
            if kind in ('review','recall'):
                if scored:
                    observation=scored[(week+day_index)%len(scored)]
                    name=observation['name']
                    label=('Repair reasoning: ' if kind=='review' else 'Fresh-question recall: ')+name
                    detail=('Review saved answer evidence, identify a missing step, then rewrite the answer.' if kind=='review' else 'Answer a NEW question in this competency without copying prior text; compare against the rubric afterward.')
                    source='stored_rubric_observation'
                else:
                    label='Practice one interview answer' if kind=='review' else 'Try a fresh role question'
                    detail='Prepare a short answer with assumptions, reasoning and a concrete example. This is a baseline suggestion; no graded skill evidence is available.'
            elif kind in ('coding','engineering'):
                matching=next((x for x in missed if x['kind']==kind),None)
                if matching:
                    label=('Retry coding exercise: ' if kind=='coding' else 'Recheck engineering case: ')+matching['id'].replace('_',' ')
                    detail='Redo the existing exercise without looking at earlier answers. A past attempt had incomplete test coverage; passing still does not prove mastery.'
                    source='practice_attempt'
                else:
                    label='Complete a Python test challenge' if kind=='coding' else 'Verify an engineering calculation'
                    detail=('Use the Practical Lab and inspect edge cases.' if kind=='coding' else 'Use the Engineering Casework or Calculation Lab; state units and assumptions.')
            tasks.append({
                'id':'task_'+uuid4().hex[:18], 'date':due.isoformat(), 'week':week+1,
                'kind':kind,'title':label[:130], 'description':detail[:400],
                'minutes':pref.minutes_per_day, 'status':'planned','completed_at':None,
                'source':source,
            })
    plan={
        'id':'plan_'+uuid4().hex[:20], 'created_at':datetime.now(timezone.utc).isoformat(),
        'goal':pref.goal,'start_date':pref.start_date.isoformat(),
        'days_per_week':pref.days_per_week,'minutes_per_day':pref.minutes_per_day,
        'duration_weeks':4,'tasks':tasks,'revision':0,
        'provenance':{
            'scored_competencies_used':len(scored),
            'incomplete_practice_exercises_used':len(missed),
            'personalized':bool(scored or missed),
            'note':('Some activities reference existing stored rubric/attempt data.' if scored or missed else 'No scored evidence is available. Activities are generic starting suggestions.'),
        },
    }
    return plan


def summarise(plan, sessions, practice):
    skills,missed,progress=priorities(sessions,practice)
    tasks=plan.get('tasks',[]) if plan else []
    completed=[t for t in tasks if t['status']=='completed']
    skipped=sum(t['status']=='skipped' for t in tasks)
    active=sorted({t.get('completed_at','')[:10] for t in completed if t.get('completed_at')})
    streak=0
    if active:
        last=date.fromisoformat(active[-1]);dates={date.fromisoformat(d) for d in active}
        # Count consecutive completion days ending on latest activity, not a promise
        while last in dates:
            streak+=1;last-=timedelta(days=1)
    return {
        'plan':plan,
        'overview':{
            'planned':len(tasks),'completed':len(completed),'skipped':skipped,
            'completed_minutes':sum(t['minutes'] for t in completed),
            'completion_percent':round(100*len(completed)/len(tasks),1) if tasks else 0,
            'last_activity_streak_days':streak,
            'total_interviews':progress['session_count'],
            'completed_interviews':progress['completed_count'],
            'scored_observations':progress['scored_competency_observations'],
            'practical_attempts':len(practice),
        },
        'priority_skills':skills,
        'practice_gaps':missed,
        'limitations':[
            'Plan completion is self-reported and is not a verified demonstration of skill.',
            'AI rubric scores are provisional, may be wrong, and are not directly comparable between different roles.',
            'Practice attempts are limited to the latest 100 stored items. No raw candidate code or answer text is stored in this workspace.',
            'The calendar is local only: no background reminders, Google Calendar integration or notifications are sent.',
        ],
    }


def calendar_ics(plan):
    """Generate a bounded portable all-day calendar, without candidate CVs or scores."""
    if not plan:return ''
    lines=['BEGIN:VCALENDAR','VERSION:2.0','PRODID:-//Auralis//Learning Workspace 5.4//EN','CALSCALE:GREGORIAN','METHOD:PUBLISH']
    def clean(s):return str(s).replace('\\','\\\\').replace(';','\\;').replace(',','\\,').replace('\n','\\n').replace('\r','')
    for t in plan['tasks']:
        day=date.fromisoformat(t['date'])
        lines += ['BEGIN:VEVENT',f"UID:{t['id']}@auralis.local",'DTSTAMP:'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ'),
                  'DTSTART;VALUE=DATE:'+day.strftime('%Y%m%d'),
                  'DTEND;VALUE=DATE:'+(day+timedelta(days=1)).strftime('%Y%m%d'),
                  'SUMMARY:'+clean(t['title']),'DESCRIPTION:'+clean(f"{t['minutes']} minute practice. {t['description']}"),'END:VEVENT']
    return '\r\n'.join(lines+['END:VCALENDAR',''])


def private_summary(plan,sessions,practice):
    """An intentionally small user-initiated export, without CVs, transcripts or code."""
    data=summarise(plan,sessions,practice)
    return {
        'product':'Auralis 5.4',
        'generated_at':datetime.now(timezone.utc).isoformat(),
        'practice_metrics':data['overview'],
        'graded_observations':data['priority_skills'],
        'practical_gaps':data['practice_gaps'],
        'current_plan':{
            'goal':plan['goal'],
            'days_per_week':plan['days_per_week'],
            'minutes_per_day':plan['minutes_per_day'],
            'start_date':plan['start_date'],
            'task_count':len(plan['tasks']),
            'completed_tasks':sum(t['status']=='completed' for t in plan['tasks']),
        } if plan else None,
        'limitations':data['limitations'],
        'privacy':'Candidate CVs, job descriptions, transcripts, answer text and submitted source code are excluded.',
    }
