"""Local readiness check; never reads or prints secret values."""
import importlib.util
import os
from pathlib import Path
from dotenv import dotenv_values
ROOT=Path(__file__).resolve().parent.parent
print('AURALIS 5.7.1 — LOCAL READINESS CHECK')
for module in ['fastapi','uvicorn','httpx','pydantic','pypdf','docx','dotenv','multipart']:
    print(f'{module:12}', 'OK' if importlib.util.find_spec(module) else 'MISSING')
for path in ['app/static/index.html','app/static/app.js','app/static/style.css','skills/adaptive-interviewer/SKILL.md','examples/auralis_codeproof_demo.zip']:
    print(f'{path:50}', 'OK' if (ROOT/path).exists() else 'MISSING')
settings=dotenv_values(ROOT/'.env') if (ROOT/'.env').exists() else {}
print('Hugging Face token present:',bool(settings.get('HF_TOKEN') or os.getenv('HF_TOKEN')))
print('Groq key present:',bool(settings.get('GROQ_API_KEY') or os.getenv('GROQ_API_KEY')))
print('Model:',settings.get('GROQ_MODEL') or os.getenv('GROQ_MODEL') or 'openai/gpt-oss-20b')
print('Local server: start.bat -> http://127.0.0.1:8000')
print('No network or model-inference test is performed by this script.')
