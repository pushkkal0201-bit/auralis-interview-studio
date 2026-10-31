"""Shared, bounded contracts for input and model output."""
from typing import Literal
from pydantic import BaseModel, Field, ConfigDict, field_validator, model_validator

class StrictModel(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)

class Setup(StrictModel):
    cv: str = Field(min_length=40, max_length=24000)
    jd: str = Field(min_length=30, max_length=16000)
    role: str = Field(default='', max_length=150)
    mode: Literal['interview','coaching'] = 'interview'
    interview_track: Literal['technical','behavioral','case_study','pressure','revision'] = 'technical'
    interviewer_persona: Literal['supportive','technical_lead','hiring_manager','panel'] = 'supportive'
    question_time_limit_seconds: Literal[0,60,90,120,180] = 0
    adaptive_difficulty: bool = True
    language: Literal['en','hi','mixed'] = 'en'
    duration_minutes: int = Field(default=10, ge=3, le=45)
    provider: Literal['demo','groq','huggingface'] = 'demo'
    ai_model: Literal['openai/gpt-oss-20b','openai/gpt-oss-120b','qwen/qwen3.8-27b','openai/gpt-oss-120b:fireworks-ai','openai/gpt-oss-20b:groq'] = 'openai/gpt-oss-20b'
    consent: bool = False
    synthetic_data: bool = False
    project_evidence: str = Field(default='', max_length=12000)
    codeproof_refs: list[dict] = Field(default_factory=list, max_length=14)  # Legacy, never trusted without a server handle
    codeproof_handle: str = Field(default='',max_length=80)
    incident_id: Literal['','booking-race','slow-api','retry-storm'] = ''
    @model_validator(mode='after')
    def live_consent(self):
        if self.provider in ('groq','huggingface') and not self.consent:
            raise ValueError('Consent is required before sending private interview data to the selected AI provider.')
        if self.provider == 'groq' and self.ai_model not in ('openai/gpt-oss-20b','openai/gpt-oss-120b','qwen/qwen3.8-27b'):
            raise ValueError('Choose a Groq model for Groq interviews.')
        if self.provider == 'huggingface' and self.ai_model not in ('openai/gpt-oss-120b:fireworks-ai','openai/gpt-oss-20b:groq'):
            raise ValueError('Choose a Hugging Face model for Hugging Face interviews.')
        return self

class Competency(StrictModel):
    id: str = Field(pattern=r'^c[1-6]$')
    name: str = Field(min_length=2,max_length=100)
    requirement: str = Field(min_length=3,max_length=350)
    criteria: list[str] = Field(min_length=2,max_length=4)

class Branch(StrictModel):
    id: str = Field(pattern=r'^b[1-6]$')
    trigger: str = Field(max_length=180)
    complication: str = Field(min_length=5,max_length=400)

class Scenario(StrictModel):
    title: str = Field(max_length=120)
    situation: str = Field(min_length=10,max_length=700)
    facts: list[str] = Field(min_length=2,max_length=8)
    branches: list[Branch] = Field(min_length=2,max_length=5)

class Claim(StrictModel):
    quote: str = Field(min_length=5,max_length=400)
    probe: str = Field(min_length=5,max_length=300)

class Plan(StrictModel):
    role: str = Field(min_length=2,max_length=150)
    seniority: str = Field(max_length=80)
    summary: str = Field(min_length=5,max_length=700)
    competencies: list[Competency] = Field(min_length=3,max_length=6)
    claims: list[Claim] = Field(max_length=4)
    scenario: Scenario
    @model_validator(mode='after')
    def unique_ids(self):
        for seq in [self.competencies,self.scenario.branches]:
            if len({v.id for v in seq}) != len(seq):
                raise ValueError('Duplicate IDs in model output')
        return self

class Decision(StrictModel):
    question: str = Field(min_length=8,max_length=900)
    competency_id: str
    why: str = Field(min_length=5,max_length=500)
    difficulty: Literal['foundation','applied','advanced']
    difficulty_reason: str = Field(min_length=5,max_length=400)
    branch_id: str = ''
    coaching: str = Field(default='',max_length=700)
    decision_action: Literal['START','CLARIFY','PROBE','ADVANCE','REVISIT'] = 'ADVANCE'
    source_ref_id: str = Field(default='',max_length=8)

class Action(StrictModel):
    text: str = Field(min_length=1,max_length=8000)
    kind: Literal['answer','clarify','hint','skip'] = 'answer'
    request_id: str = Field(min_length=8,max_length=80,pattern=r'^[A-Za-z0-9_-]+$')
    expected_question_id: str = Field(min_length=3,max_length=80)
    voice_duration_seconds: float | None = Field(default=None,ge=2,le=120,allow_inf_nan=False)
    voice_source: Literal['browser_speech','groq_transcription'] | None = None
    @model_validator(mode='after')
    def voice_pair(self):
        if (self.voice_duration_seconds is None) != (self.voice_source is None):
            raise ValueError('Voice source and duration must be supplied together.')
        if self.kind != 'answer' and self.voice_duration_seconds is not None:
            raise ValueError('Delivery metrics apply only to submitted answers.')
        return self

class AssessmentItem(StrictModel):
    competency_id: str
    status: Literal['demonstrated','partially_demonstrated','insufficient_evidence','not_assessed','incorrect_reasoning','not_scored_provider_unavailable']
    score: int | None = Field(default=None,ge=0,le=4)
    confidence: Literal['low','medium','high'] = 'low'
    feedback: str = Field(min_length=5,max_length=1200)
    evidence_ids: list[str] = Field(max_length=8)
    initial_score: int | None = Field(default=None,ge=0,le=4)
    latest_score: int | None = Field(default=None,ge=0,le=4)
    improvement_note: str = Field(default='',max_length=350)
    practice: str = Field(min_length=5,max_length=600)
    next_score_gap: str = Field(default="",max_length=600)

class Report(StrictModel):
    summary: str = Field(min_length=5,max_length=1500)
    items: list[AssessmentItem] = Field(min_length=1,max_length=6)
    limitations: list[str] = Field(min_length=1,max_length=6)

class RetryQuestion(StrictModel):
    question: str = Field(min_length=8,max_length=900)
    hints: list[str] = Field(min_length=1,max_length=3)

class RetryFeedback(StrictModel):
    comparison: str = Field(min_length=5,max_length=1200)
    next_step: str = Field(min_length=5,max_length=600)

class RetryStart(StrictModel):
    turn_id: str
    style: Literal['repair','parallel'] = 'parallel'

class RetryAnswer(StrictModel):
    retry_id: str
    text: str = Field(min_length=1,max_length=8000)

class Comparison(StrictModel):
    cv: str = Field(min_length=40,max_length=24000)
    jd_a: str = Field(min_length=30,max_length=16000)
    jd_b: str = Field(min_length=30,max_length=16000)
    provider: Literal['demo','groq','huggingface'] = 'demo'
    ai_model: Literal['openai/gpt-oss-20b','openai/gpt-oss-120b','qwen/qwen3.8-27b','openai/gpt-oss-120b:fireworks-ai','openai/gpt-oss-20b:groq'] = 'openai/gpt-oss-20b'
    consent: bool = False

    @model_validator(mode='after')
    def require_consent(self):
        if self.provider in ('groq','huggingface') and not self.consent:
            raise ValueError('Consent is required before sending data to the AI provider.')
        if self.provider == 'huggingface' and self.ai_model not in ('openai/gpt-oss-120b:fireworks-ai','openai/gpt-oss-20b:groq'):
            raise ValueError('Choose a Hugging Face model.')
        if self.provider == 'groq' and self.ai_model not in ('openai/gpt-oss-20b','openai/gpt-oss-120b','qwen/qwen3.8-27b'):
            raise ValueError('Choose a Groq model.')
        return self
