"""Safe, structured provenance for the local interview practice flow.

Contains no provider exception bodies, tokens, candidate text, or contact details.
"""
from .provider import ProviderError


def provider_failure_code(exc):
    status = getattr(exc, 'status', None)
    if status == 429:
        return 'rate_limited'
    if status in (401, 403):
        return 'authentication_or_permission'
    if status in (408, 504):
        return 'timeout'
    if isinstance(status, int) and status >= 500:
        return 'provider_or_transport_unavailable'
    if status == 400:
        return 'provider_request_rejected'
    if status == 422:
        return 'provider_output_invalid'
    return 'provider_or_validation_error'


def fallback_record(stage, reason, competency_id=None, attempts=1, code='provider_or_validation_error'):
    """Persist only safe enumerated codes and generic descriptions."""
    data = {'stage':stage, 'reason':reason, 'error_code':code,
            'attempt_count':max(1, int(attempts)), 'source':'local_rubric_fallback'}
    if competency_id:
        data['competency_id']=competency_id
    return data


def claim_provenance(setup):
    if setup.get('synthetic_data'):
        return {'status':'synthetic_test_data',
                'label':'Fictional or synthetic scenario supplied for testing. No real employment or project execution was verified.'}
    return {'status':'self_reported_unverified',
            'label':'CV and interview examples are self-reported and unverified. Auralis does not establish employment, authorship, professional experience, or actual project execution.'}


def score_gap_note(item):
    if item.get('score') is None:
        return 'No score was assigned; no next-score comparison is available.'
    if item['score'] == 4:
        return 'Highest rubric level assigned; this does not prove hands-on performance.'
    given = (item.get('next_score_gap') or '').strip()
    return given or 'The model did not specify the evidence missing for the next rubric level. Review the full response manually.'


def cautious_claim_language(text):
    """Remove a few unsupported provenance assertions, not technical content.

    This is deliberately narrow and does not 'verify' the candidate's work.
    Every report also carries an explicit provenance disclaimer.
    """
    import re
    if not isinstance(text, str):
        return text
    text = re.sub(r'\breal[ -]world (?:project )?example\b',
                  'candidate-described project example (unverified)', text, flags=re.I)
    text = re.sub(r'\bverified (?:professional )?experience\b',
                  'self-reported experience (unverified)', text, flags=re.I)
    text = re.sub(r'\bproven hands-on (?:experience|expertise)\b',
                  'described technical reasoning (unverified in practice)', text, flags=re.I)
    return text
