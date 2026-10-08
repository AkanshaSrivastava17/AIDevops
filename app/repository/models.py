"""
Repository capability and configuration data models.
"""
from enum import Enum
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class AnalysisMode(str, Enum):
    ENHANCED = "Enhanced"
    LIMITED = "Limited"
    INSUFFICIENT_EVIDENCE = "Insufficient evidence"


class CapabilityProfile(BaseModel):
    repository_id: str
    language: str
    test_framework: Optional[str] = None
    git_history: bool = True
    source_code: bool = True
    issues: bool = True
    prs: bool = True
    tests: bool = True
    python_ast: bool = True
    import_analysis: bool = True
    analysis_mode: AnalysisMode = AnalysisMode.ENHANCED
    discovered_components: List[str] = Field(default_factory=list)
    total_commits: int = 0
    total_issues: int = 0
    total_prs: int = 0
    total_tests: int = 0
    profile_summary: str = ""


class RepositoryConfig(BaseModel):
    repository_id: str
    name: str = ""
    repository_url: str
    pinned_commit: Optional[str] = None
    default_branch: str = "master"
    language: str = "Python"
    test_framework: str = "pytest"
    test_directories: List[str] = Field(default_factory=lambda: ["tests"])
    component_rules_file: Optional[str] = None
    minimum_history_thresholds: Dict[str, int] = Field(
        default_factory=lambda: {"min_commits": 30, "min_issues": 10, "min_prs": 10}
    )
    evaluation_flag: bool = False
    description: str = ""
