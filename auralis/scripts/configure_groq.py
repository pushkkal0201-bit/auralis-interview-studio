"""Secure local interactive key configuration: never echo the key or write it in Git."""
from getpass import getpass
from pathlib import Path
import re

root=Path(__file__).resolve().parent.parent
path=root/'.env'
if not path.exists():path.write_text((root/'.env.example').read_text(encoding='utf-8'),encoding='utf-8')
key=getpass('Paste your Groq API key (input hidden): ').strip().strip('\"\'').strip()
if key.lower().startswith('bearer '):key=key[7:].strip()
if not re.fullmatch(r'gsk_[A-Za-z0-9_-]{15,}',key):
    raise SystemExit('Invalid Groq key format. Use the full secret from https://console.groq.com/keys (usually gsk_...). Do not paste a key name, hf_ token or sk- key. Nothing was changed.')
content=path.read_text(encoding='utf-8')
if re.search(r'^GROQ_API_KEY=.*$',content,re.M):content=re.sub(r'^GROQ_API_KEY=.*$',lambda _: 'GROQ_API_KEY='+key,content,flags=re.M)
else:content+='\nGROQ_API_KEY='+key+'\n'
path.write_text(content,encoding='utf-8')
print('Groq key stored locally in .env. Restart start.bat to load it. Never share this file.')
