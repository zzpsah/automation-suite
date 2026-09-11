"""Bridge the production document processor to the shared GovDOC Vision engine."""
from __future__ import annotations
import hashlib, importlib.util
from pathlib import Path
from typing import Any


def _service():
    root=Path(__file__).resolve().parents[2] / "govdoc-ocr"
    init=root/"__init__.py"
    spec=importlib.util.spec_from_file_location("govdoc_ocr",init,submodule_search_locations=[str(root)])
    if spec is None or spec.loader is None: raise ImportError("Unable to load GovDOC OCR package")
    module=importlib.util.module_from_spec(spec)
    import sys
    sys.modules["govdoc_ocr"]=module
    spec.loader.exec_module(module)
    return module

process_pdf_bytes=_service().process_pdf_bytes
_CACHE: dict[str, dict[str, Any]]={}

def _run(data: bytes, filename: str="document.pdf") -> dict[str, Any]:
    key=hashlib.sha256(data).hexdigest()
    if key not in _CACHE: _CACHE[key]=process_pdf_bytes(data,filename)
    return _CACHE[key]

def install(processor_module) -> None:
    original_embedded,original_ocr,original_metadata=processor_module.embedded_pdf_text,processor_module.ocr_pdf,processor_module.extract_metadata
    def embedded(data):
        try:
            result=_run(data)
            return result['text'] if 'embedded-text' in result['extraction_method'] else ''
        except Exception:return original_embedded(data)
    def ocr(data,workdir):
        try:return _run(data)['text']
        except Exception:return original_ocr(data,workdir)
    def metadata(text,filename):
        for result in reversed(list(_CACHE.values())):
            if result.get('text')==text:
                info=result.get('metadata',{})
                return (result.get('subject',''),result.get('authority',''),result.get('reference_number',''),result.get('issue_date',''),result.get('normalized_issue_date'),result.get('short_description',''),result.get('detailed_summary',''),result.get('category_key','other'),result.get('category','Other'),result.get('confidence','MEDIUM'))
        return original_metadata(text,filename)
    processor_module.embedded_pdf_text=embedded; processor_module.ocr_pdf=ocr; processor_module.extract_metadata=metadata
