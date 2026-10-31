"""Local learning analytics derived from owner-scoped completed assessments.

No grades are calculated here: we display previously stored provider scores only.
"""
import re
from collections import defaultdict
from datetime import datetime, timezone


def _skill_key(name):
    return re.sub(r'\s+', ' ', re.sub(r'[^a-z0-9]+', ' ', str(name).lower())).strip()


def progress_from_sessions(sessions):
    """Return recent rubric-score histories, with provenance and limits surfaced."""
    timeline = defaultdict(list)
    attempts = 0
    completed = 0
    provider_scored = 0
    repaired = 0
    for s in sorted(sessions, key=lambda r: r.get('created_at', 0)):
        attempts += 1
        repaired += sum(1 for r in s.get('retry_history', []) if r.get('answer'))
        report = s.get('report') or {}
        if s.get('status') != 'completed' or not report:
            continue
        completed += 1
        if report.get('provisional') or report.get('demo') or s.get('setup', {}).get('provider') == 'demo':
            continue
        for item in report.get('items', []):
            score = item.get('score')
            name = item.get('name', '')
            # Use only explicitly model-scored values and exact normalized competency names.
            if not name or not isinstance(score, int) or isinstance(score, bool) or not 0 <= score <= 4:
                continue
            key = _skill_key(name)
            if not key:
                continue
            timeline[key].append({
                'session_id':s.get('id'),
                'at':s.get('created_at'),
                'date':datetime.fromtimestamp(s.get('created_at', 0), timezone.utc).strftime('%Y-%m-%d'),
                'role':s.get('plan', {}).get('role', 'Interview'),
                'score':score,
                'confidence':item.get('confidence', 'unknown'),
                'provider':report.get('ai_provider') or s.get('setup', {}).get('provider', 'unknown'),
                'model':report.get('ai_model') or s.get('setup', {}).get('ai_model', 'unknown'),
                'rubric_requirement':next((c.get('requirement', '') for c in s.get('plan', {}).get('competencies', []) if c.get('id') == item.get('competency_id')), ''),
            })
            provider_scored += 1
    skills = []
    for key, points in timeline.items():
        current = points[-1]
        first = points[0]
        skills.append({
            'id':key.replace(' ', '-'),
            'name':next((item.get('name') for s in reversed(sessions) for item in (s.get('report') or {}).get('items', []) if _skill_key(item.get('name')) == key), key.title()),
            'points':points[-20:],
            'session_count':len(points),
            'latest_score':current['score'],
            'earliest_score':first['score'],
            'score_change':current['score'] - first['score'] if len(points) >= 2 else None,
        })
    skills.sort(key=lambda x: (-x['session_count'], x['name'].lower()))
    return {
        'session_count':attempts,
        'completed_count':completed,
        'scored_competency_observations':provider_scored,
        'repair_attempt_count':repaired,
        'skills':skills,
        'limitations':[
            'These are stored AI rubric judgments, not validated measures of ability.',
            'Scores from different roles, question difficulty, models and rubrics may not be directly comparable.',
            'Only completed, non-demo, non-provisional assessments with numeric scores are plotted.',
            'Competencies are grouped only when their normalized names match. History is limited to the latest 100 saved sessions, and each chart shows up to 20 observations.',
        ],
    }
