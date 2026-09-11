from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from backend import available_backends, get_backend
from government_document import analyze_document
from search import search_documents

def test_tesseract_backend_available():
    assert 'tesseract' in available_backends()
    assert get_backend('tesseract').name == 'tesseract'

def test_government_intelligence_is_evidence_based():
    result=analyze_document('बिहार विद्यालय परीक्षा समिति\nविषय: स्पॉट नामांकन हेतु सूचना\nदिनांक: 12.09.2026')
    assert result['authority']['value']
    assert 'स्पॉट नामांकन' in result['subject']['value']
    assert result['document_type']['value']=='admission'

def test_keyword_search():
    docs=[{'id':'1','text':'BSEB spot admission 2026','metadata':{'district':'Gaya'}}]
    assert search_documents(docs,'BSEB admission')[0]['document_id']=='1'
