from ocr.cluster_search import ClusterSearchQuery, search_clusters, cluster_search_to_dict
from ocr.document_clustering import CandidateCluster, CandidateClusterResult
from ocr.reference_timeline import ReferenceTimeline, TimelineEvent
from ocr.search_index import SearchDocument, DocumentSearchIndex


def test_cluster_query_restricts_documents_and_timeline():
    index = DocumentSearchIndex()
    index.add_document(SearchDocument('d1', 1, 'b1', 'REF-10 education'))
    index.add_document(SearchDocument('d2', 1, 'b2', 'REF-10 education'))
    index.add_document(SearchDocument('d3', 1, 'b3', 'REF-10 education'))
    cluster = CandidateCluster('cluster:d1:d2', ('d1', 'd2'), ('r1',), ('shared_reference',), 1, .96, 'evidence')
    timeline = ReferenceTimeline((TimelineEvent('d1','document_date','01/01/2025','2025-01-01',1,'b1','date1',('ref1',),.9), TimelineEvent('d3','document_date','02/02/2026','2026-02-02',1,'b3','date3',(),.9)))
    result = search_clusters(index, ClusterSearchQuery('education', cluster_ids=frozenset({cluster.cluster_id})), clusters=CandidateClusterResult((cluster,)), timeline=timeline)
    assert {hit.document_id for hit in result.hits} == {'d1'}
    assert {event.document_id for event in result.timeline_events} == {'d1'}
    assert result.clusters[0].cluster_id == cluster.cluster_id


def test_timeline_date_filter_is_explicit_and_unparseable_excluded():
    index = DocumentSearchIndex()
    index.add_document(SearchDocument('d1', 1, 'b1', 'education'))
    timeline = ReferenceTimeline((TimelineEvent('d1','document_date','01/01/2025','2025-01-01',1,'b1','x',(),.9), TimelineEvent('d1','document_date','unknown',None,2,'b2','y',(),.9)))
    result = search_clusters(index, ClusterSearchQuery('education', date_from='2025-01-01', date_to='2025-12-31'), clusters=CandidateClusterResult(()), timeline=timeline)
    assert [event.date_iso for event in result.timeline_events] == ['2025-01-01']


def test_unknown_cluster_does_not_expand_scope():
    index = DocumentSearchIndex()
    index.add_document(SearchDocument('d1', 1, 'b1', 'education'))
    result = search_clusters(index, ClusterSearchQuery('education', cluster_ids=frozenset({'missing'})), clusters=CandidateClusterResult(()))
    assert result.hits == ()


def test_serialization_is_json_safe():
    result = search_clusters(DocumentSearchIndex(), ClusterSearchQuery('x'), clusters=CandidateClusterResult(()))
    payload = cluster_search_to_dict(result)
    assert isinstance(payload['hits'], list)
