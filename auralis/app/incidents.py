"""Fixed, synthetic interview incidents. These are exercise fixtures, not telemetry."""
INCIDENTS = [
 {'id':'booking-race','name':'Last-slot race condition','domain':'Backend / transactions',
  'severity':'P1 · simulated','summary':'Two checkout requests reserve the last available pickup slot.',
  'logs':['09:41:17.101 POST /slots/17/reserve request=A result=200','09:41:17.103 POST /slots/17/reserve request=B result=200','09:41:17.121 inventory slot=17 available=-1'],
  'facts':['Both requests read availability before either writes its reservation.','The database has no unique constraint on active reservations for this slot.'],
  'prompt':'What would you inspect first, how would you prevent the race, and what concurrent regression test would you run?',
  'concepts':['atomic transaction','locking/unique constraint','idempotency','concurrency test']},
 {'id':'slow-api','name':'API latency incident','domain':'Performance / diagnosis','severity':'P2 · simulated',
  'summary':'Latency rises after a new search endpoint is released.',
  'logs':['10:02:00 GET /search p95=380ms','10:15:00 GET /search p95=2900ms','10:15:05 db query_count_per_request=108'],
  'facts':['No upstream outage is reported.','Database queries per request rose after the release.'],
  'prompt':'Which measurements and traces would you inspect, what root-cause hypotheses are reasonable, and how would you verify a fix?',
  'concepts':['N+1 queries','query profiling','indexes','load test']},
 {'id':'retry-storm','name':'Payment retry storm','domain':'Reliability / APIs','severity':'P1 · simulated',
  'summary':'Intermittent response timeouts cause duplicate payment attempts.',
  'logs':['11:21:07 POST /payments id=op-44 timeout','11:21:08 POST /payments id=op-44 retry','11:21:09 payments created=2 operation=op-44'],
  'facts':['Client retries have no backoff.','Server does not enforce idempotency keys.'],
  'prompt':'How would you protect against duplicate side effects, handle retries and prove correctness?',
  'concepts':['idempotency key','retry backoff','transactional write','deduplication test']}
]

def public_incidents():
    return INCIDENTS

def evidence_for_incident(incident_id):
    incident=next((i for i in INCIDENTS if i['id']==incident_id),None)
    if not incident:return None
    return ('SYNTHETIC INCIDENT EXERCISE — not observed system telemetry. '
            f"Scenario: {incident['name']}. Problem: {incident['summary']}. "
            f"Facts: {' '.join(incident['facts'])} Logs: {' | '.join(incident['logs'])} "
            f"Candidate task: {incident['prompt']} Expected discussion topics (do not reveal in initial question): {', '.join(incident['concepts'])}.")


def scenario_for_incident(incident_id):
    incident=next((i for i in INCIDENTS if i['id']==incident_id),None)
    if not incident:return None
    return {'title':incident['name'],
            'situation':incident['summary']+' This is a synthetic interview exercise.',
            'facts':incident['facts']+['Simulated event: '+line for line in incident['logs'][:3]],
            'branches':[{'id':'b1','trigger':'Candidate asks about validation details',
                         'complication':'The incident logs are synthetic and do not establish a confirmed root cause.'},
                        {'id':'b2','trigger':'Candidate proposes a fix',
                         'complication':'The interviewer also wants a repeatable regression test and rollback plan.'}]}
