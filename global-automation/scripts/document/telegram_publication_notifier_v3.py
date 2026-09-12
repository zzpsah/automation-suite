#!/usr/bin/env python3
"""Deliver published documents safely through eLettersBot.

Never relabel arbitrary bytes as PDF. The delivery helper detects the real
source format, converts supported images/Office files to a valid PDF, and
validates every PDF before Telegram upload.
"""
from __future__ import annotations

import hashlib
import html
import io
import os
import sys
import time
import uuid
from datetime import datetime, timezone
from urllib.parse import quote, urlparse

import boto3
import requests

from telegram_file_delivery import prepare_delivery

SUPABASE_URL=os.environ["SUPABASE_URL"].rstrip("/")
SUPABASE_KEY=os.environ["SUPABASE_SERVICE_ROLE_KEY"]
TELEGRAM_TOKEN=os.environ["TELEGRAM_OUTPUT_BOT_TOKEN"]
EXPECTED_BOT_USERNAME=os.environ.get("TELEGRAM_OUTPUT_BOT_USERNAME","eLettersBot").lstrip("@").lower()
CONFIGURED_CHAT_IDS=[x.strip() for x in os.environ.get("TELEGRAM_NOTIFICATION_CHAT_IDS","").split(",") if x.strip()]
B2_KEY_ID=os.environ["B2_KEY_ID"]
B2_APP_KEY=os.environ["B2_APPLICATION_KEY"]
B2_BUCKET=os.environ.get("B2_BUCKET_NAME","Education-Dept-Files")
B2_ENDPOINT="https://s3.us-east-005.backblazeb2.com"
HEADERS={"apikey":SUPABASE_KEY,"Authorization":f"Bearer {SUPABASE_KEY}"}

TAG_MAP={
 "admission":["#नामांकन","#SpotAdmission","#OFSS","#Admission"],
 "bseb":["#BSEB","#बिहारविद्यालयपरीक्षासमिति","#Board"],
 "academic":["#Academic","#शैक्षणिक","#विद्यालय"],
 "exam":["#Exam","#परीक्षा","#BSEB"],
 "scholarship":["#Scholarship","#छात्रवृत्ति","#Student"],
 "salary":["#Salary","#वेतन","#Finance"],
 "service":["#Service","#सेवा","#Teacher"],
 "establishment":["#Establishment","#स्थापना","#Office"],
 "training":["#Training","#प्रशिक्षण","#Teacher"],
 "transfer":["#Transfer","#स्थानांतरण","#Service"],
 "holiday":["#Holiday","#अवकाश","#School"],
 "other":["#OfficialDocument","#सरकारीदस्तावेज"],
}

def db_get(path):
 r=requests.get(f"{SUPABASE_URL}/rest/v1/{path}",headers=HEADERS,timeout=30); r.raise_for_status(); return r.json()

def db_insert_audit(payload):
 r=requests.post(f"{SUPABASE_URL}/rest/v1/document_operations_audit",headers={**HEADERS,"Content-Type":"application/json","Prefer":"return=minimal"},json=payload,timeout=30); r.raise_for_status()

def telegram(method,payload=None,files=None):
 last=None
 for attempt in range(4):
  try:
   r=requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/{method}",data=payload,files=files,timeout=120)
   if r.status_code==429:
    try: retry_after=int((r.json().get("parameters") or {}).get("retry_after") or 5)
    except Exception: retry_after=5
    time.sleep(min(max(retry_after,1),60)); continue
   if r.status_code>=500:
    last=f"HTTP {r.status_code}"; time.sleep(2**attempt); continue
   r.raise_for_status(); data=r.json()
   if not data.get("ok"): raise RuntimeError(f"Telegram {method}: {data.get('description','unknown error')}")
   return data.get("result")
  except (requests.Timeout,requests.ConnectionError) as exc:
   last=str(exc); time.sleep(2**attempt)
 raise RuntimeError(f"Telegram {method} transient failure: {last or 'unknown error'}")

def verify_output_bot():
 me=telegram("getMe"); username=str(me.get("username") or "").lstrip("@").lower()
 if username!=EXPECTED_BOT_USERNAME: raise RuntimeError(f"Wrong Telegram output bot: @{username or 'unknown'}; expected @{EXPECTED_BOT_USERNAME}")
 print(f"Telegram output bot verified: @{username}")

def b2_client():
 return boto3.client("s3",endpoint_url=B2_ENDPOINT,aws_access_key_id=B2_KEY_ID,aws_secret_access_key=B2_APP_KEY,region_name="us-east-005")

def b2_download(object_key):
 buf=io.BytesIO(); b2_client().download_fileobj(B2_BUCKET,object_key,buf); data=buf.getvalue()
 if not data: raise RuntimeError(f"B2 returned empty object: {object_key}")
 return data

def clean_text(value):
 s=" ".join(str(value or "").replace("\\n"," ").split())
 s=s.strip(" \t,;:-")
 s=s.replace(" ,",",").replace(" ;",";").replace(" :",":")
 return s

def esc(value): return html.escape(clean_text(value) or "—",quote=False)
def display_date(value): return clean_text(str(value)[:10]) if value else "पहचान उपलब्ध नहीं"

def tags_for(doc):
 key=clean_text(doc.get("category_key") or "other").lower(); tags=TAG_MAP.get(key,TAG_MAP["other"]); subject=clean_text(doc.get("subject")).lower()
 if "नामांकन" in subject or "admission" in subject or "spot" in subject: tags=list(dict.fromkeys(tags+["#नामांकन","#Admission"]))
 if "परीक्षा" in subject or "exam" in subject: tags=list(dict.fromkeys(tags+["#परीक्षा","#Exam"]))
 return " ".join(tags[:8])

def recipients(intake_rows):
 ids=list(CONFIGURED_CHAT_IDS)
 for row in intake_rows:
  chat=str(row.get("telegram_chat_id") or "").strip()
  if chat and chat not in ids: ids.append(chat)
 return ids

def already_sent(document_id,chat_id):
 q=("document_operations_audit?select=id&document_id=eq."+quote(str(document_id),safe="")+"&operation=eq.telegram_publication_notification&details->>chat_id=eq."+quote(str(chat_id),safe="")+"&limit=1")
 return bool(db_get(q))

def format_message(doc):
 lines=["<b>📢 नया सरकारी दस्तावेज़ प्रकाशित</b>"]
 fields=[("पत्रांक",doc.get("reference_number")),("जारी तिथि",display_date(doc.get("normalized_issue_date"))),
         ("जारीकर्ता",clean_text(doc.get("issuing_authority"))),(
         "विषय",clean_text(doc.get("subject"))), ("संक्षिप्त विवरण",clean_text(doc.get("short_description"))),
         ("श्रेणी",clean_text(doc.get("category") or doc.get("category_key"))), ("खोज टैग",tags_for(doc))]
 for label,value in fields:
  if value: lines.append(f"<b>{label}:</b> {esc(value)}")
 lines.append("")
 lines.append("📎 संलग्न फ़ाइल सत्यापित करके भेजी गई है।")
 return "\n".join(lines)

def find_intake_for_document(doc):
 source=str(doc.get("source_message_id") or "").strip()
 if not source: return []
 try: uuid.UUID(source)
 except ValueError: return []
 return db_get("telegram_intake?select=id,telegram_chat_id,metadata,file_name,mime_type&limit=1&id=eq."+quote(source,safe=""))

def expected_sha256(intake):
 meta=intake.get("metadata") or {}; storage=meta.get("storage") or {}
 for key in ("sha256","checksum_sha256","checksum"):
  value=str(storage.get(key) or meta.get(key) or "").strip().lower()
  if len(value)==64 and all(c in "0123456789abcdef" for c in value): return value
 return None

def main():
 verify_output_bot()
 docs=db_get("documents?select=id,source_message_id,original_filename,display_filename,subject,short_description,issuing_authority,reference_number,normalized_issue_date,received_at,published_at,category,category_key,publication_status,approved_for_publication&publication_status=eq.Published&approved_for_publication=is.true&order=published_at.desc.nullslast,received_at.desc.nullslast&limit=50")
 sent=failed=skipped=0
 for doc in docs:
  intake=find_intake_for_document(doc)
  if not intake: skipped+=1; continue
  row=intake[0]; object_key=((row.get("metadata") or {}).get("storage") or {}).get("b2_key")
  if not object_key: skipped+=1; continue
  targets=recipients(intake)
  if not targets: skipped+=1; continue
  try:
   source=b2_download(object_key); source_sha256=hashlib.sha256(source).hexdigest(); expected=expected_sha256(row)
   if expected and expected!=source_sha256: raise RuntimeError(f"B2 checksum mismatch: expected={expected}, actual={source_sha256}")
   delivery=prepare_delivery(source,row.get("file_name") or doc.get("original_filename") or "document",row.get("mime_type") or "")
   delivery_sha256=hashlib.sha256(delivery["data"]).hexdigest()
   print(f"document={doc['id']} source={delivery['source_format']} delivery={delivery['delivery_format']} converted={delivery['converted']} pages={delivery['pages']} bytes={len(delivery['data'])}")
  except Exception as exc:
   failed+=1; print(f"Delivery preparation failed document={doc['id']}: {exc}"); continue
  message=format_message(doc)
  for chat_id in targets:
   if already_sent(doc["id"],chat_id): continue
   try:
    telegram("sendMessage",payload={"chat_id":chat_id,"text":message,"parse_mode":"HTML","disable_web_page_preview":"true"})
    telegram("sendDocument",payload={"chat_id":chat_id,"caption":f"📎 {delivery['filename']}"},files={"document":(delivery["filename"],delivery["data"],delivery["mime_type"])})
    db_insert_audit({"document_id":doc["id"],"operation":"telegram_publication_notification","actor_type":"system","from_status":{"publication_status":"Published"},"to_status":{"telegram":"Sent"},"details":{"chat_id":chat_id,"bot_username":EXPECTED_BOT_USERNAME,"delivery_format_version":2,"source_format":delivery["source_format"],"delivery_format":delivery["delivery_format"],"converted":delivery["converted"],"pages":delivery["pages"],"source_sha256":source_sha256,"delivery_sha256":delivery_sha256,"bytes":len(delivery["data"]),"filename":delivery["filename"],"mime_type":delivery["mime_type"],"sent_at":datetime.now(timezone.utc).isoformat()}})
    sent+=1
   except Exception as exc:
    failed+=1; print(f"Notification failed document={doc['id']} chat={chat_id}: {exc}")
 print(f"Telegram publication notifier: sent={sent}, failed={failed}, skipped={skipped}")
 return 1 if failed else 0

if __name__=="__main__": sys.exit(main())
