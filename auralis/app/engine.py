"""Interview state machine. Mutations commit only after validation succeeds."""
import copy
import asyncio
import time
import os
import uuid
from fastapi import HTTPException
from .schemas import Plan, Decision, Report, RetryQuestion, RetryFeedback
from .provider import ProviderError
from .incidents import scenario_for_incident
from .assessment_integrity import build_assessment_turns,short_evidence,contradicted_electrical_criticism,contradicted_power_factor_criticism
from .offline_plan import local_plan
from .usage_budget import UsageBudget
from .audit import provider_failure_code, fallback_record, claim_provenance, score_gap_note, cautious_claim_language
from .interview_realism import interview_guidance,delivery_observation,delivery_summary
from .policy import (target_competency, is_repeated, rubric_fallback,
                     coverage_summary, MIN_SECONDS_FOR_NEW_QUESTION)


def uid(prefix):return prefix+'_'+uuid.uuid4().hex

def grounded_plan(plan,cv):
    p=plan.model_dump()
    p['claims']=[v for v in p['claims'] if v['quote'] in cv]
    return p

def validate_report(report, s):
    """Reject invented citations and inconsistent AI scoring; never infer grades locally."""
    r = report.model_dump()
    comps = {c['id']:c for c in s['plan']['competencies']}
    if {i['competency_id'] for i in r['items']} != set(comps) or len(r['items']) != len(comps):
        raise ProviderError('Assessment did not cover the agreed rubric. Retry the report.')
    answers = {t['id']:t for t in s['turns'] if t['kind']=='answer'}
    for item in r['items']:
        valid = []
        for tid in dict.fromkeys(item['evidence_ids']):
            t = answers.get(tid)
            if not t or t['question']['competency_id'] != item['competency_id']:
                raise ProviderError('Assessment referenced unsupported evidence. Retry the report.')
            valid.append({'turn_id':tid,'quote':short_evidence(t['text']),'question':t['question']['text'],'full_answer_in_replay':True})
        item['evidence'] = valid
        item['name'] = comps[item['competency_id']]['name']
        actual = [t for t in answers.values() if t['question']['competency_id']==item['competency_id']]
        if not actual:
            item.update(status='not_assessed',score=None,confidence='low',
                        feedback='No submitted answer evidence for this competency.',evidence=[])
        elif s['setup']['provider']=='demo':
            item['score']=None
        else:
            status,score=item['status'],item['score']
            if status in ('not_assessed','not_scored_provider_unavailable'):
                raise ProviderError('Assessment treated answered questions as unassessed. Retry the report.')
            if status=='incorrect_reasoning' and score!=0:
                raise ProviderError('Assessment must score demonstrated incorrect reasoning as 0/4.')
            if status=='partially_demonstrated' and score not in (1,2):
                raise ProviderError('Assessment partial-score rubric is inconsistent.')
            if status=='demonstrated' and score not in (3,4):
                raise ProviderError('Assessment demonstrated-score rubric is inconsistent.')
            if status=='insufficient_evidence' and score is not None:
                raise ProviderError('Insufficient evidence must be unscored.')
            if status=='insufficient_evidence' and len(actual)>=2 and any(
                    token in item['feedback'].lower() for token in
                    ('incorrect', 'misunderstand', 'fundamental error', 'factually wrong',
                     'false claim', 'wrong approach', 'incorrectly', 'misconception')):
                raise ProviderError('Report incorrectly treats evidenced technical errors as insufficient evidence. Retry scoring.')
            if status!='insufficient_evidence' and not valid:
                raise ProviderError('A numerical assessment requires exact answer evidence.')
        if item['score']==0 and item.get('latest_score') is not None and item['latest_score']>=3:
            raise ProviderError('Assessment contradicts its own later-answer improvement score. Review and retry.')
        if item['score']==0 and contradicted_electrical_criticism(item,[t['text'] for t in actual]):
            raise ProviderError('Numerical claims contradict a deterministic three-phase calculation check. Review and retry.')
        if item['score']==0 and contradicted_power_factor_criticism(item,[t['text'] for t in actual]):
            raise ProviderError('A later answer correctly states the power triangle; a blanket 0/4 requires a new assessment.')
        if item['score']==0 and len(actual)>=2 and s['setup']['provider']!='demo':
            if item.get('initial_score') is None or item.get('latest_score') is None:
                raise ProviderError('Assessment of multiple responses requires separate initial/latest evidence scores.')

        if item['status'] in ('not_assessed','insufficient_evidence','not_scored_provider_unavailable'):
            item['score']=None
        item['feedback'] = cautious_claim_language(item['feedback'])
        item['practice'] = cautious_claim_language(item['practice'])
        item['score_gap'] = score_gap_note(item)
    r['summary']=cautious_claim_language(r['summary'])
    r['demo']=s['setup']['provider']=='demo'
    r['ai_provider']=s['setup']['provider']
    r['ai_model']=s['setup'].get('ai_model') if not r['demo'] else 'scripted-demo'
    r['evidence_policy']='Chronological, sampled excerpts for long answers; full text retained in replay. Scores are provisional practice judgments.'
    r['generated_at']=time.time()
    r['claim_provenance']=claim_provenance(s['setup'])
    r['question_sources']=[{'turn_id':t['id'], 'question_id':t['question']['id'],
                            'source':t['question'].get('source','unknown'),
                            'competency_id':t['question']['competency_id'],
                            'revisit':t['question'].get('revisit',False)}
                           for t in s['turns'] if t['kind']=='answer']
    r['rubric']=s['plan']['competencies']
    r['coverage']=coverage_summary(s)
    r['delivery_summary']=delivery_summary(s['turns'])
    r['provisional']=False
    r['fallback_events']=copy.deepcopy(s.get('fallback_events',[]))
    return r


def local_unscored_report(s, cause):
    """Explicit provider-outage continuity, never fabricated model assessment."""
    items=[]
    for c in s['plan']['competencies']:
        evidence=[{'turn_id':t['id'],'quote':short_evidence(t['text']),'question':t['question']['text'],'full_answer_in_replay':True}
                  for t in s['turns'] if t['kind']=='answer' and t['question']['competency_id']==c['id']]
        items.append({'competency_id':c['id'],'name':c['name'],
                      'status':'not_scored_provider_unavailable' if evidence else 'not_assessed',
                      'score':None,'confidence':'low',
                      'feedback':('Answers are saved, but AI grading was unavailable. No competence judgement is made.'
                                  if evidence else 'No answer was collected for this competency.'),
                      'evidence_ids':[e['turn_id'] for e in evidence][:8],
                      'evidence':evidence[:8],
                      'practice':'Review the competency criteria and retry AI assessment when service is available.',
                      'score_gap':'No AI score was assigned.'})
    return {'summary':'PROVISIONAL OFFLINE REPORT: Interview answers were saved, but the live assessment '
                      'could not be verified. Scores are intentionally withheld.',
            'items':items,'limitations':['A provider or validation error prevented model assessment.',
            'This is a local evidence inventory, not an AI evaluation.',
            'Use Retry AI assessment when connectivity or quota is restored.'],
            'demo':False,'generated_at':time.time(),'rubric':s['plan']['competencies'],
            'coverage':coverage_summary(s),'provisional':True,
            'ai_provider':s['setup']['provider'],'ai_model':s['setup'].get('ai_model'),
            'evidence_policy':'Saved in full; unscored because the model or validation was unavailable.',
            'fallback_cause':cause,'fallback_events':copy.deepcopy(s.get('fallback_events',[])),
            'claim_provenance':claim_provenance(s['setup']),
            'delivery_summary':delivery_summary(s['turns']),
            'question_sources':[{'turn_id':t['id'],'question_id':t['question']['id'],
                                 'source':t['question'].get('source','unknown'),
                                 'competency_id':t['question']['competency_id']}
                                for t in s['turns'] if t['kind']=='answer']}

class Engine:
    def __init__(self,store,demo,live,hf=None,strict_live=False):
        self.store=store;self.demo=demo;self.live=live;self.hf=hf;self.strict_live=strict_live
        self.usage_budget=UsageBudget(store.path if strict_live else None)
    def provider(self,kind):
        if kind=='demo':return self.demo
        if kind=='groq':return self.live
        if kind=='huggingface' and self.hf is not None:return self.hf
        raise ProviderError('AI provider is not configured.',503)
    async def generate_for(self,setup,task,context,schema,quota_owner=None):
        # Keep model selection session-scoped. Never mutate a shared provider's model
        # while another interview is in progress.
        if setup.get('provider') in ('groq','huggingface'):
            self.usage_budget.consume(quota_owner)
            context={**context,'ai_model':setup.get('ai_model','openai/gpt-oss-20b')}
        return await self.provider(setup['provider']).generate(task,context,schema)
    def load(self,sid,owner):
        s=self.store.load(sid,owner)
        if not s:raise HTTPException(404,'Interview not found in this browser workspace.')
        return s
    async def prepare(self,setup,owner):
        data=setup.model_dump()
        fallbacks=[]
        try:
            p=await self.generate_for(data,'plan',data,Plan,quota_owner=owner)
            plan=grounded_plan(p,data['cv'])
            plan_source='scripted_demo' if data['provider']=='demo' else 'live_ai'
        except ProviderError as exc:
            if data['provider']=='demo' or self.strict_live:raise
            plan=local_plan(data).model_dump()
            plan_source='local_rubric_fallback'
            fallbacks=[{'at':time.time(), **fallback_record('plan','Live plan generation unavailable; local job-derived plan was used.',code=provider_failure_code(exc))}]
        if data.get('incident_id'):plan['scenario']=scenario_for_incident(data['incident_id'])
        s={'id':uid('session'),'revision':0,'created_at':time.time(),'status':'ready','setup':data,'plan':plan,'turns':[],'current':None,'started_at':None,'deadline':None,'report':None,'retry':None,'retry_history':[],'request_ids':[],'branch_events':[],'last_reply':'','hint_count':0,'fallback_events':fallbacks,'plan_source':plan_source}
        self.store.create(s,owner);return s
    def context(self,s,assessment=False):
        if s['setup']['provider']=='demo':return copy.deepcopy(s)
        # Budget is across ALL answer turns, not the first 900 characters each.
        # Include beginning, numerical/method passages, and conclusion; mark excerpts.
        if assessment:
            turns=build_assessment_turns(s['turns'])
        else:
            turns=[]
            for t in s['turns'][-6:]:
                turns.append({'id':t['id'],'kind':t['kind'],'text':t['text'][:1600],
                              'excerpted':len(t['text'])>1600,
                              'question':{'text':t['question']['text'][:350],
                                          'competency_id':t['question']['competency_id']}})
        return {'plan':s['plan'],'turns':turns,'branch_events':s['branch_events'],
                'language':s['setup']['language'],'mode':s['setup']['mode'],
                'interview_guidance':interview_guidance(s['setup']),
                'remaining_seconds':max(0,int((s.get('deadline') or time.time())-time.time())),
                'coverage':{c['id']:sum(t['kind']=='answer' and t['question']['competency_id']==c['id'] for t in s['turns']) for c in s['plan']['competencies']},
                'project_evidence':s['setup']['project_evidence'][:3200] if not assessment else '',
                'codeproof_refs':[{k:r.get(k) for k in ('id','path','symbol','line_start','line_end','indicators')} for r in s['setup'].get('codeproof_refs',[])[:8]] if not assessment and s['setup'].get('codeproof_source_verified') else [],
                'selected_incident':s['setup'].get('incident_id','') if not assessment else '',
                'instruction':('Some long answers include explicitly marked excerpts from beginning, middle and end. '
                               'Judge only visible evidence; distinguish a candidate correcting an initial mistake '
                               'from persisting with it. No hallucinated calculations or missing evidence.')}
    async def question(self,s,owner=None):
        remaining=max(0,int((s.get('deadline') or (time.time()+s['setup']['duration_minutes']*60))-time.time()))
        target=target_competency(s,remaining)
        context=self.context(s)
        context['mandatory_competency_id']=target
        context['interview_guidance']=interview_guidance(s['setup'])
        context['controller_policy']='You MUST ask about mandatory_competency_id. Rotate to other skills after at most two answered attempts. Do not rephrase previous questions.'
        context['previous_questions']=[t['question']['text'][:250] for t in s['turns'][-8:]]
        d=None
        reason=''
        failure_code='provider_or_validation_error'
        attempts=0
        rejected_repetitions=0
        for attempt in range(2):
            attempts+=1
            try:
                candidate=(await self.generate_for(s['setup'],'question',context,Decision,quota_owner=owner)).model_dump()
            except ProviderError as e:
                if s['setup']['provider']=='demo' or self.strict_live:raise
                failure_code=provider_failure_code(e)
                reason='Live question generation unavailable. Provider retry remains possible.'
                # Only retry a transient server error; never burn credits on an
                # authentication error or rate limit. No secrets are logged.
                if failure_code in ('provider_or_transport_unavailable','timeout') and attempt==0:
                    await asyncio.sleep(0.15)
                    continue
                break
            duplicate=is_repeated(candidate['question'],s,target)
            if candidate['competency_id']==target and not duplicate:
                d=candidate
                break
            rejected_repetitions+=int(duplicate)
            failure_code='question_repeated' if duplicate else 'wrong_competency'
            reason='Model question violated coverage or repetition rules.'
            context['controller_policy']='REPAIR: Last generated question was rejected. EXACT mandatory_competency_id='+target+'; require a NEW applied task, NOT a paraphrase.'
        if d is None and self.strict_live:
            raise ProviderError('Could not generate a valid new live question. Please retry.',503)
        if d is None:
            d=rubric_fallback(s,target,reason or 'Controller could not obtain a valid model question.')
            d['source']='local_rubric_fallback'
            s.setdefault('fallback_events',[]).append({'at':time.time(), **fallback_record(
                'question',reason or 'Model output invalid',target,attempts,failure_code)})
        else:
            d['source']='scripted_demo' if s['setup']['provider']=='demo' else 'live_ai'
        if d['source'] in ('scripted_demo','local_rubric_fallback'):
            track=s['setup'].get('interview_track','technical')
            if track=='behavioral':
                d['question']+=' Describe a specific situation, your actions, the result, and what you learned.'
            elif track=='case_study':
                d['question']+=' State your assumptions, compare two options, and describe how you would test the decision.'
            elif track=='pressure':
                d['question']+=' Give your priority decision first, then one key risk and mitigation.'
            elif track=='revision':
                d['question']+=' Show how you would transfer the idea to a different scenario, not simply repeat a memorized answer.'
            d['question']=d['question'][:900]
        d['generation_attempts']=attempts
        d['repeat_rejections']=rejected_repetitions
        count_for_target=sum(t['kind']=='answer' and t['question']['competency_id']==target for t in s['turns'])
        all_covered=all(any(t['kind']=='answer' and t['question']['competency_id']==c['id'] for t in s['turns']) for c in s['plan']['competencies'])
        d['revisit']=bool(all_covered and count_for_target>0)
        if d['revisit']:d['decision_action']='REVISIT'
        d['selection_reason']=('Competency coverage is complete; this question revisits '+target+
                               ' to check improvement or application in a new setting.' if d['revisit']
                               else 'Coverage controller selected '+target+' to develop or verify the planned skill.')
        branches={b['id']:b for b in s['plan']['scenario']['branches']}
        if d['branch_id'] and d['branch_id'] not in branches:
            d['branch_id']=''
        if d['branch_id'] and d['branch_id'] not in [e['id'] for e in s['branch_events']]:
            s['branch_events'].append(branches[d['branch_id']])
        if s['setup']['mode']=='interview':d['coaching']=''
        available={r.get('id'):r for r in s['setup'].get('codeproof_refs',[]) if isinstance(r,dict)} if s['setup'].get('codeproof_source_verified') else {}
        cited=available.get(d.get('source_ref_id',''))
        if d.get('source_ref_id') and not cited:d['source_ref_id']=''
        previous=next((t for t in reversed(s['turns']) if t['kind']=='answer'),None)
        count_so_far=sum(t['kind']=='answer' and t['question']['competency_id']==target for t in s['turns'])
        criterion=next(c for c in s['plan']['competencies'] if c['id']==target)['criteria'][0]
        verified_reason=(f'Coverage controller selected {target} ({next(c["name"] for c in s["plan"]["competencies"] if c["id"]==target)}). '
                         f'This competency had {count_so_far} prior recorded answer(s). '
                         f'Assessment criterion: {criterion}. '+d['selection_reason'])
        d['why']=verified_reason
        d['difficulty_reason']='Question difficulty is model-generated or from the rubric; it has not been independently verified.'
        d['xray']={'decision':d['decision_action'] if previous else 'START',
                   'competency_id':d['competency_id'],
                   'based_on_turn':previous['id'] if previous else None,
                   'reason':d['why'],'difficulty_reason':d['difficulty_reason'],
                   'source':{'path':cited.get('path'),'line_start':cited.get('line_start'),
                             'line_end':cited.get('line_end'),'snippet':cited.get('snippet','')[:1300]} if cited else None,
                   'note':'Controller rationale is an explanation, not verified hidden model reasoning.',
                   'question_source':d['source'], 'generation_attempts':attempts,
                   'repeat_rejections':rejected_repetitions, 'revisit':d['revisit']}
        return {'id':uid('q'),'text':d.pop('question'),'issued_at':time.time(),
                'interview_track':s['setup'].get('interview_track','technical'),
                'interviewer_persona':s['setup'].get('interviewer_persona','supportive'),
                'time_limit_seconds':s['setup'].get('question_time_limit_seconds',0),**d}
    async def start(self,sid,owner):
        s=self.load(sid,owner)
        if s['status']=='paused_provider':
            s['current']=await self.question(s,owner)
            s['status']='active'
            self.store.save(s,owner)
            return s
        if s['status']=='active':return s
        if s['status']!='ready':raise HTTPException(409,'This session has already ended.')
        s['current']=await self.question(s,owner);s['status']='active';s['started_at']=time.time();s['deadline']=s['started_at']+s['setup']['duration_minutes']*60
        self.store.save(s,owner);return s
    async def action(self,sid,owner,a):
        s=self.load(sid,owner)
        if a.request_id in s['request_ids']:return s
        if s['status']!='active':raise HTTPException(409,'Interview is not active.')
        if time.time()>=s['deadline']:raise HTTPException(409,'Interview time has ended. Generate your report.')
        if a.expected_question_id!=s['current']['id']:raise HTTPException(409,'This question has changed. Refresh the interview.')
        if len(s['turns'])>=36:raise HTTPException(409,'Turn limit reached. Generate your report.')
        if a.kind=='hint' and s['setup']['mode']!='coaching':raise HTTPException(409,'Hints are available in coaching mode.')
        now=time.time()
        issued=s['current'].get('issued_at',s.get('started_at') or now)
        elapsed=max(0,now-issued)
        question_limit=s['current'].get('time_limit_seconds',0)
        t={'id':uid('turn'),'kind':a.kind,'text':a.text,'question':copy.deepcopy(s['current']),
           'created_at':now,'response_seconds':round(elapsed,2),
           'question_time_limit_seconds':question_limit,
           'over_question_limit':bool(question_limit and elapsed>question_limit)}
        if a.kind=='answer' and a.voice_duration_seconds is not None:
            t['delivery']=delivery_observation(a.text,a.voice_duration_seconds,a.voice_source)
        s['turns'].append(t);s['last_reply']=''
        if a.kind=='clarify':
            # Fixed facts make repeated clarifications consistent, without another model call.
            facts=s['plan']['scenario']['facts']+[b['complication'] for b in s['branch_events']]
            s['last_reply']='Scenario facts: '+' '.join(facts)+' If your question is not covered, state a reasonable assumption explicitly.'
            t['reply']=s['last_reply']
        elif a.kind=='hint':
            s['hint_count']+=1
            c=next(c for c in s['plan']['competencies'] if c['id']==s['current']['competency_id'])
            level=min(s['hint_count']-1,len(c['criteria'])-1)
            s['last_reply']='Consider this criterion: '+c['criteria'][level];t['reply']=s['last_reply']
        elif (len([t for t in s['turns'] if t['kind'] in ('answer','skip')])>=12
              or s['deadline']-time.time()<=MIN_SECONDS_FOR_NEW_QUESTION):
            s['status']='awaiting_report';s['last_reply']='Interview finished (question/time budget). Generate your report.'
        else:
            if self.strict_live:
                # Commit the candidate's actual answer before another paid model call.
                # Failed question generation must never silently discard that answer.
                s['request_ids'].append(a.request_id)
                s['status']='paused_provider';s['current']=None
                self.store.save(s,owner)
                try:
                    next_question=await self.question(s,owner)
                except ProviderError:
                    raise ProviderError('Your answer was saved. Live question generation is temporarily unavailable. Use Resume interview to retry.',503)
                s['current']=next_question;s['status']='active';s['hint_count']=0
                self.store.save(s,owner)
                return s
            s['current']=await self.question(s,owner);s['hint_count']=0
        s['request_ids'].append(a.request_id);self.store.save(s,owner);return s
    async def finish(self,sid,owner):
        s=self.load(sid,owner)
        if s['report'] and not s['report'].get('provisional'):return s
        if s['status']=='ready':raise HTTPException(409,'Start the interview before generating a report.')
        # Save real answer evidence even if the provider is offline. Do not call a
        # scripted model and pretend it reviewed candidate competence.
        if s['setup']['provider']!='demo' and not any(t['kind']=='answer' for t in s['turns']):
            s['report']=local_unscored_report(s,'No answers were submitted.')
            s['status']='completed';self.store.save(s,owner);return s
        try:
            assessment=self.context(s,assessment=True)
            for attempt in range(2):
                try:
                    r=await self.generate_for(s['setup'],'report',assessment,Report,quota_owner=owner)
                    report=validate_report(r,s)
                    break
                except ProviderError:
                    if attempt:raise
                    assessment['validation_instruction']='REPAIR: Scores 0 must be incorrect_reasoning; answered competencies must have valid evidence and consistent statuses. Strictly apply rubric.'
        except ProviderError as e:
            if s['setup']['provider']=='demo' or self.strict_live:raise
            s['report']=local_unscored_report(s,'Provider unavailable or invalid assessment output.')
            s.setdefault('fallback_events',[]).append({'at':time.time(), **fallback_record(
                'report','Live assessment unavailable; scores withheld.',attempts=2,code=provider_failure_code(e))})
            s['report']['fallback_events']=copy.deepcopy(s['fallback_events'])
        else:
            s['report']=report
            if s['setup']['provider'] in ('groq','huggingface') and any(len(t['text'])>1900 for t in s['turns'] if t['kind']=='answer'):
                s['report']['limitations'].append('Long answers were assessed from balanced evidence excerpts with calculations and later corrections included where possible. Full answers remain available in replay; manual review may be needed.')
        s['status']='completed';self.store.save(s,owner);return s
    async def retry(self,sid,owner,request):
        s=self.load(sid,owner)
        if s['status']!='completed':raise HTTPException(409,'Finish the interview first.')
        t=next((t for t in s['turns'] if t['id']==request.turn_id and t['kind']=='answer'),None)
        if not t:raise HTTPException(422,'Select a recorded answer to retry.')
        if len(s['retry_history'])>=10:raise HTTPException(409,'Retry limit reached for this session.')
        c=next(c for c in s['plan']['competencies'] if c['id']==t['question']['competency_id'])
        ctx={'original':t,'competency':c,'language':s['setup']['language']}
        if request.style=='repair':q={'question':t['question']['text'],'hints':c['criteria']}
        else:
            try:q=(await self.generate_for(s['setup'],'retry_question',ctx,RetryQuestion,quota_owner=owner)).model_dump()
            except ProviderError:
                if s['setup']['provider']=='demo' or self.strict_live:raise
                q={'question':f'Apply {c["name"]} to a different case. Explain a practical example, likely failure, and verification.',
                   'hints':c['criteria'][:2]}
                s.setdefault('fallback_events',[]).append({'at':time.time(),'stage':'retry_question','reason':'Local rubric retry after model failure.'})
        s['retry']={'id':uid('retry'),'original_turn_id':t['id'],'style':request.style,'competency':c,**q,'feedback':None,'answer':None,'hints_used':0}
        self.store.save(s,owner);return s
    def retry_hint(self,sid,owner):
        s=self.load(sid,owner);r=s['retry']
        if not r or r['feedback']:raise HTTPException(409,'No active retry.')
        r['hints_used']=min(r['hints_used']+1,len(r['hints']));self.store.save(s,owner);return s
    async def retry_regrade(self,sid,owner):
        s=self.load(sid,owner)
        r=s.get('retry')
        if not r or not r.get('answer'):
            raise HTTPException(409,'Submit a retry answer first.')
        if r.get('feedback_source')!='unscored_offline_fallback':
            return s
        original=next(t for t in s['turns'] if t['id']==r['original_turn_id'])
        ctx={'original':original,'retry_question':r['question'],'retry_answer':r['answer'],
             'competency':r['competency'],'hints_used':r['hints_used'],'style':r['style'],
             'language':s['setup']['language']}
        try:
            r['feedback']=(await self.generate_for(s['setup'],'retry_feedback',ctx,RetryFeedback,quota_owner=owner)).model_dump()
        except ProviderError:
            raise ProviderError('AI is still unavailable. The saved retry answer and provisional feedback remain intact.',503)
        r['feedback_source']='live_ai'
        for t in reversed(s['retry_history']):
            if t['id']==r['id']:
                t['feedback']=copy.deepcopy(r['feedback']);t['feedback_source']='live_ai';break
        self.store.save(s,owner)
        return s

    async def retry_answer(self,sid,owner,request):
        s=self.load(sid,owner);r=s['retry']
        if not r or r['id']!=request.retry_id:raise HTTPException(409,'This retry is no longer current.')
        if r['feedback']:return s
        original=next(t for t in s['turns'] if t['id']==r['original_turn_id'])
        ctx={'original':original,'retry_question':r['question'],'retry_answer':request.text,'competency':r['competency'],'hints_used':r['hints_used'],'style':r['style'],'language':s['setup']['language']}
        try:
            r['feedback']=(await self.generate_for(s['setup'],'retry_feedback',ctx,RetryFeedback,quota_owner=owner)).model_dump()
            r['feedback_source']='live_ai' if s['setup']['provider']!='demo' else 'scripted_demo'
        except ProviderError:
            if s['setup']['provider']=='demo' or self.strict_live:raise
            r['feedback']={'comparison':'Your retry answer was saved. AI comparison is unavailable and no improvement was graded.',
                           'next_step':'Retry the feedback assessment once the provider is available.'}
            r['feedback_source']='unscored_offline_fallback'
            s.setdefault('fallback_events',[]).append({'at':time.time(),'stage':'retry_feedback','reason':'Model unavailable; no rating fabricated.'})
        r['answer']=request.text;s['retry_history'].append(copy.deepcopy(r));self.store.save(s,owner);return s
