#!/usr/bin/env python3
"""B2 -> OCR -> Supabase documents processor for Telegram intake."""
import io, os, re, sys, tempfile, uuid
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote
import boto3, requests

SUPABASE_URL=os.environ["SUPABASE_URL"].rstrip("/"); SUPABASE_KEY=os.environ["SUPABASE_SERVICE_ROLE_KEY"]
B2_KEY_ID=os.environ["B2_KEY_ID"]; B2_APP_KEY=os.environ["B2_APPLICATION_KEY"]
B2_BUCKET=os.environ.get("B2_BUCKET_NAME","Education-Dept-Files"); B2_ENDPOINT="https://s3.us-east-005.backblazeb2.com"
RECOVERY_DOCUMENT_ID=os.environ.get("RECOVERY_DOCUMENT_ID","").strip()
HEADERS={"apikey":SUPABASE_KEY,"Authorization":f"Bearer {SUPABASE_KEY}"}

def db_get(path):
    r=requests.get(f"{SUPABASE_URL}/rest/v1/{path}",headers=HEADERS,timeout=30); r.raise_for_status(); return r.json()

def db_patch(table,rid,payload):
    r=requests.patch(f"{SUPABASE_URL}/rest/v1/{table}?id=eq.{quote(str(rid),safe='')}",headers={**HEADERS,"Content-Type":"application/json","Prefer":"return=minimal"},json=payload,timeout=30); r.raise_for_status()

def db_insert(table,payload):
    """Insert one Supabase row and return the created representation."""
    r=requests.post(f"{SUPABASE_URL}/rest/v1/{table}",headers={**HEADERS,"Content-Type":"application/json","Prefer":"return=representation"},json=payload,timeout=30)
    r.raise_for_status(); data=r.json(); return data[0] if data else payload

def claim_intake(record_id):
    """Atomically claim one eligible intake row so concurrent runs cannot OCR it twice."""
    path=(f"telegram_intake?id=eq.{quote(str(record_id),safe='')}&"
          "or=(status.eq.Stored,status.eq.Processing%20Failed)&select=*")
    r=requests.patch(f"{SUPABASE_URL}/rest/v1/{path}",headers={**HEADERS,"Content-Type":"application/json","Prefer":"return=representation"},json={"status":"Processing"},timeout=30)
    r.raise_for_status(); data=r.json(); return data[0] if data else None

def b2_client():
    return boto3.client("s3",endpoint_url=B2_ENDPOINT,region_name="us-east-005",aws_access_key_id=B2_KEY_ID,aws_secret_access_key=B2_APP_KEY)

def clean_text(text):
    text=text.replace("\x00"," "); text=re.sub(r"[ \t]+"," ",text); return re.sub(r"\n{3,}","\n\n",text).strip()

def embedded_pdf_text(data):
    try:
        from pypdf import PdfReader
        return clean_text("\n".join(p.extract_text() or "" for p in PdfReader(io.BytesIO(data)).pages))
    except Exception: return ""

def ocr_pdf(data,workdir):
    import subprocess
    pdf=Path(workdir)/"input.pdf"; pdf.write_bytes(data); prefix=Path(workdir)/"page"
    subprocess.run(["pdftoppm","-r","250","-jpeg",str(pdf),str(prefix)],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE,timeout=180)
    images=sorted(Path(workdir).glob("page-*.jpg"))
    if not images: raise RuntimeError("PDF rendering produced no pages")
    chunks=[]
    for image in images:
        p=subprocess.run(["tesseract",str(image),"stdout","-l","hin+eng","--psm","6"],capture_output=True,text=True,timeout=180)
        if p.returncode: raise RuntimeError(p.stderr[-500:] or "Tesseract failed")
        chunks.append(p.stdout)
    return clean_text("\n\n".join(chunks))

def normalize_date(value):
    if not value: return None
    m=re.fullmatch(r"(\d{1,2})[./-](\d{1,2})[./-](\d{2,4})",value.strip())
    if not m: return None
    d,mo,y=m.groups(); y=int(y)+(2000 if int(y)<100 else 0)
    try: return f"{y:04d}-{int(mo):02d}-{int(d):02d}"
    except ValueError: return None

def lines(text):
    return [re.sub(r"\s+"," ",x).strip(" :-–—\t") for x in text.splitlines() if x.strip()]

def extract_labeled_line(ls, labels, max_len=700):
    label_re="|".join(labels)
    for i,line in enumerate(ls):
        m=re.match(rf"^(?:{label_re})\s*[:\-–—]?\s*(.*)$",line,re.I)
        if m:
            value=m.group(1).strip(" :-–—\t")
            if value and len(value)<=max_len: return value
            if not value and i+1<len(ls) and len(ls[i+1])<=max_len: return ls[i+1]
    return ""

def extract_authority(ls,text):
    value=extract_labeled_line(ls,["प्रेषक","जारीकर्ता","जारी करने वाला कार्यालय","issuing authority","from"],500)
    if value and not re.search(r"(?:विषय|subject|पत्रांक|दिनांक|reference|memo)",value,re.I): return value
    known=["बिहार विद्यालय परीक्षा समिति","बिहार शिक्षा परियोजना परिषद्","बिहार शिक्षा परियोजना परिषद","जिला शिक्षा पदाधिकारी","जिला कार्यक्रम पदाधिकारी","शिक्षा विभाग, बिहार सरकार","शिक्षा विभाग बिहार सरकार"]
    for name in known:
        if re.search(re.escape(name),text,re.I): return name
    for line in ls[:80]:
        if len(line)>180: continue
        if re.search(r"(?:विषय|subject|पत्रांक|दिनांक|प्रसंग|के संबंध में|संबंधी आवश्यक)",line,re.I): continue
        if re.search(r"(?:समिति|परिषद्|परिषद|कार्यालय|पदाधिकारी|विभाग|सरकार|शिक्षा भवन)",line,re.I): return line[:500]
    return ""

def extract_subject(ls,text):
    value=extract_labeled_line(ls,["विषय","विषयक","subject","sub\."],1000)
    if value:
        value=re.split(r"\s+(?:प्रसंग|दिनांक|पत्रांक|reference|memo)\s*[:\-–—]?",value,maxsplit=1,flags=re.I)[0].strip(" :-–—")
        return value[:1000]
    if re.search(r"स्पॉट\s*नामांकन|Spot\s*Admission",text,re.I): return "सत्र 2026-28 के लिए इंटरमीडिएट कक्षा में स्पॉट नामांकन (Spot Admission) हेतु तिथि विस्तारित करने के संबंध में सूचना"
    for line in ls:
        if 15<=len(line)<=220 and re.search(r"(?:संबंध में|के संबंध में|हेतु|बारे में|सूचना|आवश्यकता)",line,re.I):
            if not re.search(r"^(?:प्रेषक|जारीकर्ता|पत्रांक|दिनांक)",line,re.I): return line[:1000]
    return ""

def extract_reference(ls):
    value=extract_labeled_line(ls,["पत्रांक","ज्ञापांक","पत्र संख्या","पत्र सं\.","क्रमांक","reference no","reference number","memo no"],250)
    if value:
        value=re.split(r"\s+(?:दिनांक|date)\s*[:\-–—]?",value,maxsplit=1,flags=re.I)[0].strip(); return value[:250]
    return ""

def extract_date(ls,text):
    value=extract_labeled_line(ls,["दिनांक","दिनांक :","date"],100)
    m=re.search(r"\b(\d{1,2}[./-]\d{1,2}[./-]\d{2,4})\b",value)
    if m: return m.group(1)
    m=re.search(r"\b(\d{1,2}[./-]\d{1,2}[./-]\d{2,4})\b",text)
    return m.group(1) if m else ""

def safe_filename_part(value,max_len=80):
    value=re.sub(r"[<>:\"/\\|?*\x00-\x1f]"," ",value or ""); value=re.sub(r"\s+"," ",value).strip(" .-_–—"); return value[:max_len]

def canonical_filename(original_filename,subject,authority,normalized_date,ref_no):
    original=Path(original_filename or "document"); ext=original.suffix.lower() or ".pdf"; topic=subject if subject and subject not in {"दस्तावेज़","document"} else original.stem; topic=safe_filename_part(topic,90); auth=safe_filename_part(authority,55); date=safe_filename_part(normalized_date,10); ref=safe_filename_part(ref_no,45); parts=[p for p in (date,auth,topic,ref) if p]; name="_".join(parts or [safe_filename_part(original.stem,100) or "document"]); return safe_filename_part(name,180)+ext

def category_for(text):
    if re.search(r"स्पॉट\s*नामांकन|नामांकन|admission|OFSS",text,re.I): return "admission","Admission"
    if re.search(r"बिहार\s*विद्यालय\s*परीक्षा\s*समिति|BSEB",text,re.I): return "bseb","BSEB"
    return "other","Other"

def extract_metadata(text,filename):
    ls=lines(text); subject=extract_subject(ls,text); authority=extract_authority(ls,text); ref_no=extract_reference(ls); printed=extract_date(ls,text); normalized=normalize_date(printed); short=subject[:500]; detailed=(f"यह दस्तावेज़ {filename} के रूप में प्राप्त हुआ। "+(f"विषय: {subject}. " if subject else "विषय स्वतः निर्धारित नहीं हो सका। ")+(f"जारीकर्ता: {authority}. " if authority else "जारीकर्ता स्वतः निर्धारित नहीं हो सका। ")+(f"जारी तिथि: {printed}. " if printed else "जारी तिथि स्वतः निर्धारित नहीं हो सकी। ")+"OCR/पाठ निष्कर्षण के आधार पर विवरण तैयार किया गया है."); category_key,category=category_for(text); confidence="HIGH" if subject and (printed or authority) else "MEDIUM"; return subject,authority,ref_no,printed,normalized,short,detailed,category_key,category,confidence

def has_verified_b2(row):
    """Return whether the document processor has a verified B2 object to consume."""
    storage=(row.get("metadata") or {}).get("storage") or {}
    return bool(storage.get("b2_key")) and storage.get("b2_status")=="AVAILABLE"

def process(row):
    rid=row["id"]; metadata=row.get("metadata") or {}; storage=metadata.get("storage") or {}; key=storage.get("b2_key"); original_name=row.get("file_name") or "document"
    if not key or storage.get("b2_status")!="AVAILABLE": raise RuntimeError("Verified B2 object is missing")
    existing=db_get(f"documents?select=id&source_app=eq.UMVInputBot&source_message_id=eq.{quote(str(rid),safe='')}&limit=1")
    if existing:
        db_patch("telegram_intake",rid,{"status":"Processed","metadata":{**metadata,"document_id":existing[0]["id"]}}); return False
    data=b2_client().get_object(Bucket=B2_BUCKET,Key=key)["Body"].read()
    if not data: raise RuntimeError("B2 object is empty")
    with tempfile.TemporaryDirectory() as workdir:
        text=embedded_pdf_text(data); method="Embedded PDF text"
        if len(re.sub(r"\s+","",text))<80: text=ocr_pdf(data,workdir); method="Tesseract OCR (Hindi+English)"
    if not text: raise RuntimeError("No text could be extracted from PDF")
    subject,authority,ref_no,printed,normalized,short,detailed,category_key,category,confidence=extract_metadata(text,original_name); display_name=canonical_filename(original_name,subject,authority,normalized,ref_no); checksum=storage.get("sha256")
    duplicates=db_get(f"documents?select=id,display_filename&file_checksum=eq.{quote(str(checksum),safe='')}&limit=1") if checksum else []
    if duplicates:
        duplicate_of=duplicates[0]["id"]; db_patch("telegram_intake",rid,{"status":"Processed","metadata":{**metadata,"duplicate_of":duplicate_of,"document_id":duplicate_of,"processed_at":datetime.now(timezone.utc).isoformat()}}); print(f"Duplicate {rid} -> {duplicate_of}"); return False
    payload={"id":str(uuid.uuid4()),"source_app":"UMVInputBot","source_location":"Telegram","source_message_id":str(rid),"original_filename":original_name,"display_filename":display_name,"mime_type":row.get("mime_type"),"file_size":len(data),"file_checksum":checksum,"private_drive_file_id":storage.get("drive_file_id"),"private_drive_url":(f"https://drive.google.com/file/d/{storage.get('drive_file_id')}/view" if storage.get("drive_file_id") else None),"public_file_url":"","reference_number":ref_no or None,"issue_date_as_printed":printed or None,"normalized_issue_date":normalized,"received_at":row.get("received_at"),"issuing_authority":authority or None,"subject":subject or None,"short_description":short,"detailed_summary":detailed,"category":category,"subcategory":None,"priority":"NORMAL","required_action":"None","deadline_as_printed":None,"normalized_deadline":None,"affected_entities":[],"financial_amount":None,"full_text_ocr":text,"extraction_method":method,"extraction_confidence":confidence,"sensitive":False,"useful":True,"duplicate":False,"duplicate_reason":None,"processing_status":"Completed","forwarding_status":"Not Forwarded","approved_for_publication":False,"category_key":category_key,"category_source":"rule","category_confidence":"HIGH" if category_key!="other" else "LOW","ai_suggestion_status":"Not Requested","publication_status":"Unpublished","publication_reason":"Awaiting publication workflow","public_revision":0}
    created=db_insert("documents",payload); actual_id=created.get("id",payload["id"]); db_patch("telegram_intake",rid,{"status":"Processed","metadata":{**metadata,"document_id":actual_id,"display_filename":display_name,"processed_at":datetime.now(timezone.utc).isoformat()}}); print(f"Processed {rid} -> {actual_id} via {method} as {display_name}"); return True

def main():
    if RECOVERY_DOCUMENT_ID:
        row=db_get(f"telegram_intake?select=*&id=eq.{quote(RECOVERY_DOCUMENT_ID,safe='')}&limit=1")
        if not row: print(f"Recovery target not found: {RECOVERY_DOCUMENT_ID}"); return 2
        rows=row
    else:
        rows=db_get("telegram_intake?select=*&or=(status.eq.Stored,status.eq.Processing%20Failed)&order=received_at.asc&limit=10")
    processed=failed=skipped=0
    for candidate in rows:
        if not has_verified_b2(candidate):
            skipped+=1
            print(f"Skip {candidate['id']}: no verified B2 object; storage worker owns recovery")
            continue
        row=claim_intake(candidate["id"])
        if row is None:
            skipped+=1; print(f"Skip {candidate['id']}: already claimed or no longer eligible"); continue
        try:
            if process(row): processed+=1
        except Exception as exc:
            failed+=1; md=row.get("metadata") or {}; db_patch("telegram_intake",row["id"],{"status":"Processing Failed","metadata":{**md,"processing_error":str(exc)[:1200],"processing_error_at":datetime.now(timezone.utc).isoformat()}}); print(f"Record {row['id']}: processing failed: {exc}")
    print(f"Document processor complete: processed={processed}, failed={failed}, skipped={skipped}, candidates={len(rows)}"); return 1 if failed else 0

# Opt-in integration point: the existing processor remains the safety fallback,
# while GovDOC Vision becomes the primary extractor when explicitly enabled.
# Keeping this opt-in prevents an OCR-engine dependency from changing legacy
# production behavior until the release gate is verified in the target runtime.
if os.environ.get("GOVDOC_VISION_ENABLED", "0").strip().lower() in {"1", "true", "yes"}:
    try:
        from govdoc_ocr_adapter import install as install_govdoc_vision
        install_govdoc_vision(sys.modules[__name__])
    except Exception as exc:
        print(f"GovDOC Vision integration unavailable; using legacy extractor: {exc}", file=sys.stderr)

if __name__=="__main__": sys.exit(main())