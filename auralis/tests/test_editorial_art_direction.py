"""V4 design architecture checks. Functional tests are in the backend suite."""
from pathlib import Path
from bs4 import BeautifulSoup
import re
ROOT=Path(__file__).resolve().parents[1]
HTML=(ROOT/'app/static/index.html').read_text(encoding='utf-8')
CSS=(ROOT/'app/static/studio.css').read_text(encoding='utf-8')
LEGACY=(ROOT/'app/static/style.css').read_text(encoding='utf-8')
SOUP=BeautifulSoup(HTML,'html.parser')

def test_art_direction_tokens_and_no_banned_template_styles():
    for c in ['#f1eee5','#242b26','#6e795d']:
        assert c in CSS.lower()
    for banned in ['linear-gradient','radial-gradient','conic-gradient','#000000','#ffffff']:
        assert banned not in CSS.lower()
    for banned in ['inter,','roboto','fraunces','space grotesque']:
        assert banned not in CSS.lower()
    assert not re.search(r'linear-gradient|radial-gradient', LEGACY)

def test_original_interactive_ids_and_scripts_are_retained():
    ids=[x['id'] for x in SOUP.select('[id]')]
    assert len(ids)==len(set(ids))
    required={'setup-form','cv','cv-file','jd','role','provider','ai-model','consent','synthetic-data',
              'sample','hero-sample','start','answer','submit-answer','stop-record','finish',
              'print','print-full','export','retry-submit','report-content','transcript','history-list',
              'compare-button','inspect-zip','inspect-github','incident-select','delete-all','check-live'}
    assert required.issubset(set(ids)),required-set(ids)
    for src in ['/static/style.css','/static/studio.css','/static/app.js','/static/premium.js']:
        assert src in HTML
    assert SOUP.select_one('link[href="/static/style.css"]').get('media')=='print'
    assert {'setup','arena','report','history','compare','lab','practical','workspace','campus','bilingual','bank','college','reliability','live','match','whiteboard','score-evidence','knowledge'}.issubset({x.get('data-view') for x in SOUP.select('.nav')})

def test_real_interface_capture_not_generic_hero_art():
    capture=SOUP.select_one('.product-capture img')
    assert capture and capture.get('src')=='/static/media/practice-room.webp'
    assert 'A VIEW FROM THE PRACTICE ROOM' in HTML
    assert (ROOT/'app/static/media/practice-room.webp').stat().st_size>10000
    assert 'not a human evaluator' in HTML
    assert not any((ROOT/'app/static').rglob('*.ttf'))
    assert not any((ROOT/'app/static').rglob('*.woff*'))

def test_structured_brief_and_optional_tools():
    assert len(SOUP.select('#setup-form>.two-col>.panel'))==2
    extras=SOUP.select_one('details#advanced-tools')
    assert extras is not None and not extras.has_attr('open')
    for control in ['inspect-zip','inspect-github','incident-select','rea-file']:
        assert extras.select_one('#'+control)
    assert SOUP.select_one('#setup-form .finalize-block #consent')
    assert SOUP.select_one('#setup-form .finalize-block #synthetic-data')
    assert len(SOUP.select('.process-story'))==3
    assert not SOUP.select('.hero .hero-image')

def test_font_allowlist_remains_constrained():
    backend=(ROOT/'app/main.py').read_text(encoding='utf-8')
    assert 'https://fonts.googleapis.com' in backend
    assert 'https://fonts.gstatic.com' in backend
    assert "script-src 'self'" in backend
    assert 'font-src' in backend
