"""
AI Request Clarity Assistant, Suggested Criteria & Duplicate Detection.
Implements Section 8.3 (Feature Intake Inline AI Assistance).
"""
import re
from typing import List, Dict, Any, Optional

from app.workflow.models import FeatureRequest
from app.workflow.db import WorkflowDB
from app.rag.hybrid_retriever import HybridRetriever


class ClarityAssistant:
    def __init__(self, db: WorkflowDB, retriever: HybridRetriever):
        self.db = db
        self.retriever = retriever

    def analyze_request_clarity(
        self,
        title: str,
        description: str,
        acceptance_criteria: List[str],
        repo_id: str,
        project_id: str
    ) -> Dict[str, Any]:
        """
        Flags vague/untestable criteria, generates suggested criteria,
        discovers similar past work and checks for duplicate requests.
        """
        flags: List[Dict[str, str]] = []
        suggested_criteria: List[Dict[str, Any]] = []

        combined_text = f"{title}\n{description}\n" + "\n".join(acceptance_criteria)
        text_lower = combined_text.lower()

        # 1. Criteria Clarity Checks
        vague_terms = [
            ("improve", "Criterion uses ambiguous term 'improve'. Specify measurable throughput, latency, or functional target."),
            ("fast", "Term 'fast' is untestable. Define maximum response latency (e.g., < 250ms)."),
            ("better", "Term 'better' is subjective. Define explicit pass/fail conditions."),
            ("handle errors", "Specify concrete error codes (e.g., HTTP 400 ValidationError) and expected exception payloads."),
            ("support all", "Specify the exact parameter matrix, types, or protocols supported.")
        ]

        for idx, criterion in enumerate(acceptance_criteria):
            c_low = criterion.lower()
            for term, explanation in vague_terms:
                if re.search(r"\b" + re.escape(term) + r"\b", c_low):
                    flags.append({
                        "criterion_index": idx,
                        "criterion": criterion,
                        "term": term,
                        "flag": "vague_term",
                        "question": f"Reviewer question: {explanation}"
                    })

        # Check edge cases
        if not any("error" in c.lower() or "fail" in c.lower() or "exception" in c.lower() or "invalid" in c.lower() for c in acceptance_criteria):
            flags.append({
                "criterion_index": -1,
                "criterion": "General",
                "term": "missing_error_handling",
                "question": "No error handling criterion defined. What happens when inputs are malformed or resource state is invalid?"
            })
            suggested_criteria.append({
                "id": "sug-err-1",
                "text": "Raise a structured ValidationError with explicit machine-readable error codes when boundary conditions are violated.",
                "reason": "Ensure deterministic failure handling for invalid inputs."
            })

        if not any("backward" in c.lower() or "legacy" in c.lower() or "compatible" in c.lower() for c in acceptance_criteria):
            suggested_criteria.append({
                "id": "sug-compat-1",
                "text": "Preserve backward compatibility for existing callers and legacy configurations without breaking API contracts.",
                "reason": "Prevent regressions in dependent service callers."
            })

        # Generate targeted domain suggestion based on title/description
        if "validate" in text_lower or "containment" in text_lower or "vrf" in text_lower:
            suggested_criteria.append({
                "id": "sug-domain-1",
                "text": "Enforce boundary containment checks across both IPv4 and IPv6 address formats.",
                "reason": "Dual-stack parity ensures consistent validation across network families."
            })
        elif "calculator" in text_lower or "math" in text_lower or "divide" in text_lower:
            suggested_criteria.append({
                "id": "sug-domain-2",
                "text": "Assert ZeroDivisionError or ValueError with explanatory messages on division by zero.",
                "reason": "Guard arithmetic boundary conditions."
            })
        else:
            suggested_criteria.append({
                "id": "sug-domain-gen",
                "text": "Include automated unit and regression test coverage exercising both happy path and boundary failure states.",
                "reason": "Ensure automated CI pipeline verification."
            })

        # 2. Similar Past Work from Repository Memory
        evidence_pack = self.retriever.build_evidence_pack(
            repository_id=repo_id,
            query_or_change=f"{title} {description}",
            system_mode="History-RAG",
            top_k=6
        )

        similar_past_work: List[Dict[str, Any]] = []
        for c in evidence_pack.commit_evidence[:3]:
            similar_past_work.append({
                "type": "commit",
                "id": c.get("commit_sha", "")[:8],
                "title": c.get("title", ""),
                "similarity": c.get("similarity", 0.8),
                "url": f"https://github.com/mock/{repo_id}/commit/{c.get('commit_sha')}"
            })
        for i in (evidence_pack.issue_evidence + evidence_pack.pr_evidence)[:3]:
            similar_past_work.append({
                "type": "issue" if "issue" in i.get("id", "") else "pr",
                "id": str(i.get("issue_id") or i.get("pr_id") or "1"),
                "title": i.get("title", ""),
                "similarity": i.get("similarity", 0.75),
                "url": f"https://github.com/mock/{repo_id}/issues"
            })

        # 3. Duplicate Warning Check across existing Feature Requests
        duplicate_warning: Optional[Dict[str, Any]] = None
        existing_requests = self.db.list_feature_requests(project_id=project_id)
        for ex in existing_requests:
            if ex.title.lower() == title.lower():
                duplicate_warning = {
                    "request_id": ex.id,
                    "title": ex.title,
                    "status": ex.status.value,
                    "match_type": "exact_title",
                    "message": f"Exact title match found: '{ex.title}' is currently {ex.status.value}."
                }
                break
            elif len(set(ex.title.lower().split()) & set(title.lower().split())) >= 4:
                duplicate_warning = {
                    "request_id": ex.id,
                    "title": ex.title,
                    "status": ex.status.value,
                    "match_type": "high_overlap",
                    "message": f"High semantic similarity with existing request: '{ex.title}' ({ex.status.value})."
                }
                break

        return {
            "flags": flags,
            "suggested_criteria": suggested_criteria,
            "similar_past_work": similar_past_work,
            "duplicate_warning": duplicate_warning,
            "overall_clarity_score": max(0.4, 1.0 - (len(flags) * 0.15))
        }
