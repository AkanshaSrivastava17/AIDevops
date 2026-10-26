"""
Unit tests for Prometheus Metrics (Section 33, Enhancement #5).
"""
import pytest
from app.monitoring.metrics import MetricsManager


def test_metrics_recording_and_payload_generation():
    # Record some simulated telemetry
    MetricsManager.record_change_analysis(mode="History-RAG", impact_level="HIGH", status="success")
    MetricsManager.record_test_execution(passed=3, failed=0)
    MetricsManager.record_gate_decision(decision="APPROVED")
    MetricsManager.record_rollback(environment="qa")
    MetricsManager.set_active_known_good_image("historyrag:v1.0.0-stable")

    payload = MetricsManager.get_metrics_payload()
    assert isinstance(payload, bytes)
    text = payload.decode("utf-8")

    # Assert standard Prometheus format markers and metric names exist
    assert "historyrag_change_analyses_total" in text
    assert "historyrag_impact_predictions_total" in text
    assert "historyrag_tests_executed_total" in text
    assert "historyrag_pipeline_gate_decisions_total" in text
    assert "historyrag_rollbacks_total" in text
    assert "historyrag_known_good_version_info" in text
