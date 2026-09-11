"""Evidence-based Government Document Intelligence v2."""
from __future__ import annotations
import re

AUTHORITY_HINTS = ("बिहार विद्यालय परीक्षा समिति", "शिक्षा विभाग", "बिहार शिक्षा परियोजना परिषद", "जिला शिक्षा पदाधिकारी", "प्रखंड शिक्षा पदाधिकारी", "जिला कार्यक्रम पदाधिकारी", "राज्य परियोजना निदेशक", "Bihar School Examination Board", "BSEB", "District Education Officer", "Block Education Officer")
TYPE_RULES = {
 "admission": ("स्पॉट नामांकन", "नामांकन", "OFSS", "spot admission", "admission"),
 "examination": ("परीक्षा", "परीक्षार्थी", "परीक्षा कार्यक्रम", "result", "परिणाम", "exam"),
 "transfer": ("स्थानांतरण", "स्थानान्तरण", "पदस्थापन", "transfer"),
 "service": ("सेवा इतिहास", "सेवा संबंधी", "सेवाकाल", "service"),
 "training": ("प्रशिक्षण", "training"), "scholarship": ("छात्रवृत्ति", "scholarship"), "holiday": ("अवकाश", "holiday")}
ACTION_PATTERNS = (r"(?:सूचित|निर्देशित|अनुरोध|आदेश)\s+(?:किया|करते|दिया|गया)", r"(?:करना|करें|कराया|लेने|जमा करने|प्रदर्शित करने)\s+(?:होगा|होगी|करेंगे|करें)", r"(?:तक|दिनांक)\s+(?:विस्तारित|निर्धारित|निश्चित)")

def _lines(text): return [re.sub(r"\s+", " ", x).strip() for x in (text or "").splitlines() if x.strip()]
def _header(lines): return lines[:max(8, int(len(lines)*.22))]

def extract_header_authority(text):
    lines=_lines(text); hits=[x for x in _header(lines) if any(a.casefold() in x.casefold() for a in AUTHORITY_HINTS)]
    return {"value": hits[0][:300], "source":"header", "confidence":"HIGH"} if hits else {"value":None,"source":None,"confidence":"LOW"}

def extract_official_subject(text, fallback=None):
    lines=_lines(text); label=re.compile(r"^\s*(?:विषय|विषयक|subject)\s*[:：\-–—]?\s*(.*)$",re.I); stop=re.compile(r"^(?:पत्रांक|ज्ञापांक|क्रमांक|दिनांक|कार्यालय|विभाग|सेवा में|महोदय|प्रतिलिपि|प्रति|संलग्न)\b",re.I)
    for i,line in enumerate(lines):
        m=label.match(line)
        if not m: continue
        parts=[m.group(1).strip(" :-–—")] if m.group(1).strip() else []
        for nxt in lines[i+1:i+5]:
            if stop.match(nxt) or re.match(r"^\d+[.)]\s+",nxt): break
            parts.append(nxt)
        value=re.sub(r"\s+"," "," ".join(parts)).strip()
        if 8<=len(value)<=500: return {"value":value,"source":"subject_label","confidence":"HIGH"}
    return {"value":fallback.strip(),"source":"normalized_subject","confidence":"MEDIUM"} if fallback and 8<=len(fallback.strip())<=500 else {"value":None,"source":None,"confidence":"LOW"}

def classify_document(text):
    low=(text or '').casefold(); scores={k:sum(t.casefold() in low for t in terms) for k,terms in TYPE_RULES.items()}; best=max(scores,key=scores.get); score=scores[best]
    return {"value":best if score else "other","evidence_terms":[k for k,v in scores.items() if v],"confidence":"HIGH" if score>=2 else "MEDIUM" if score else "LOW"}

def extract_actions(text): return [line[:500] for line in _lines(text) if any(re.search(p,line,re.I) for p in ACTION_PATTERNS)][:5]
def extract_deadlines(text): return list(dict.fromkeys(re.findall(r"\b\d{1,2}[./-]\d{1,2}[./-]\d{4}\b",text or "")))[:12]
def build_short_description(subject,actions,category):
    if not subject:return None
    return f"{subject.rstrip('.')}। पत्र में संबंधित कार्यवाही/निर्देश के रूप में {actions[0][:220]}।" if actions else f"यह दस्तावेज़ {category} संबंधी सूचना/निर्देश से संबंधित है: {subject.rstrip('.')}."
def analyze_document(text, normalized_subject=None):
    authority=extract_header_authority(text); subject=extract_official_subject(text,normalized_subject); typ=classify_document(text); actions=extract_actions(text); deadlines=extract_deadlines(text)
    return {"authority":authority,"subject":subject,"document_type":typ,"actions":actions,"deadlines":deadlines,"short_description":build_short_description(subject['value'],actions,typ['value']),"evidence_policy":"source-backed; no invented metadata"}
