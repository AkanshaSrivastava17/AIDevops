"""
Temporal Leakage Filter.
Strictly prevents future information leakage into historical evaluation cases (Sections 8.1, 16.3).
"""
import logging
from datetime import datetime
from typing import List, Optional, Set
from app.ingestion.schema import NormalizedDocument

logger = logging.getLogger(__name__)


class TemporalLeakageFilter:
    def __init__(
        self,
        target_time: Optional[str] = None,
        excluded_commit_shas: Optional[Set[str]] = None,
        excluded_issue_ids: Optional[Set[str]] = None,
        excluded_pr_ids: Optional[Set[str]] = None,
        excluded_test_paths: Optional[Set[str]] = None,
    ):
        self.target_time = target_time
        self.excluded_commit_shas = excluded_commit_shas or set()
        self.excluded_issue_ids = excluded_issue_ids or set()
        self.excluded_pr_ids = excluded_pr_ids or set()
        self.excluded_test_paths = excluded_test_paths or set()

    def is_valid_evidence(self, doc: NormalizedDocument) -> bool:
        # Rule 1: Target change's own commit is strictly excluded
        if doc.commit_sha and doc.commit_sha in self.excluded_commit_shas:
            return False

        # Rule 2: Target change's own PR and linked issues are excluded
        if doc.pr_id and doc.pr_id in self.excluded_pr_ids:
            return False
        if doc.issue_id and doc.issue_id in self.excluded_issue_ids:
            return False

        # Rule 3: Tests added by the change were non-existent at parent commit -> excluded
        if doc.path and doc.path in self.excluded_test_paths:
            return False

        # Rule 4: Event-level timestamp strictly before target_time T
        if self.target_time and doc.event_timestamp:
            try:
                # Compare ISO timestamps lexicographically / chronologically
                t_event = doc.event_timestamp.replace("Z", "+00:00")
                t_target = self.target_time.replace("Z", "+00:00")
                if t_event >= t_target:
                    return False
            except Exception:
                pass

        # Rule 5: If an issue or PR was updated/edited after T and lacks pre-T snapshot, exclude
        if self.target_time and doc.metadata.get("updated_at"):
            try:
                t_updated = doc.metadata["updated_at"].replace("Z", "+00:00")
                t_target = self.target_time.replace("Z", "+00:00")
                if t_updated > t_target:
                    # Edited post-target; considered potentially contaminated
                    return False
            except Exception:
                pass

        return True

    def filter_documents(self, documents: List[NormalizedDocument]) -> List[NormalizedDocument]:
        return [doc for doc in documents if self.is_valid_evidence(doc)]
