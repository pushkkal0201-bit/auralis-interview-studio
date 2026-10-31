"""Hugging Face Inference Providers adapter for real open-weight GPT-OSS calls.

No silent demo fallback, no arbitrary user-supplied endpoint, no keys in logs.
Uses the documented OpenAI-compatible chat-completions router and locally
validates every response against the SAME Pydantic contracts as Groq.
"""
import json
import os

import httpx
from pydantic import ValidationError

from .provider import ProviderError, SYSTEM, TASKS
from .skill_loader import load_interviewer_skill

HUGGINGFACE_MODELS = {
    'openai/gpt-oss-120b:fireworks-ai': 'GPT-OSS 120B · Hugging Face (structured output)',
    'openai/gpt-oss-20b:groq': 'GPT-OSS 20B · Hugging Face routed via Groq',
}
DEFAULT_HF_MODEL = 'openai/gpt-oss-120b:fireworks-ai'
HF_URL = 'https://router.huggingface.co/v1/chat/completions'


class HuggingFaceProvider:
    def __init__(self, key=None, transport=None):
        self.key = key if key is not None else os.getenv('HF_TOKEN', '')
        self.model = os.getenv('HF_MODEL', DEFAULT_HF_MODEL)
        self.transport = transport

    def configured(self):
        return bool(self.key)

    def _select_model(self, requested_model=None):
        model = requested_model or self.model
        if model not in HUGGINGFACE_MODELS:
            raise ProviderError('Choose a supported Hugging Face open-weight model.', 422)
        return model

    async def _post(self, body):
        if not self.key:
            raise ProviderError('HF_TOKEN is missing. Run configure-hf.bat locally or use Groq.', 503)
        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(100, connect=15), transport=self.transport) as client:
                response = await client.post(
                    HF_URL,
                    headers={'Authorization': 'Bearer ' + self.key, 'Content-Type': 'application/json'},
                    json=body,
                )
        except (httpx.TimeoutException, httpx.NetworkError) as exc:
            raise ProviderError('Hugging Face inference is unreachable or timed out. Session progress was not saved for this turn.', 503) from exc
        if response.status_code == 429:
            raise ProviderError('Hugging Face inference quota or rate limit reached. Wait or select Groq; there is no automatic paid fallback.', 429, response.headers.get('retry-after', '60'))
        if response.status_code in (401, 403):
            raise ProviderError('Hugging Face rejected your token or inference permissions. Check HF_TOKEN.', 503)
        if response.status_code in (400, 404, 422):
            raise ProviderError('The selected Hugging Face model or structured-output format was unavailable. Choose another listed model or Groq.', 502)
        if response.status_code >= 400:
            raise ProviderError('Hugging Face inference failed. Check your provider credits and retry.', 503)
        try:
            return response.json()
        except ValueError as exc:
            raise ProviderError('Hugging Face returned an unreadable response.', 502) from exc

    async def check_connection(self, requested_model=None):
        """A genuine miniature inference call, not just a token-format guess."""
        model = self._select_model(requested_model)
        data = await self._post({
            'model': model,
            'messages': [
                {'role': 'system', 'content': 'You are a connection test. Reply with exactly OK.'},
                {'role': 'user', 'content': 'Reply OK.'},
            ],
            'max_tokens': 250,
        })
        try:
            content = data['choices'][0]['message']['content']
            if not isinstance(content, str) or not content.strip():
                raise ValueError('Empty content')
        except (KeyError, IndexError, TypeError, ValueError) as exc:
            raise ProviderError('Hugging Face returned an unexpected completion shape.', 502) from exc
        return {'connected': True, 'model': model,
                'message': 'Hugging Face returned a real model completion. CV-to-report workflow still requires end-to-end testing.'}

    async def generate(self, task, context, schema):
        if task not in TASKS:
            raise ProviderError('Unknown interview generation task.', 422)
        context = dict(context)
        model = self._select_model(context.pop('ai_model', None))
        if task == 'plan':
            context['cv'] = context.get('cv', '')[:10000]
            context['jd'] = context.get('jd', '')[:7000]
            context['project_evidence'] = context.get('project_evidence', '')[:2500]
        prompt = SYSTEM + '\nAGENT SKILL:\n' + load_interviewer_skill() + '\n' + TASKS[task]
        # HF officially documents JSON schema on GPT-OSS via Fireworks.
        # Both formats are still validated locally; no raw JSON goes to UI.
        if model.endswith(':fireworks-ai'):
            fmt = {'type': 'json_schema', 'json_schema': {'name': 'auralis_' + task, 'schema': schema.model_json_schema()}}
        else:
            fmt = {'type': 'json_object'}
            prompt += '\nReturn only valid JSON matching this schema: ' + json.dumps(schema.model_json_schema())
        body = {
            'model': model,
            'messages': [
                {'role': 'system', 'content': prompt},
                {'role': 'user', 'content': json.dumps(context, ensure_ascii=False)},
            ],
            'response_format': fmt,
            'temperature': 0.2,
            'max_tokens': 3000,
        }
        data = await self._post(body)
        try:
            raw = data['choices'][0]['message']['content']
            if not isinstance(raw, str):
                raise ValueError('No output text')
            return schema.model_validate_json(raw)
        except (KeyError, IndexError, TypeError, ValueError, ValidationError) as exc:
            raise ProviderError('The model output did not match the interview schema. Retry; nothing was committed.', 502) from exc
