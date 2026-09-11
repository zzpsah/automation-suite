"""Golden retrieval benchmark with a release-gate friendly result contract."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Iterable

from ...search_index import SearchHit


@dataclass(frozen=True)
class BenchmarkCase:
    case_id: str
    query: str
    expected_document_ids: tuple[str, ...]
    top_k: int = 5
    required_provenance: bool = True


@dataclass(frozen=True)
class BenchmarkReport:
    total_cases: int
    passed_cases: int
    hit_rate: float
    provenance_accuracy: float
    deterministic: bool
    failures: tuple[str, ...]

    @property
    def passed(self) -> bool:
        return self.total_cases > 0 and self.passed_cases == self.total_cases and self.provenance_accuracy == 1.0 and self.deterministic


def _ids(hits: Iterable[SearchHit], top_k: int) -> tuple[str, ...]:
    return tuple(hit.document_id for hit in tuple(hits)[:top_k])


def run_benchmark(cases: Iterable[BenchmarkCase], search: Callable[[str, int], tuple[SearchHit, ...]]) -> BenchmarkReport:
    cases = tuple(cases)
    failures: list[str] = []
    passed = 0
    hit_cases = 0
    provenance_checks = 0
    provenance_ok = 0
    deterministic = True
    for case in cases:
        first = search(case.query, case.top_k)
        second = search(case.query, case.top_k)
        first_ids = _ids(first, case.top_k)
        second_ids = _ids(second, case.top_k)
        if first_ids != second_ids:
            deterministic = False
            failures.append(f"{case.case_id}: nondeterministic ordering")
        if any(document_id in case.expected_document_ids for document_id in first_ids):
            hit_cases += 1
        else:
            failures.append(f"{case.case_id}: expected document not in top-k")
        if case.required_provenance:
            provenance_checks += 1
            if all(hit.document_id and hit.block_id and hit.page_number >= 1 for hit in first):
                provenance_ok += 1
            else:
                failures.append(f"{case.case_id}: invalid provenance")
        if (any(document_id in case.expected_document_ids for document_id in first_ids)
                and (not case.required_provenance or all(hit.document_id and hit.block_id and hit.page_number >= 1 for hit in first))):
            passed += 1
    total = len(cases)
    return BenchmarkReport(total, passed, hit_cases / total if total else 0.0, provenance_ok / provenance_checks if provenance_checks else 1.0, deterministic, tuple(failures))


def assert_release_gate(report: BenchmarkReport, *, min_hit_rate: float = 0.95) -> None:
    if not 0.0 <= min_hit_rate <= 1.0:
        raise ValueError("min_hit_rate must be between 0 and 1")
    if report.hit_rate < min_hit_rate or report.provenance_accuracy < 1.0 or not report.deterministic:
        raise AssertionError("search regression gate failed")


__all__ = ["BenchmarkCase", "BenchmarkReport", "run_benchmark", "assert_release_gate"]
