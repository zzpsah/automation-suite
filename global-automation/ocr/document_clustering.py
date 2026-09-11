"""Conservative candidate clustering over cross-document evidence."""
from __future__ import annotations

from dataclasses import asdict, dataclass

from .cross_document import CrossDocumentGraph, CrossDocumentRelation


@dataclass(frozen=True)
class CandidateCluster:
    cluster_id: str
    document_ids: tuple[str, ...]
    relation_ids: tuple[str, ...]
    relation_types: tuple[str, ...]
    evidence_count: int
    confidence: float
    reason: str


@dataclass(frozen=True)
class CandidateClusterResult:
    clusters: tuple[CandidateCluster, ...]


def _relation_id(relation: CrossDocumentRelation) -> str:
    return "|".join((
        relation.source_document_id,
        relation.target_document_id,
        relation.relation_type,
        relation.source_entity_id,
        relation.target_entity_id,
    ))


def _qualifies(relations: list[CrossDocumentRelation]) -> bool:
    types = {relation.relation_type for relation in relations}
    return "shared_reference" in types or len(types) >= 2


def build_candidate_clusters(
    graph: CrossDocumentGraph,
    *,
    min_confidence: float = 0.0,
) -> CandidateClusterResult:
    """Build deterministic evidence-based candidate document clusters.

    A cluster is not a claim of same-case/legal identity. A connected component
    qualifies when it contains a shared reference or at least two independent
    cross-document evidence types. Authority/contact-only components are excluded.
    """
    if not 0.0 <= min_confidence <= 1.0:
        raise ValueError("min_confidence must be between 0 and 1")

    relations = sorted(
        (r for r in graph.relations if r.confidence >= min_confidence),
        key=_relation_id,
    )
    parent: dict[str, str] = {}

    def find(item: str) -> str:
        parent.setdefault(item, item)
        while parent[item] != item:
            parent[item] = parent[parent[item]]
            item = parent[item]
        return item

    def union(left: str, right: str) -> None:
        left_root, right_root = find(left), find(right)
        if left_root == right_root:
            return
        parent[max(left_root, right_root)] = min(left_root, right_root)

    for relation in relations:
        union(relation.source_document_id, relation.target_document_id)

    groups: dict[str, list[CrossDocumentRelation]] = {}
    for relation in relations:
        root = find(relation.source_document_id)
        groups.setdefault(root, []).append(relation)

    clusters: list[CandidateCluster] = []
    for root, group in sorted(groups.items()):
        if not _qualifies(group):
            continue
        documents = sorted({d for r in group for d in (r.source_document_id, r.target_document_id)})
        relation_ids = tuple(sorted(_relation_id(r) for r in group))
        relation_types = tuple(sorted({r.relation_type for r in group}))
        confidence = round(sum(r.confidence for r in group) / len(group), 6)
        clusters.append(CandidateCluster(
            cluster_id="cluster:" + ":".join(documents),
            document_ids=tuple(documents),
            relation_ids=relation_ids,
            relation_types=relation_types,
            evidence_count=len(group),
            confidence=confidence,
            reason="candidate cluster supported by cross-document evidence",
        ))

    clusters.sort(key=lambda c: c.cluster_id)
    return CandidateClusterResult(tuple(clusters))


def candidate_clusters_to_dict(result: CandidateClusterResult) -> dict:
    """Return JSON-compatible cluster data."""
    payload = []
    for cluster in result.clusters:
        item = asdict(cluster)
        item["document_ids"] = list(cluster.document_ids)
        item["relation_ids"] = list(cluster.relation_ids)
        item["relation_types"] = list(cluster.relation_types)
        payload.append(item)
    return {"clusters": payload}
