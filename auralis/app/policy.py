"""Deterministic, inspectable interview orchestration. Never grades a candidate.

The language model writes questions; this policy decides which rubric competency
must be covered and validates the output before accepting it.
"""
from difflib import SequenceMatcher
import re

MAX_QUESTIONS_PER_COMPETENCY = 2
MIN_SECONDS_FOR_NEW_QUESTION = 35


def answered_counts(session):
    return {c['id']:sum(t['kind'] in ('answer','skip') and t['question']['competency_id']==c['id']
            for t in session['turns']) for c in session['plan']['competencies']}


def target_competency(session, remaining_seconds=None):
    """Ensure broad coverage, allowing one follow-up on the current competency."""
    comps = session['plan']['competencies']
    counts = answered_counts(session)
    if not comps:
        raise ValueError('An interview needs at least one competency')
    last = next((t for t in reversed(session['turns']) if t['kind'] in ('answer','skip')), None)
    not_covered = [c['id'] for c in comps if counts[c['id']] == 0]
    if last:
        cid = last['question']['competency_id']
        # Rotate early enough to cover all competencies. Never probe a topic > 2 times.
        if not_covered and (counts.get(cid, 0) >= MAX_QUESTIONS_PER_COMPETENCY or
            (remaining_seconds is not None and remaining_seconds <= len(not_covered) * 100)):
            return not_covered[0]
        if counts.get(cid, 0) == 1 and last['kind'] == 'answer':
            return cid
    if not_covered:
        return not_covered[0]
    return min(comps, key=lambda c:(counts[c['id']], comps.index(c)))['id']


_QUESTION_STOPWORDS = frozenset('the a an of for in on to by with from how would will you your and or that this which what why does do is are as such including include please explain describe discuss given under when creating considering using about can should its their it auralis'.split())


def _topic_words(text):
    # English-only heuristic. Never use this score to grade an answer.
    terms=re.findall(r'[a-z][a-z0-9]*', text.lower())
    normalized=[]
    for term in terms:
        if term in _QUESTION_STOPWORDS or len(term)<3:continue
        if term.endswith('ies') and len(term)>5:term=term[:-3]+'y'
        elif term.endswith('s') and len(term)>5 and not term.endswith('ss'):term=term[:-1]
        elif term.endswith('ing') and len(term)>7:term=term[:-3]
        normalized.append(term)
    return set(normalized)


def is_repeated(question, session, competency_id=None):
    """Reject lexical duplicates and strong same-topic paraphrases.

    Heuristic protects against accidental re-asking; an interviewer can still
    deliberately revisit a skill via a different applied scenario.
    """
    def normalize(text):
        return re.sub(r'[^a-z0-9 ]+', '', text.lower()).strip()
    candidate=normalize(question)
    tokens=_topic_words(question)
    for turn in session['turns']:
        if competency_id is not None and turn['question']['competency_id']!=competency_id:
            continue
        prior=normalize(turn['question']['text'])
        if prior==candidate or SequenceMatcher(None,candidate,prior).ratio()>=0.82:
            return True
        prior_words=_topic_words(turn['question']['text'])
        if len(tokens)>=7 and len(prior_words)>=7:
            shared=len(tokens & prior_words)
            overlap=shared/max(1,min(len(tokens),len(prior_words)))
            # Word overlap alone is noisy; demand most of BOTH questions' topic.
            jaccard=shared/max(1,len(tokens|prior_words))
            if (overlap>=0.73 and jaccard>=0.40) or (overlap>=0.62 and jaccard>=0.45):
                return True
    return False


def rubric_fallback(session, competency_id, reason):
    """A transparent local continuity question, NOT AI inference or scoring."""
    competency = next(c for c in session['plan']['competencies'] if c['id'] == competency_id)
    count = answered_counts(session)[competency_id]
    criterion = competency['criteria'][min(count, len(competency['criteria'])-1)]
    question = (f"For {competency['name']}, explain your approach to this requirement: "
                f"{criterion} Give a concrete example, a failure case, and how you would verify it.")
    if is_repeated(question, session, competency_id):
        question = (f"For {competency['name']}, present an alternative approach to "
                    f"'{competency['requirement']}' and describe how you would test its trade-offs.")
    return {
        'question': question[:900], 'competency_id': competency_id,
        'why':'This is a local rubric-based continuity question, not model-generated. ' + reason,
        'difficulty':'applied',
        'difficulty_reason':'Follows the published rubric; no automated judgement of your previous answer.',
        'branch_id':'', 'coaching':'', 'decision_action':'ADVANCE', 'source_ref_id':'',
    }


def coverage_summary(session):
    counts = answered_counts(session)
    total = len(counts)
    evidence_counts = {c['id']:sum(t['kind']=='answer' and t['question']['competency_id']==c['id']
                               for t in session['turns']) for c in session['plan']['competencies']}
    assessed = sum(v > 0 for v in evidence_counts.values())
    return {'answered_by_competency':evidence_counts,'attempts_by_competency':counts,'covered_count':assessed,'total_count':total,
            'coverage_percent':round(100*assessed/total) if total else 0,
            'unassessed_ids':[key for key,num in evidence_counts.items() if num == 0]}
