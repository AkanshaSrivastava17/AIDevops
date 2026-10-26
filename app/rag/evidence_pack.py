"""
Evidence Pack data model.
Encapsulates all evidence retrieved for a question or proposed change.
"""
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field


class EvidencePack(BaseModel):
    repository_id: str
    query_or_change: str
    target_time: Optional[str] = None
    system_mode: str = "History-RAG"  # "History-RAG", "Code-RAG", "LLM-only"
    analysis_mode: str = "Enhanced"   # "Enhanced", "Limited", "Insufficient evidence"
    candidate_components: List[str] = Field(default_factory=list)
    code_evidence: List[Dict[str, Any]] = Field(default_factory=list)
    commit_evidence: List[Dict[str, Any]] = Field(default_factory=list)
    issue_evidence: List[Dict[str, Any]] = Field(default_factory=list)
    pr_evidence: List[Dict[str, Any]] = Field(default_factory=list)
    cochange_evidence: Dict[str, Dict[str, int]] = Field(default_factory=dict)
    dependency_evidence: List[Dict[str, Any]] = Field(default_factory=list)
    available_tests: List[str] = Field(default_factory=list)
    graph_paths: List[Dict[str, Any]] = Field(default_factory=list)
    graph_ranked_tests: List[Dict[str, Any]] = Field(default_factory=list)
    citations: List[str] = Field(default_factory=list)

    def total_evidence_items(self) -> int:
        return (
            len(self.code_evidence)
            + len(self.commit_evidence)
            + len(self.issue_evidence)
            + len(self.pr_evidence)
            + len(self.dependency_evidence)
        )
