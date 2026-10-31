"""Bounded evidence selection and deterministic checks for practice grading.

Never treats a model's rubric verdict as ground truth. Keeps chronological
context, both ends of long answers, and numeric/methodology-bearing passages.
"""
import math
import re

MAX_ASSESSMENT_CHARS = 19000


def evidence_excerpt(answer: str, budget: int = 1900) -> tuple[str, bool]:
    answer = answer.strip()
    if len(answer) <= budget:
        return answer, False
    # Never silently present an excerpt as complete testimony.
    # Reserve both the introduction and conclusion, then select detailed middle
    # paragraphs with quantities, equations, exceptions, and verification steps.
    start = answer[:min(350, budget // 4)]
    end = answer[-min(440, budget // 4):]
    center = answer[len(start):len(answer)-len(end)]
    paras = [p.strip() for p in re.split(r'\n\s*\n|(?<=\.)\s+(?=[A-Z])', center) if p.strip()]
    def importance(p):
        words = p.lower()
        score = 0
        score += 5 if re.search(r'\b\d+(?:[.,]\d+)?\s*(?:mw|kva|mva|kv|ka|amps?|a|v|%)\b', words) else 0
        score += 4 if re.search(r'\b(?:calculate|formula|\bif\b|however|therefore|leakage|verify|limitations|maximum|minimum|fault|test|compare|actual|assum)', words) else 0
        score += 3 if any(z in p for z in ('=', '√', '≈', '×', '→')) else 0
        return score
    remaining = max(0, budget - len(start) - len(end) - 90)
    selected = []
    for idx,p in sorted(enumerate(paras),key=lambda x:(-importance(x[1]),x[0])):
        if remaining <= 45:break
        piece = p[:min(len(p),500)]
        if len(piece)+3<=remaining:
            selected.append((idx,piece))
            remaining-=len(piece)+3
    body='\n...\n'.join(p for _,p in sorted(selected))
    return (start+'\n[Middle evidence excerpts; some text omitted]\n'+body+'\n[Final answer excerpt]\n'+end)[:budget+100], True


def build_assessment_turns(turns, total_budget=MAX_ASSESSMENT_CHARS):
    answers=[t for t in turns if t['kind']=='answer']
    if not answers:return []
    per=min(1900,max(900,(total_budget-600)//len(answers)))
    output=[]
    for t in answers:
        excerpt,short=evidence_excerpt(t['text'],per)
        output.append({'id':t['id'],'kind':'answer','text':excerpt,'excerpted':short,
                       'source_length':len(t['text']),
                       'question':{'text':t['question']['text'][:350],
                                   'competency_id':t['question']['competency_id']}})
    return output


def short_evidence(text, limit=320):
    """Report-card excerpt only; full, unmodified testimony remains in replay."""
    text=text.strip()
    if len(text)<=limit:return text
    return text[:limit-24].rstrip()+' ... [read full replay]'


def contradicted_electrical_criticism(item, answer_texts):
    """Narrow calculation sanity guard, *not* a general engineering verifier.

    Prevents the known 3.1 regression: grading a correct 5 MW, PF=.9 three-
    phase current estimate as 'unrealistic'. Values are illustrative and do not
    verify actual breaker sizing or a real plant design.
    """
    criticism=item.get('feedback','').lower()
    if not any(x in criticism for x in ('unrealistic current','incorrect current calculation',
                                         'wrong current calculation','incorrect fault-current calculations',
                                         'confusion between low- and medium-voltage')):
        return False
    alltext=' '.join(answer_texts).lower().replace(',','')
    if not (re.search(r'5\s*mw',alltext) and re.search(r'0[.,]9',alltext)):
        return False
    load=5_000_000
    iv_low=load/(math.sqrt(3)*415*.9)
    iv_high=load/(math.sqrt(3)*11_000*.9)
    low=bool(re.search(r'415\s*v.{0,120}\b(77[0-9]{2})\s*a\b',alltext,re.S))
    high=bool(re.search(r'11\s*kv.{0,120}\b(29[0-9])\s*a\b',alltext,re.S))
    calc_ok=abs(iv_low-7730)/iv_low<.01 and abs(iv_high-292)/iv_high<.01
    if not calc_ok:return False
    if 'confusion between low- and medium-voltage' in criticism:
        return high and ('mccb' in alltext and ('not suitable' in alltext or 'not be suitable' in alltext))
    return low or high


def contradicted_power_factor_criticism(item, answer_texts):
    """Known regression guard: a later explicit correction of basic P/Q formulas.

    This is deliberately narrow; not a substitute for a licensed engineer or a
    comprehensive formula checker. Scores are withheld on contradiction.
    """
    if item.get('score') != 0 or len(answer_texts)<2:
        return False
    last=answer_texts[-1].lower().replace(' ','').replace('\n','')
    correct_p=('p=√3' in last and 'cos' in last.split('p=√3',1)[1][:50])
    correct_q=('q=√3' in last and 'sin' in last.split('q=√3',1)[1][:50])
    correct_s=('s²=p²+q²' in last or 's^2=p^2+q^2' in last)
    return correct_p and correct_q and correct_s
