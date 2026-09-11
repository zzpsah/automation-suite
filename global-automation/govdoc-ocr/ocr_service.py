"""Reusable GovDOC OCR/Vision service for government documents."""
from __future__ import annotations
import re, subprocess, tempfile
from pathlib import Path
from typing import Any
from .backend import get_backend
from .preprocess import preprocess_image
from .government_document import analyze_document
from .sarkari_normalizer import normalize_sarkari_text

OCR_SERVICE_VERSION="3.0"

def _clean(text):
    text=(text or '').replace('\x00',' '); text=re.sub(r'[ \t]+',' ',text); return re.sub(r'\n{3,}','\n\n',text).strip()

def _embedded(path):
    try:
        from pypdf import PdfReader
        return _clean('\n'.join(p.extract_text() or '' for p in PdfReader(str(path)).pages))
    except Exception:return ''

def _render(path,workdir):
    prefix=Path(workdir)/'page'; subprocess.run(['pdftoppm','-r','250','-jpeg',str(path),str(prefix)],check=True,capture_output=True,text=True,timeout=180)
    return sorted(Path(workdir).glob('page-*.jpg'))

def _ocr_images(images,workdir,backend_name='tesseract',language='hin+eng'):
    backend=get_backend(backend_name); pages=[]; all_text=[]
    for i,image in enumerate(images,1):
        prepared=Path(workdir)/f'prepared-{i}.png'
        prep=preprocess_image(str(image),str(prepared),profile='document')
        result=backend.extract_image(prep['path'],language=language)
        text=_clean(result.text); pages.append({'page_number':i,'text':text,'backend':result.backend,'confidence':result.confidence,'preprocessing':prep})
        all_text.append(text)
    return '\n\n'.join(all_text),pages

def _build(text,filename,method,pages=None,backend=None):
    normalized=normalize_sarkari_text(text); intelligence=analyze_document(normalized)
    meta=intelligence.get('subject',{}).get('value')
    result={
      'text':text,'normalized_text':normalized,'extraction_method':method,'filename':filename,
      'ocr_service_version':OCR_SERVICE_VERSION,'metadata':intelligence,
      'subject':meta or '','authority':intelligence.get('authority',{}).get('value') or '',
      'category':intelligence.get('document_type',{}).get('value','other'),
      'short_description':intelligence.get('short_description'),
      'pages':pages or [],'ocr':{'backend':backend,'language':'hin+eng'} if backend else {'backend':None,'language':None}
    }
    return result

def process_pdf(pdf_path,work_dir,*,min_embedded_chars=80,backend='tesseract'):
    path=Path(pdf_path)
    if not path.exists():raise FileNotFoundError(pdf_path)
    if path.suffix.lower()!='.pdf':raise ValueError('GovDOC OCR accepts PDF files only')
    text=_embedded(path); method='GovDOC Vision: embedded-text'; pages=[]; used_backend=None
    if len(re.sub(r'\s+','',text))<min_embedded_chars:
        images=_render(path,work_dir); text,pages=_ocr_images(images,work_dir,backend); method=f'GovDOC Vision: {backend} Hindi+English'; used_backend=backend
    if not text:raise RuntimeError('No text could be extracted from PDF')
    return _build(text,path.name,method,pages,used_backend)

def process_image(image_path,work_dir,*,backend='tesseract',language='hin+eng'):
    path=Path(image_path)
    if not path.exists():raise FileNotFoundError(image_path)
    with tempfile.TemporaryDirectory(dir=work_dir) as tmp:
        prepared=Path(tmp)/'prepared.png'; prep=preprocess_image(str(path),str(prepared),profile='document')
        result=get_backend(backend).extract_image(str(prepared),language=language)
        text=_clean(result.text)
        if not text:raise RuntimeError('No text could be extracted from image')
        output=_build(text,path.name,f'GovDOC Vision: {backend}',[{'page_number':1,'text':text,'backend':result.backend,'confidence':result.confidence,'preprocessing':prep}],backend)
        return output

def process_document(path,work_dir,*,backend='tesseract'):
    suffix=Path(path).suffix.lower()
    if suffix=='.pdf':return process_pdf(path,work_dir,backend=backend)
    if suffix in {'.jpg','.jpeg','.png','.tif','.tiff','.webp'}:return process_image(path,work_dir,backend=backend)
    raise ValueError(f'Unsupported document type: {suffix}')

def process_pdf_bytes(data,filename='document.pdf',work_dir=None):
    if not data:raise ValueError('PDF data is empty')
    with tempfile.TemporaryDirectory(dir=work_dir) as tmp:
        path=Path(tmp)/(Path(filename).name or 'document.pdf'); path.write_bytes(data); return process_pdf(str(path),tmp)
