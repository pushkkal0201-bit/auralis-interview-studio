"""Minimal standards-compliant Agent Skill loader; never evaluates bundled files."""
from pathlib import Path
import re
ROOT = Path(__file__).resolve().parent.parent/'skills'/'adaptive-interviewer'

def load_interviewer_skill():
    text=(ROOT/'SKILL.md').read_text(encoding='utf-8')
    if not text.startswith('---\n'):raise ValueError('Agent Skill frontmatter missing')
    meta,body=text[4:].split('\n---\n',1)
    if not re.search(r'^name:\s*adaptive-interviewer\s*$',meta,re.M):raise ValueError('Unexpected skill name')
    if not re.search(r'^description:\s*\S+',meta,re.M):raise ValueError('Agent Skill description required')
    rubric=(ROOT/'references'/'rubric.md').read_text(encoding='utf-8')
    decision=(ROOT/'references'/'decision-policy.md').read_text(encoding='utf-8')
    return '\n'.join([body,rubric,decision])[:8500]
