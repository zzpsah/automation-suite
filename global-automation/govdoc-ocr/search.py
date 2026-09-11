"""Search-ready retrieval primitives for GovDOC outputs.

This module is deliberately storage-neutral. It provides deterministic keyword
matching now and a stable boundary for Postgres full-text/pgvector later.
"""
from __future__ import annotations
import re

def _norm(value): return re.sub(r"\s+", " ", str(value or "")).strip().casefold()
def searchable_text(document):
    meta=document.get("metadata",document)
    values=[document.get("text"),document.get("normalized_text"),meta.get("subject"),meta.get("authority"),meta.get("department"),meta.get("office"),meta.get("district"),meta.get("block"),meta.get("school"),meta.get("category"),meta.get("document_type"),meta.get("reference_number"),document.get("filename")]
    return _norm(" ".join(str(x) for x in values if x))

def score_document(document, query):
    q=_norm(query)
    if not q:return 0.0
    hay=searchable_text(document); tokens=[t for t in re.findall(r"\w+",q,flags=re.UNICODE) if len(t)>1]
    if not tokens:return 0.0
    return sum(1 for t in tokens if t in hay)/len(tokens)

def search_documents(documents, query, filters=None, limit=20):
    filters=filters or {}; results=[]
    for doc in documents:
        meta=doc.get("metadata",doc)
        if any(_norm(meta.get(k)) != _norm(v) for k,v in filters.items() if v is not None): continue
        score=score_document(doc,query)
        if score>0: results.append({"document_id":doc.get("document_id") or doc.get("id"),"score":round(score,4),"matched_query":query,"metadata":meta})
    return sorted(results,key=lambda x:(-x["score"],str(x["document_id"])))[:limit]

class SearchBackend:
    """Stable interface for keyword/full-text/vector implementations."""
    def search(self, documents, query, filters=None, limit=20): return search_documents(documents,query,filters,limit)
