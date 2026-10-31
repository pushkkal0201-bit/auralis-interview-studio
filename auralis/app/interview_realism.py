"""Auralis 5.2 interview realism settings and transparent delivery observations.

No inference about confidence, honesty, health, personality or employability is made
from pace or filler words. Raw audio is not retained by this module.
"""
import re

TRACKS={
 'technical': 'Ask a job-relevant technical reasoning or design question, including assumptions, trade-offs and checks.',
 'behavioral': 'Ask for a specific prior experience using situation, task, action, result and reflection. CV experiences are unverified; avoid presuming they occurred.',
 'case_study': 'Present a bounded realistic role-specific scenario from the plan, and request a decision, assumptions, trade-offs and verification.',
 'pressure': 'Keep the question concise, prioritize one clear applied decision, and ask a firm but respectful follow-up. Never insult or harass the candidate.',
 'revision': 'Ask a NEW transfer or correction-check question, drawing on observed missed reasoning if any. Do not repeat the original wording or claim actual mastery.',
}
PERSONAS={
 'supportive': 'Use a warm, neutral, precise interviewer voice; challenge assumptions respectfully.',
 'technical_lead': 'Act as a careful technical lead: press for feasibility, trade-offs, failure cases and verification.',
 'hiring_manager': 'Focus on decisions, scope, responsibility, communication, results and prioritization; avoid unsupported hiring conclusions.',
 'panel': 'Ask one question from a multi-disciplinary team perspective without pretending multiple real people are present.',
}
FILLERS=re.compile(r'(?<![\w])(?:um+|uh+|erm+|ahh+|you know|sort of|kind of)(?![\w])',re.IGNORECASE)

def interview_guidance(setup):
    track=setup.get('interview_track','technical')
    persona=setup.get('interviewer_persona','supportive')
    return {'track':track,'persona':persona,
            'track_instruction':TRACKS.get(track,TRACKS['technical']),
            'persona_instruction':PERSONAS.get(persona,PERSONAS['supportive']),
            'adaptive_difficulty':bool(setup.get('adaptive_difficulty',True)),
            'question_time_limit_seconds':int(setup.get('question_time_limit_seconds') or 0),
            'note':'These are permitted pre-selected interview instructions, not untrusted candidate instructions.'}

def delivery_observation(text, duration_seconds, source):
    """Approximate words/minute from transcript and elapsed capture time, not speech fluency or competence."""
    if not isinstance(text,str) or not isinstance(duration_seconds,(float,int)) or isinstance(duration_seconds,bool):
        return None
    if not 2<=duration_seconds<=120 or source not in ('browser_speech','groq_transcription'):
        return None
    words=re.findall(r"\b[\w]+(?:['’-][\w]+)*\b",text,flags=re.UNICODE)
    count=len(words)
    pace=round(60*count/duration_seconds,1)
    filler_matches=FILLERS.findall(text)
    return {'source':source,'duration_seconds':round(duration_seconds,1),
            'transcript_word_count':count,'estimated_wpm':pace,
            'identified_fillers':len(filler_matches),
            'filler_examples':sorted({f.lower() for f in filler_matches})[:5],
            'limitations':'Estimated from submitted transcript and client-reported capture duration. Pauses, acoustic qualities, confidence, and personal traits are NOT measured. Edits or recognition errors affect accuracy.'}

def delivery_summary(turns):
    entries=[t.get('delivery') for t in turns if t.get('kind')=='answer' and t.get('delivery')]
    return {'samples':len(entries), 'mean_estimated_wpm':round(sum(e['estimated_wpm'] for e in entries)/len(entries),1) if entries else None,
            'filler_count':sum(e['identified_fillers'] for e in entries),
            'note':'Transcript-derived observations only; not part of Skill DNA scores. No audio or pause timing is stored.'}
