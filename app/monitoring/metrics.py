"""
Prometheus Metrics Instrumentation (Section 33, Enhancement #5).
Exposes infrastructure, change analysis, RAG retrieval, impact scoring,
pytest regression execution, CI/CD gates, and auto-rollback telemetry.
"""
import time
from typing import Optional
from prometheus_client import (
    Counter,
    Gauge,
    Histogram,
    CollectorRegistry,
    generate_latest,
    CONTENT_TYPE_LATEST,
    REGISTRY
)

# Custom Registry to avoid collision in test suites
registry = REGISTRY

# 1. RAG & API Request Metrics
CHANGE_ANALYSES_TOTAL = Counter(
    "historyrag_change_analyses_total",
    "Total change-impact analysis requests processed",
    ["mode", "status"],
    registry=registry
)

IMPACT_PREDICTIONS_TOTAL = Counter(
    "historyrag_impact_predictions_total",
    "Total component impact level classifications",
    ["impact_level"],
    registry=registry
)

RAG_RETRIEVAL_SECONDS = Histogram(
    "historyrag_rag_retrieval_seconds",
    "Latency of hybrid evidence pack construction in seconds",
    registry=registry,
    buckets=(0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0)
)

# 2. DevOps & Testing Metrics
TESTS_EXECUTED_TOTAL = Counter(
    "historyrag_tests_executed_total",
    "Total recommended regression tests executed",
    ["status"],
    registry=registry
)

PIPELINE_GATE_DECISIONS_TOTAL = Counter(
    "historyrag_pipeline_gate_decisions_total",
    "CI/CD policy gate evaluation decisions",
    ["decision"],
    registry=registry
)

ROLLBACKS_TOTAL = Counter(
    "historyrag_rollbacks_total",
    "Automated container deployment rollbacks executed",
    ["environment"],
    registry=registry
)

# 3. Repository Knowledge Base Metrics
INDEXED_DOCUMENTS_GAUGE = Gauge(
    "historyrag_indexed_documents_total",
    "Total documents indexed in SQLite metadata store",
    ["repository_id", "doc_type"],
    registry=registry
)

ACTIVE_KNOWN_GOOD_VERSION = Gauge(
    "historyrag_known_good_version_info",
    "Information gauge indicating active known-good image version",
    ["image_tag"],
    registry=registry
)


class MetricsManager:
    """Helper for incrementing and recording History-RAG Prometheus telemetry."""

    @staticmethod
    def record_change_analysis(mode: str, impact_level: str, status: str = "success") -> None:
        CHANGE_ANALYSES_TOTAL.labels(mode=mode, status=status).inc()
        IMPACT_PREDICTIONS_TOTAL.labels(impact_level=impact_level).inc()

    @staticmethod
    def record_test_execution(passed: int, failed: int) -> None:
        if passed > 0:
            TESTS_EXECUTED_TOTAL.labels(status="PASS").inc(passed)
        if failed > 0:
            TESTS_EXECUTED_TOTAL.labels(status="FAIL").inc(failed)

    @staticmethod
    def record_gate_decision(decision: str) -> None:
        PIPELINE_GATE_DECISIONS_TOTAL.labels(decision=decision).inc()

    @staticmethod
    def record_rollback(environment: str = "qa") -> None:
        ROLLBACKS_TOTAL.labels(environment=environment).inc()

    @staticmethod
    def set_active_known_good_image(image_tag: str) -> None:
        ACTIVE_KNOWN_GOOD_VERSION.labels(image_tag=image_tag).set(1)

    @staticmethod
    def update_indexed_documents(repository_id: str, doc_type: str, count: int) -> None:
        INDEXED_DOCUMENTS_GAUGE.labels(repository_id=repository_id, doc_type=doc_type).set(count)

    @staticmethod
    def get_metrics_payload() -> bytes:
        return generate_latest(registry)
