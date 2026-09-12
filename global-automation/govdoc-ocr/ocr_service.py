"""Reusable GovDOC OCR/Vision service for government documents."""
from __future__ import annotations
import re, subprocess, tempfile
from pathlib import Path
from .backend import available_backends, get_backend
from .backend_policy import choose_backend
from .preprocess import preprocess_image
from .government_document import analyze_document
from .sarkari_normalizer import normalize_sarkari_text
from .diagnostics import inspect_image
from .reading_order import line_text
from .visual_marks import analyze_visual_marks

OCR_SERVICE_VERSION="4.4"

def _clean(text):
    text=(text or '').replace('\x00',' '); text=re.sub(r'[ \t]+',' ',text); return re.sub(r'\n{3,}','\n\n',text).strip()

def _embedded_pages(path):
    try:
        from pypdf import PdfReader
        return [_clean(page.extract_text() or '') for page in PdfReader(str(path)).pages]
    except Exception:
        return []

def _embedded(path): return _clean('\n\n'.join(_embedded_pages(path)))

def _render(path,workdir):
    prefix=Path(workdir)/'page'; subprocess.run(['pdftoppm','-r','250','-jpeg',str(path),str(prefix)],check=True,capture_output=True,text=True,timeout=180)
    return sorted(Path(workdir).glob('page-*.jpg'))

def _render_page(path,workdir,page_number):
    prefix=Path(workdir)/f'page-{page_number}'
    subprocess.run(['pdftoppm','-f',str(page_number),'-singlefile','-r','250','-jpeg',str(path),str(prefix)],check=True,capture_output=True,text=True,timeout=180)
    return prefix.with_suffix('.jpg')

def _select_backend(image_path, requested):
    diagnostics=inspect_image(str(image_path)).to_dict()
    decision=choose_backend(requested=requested,quality_score=diagnostics.get('quality_score'),available=tuple(available_backends()))
    return decision,diagnostics

def _ocr_page(image,workdir,page_number,backend_name='tesseract',language='hin+eng'):
    decision,diagnostics=_select_backend(image,backend_name)
    prepared=Path(workdir)/f'prepared-{page_number}.png'
    prep=preprocess_image(str(image),str(prepared),profile='document')
    result=get_backend(decision.backend).extract_image(str(prepared),language=language)
    text=_clean(result.text)
    regions=[region.to_dict() for region in result.regions]
    lines=line_text(regions) if regions else []
    visual_marks=analyze_visual_marks(str(image))
    page={'page_number':page_number,'text':text,'backend':result.backend,'confidence':result.confidence,'preprocessing':prep,'diagnostics':diagnostics,'visual_marks':visual_marks,'regions':regions,'lines':lines,'backend_policy':{'requested':backend_name,'selected':decision.backend,'reason':decision.reason,'escalated':decision.escalated},'extraction_method':f'ocr:{result.backend}'}
    return text,page,decision

def _ocr_images(images,workdir,backend_name='tesseract',language='hin+eng'):
    pages=[]; all_text=[]; decisions=[]
    for i,image in enumerate(images,1):
        text,page,decision=_ocr_page(image,workdir,i,backend_name,language); pages.append(page); all_text.append(text); decisions.append(decision)
    return '\n\n'.join(all_text),pages,decisions

def _build(text,filename,method,pages=None,backend=None,backend_decisions=None):
    normalized=normalize_sarkari_text(text); intelligence=analyze_document(normalized); meta=intelligence.get('subject',{}).get('value')
    return {'schema_version':'1.1','text':text,'normalized_text':normalized,'extraction_method':method,'filename':filename,'ocr_service_version':OCR_SERVICE_VERSION,'metadata':intelligence,'subject':meta or '','authority':intelligence.get('authority',{}).get('value') or '','category':intelligence.get('document_type',{}).get('value','other'),'short_description':intelligence.get('short_description'),'pages':pages or [],'ocr':{'backend':backend,'language':'hin+eng','backend_decisions':backend_decisions or []} if backend else {'backend':None,'language':None,'backend_decisions':[]}}

def process_pdf(pdf_path,work_dir,*,min_embedded_chars=80,backend='tesseract'):
    path=Path(pdf_path)
    if not path.exists(): raise FileNotFoundError(pdf_path)
    if path.suffix.lower()!='.pdf': raise ValueError('GovDOC OCR accepts PDF files only')
    Path(work_dir).mkdir(parents=True, exist_ok=True)
    embedded_pages=_embedded_pages(path)
    if not embedded_pages: raise RuntimeError('Unable to read PDF pages')
    threshold=max(1,int(min_embedded_chars)); pages=[]; texts=[]; decisions=[]; ocr_used=False
    for page_number,embedded_text in enumerate(embedded_pages,1):
        if len(re.sub(r'\s+','',embedded_text)) >= threshold:
            pages.append({'page_number':page_number,'text':embedded_text,'backend':None,'confidence':None,'preprocessing':None,'diagnostics':None,'visual_marks':None,'regions':[],'lines':[],'backend_policy':None,'extraction_method':'embedded-text'}); texts.append(embedded_text); continue
        image=_render_page(path,work_dir,page_number); text,page,decision=_ocr_page(image,work_dir,page_number,backend); pages.append(page); texts.append(text); decisions.append({'page':page_number,'requested':backend,'selected':decision.backend,'reason':decision.reason,'escalated':decision.escalated}); ocr_used=True
    text=_clean('\n\n'.join(texts))
    if not text: raise RuntimeError('No text could be extracted from PDF')
    method=(f'GovDOC Vision: mixed embedded-text/{backend} OCR' if ocr_used and any(p['extraction_method']=='embedded-text' for p in pages) else (f'GovDOC Vision: {backend} Hindi+English' if ocr_used else 'GovDOC Vision: embedded-text'))
    return _build(text,path.name,method,pages,backend if ocr_used else None,decisions)

def process_image(image_path,work_dir,*,backend='tesseract',language='hin+eng'):
    path=Path(image_path)
    if not path.exists(): raise FileNotFoundError(image_path)
    Path(work_dir).mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=work_dir) as tmp:
        text,page,decision=_ocr_page(str(path),tmp,1,backend,language)
        if not text: raise RuntimeError('No text could be extracted from image')
        return _build(text,path.name,f'GovDOC Vision: {decision.backend}',[page],decision.backend,[{'page':1,'requested':backend,'selected':decision.backend,'reason':decision.reason,'escalated':decision.escalated}])

def process_document(path,work_dir,*,backend='tesseract'):
    suffix=Path(path).suffix.lower()
    if suffix=='.pdf': return process_pdf(path,work_dir,backend=backend)
    if suffix in {'.jpg','.jpeg','.png','.tif','.tiff','.webp'}: return process_image(path,work_dir,backend=backend)
    raise ValueError(f'Unsupported document type: {suffix}')

def process_pdf_bytes(data,filename='document.pdf',work_dir=None,*,backend='tesseract'):
    if not data: raise ValueError('PDF data is empty')
    with tempfile.TemporaryDirectory(dir=work_dir) as tmp:
        path=Path(tmp)/(Path(filename).name or 'document.pdf'); path.write_bytes(data); return process_pdf(str(path),tmp,backend=backend)
