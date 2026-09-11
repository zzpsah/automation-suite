"""Conservative Hindi/English government-document normalization."""
from __future__ import annotations
import re
LABEL_ALIASES={"विषयक":"विषय:","विषयः":"विषय:","पत्र संख्या":"पत्रांक:","पत्र सं.":"पत्रांक:","पत्र सं":"पत्रांक:","ज्ञाप संख्या":"ज्ञापांक:","ज्ञाप सं.":"ज्ञापांक:","दिनांकित":"दिनांक:","दिनांकः":"दिनांक:"}
def normalize_whitespace(text):
    text=(text or '').replace('\r\n','\n').replace('\r','\n').replace('\u00a0',' ').replace('\u200b','')
    return '\n'.join(re.sub(r'[ \t]+',' ',x).strip() for x in text.split('\n')).strip()
def normalize_labels(text):
    for src,dst in sorted(LABEL_ALIASES.items(),key=lambda x:-len(x[0])): text=text.replace(src,dst)
    return text
def normalize_dates(text): return re.sub(r'(?<!\d)(\d{1,2})\s*[./-]\s*(\d{1,2})\s*[./-]\s*(\d{4})(?!\d)',r'\1/\2/\3',text)
def normalize_sarkari_text(text): return normalize_whitespace(normalize_dates(normalize_labels(normalize_whitespace(text))))
