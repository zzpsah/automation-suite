import pytest

from ocr.search_filters import SearchFilter
from ocr.search_index import SearchDocument, SearchEntity
from ocr.storage.supabase_search import SupabaseSearchStore


class FakeResponse:
    def __init__(self, data):
        self.data = data


class FakeQuery:
    def __init__(self, table, rows):
        self.table_name = table
        self.rows = rows
        self._needle = None
        self._limit = None

    def select(self, *_): return self
    def upsert(self, payload, **_):
        values = payload if isinstance(payload, list) else [payload]
        for value in values:
            self.rows.append(dict(value))
        return self
    def ilike(self, _, pattern):
        self._needle = pattern.strip('%').casefold()
        return self
    def limit(self, value): self._limit = value; return self
    def execute(self):
        data = self.rows
        if self._needle is not None:
            data = [r for r in data if self._needle in str(r.get('value', r.get('text', ''))).casefold()]
        if self._limit is not None:
            data = data[:self._limit]
        return FakeResponse(data)


class FakeClient:
    def __init__(self): self.tables = {'docs': [], 'entities': []}
    def table(self, name): return FakeQuery(name, self.tables[name])


def test_supabase_adapter_search_and_filter():
    client = FakeClient()
    store = SupabaseSearchStore(client, documents_table='docs', entities_table='entities')
    store.upsert_many(
        documents=[SearchDocument('d1', 1, 'b1', 'District Education Officer letter')],
        entities=[SearchEntity('d1', 'e1', 'authority', 'District Education Officer', 1, 'b1', 0.9)],
    )
    hits = store.search('education', search_filter=SearchFilter(entity_types=frozenset({'authority'})))
    assert len(hits) == 1
    assert hits[0].entity_id == 'e1'
    assert hits[0].document_id == 'd1'


def test_supabase_adapter_missing_dependency_is_clear(monkeypatch):
    import builtins
    original = builtins.__import__
    def blocked(name, *args, **kwargs):
        if name == 'supabase':
            raise ImportError('blocked')
        return original(name, *args, **kwargs)
    monkeypatch.setattr(builtins, '__import__', blocked)
    with pytest.raises(RuntimeError, match='optional.*supabase'):
        SupabaseSearchStore.from_url_key('https://example.supabase.co', 'key')
