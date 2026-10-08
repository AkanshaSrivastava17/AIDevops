"""
Unit tests for Repository Adapter, Profiler, and Capability Profile models.
"""
import os
import pytest
from app.repository.models import RepositoryConfig, AnalysisMode, CapabilityProfile
from app.repository.profiler import RepositoryProfiler
from app.repository.adapter import RepositoryAdapter


def test_repository_config_loading():
    config = RepositoryConfig(
        repository_id="test_repo",
        repository_url="https://github.com/example/test",
        language="Python",
        test_framework="pytest"
    )
    assert config.repository_id == "test_repo"
    assert config.language == "Python"
    assert config.test_framework == "pytest"


def test_repository_profiler_enhanced_mode():
    profiler = RepositoryProfiler()
    # Profile against netbox directory
    repo_path = "data/raw/netbox"
    if os.path.exists(repo_path):
        profile = profiler.profile_repository(
            repo_path=repo_path,
            has_git=True,
            commit_count=60,
            issue_count=30,
            pr_count=30
        )
        assert profile.analysis_mode == AnalysisMode.ENHANCED
        assert profile.git_history is True
        assert profile.python_ast is True
        assert profile.import_analysis is True
        assert profile.tests is True
        assert len(profile.discovered_components) > 0


def test_repository_profiler_insufficient_evidence():
    profiler = RepositoryProfiler()
    # Non-existent repository path with 0 commits
    profile = profiler.profile_repository(
        repo_path="data/raw/non_existent_path",
        has_git=False,
        commit_count=0
    )
    assert profile.analysis_mode == AnalysisMode.INSUFFICIENT_EVIDENCE
    assert "Insufficient" in profile.profile_summary


def test_repository_adapter_file_mapping():
    adapter = RepositoryAdapter("configs/netbox.yaml")
    comp1 = adapter.map_file_to_component("netbox/dcim/models/devices.py")
    assert comp1 == "dcim"
    comp2 = adapter.map_file_to_component("netbox/ipam/models/ip.py")
    assert comp2 == "ipam"
    comp3 = adapter.map_file_to_component("netbox/tenancy/models.py")
    assert comp3 == "tenancy"


def test_repository_adapter_is_test_file():
    adapter = RepositoryAdapter("configs/netbox.yaml")
    assert adapter.is_test_file("netbox/dcim/tests/test_devices.py") is True
    assert adapter.is_test_file("tests/test_routing.py") is True
    assert adapter.is_test_file("netbox/dcim/models.py") is False
