"""Secure local token setup. No token printed to console."""
from getpass import getpass
from pathlib import Path
import re

root = Path(__file__).resolve().parent.parent
path = root / '.env'
if not path.exists():
    path.write_text((root / '.env.example').read_text(encoding='utf-8'), encoding='utf-8')
token = getpass('Paste your Hugging Face access token (input hidden): ').strip()
if not re.fullmatch(r'hf_[A-Za-z0-9]{15,}', token):
    raise SystemExit('This does not look like a Hugging Face token (hf_...). Nothing was changed.')
content = path.read_text(encoding='utf-8')
if re.search(r'^HF_TOKEN=.*$', content, re.M):
    content = re.sub(r'^HF_TOKEN=.*$', lambda _: 'HF_TOKEN=' + token, content, flags=re.M)
else:
    content += '\nHF_TOKEN=' + token + '\n'
path.write_text(content, encoding='utf-8')
print('Token stored in local .env. Restart the server; never share this file.')
