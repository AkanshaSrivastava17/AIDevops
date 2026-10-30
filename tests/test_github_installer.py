"""
Unit and Integration Tests for GitHub Workflow Installer (1-Click Onboarding).
"""
import pytest
from app.devops.github_installer import GitHubWorkflowInstaller, parse_repo_slug
from app.api.routes import install_workflow_endpoint, WorkflowInstallRequest


def test_parse_repo_slug():
    # Full URL
    o, r = parse_repo_slug("https://github.com/Radhikag19/PyCalculator")
    assert o == "Radhikag19"
    assert r == "PyCalculator"

    # URL with .git
    o, r = parse_repo_slug("https://github.com/AkanshaSrivastava17/AIDevops.git")
    assert o == "AkanshaSrivastava17"
    assert r == "AIDevops"

    # Shorthand slug
    o, r = parse_repo_slug("pallets/flask")
    assert o == "pallets"
    assert r == "flask"

    # Invalid empty
    o, r = parse_repo_slug("")
    assert o is None and r is None


def test_generate_workflow_yaml():
    installer = GitHubWorkflowInstaller()
    yaml_text = installer.generate_workflow_yaml(
        repo_name="PyCalculator",
        components=["Calculator", "Evaluator"],
        default_tests=["tests/test_calculator.py"]
    )
    assert "name: History-RAG AI-Enhanced CI/CD" in yaml_text
    assert "Calculator" in yaml_text
    assert "actions/checkout@v4" in yaml_text
    assert "pull-requests: write" in yaml_text
    assert "actions/github-script@v7" in yaml_text
    assert "History-RAG AI Change-Impact Analysis" in yaml_text


def test_install_simulation_dry_run():
    installer = GitHubWorkflowInstaller()
    result = installer.install(
        repo_url_or_slug="https://github.com/Radhikag19/PyCalculator",
        token="demo",
        branch_name="historyrag-setup-cicd",
        commit_to_main=False
    )
    assert result["status"] == "success"
    assert result["dry_run"] is True
    assert result["owner"] == "Radhikag19"
    assert result["repo"] == "PyCalculator"
    assert result["pr_number"] == 101
    assert "pull/101" in result["pr_url"]
    assert ".github/workflows/historyrag.yml" in result["workflow_file"]
    assert "name: History-RAG" in result["workflow_content"]


def test_install_simulation_direct_commit():
    installer = GitHubWorkflowInstaller()
    result = installer.install(
        repo_url_or_slug="Radhikag19/PyCalculator",
        token=None,
        commit_to_main=True,
        dry_run=True
    )
    assert result["status"] == "success"
    assert result["mode"] == "direct_commit"
    assert result["target_branch"] == "main"
    assert result["pr_number"] is None


def test_install_invalid_slug():
    installer = GitHubWorkflowInstaller()
    with pytest.raises(ValueError):
        installer.install(repo_url_or_slug="")


def test_api_install_workflow_endpoint():
    req = WorkflowInstallRequest(
        repository_url_or_slug="https://github.com/Radhikag19/PyCalculator",
        github_token="demo",
        branch_name="historyrag-setup-cicd",
        commit_to_main=False,
        dry_run=True
    )
    data = install_workflow_endpoint(req)
    assert data["status"] == "success"
    assert data["dry_run"] is True
    assert data["owner"] == "Radhikag19"
    assert data["repo"] == "PyCalculator"
    assert "pull/101" in data["pr_url"]
