"""Public-facing product cleanup: copy, navigation and safe disclosure regressions."""
from pathlib import Path
from bs4 import BeautifulSoup

ROOT=Path(__file__).resolve().parents[1]/'app'/'static'
HTML=(ROOT/'index.html').read_text(encoding='utf-8')
DOM=BeautifulSoup(HTML,'html.parser')
JS=(ROOT/'app.js').read_text(encoding='utf-8')


def test_public_markup_has_no_build_labels_or_template_placeholders():
    text=' '.join(DOM.stripped_strings).lower()
    for banned in ['intelligence / 5.6','auralis 5.6','lorem ipsum','feature title goes here',
                   'captured from the scripted demo','dev mode','build #','powered by ai',
                   'model-generated practice feedback','local pilot']:
        assert banned not in text
    assert DOM.title.string=='Auralis | The Interview Studio'


def test_core_flow_and_preserved_modules():
    views={e.get('data-view') for e in DOM.select('.nav')}
    assert len(views)==18
    assert set(['setup','arena','report','history','campus','bilingual','college','whiteboard','match','knowledge']).issubset(views)
    groups=DOM.select('nav details.nav-collection')
    assert len(groups)==2
    assert all(not group.has_attr('open') for group in groups)
    assert DOM.select_one('#setup-form #cv')
    assert DOM.select_one('#setup-form #jd')
    assert DOM.select_one('#setup-form #consent')
    assert DOM.select_one('#setup-form #synthetic-data')


def test_transparency_is_accessible_without_warning_wall():
    assert DOM.select_one('.connection-details #connection')
    assert DOM.select_one('#assessment-disclosure summary')
    assert DOM.select_one('#assessment-disclosure')
    assert DOM.select_one('#live-camera')
    assert DOM.select_one('#evidence-session').name=='select'
    assert DOM.select_one('.xray').get('open') is None


def test_genuine_product_capture_and_sanitized_report_detail():
    assert (ROOT/'media/practice-room.webp').stat().st_size>30000
    assert 'report-method-details' in JS
    assert 'Question preparation notes' in JS
    assert 'MODEL-GENERATED PRACTICE FEEDBACK' not in JS
    assert 'GENERATION ATTEMPTS:' not in JS
    assert "document.createTextNode(part)" in JS
    assert 'claim_provenance' in JS


def test_specialist_navigation_is_revealed_when_opened_programmatically():
    assert "closest('details.nav-collection')" in JS
    assert 'if(activeSection)activeSection.open=true' in JS
