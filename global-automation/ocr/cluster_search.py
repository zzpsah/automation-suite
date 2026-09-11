"""Evidence-bounded search across candidate clusters and explicit timelines."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date
from typing import Iterable, Mapping

from .document_clustering import CandidateCluster, CandidateClusterResult
from .reference_timeline import ReferenceTimeline, TimelineEvent
from .search_contract import SearchStore
from .search_filters import SearchFilter
from .search_index import SearchHit


@dataclass(frozen=True)
class ClusterSearchQuery:
    query: str
    limit: int = 20
    cluster_ids: frozenset[str] = frozenset()
    date_from: str | None = None
    date_to: str | None = None

    def __post_init__(self) -> None:
        if self.limit < 1:
            raise ValueError("limit must be >= 1")
        for value, name in ((self.date_from, "date_from"), (self.date_to, "date_to")):
            if value is not None:
                try:
                    date.fromisoformat(value)
                except ValueError as exc:
                    raise ValueError(f"{name} must be ISO date YYYY-MM-DD") from exc
        if self.date_from and self.date_to and self.date_from > self.date_to:
            raise ValueError("date_from must not be after date_to")


@dataclass(frozen=True)
class ClusterSearchResult:
    hits: tuple[SearchHit, ...]
    timeline_events: tuple[TimelineEvent, ...]
    clusters: tuple[CandidateCluster, ...]


def _cluster_map(result: CandidateClusterResult) -> dict[str, CandidateCluster]:
    return {cluster.cluster_id: cluster for cluster in result.clusters}


def _timeline_allowed(event: TimelineEvent, query: ClusterSearchQuery) -> bool:
    if event.date_iso is None:
        return query.date_from is None and query.date_to is None
    if query.date_from and event.date_iso < query.date_from:
        return False
    if query.date_to and event.date_iso > query.date_to:
        return False
    return True


def search_clusters(
    store: SearchStore,
    query: ClusterSearchQuery,
    *,
    clusters: CandidateClusterResult,
    timeline: ReferenceTimeline | None = None,
    search_filter: SearchFilter | None = None,
) -> ClusterSearchResult:
    """Search explicit candidate clusters; never infer clusters from search text."""
    cluster_by_id = _cluster_map(clusters)
    selected = [cluster_by_id[cid] for cid in sorted(query.cluster_ids) if cid in cluster_by_id]
    if query.cluster_ids:
        allowed_documents = frozenset(d for cluster in selected for d in cluster.document_ids)
        effective = search_filter or SearchFilter()
        effective = SearchFilter(
            document_ids=(effective.document_ids & allowed_documents) if effective.document_ids else allowed_documents,
            page_numbers=effective.page_numbers,
            block_ids=effective.block_ids,
            entity_types=effective.entity_types,
            min_score=effective.min_score,
        )
    else:
        effective = search_filter
    hits = store.search(query.query, limit=query.limit, search_filter=effective)

    selected_documents = frozenset(d for cluster in selected for d in cluster.document_ids) if query.cluster_ids else None
    events: tuple[TimelineEvent, ...] = ()
    if timeline is not None:
        event_list = [e for e in timeline.events if (selected_documents is None or e.document_id in selected_documents) and _timeline_allowed(e, query)]
        event_list.sort(key=lambda e: (e.date_iso is None, e.date_iso or '9999-12-31', e.document_id, e.page_number, e.block_id, e.date_entity_id))
        events = tuple(event_list)
    return ClusterSearchResult(tuple(hits), events, tuple(selected))


def cluster_search_to_dict(result: ClusterSearchResult) -> dict:
    return {
        "hits": [asdict(hit) for hit in result.hits],
        "timeline_events": [asdict(event) | {"reference_entity_ids": list(event.reference_entity_ids)} for event in result.timeline_events],
        "clusters": [asdict(cluster) | {"document_ids": list(cluster.document_ids), "relation_ids": list(cluster.relation_ids), "relation_types": list(cluster.relation_types)} for cluster in result.clusters],
    }


__all__ = ["ClusterSearchQuery", "ClusterSearchResult", "search_clusters", "cluster_search_to_dict"]
