"""
Existing-Test Recommendation Engine.
Ranks and recommends tests that already exist in the repository (Section 11, 11.2).
Tests added by the change itself are strictly excluded.
"""
import re
import logging
from typing import List, Dict, Any, Optional
from app.rag.evidence_pack import EvidencePack

logger = logging.getLogger(__name__)


class TestRecommender:
    __test__ = False

    def __init__(
        self,
        w_path: float = 0.35,
        w_dependency: float = 0.25,
        w_cochange: float = 0.25,
        w_issue_ref: float = 0.15
    ):
        self.w_path = w_path
        self.w_dep = w_dependency
        self.w_cochange = w_cochange
        self.w_issue = w_issue_ref

    def rank_tests(
        self,
        evidence_pack: EvidencePack,
        affected_components: List[str],
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        available_tests = evidence_pack.available_tests
        if not available_tests:
            return []

        # If analysis mode is insufficient evidence, return empty or low confidence
        if evidence_pack.analysis_mode == "Insufficient evidence":
            return []

        scores: Dict[str, Dict[str, Any]] = {}

        for test_path in available_tests:
            test_norm = test_path.replace("\\", "/").lower()
            
            # 1. Path & Naming convention match with affected components
            path_score = 0.0
            matched_comps = []
            for comp in affected_components:
                c_low = comp.lower()
                if f"test_{c_low}.py" in test_norm or f"/{c_low}/tests/" in test_norm or f"/tests/{c_low}/" in test_norm:
                    path_score = 1.0
                    matched_comps.append(comp)
                elif c_low in test_norm:
                    path_score = max(path_score, 0.6)
                    matched_comps.append(comp)

            # 2. Dependency / Import evidence (if in Enhanced mode)
            dep_score = 0.0
            if evidence_pack.analysis_mode == "Enhanced":
                for dep in evidence_pack.dependency_evidence:
                    target_comp = dep.get("target_component", "").lower()
                    if target_comp in [c.lower() for c in affected_components]:
                        if target_comp in test_norm:
                            dep_score = max(dep_score, 0.8)

            # 3. Historical co-change (tests touched together with components in past commits)
            cochange_score = 0.0
            if evidence_pack.system_mode == "History-RAG":
                for commit in evidence_pack.commit_evidence:
                    files = commit.get("files_changed", [])
                    has_comp_file = any(
                        any(c.lower() in f.lower() for c in affected_components)
                        for f in files
                    )
                    if has_comp_file and test_path in files:
                        cochange_score = min(1.0, cochange_score + 0.4)

            # 4. Issue and PR references to tests
            issue_score = 0.0
            if evidence_pack.system_mode in ("History-RAG", "History-RAG + Graph"):
                test_name = test_path.split("/")[-1]
                for doc in evidence_pack.issue_evidence + evidence_pack.pr_evidence:
                    content = doc.get("content", "").lower()
                    if test_name.lower() in content:
                        issue_score = max(issue_score, 0.9)

            # 5. Graph proximity score (Section 33 Enhancement #1)
            graph_score = 0.0
            graph_hops = None
            if evidence_pack.graph_ranked_tests:
                for gt in evidence_pack.graph_ranked_tests:
                    if gt.get("test_file") == test_path:
                        graph_score = gt.get("graph_score", 0.0)
                        graph_hops = gt.get("hops")
                        break

            # Composite test score
            composite = (
                (self.w_path * path_score)
                + (self.w_dep * dep_score)
                + (self.w_cochange * cochange_score)
                + (self.w_issue * issue_score)
            )
            if evidence_pack.system_mode == "History-RAG + Graph" and graph_score > 0:
                composite = round(0.75 * composite + 0.25 * graph_score, 4)

            score = round(min(1.0, max(0.0, composite)), 4)
            reasons = []
            if path_score > 0.5:
                reasons.append(f"Direct component path match ({', '.join(matched_comps)})")
            if dep_score > 0.4:
                reasons.append("Import dependency linkage")
            if cochange_score > 0.3:
                reasons.append("Frequently co-changed with component in past commits")
            if issue_score > 0.4:
                reasons.append("Explicitly referenced in historical PR/issue discussion")
            if graph_score > 0 and graph_hops:
                reasons.append(f"Knowledge Graph proximity ({graph_hops} hop(s))")

            breakdown_dict = {
                "path_score": path_score,
                "dependency_score": dep_score,
                "cochange_score": cochange_score,
                "issue_reference_score": issue_score
            }
            if graph_score > 0:
                breakdown_dict["graph_proximity_score"] = graph_score

            scores[test_path] = {
                "test_file": test_path,
                "score": score,
                "breakdown": breakdown_dict,
                "reasons": reasons or ["Available regression test"]
            }

        # Filter out tests with 0.0 score unless none found
        ranked = [v for v in scores.values() if v["score"] > 0.0]
        ranked.sort(key=lambda x: (-x["score"], x["test_file"]))
        
        # If no tests scored above 0, return top available as fallback
        if not ranked and available_tests:
            for t in available_tests[:top_k]:
                ranked.append({
                    "test_file": t,
                    "score": 0.1,
                    "breakdown": {"path_score": 0.1, "dependency_score": 0.0, "cochange_score": 0.0, "issue_reference_score": 0.0},
                    "reasons": ["General test suite fallback"]
                })

        return ranked[:top_k]
