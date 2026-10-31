"""Static, non-executing Python repository inspection for evidence-grounded interviews.

This does not prove authorship, safety, exploitability, or behavior at runtime.
"""
from __future__ import annotations
import ast
import io
import re
import stat
import zipfile
from pathlib import PurePosixPath

MAX_ARCHIVE = 4 * 1024 * 1024
MAX_UNCOMPRESSED = 1600 * 1024
MAX_PY_FILE = 100 * 1024
MAX_FILES = 45
MAX_REFS = 14
SKIP_PARTS = {'.git', '.venv', 'venv', 'node_modules', '__pycache__', 'site-packages',
              'dist', 'build', 'vendor', '.tox', '.mypy_cache', '.pytest_cache', 'tests'}
SECRET_PARTS = {'secret', 'credential', 'private', 'password', '.env', 'token', 'apikey', 'api_key'}
SRC_SYMBOLS = re.compile(r'book|slot|reserv|queue|concurr|transact|payment|auth|login|order|api|route|valid|lock|session|cache|worker|retry|database|db|health|rate|test', re.I)
SECRET_LINES = re.compile(r'(api[_-]?key|password|access[_-]?token|secret|private[_-]?key)\s*[=:]', re.I)
# Redact common actual credential values, including embedded Authorization strings.
# Not an exhaustive DLP scanner; never upload a repository containing real secrets.
SECRET_VALUES = re.compile(
    r'(?:gsk_[A-Za-z0-9_-]{10,}|hf_[A-Za-z0-9]{10,}|sk-[A-Za-z0-9_-]{16,}|'
    r'ghp_[A-Za-z0-9]{16,}|github_pat_[A-Za-z0-9_]{16,}|AKIA[A-Z0-9]{16}|'
    r'Bearer\s+[A-Za-z0-9._~+/-]{15,}|-----BEGIN [A-Z ]*PRIVATE KEY-----)',re.I)


class CodeProofError(ValueError):
    pass


def _allowed_path(name: str) -> str | None:
    clean=name.replace('\\','/')
    parts=PurePosixPath(clean).parts
    if not parts or clean.startswith('/') or any(p in ('..','.') for p in parts): return None
    # Github ZIP archives have a varying top-level directory. Remove it only when present.
    if len(parts)>1 and '-' in parts[0] and not parts[0].endswith('.py'):
        parts=parts[1:]
    if not parts or len(parts)>8 or any(p.startswith('.') or p in SKIP_PARTS for p in parts[:-1]):return None
    filename=parts[-1]
    if not filename.endswith('.py') or filename.startswith('.') or filename == '__init__.py':return None
    if any(t in filename.lower() for t in SECRET_PARTS):return None
    return '/'.join(parts)


def _redact(line: str) -> str:
    if SECRET_LINES.search(line): return '[REDACTED CONFIG/SECRET-LIKE ASSIGNMENT]'
    if SECRET_VALUES.search(line): return '[REDACTED EMBEDDED SECRET-LIKE VALUE]'
    if len(line)>170:return line[:167]+'...'
    return line


def inspect_zip(data: bytes) -> dict:
    if not data or len(data)>MAX_ARCHIVE:raise CodeProofError('Provide a ZIP smaller than 4 MB.')
    try: archive=zipfile.ZipFile(io.BytesIO(data))
    except (ValueError,zipfile.BadZipFile) as ex:raise CodeProofError('Not a valid ZIP archive.') from ex
    with archive:
        members=archive.infolist()
        if len(members)>250:raise CodeProofError('Too many archive entries. Use a small source-only ZIP.')
        if sum(m.file_size for m in members)>MAX_UNCOMPRESSED:raise CodeProofError('Repository expands beyond the safe 1.6 MB limit.')
        permitted=[];seen=set()
        for member in members:
            mode=member.external_attr >> 16
            if member.is_dir() or stat.S_ISLNK(mode):continue
            path=_allowed_path(member.filename)
            if path and path not in seen:
                if member.file_size>MAX_PY_FILE:continue
                if member.flag_bits & 1:continue
                seen.add(path);permitted.append((path,member))
        if not permitted:raise CodeProofError('No supported Python source files found. Upload a source-only ZIP.')
        if len(permitted)>MAX_FILES:raise CodeProofError('Limit the project to 45 Python files or fewer.')
        refs=[];parse_errors=[]
        for path,member in permitted:
            try:
                raw=archive.read(member)
                source=raw.decode('utf-8-sig')
                tree=ast.parse(source,filename=path)
            except (UnicodeError, SyntaxError, RuntimeError,zipfile.BadZipFile) as e:
                parse_errors.append(path+': '+type(e).__name__);continue
            lines=source.splitlines()
            candidates=[]
            for node in ast.walk(tree):
                if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef)):
                    name=node.name
                    importance=(12 if SRC_SYMBOLS.search(name) else 1)
                    if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)):
                        importance+=3
                    # Deterministic *indicators*, not claims that a vulnerability exists.
                    segment='\n'.join(lines[max(0,node.lineno-1):min(len(lines),getattr(node,'end_lineno',node.lineno))])
                    tags=[]
                    if re.search(r'commit\(|transaction|begin\(|with_for_update|select_for_update|atomic\(',segment,re.I):tags.append('transaction-related code')
                    if re.search(r'if\s+.*(avail|capacity|slot|exists)|if\s+not\s+.*(book|reserv)',segment,re.I):tags.append('availability/validation condition')
                    if re.search(r'lock|semaphore|mutex',segment,re.I):tags.append('synchronization reference')
                    if re.search(r'insert|create|save\(|add\(|update\(',segment,re.I):tags.append('write operation')
                    if re.search(r'@app\.|@router\.|@api\.',segment,re.I):tags.append('API route')
                    if re.search(r'raise\s+|except\s+',segment,re.I):tags.append('error handling')
                    importance+=min(len(tags),5)
                    candidates.append((importance,node,tags))
            candidates.sort(key=lambda x:(-x[0],x[1].lineno))
            for _,node,tags in candidates[:5]:
                end=min(len(lines),getattr(node,'end_lineno',node.lineno),node.lineno+12)
                snippet='\n'.join(f'{idx+1:>4}: {_redact(lines[idx])}' for idx in range(node.lineno-1,end))
                refs.append({'id':f'R{len(refs)+1:02d}','path':path,'symbol':node.name,'line_start':node.lineno,
                             'line_end':getattr(node,'end_lineno',node.lineno),'snippet':snippet[:1800],
                             'indicators':tags,'note':'Static source observation only; runtime behavior not verified.'})
                if len(refs)>=MAX_REFS:break
            if len(refs)>=MAX_REFS:break
    if not refs:raise CodeProofError('Python files found but no extractable functions or classes. Try a different source ZIP.')
    excerpt=['CODEPROOF — UNTRUSTED STATIC SOURCE OBSERVATIONS. Do not treat as proof of ownership, behavior, or an exploitable bug.']
    for r in refs:
        excerpt.append(f"[{r['id']}] {r['path']}:{r['line_start']}-{r['line_end']} {r['symbol']} | indicators: {', '.join(r['indicators']) or 'function/class'}\n{r['snippet'][:420]}")
    return {'language':'Python','source_files_scanned':len(permitted),'refs':refs,'parse_errors':parse_errors[:8],
            'evidence_text':'\n'.join(excerpt)[:11500],
            'limitations':['No uploaded code was executed.','Indicators are not verified defects or runtime observations.',
                           'Only bounded source excerpts are analyzed; not a full security audit.']}
