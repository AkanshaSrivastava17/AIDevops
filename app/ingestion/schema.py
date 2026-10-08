"""
Common schema definitions for normalized repository evidence.
Follows Sections 8.1, 8.2, 10 of the implementation plan.
"""
from enum import Enum
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class DocumentType(str, Enum):
    CODE = "code"
    COMMIT = "commit"
    ISSUE = "issue"
    PR = "pr"
    DIFF = "diff"
    TEST = "test"
    DOCUMENTATION = "documentation"


class EventType(str, Enum):
    COMMIT = "commit"
    ISSUE_CREATED = "issue_created"
    ISSUE_COMMENT = "issue_comment"
    PR_CREATED = "pr_created"
    PR_COMMENT = "pr_comment"
    PR_REVIEW = "pr_review"
    PR_UPDATE = "pr_update"
    TEST_CHANGE = "test_change"
    CODE_CHUNK = "code_chunk"


class NormalizedDocument(BaseModel):
    document_id: str
    repository_id: str
    type: DocumentType
    path: Optional[str] = None
    component: str = "general"
    commit_sha: Optional[str] = None
    issue_id: Optional[str] = None
    pr_id: Optional[str] = None
    event_timestamp: str  # ISO 8601 format
    event_type: EventType
    language: str = "Python"
    source_url: str = ""
    title: str = ""
    content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ComponentMappingRule(BaseModel):
    prefix: str
    component: str


class DependencyLink(BaseModel):
    source_component: str
    target_component: str
    import_statement: str
    source_file: str


class CoChangeRecord(BaseModel):
    commit_sha: str
    timestamp: str
    components: List[str]
    files: List[str]
