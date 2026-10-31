"""Transparent scripted simulator. Never represents an AI assessment."""
from .schemas import Plan, Decision, Report, RetryQuestion, RetryFeedback

class DemoProvider:
    async def generate(self, task, context, schema):
        if task=='plan':
            jd=context['jd'].lower()
            if any(x in jd for x in ['support','helpdesk']):
                role='Technical support'; names=['Incident triage','Troubleshooting','Customer communication']; situation='Employees cannot sign in to an internal portal.'
                facts=['100 employees are affected.', 'Only office-network users are affected.', 'No passwords should be requested from users.']
                branches=[('Network diagnosis','A second office now reports the same problem.'),('Workaround','The normal workaround also fails.')]
            elif any(x in jd for x in ['analyst','analytics','data analysis']):
                role='Data analyst'; names=['Metric definition','Data validation','Communicating findings']; situation='A team wants to know whether its booking process reduced waiting times.'
                facts=['Two months of anonymized booking records are available.', 'Some check-in timestamps are missing.', 'No causal experiment has been run.']
                branches=[('Missing data','Missing timestamps occur mostly during peak hours.'),('Metrics','The median improved but the longest waits increased.')]
            elif any(x in jd for x in ['security','cyber']):
                role='Security analyst'; names=['Incident triage','Evidence handling','Risk communication']; situation='An internal service shows unusual failed sign-in attempts.'
                facts=['Only authorized internal logs may be inspected.', 'The service must remain available.', 'The cause has not been confirmed.']
                branches=[('Containment','Some legitimate accounts now experience lockouts.'),('Evidence','A log source is temporarily unavailable.')]
            else:
                role=context.get('role') or 'Backend developer'; names=['Concurrency and correctness','API design','Testing and trade-offs']; situation='Design a booking service with limited slots.'
                facts=['There are 100 available slots.', 'Up to 1,000 users may request the final slot.', 'Clients may retry requests after timeouts.']
                branches=[('Existence check','Two requests pass the availability check simultaneously.'),('Transactions','A booking succeeds, but the client times out and retries.')]
            claim=context['cv'].split('\n')[0][:300]
            result=dict(role=role,seniority='Practice level',summary='Scripted demo plan. Live AI generates role-specific plans for arbitrary IT job descriptions.',competencies=[dict(id=f'c{i+1}',name=n,requirement=n,criteria=['Explain your approach and assumptions.','Identify a failure case and how to verify the solution.']) for i,n in enumerate(names)],claims=[dict(quote=claim,probe='What was your own contribution, and which trade-off did you make?')],scenario=dict(title=f'{role} scenario',situation=situation,facts=facts,branches=[dict(id=f'b{i+1}',trigger=a,complication=b) for i,(a,b) in enumerate(branches)]))
        elif task=='question':
            s=context; answers=[t for t in s['turns'] if t['kind']=='answer']; comps=s['plan']['competencies']; last=answers[-1]['text'].lower() if answers else ''
            count=len(answers)+len([t for t in s['turns'] if t['kind']=='skip'])
            branch=''; cid=comps[min(count//2,len(comps)-1)]['id']
            if not count:
                q=f"Your CV says: {s['plan']['claims'][0]['quote'] if s['plan']['claims'] else 'you have project experience'}. What did you personally implement, and what trade-off did you make?"
            elif count==1:
                q=s['plan']['scenario']['situation']+' What assumptions would you clarify, and how would you approach it?'
            else:
                branches=s['plan']['scenario']['branches']; choice=1 if any(w in last for w in ['transaction','lock','unique','retry','test']) else 0
                b=branches[choice]; branch=b['id']; q=b['complication']+' How would you handle this and test your approach?'
            if count>4:
                q=f"For {comps[min(count//2,len(comps)-1)]['name']}, describe a failure you would test and explain the trade-offs in your approach."
            result=dict(question=q,competency_id=cid,why='Scripted demo: this question follows the current topic and the recorded answer.',difficulty='applied' if count else 'foundation',difficulty_reason='Illustrative progression only. Demo does not judge competence.',branch_id=branch,coaching='State the assumptions, choose an approach, and explain one failure case.' if s['setup']['mode']=='coaching' else '')
        elif task=='report':
            s=context; result=dict(summary='Scripted demonstration report. No AI competence assessment was performed.',items=[],limitations=['Demo output is illustrative, not a skill assessment.','Spoken answers do not verify hands-on coding ability.'])
            for c in s['plan']['competencies']:
                ids=[t['id'] for t in s['turns'] if t['kind']=='answer' and t['question']['competency_id']==c['id']]
                result['items'].append(dict(competency_id=c['id'],status='insufficient_evidence' if ids else 'not_assessed',score=None,feedback='Answer recorded for workflow testing. Live mode is needed for AI feedback.' if ids else 'This skill was not assessed.',evidence_ids=ids[:4],practice='Try explaining an assumption, a failure case, and a test.'))
        elif task=='retry_question':
            result=dict(question='Consider a similar task with twice the workload and one dependency unavailable. How would you adapt your original approach?',hints=['Identify which assumption changed.','Explain how you would verify recovery.'])
        elif task=='retry_feedback':
            result=dict(comparison='Both attempts were saved. This scripted demo does not judge improvement.',next_step='In live mode, compare the reasoning against the same competency criteria.')
        else:
            raise ValueError('Unknown demo task')
        return schema.model_validate(result)
