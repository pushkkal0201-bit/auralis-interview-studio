"""Transparent, role-oriented plan when live plan generation is unavailable.
No claim of AI inference, subject-matter expertise, or candidate competence.
"""
import re
from .schemas import Plan

KEYWORDS=[('Electrical engineering',('electrical','power','transformer','etap','relay','switchgear')),
          ('Machine learning',('machine learning','pandas','classification','scikit','model training')),
          ('Software engineering',('backend','frontend','api','python','java','software')),
          ('Data analysis',('analysis','sql','dashboard','reporting','data'))]

def local_plan(setup):
    jd=setup['jd']
    role=(setup.get('role') or next((line for line in jd.splitlines() if len(line.strip())>5),'Interview practice'))[:140]
    text=jd.lower()
    matched=next((v for v in KEYWORDS if any(w in text for w in v[1])),None)
    focus=matched[0] if matched else 'Role-specific'
    phrases=[x.strip(' -•\t') for x in re.split(r'[\n;.]',jd) if len(x.strip())>=12]
    phrases=phrases[:9]
    while len(phrases)<3:
        phrases.append('Explain a role-specific technical problem and a safe verification method.')
    names=[focus+' fundamentals','Applied problem solving','Verification, safety & communication']
    comps=[]
    for i,name in enumerate(names):
        requirement=phrases[i][:300]
        comps.append({'id':f'c{i+1}','name':name,'requirement':requirement,
                      'criteria':['Explain the relevant reasoning and assumptions.',
                                  'Describe a concrete check, limitation or verification step.']})
    return Plan.model_validate({'role':role,'seniority':'Offline practice (not inferred)',
          'summary':'Local continuity rubric derived from job description; not generated or verified by AI.',
          'competencies':comps,'claims':[],
          'scenario':{'title':'Role-specific verification exercise',
                      'situation':('Consider a realistic work task for the role: '+phrases[0])[:690],
                      'facts':['Use only the job information supplied.',
                               'Where system details are missing, state assumptions explicitly.'],
                      'branches':[{'id':'b1','trigger':'New constraint','complication':'A key component or input becomes unavailable.'},
                                  {'id':'b2','trigger':'Quality concern','complication':'A verification result does not match the expected outcome.'}]}})
