"""
Evidence Scoring Engine for Change-Impact Analysis.
Conforms strictly to Sections 10.1 and 10.2 of the implementation plan.
The measurable prediction is made by this deterministic engine, not by the LLM.
"""
import re
import logging
from typing import List, Dict, Any, Optional
from app.rag.evidence_pack import EvidencePack

logger = logging.getLogger(__name__)


class ImpactScoringEngine:
    def __init__(
        self,
        w1_semantic: float = 0.25,
        w2_dependency: float = 0.25,
        w3_cochange: float = 0.25,
        w4_test: float = 0.25
    ):
        self.w1 = w1_semantic
        self.w2 = w2_dependency
        self.w3 = w3_cochange
        self.w4 = w4_test

    def score_components(
        self,
        evidence_pack: EvidencePack,
        system_mode: str = "History-RAG",
        threshold_high: float = 0.55,
        threshold_medium: float = 0.25
    ) -> List[Dict[str, Any]]:
        candidate_components = evidence_pack.candidate_components
        if not candidate_components:
            return []

        # If analysis mode is insufficient evidence, return low scores with warning
        if evidence_pack.analysis_mode == "Insufficient evidence":
            return [
                {
                    "component": c,
                    "score": 0.0,
                    "impact_level": "LOW",
                    "breakdown": {"semantic": 0.0, "dependency": 0.0, "cochange": 0.0, "test": 0.0},
                    "reasons": ["Insufficient repository evidence available"]
                }
                for c in candidate_components
            ]

        # 1. Semantic relevance term per component
        semantic_scores = self._compute_semantic_scores(candidate_components, evidence_pack)

        # 2. Dependency evidence term
        dep_scores = self._compute_dependency_scores(candidate_components, evidence_pack)

        # 3. Historical co-change term (disabled in Code-RAG)
        if system_mode == "Code-RAG":
            cochange_scores = {c: 0.0 for c in candidate_components}
        else:
            cochange_scores = self._compute_cochange_scores(candidate_components, evidence_pack)

        # 4. Test relationship term
        test_scores = self._compute_test_scores(candidate_components, evidence_pack)

        # 5. Graph path connectivity (for Section 33 Enhancement #1: History-RAG + Graph)
        graph_scores = {}
        if system_mode == "History-RAG + Graph" and evidence_pack.graph_paths:
            for c in candidate_components:
                comp_node = f"comp:{c}"
                matching_paths = [
                    p for p in evidence_pack.graph_paths
                    if comp_node in p.get("path_nodes", [])
                ]
                if matching_paths:
                    shortest_hops = min(p.get("hops", 9) for p in matching_paths)
                    graph_scores[c] = round(max(0.05, 0.35 / max(1, shortest_hops)), 4)
                else:
                    graph_scores[c] = 0.0

        # In Limited Mode, dependency evidence is unavailable -> 0
        if evidence_pack.analysis_mode == "Limited":
            dep_scores = {c: 0.0 for c in candidate_components}

        # Calculate weighted composite score
        results = []
        for c in candidate_components:
            s_sem = semantic_scores.get(c, 0.0)
            s_dep = dep_scores.get(c, 0.0)
            s_co = cochange_scores.get(c, 0.0)
            s_test = test_scores.get(c, 0.0)
            s_graph = graph_scores.get(c, 0.0)

            if system_mode == "History-RAG + Graph":
                # Re-balance 5 terms: sem(0.20) + dep(0.20) + co(0.20) + test(0.20) + graph(0.20)
                total_score = (
                    (0.20 * s_sem)
                    + (0.20 * s_dep)
                    + (0.20 * s_co)
                    + (0.20 * s_test)
                    + (0.20 * s_graph)
                )
            else:
                total_score = (
                    (self.w1 * s_sem)
                    + (self.w2 * s_dep)
                    + (self.w3 * s_co)
                    + (self.w4 * s_test)
                )
            # Normalize between 0.0 and 1.0
            score = round(min(1.0, max(0.0, total_score)), 4)

            # Impact level classification
            if score >= threshold_high:
                level = "HIGH"
            elif score >= threshold_medium:
                level = "MEDIUM"
            else:
                level = "LOW"

            reasons = []
            if s_sem > 0.4:
                reasons.append(f"High direct semantic similarity ({s_sem:.2f})")
            if s_dep > 0.3:
                reasons.append(f"Import dependency connection ({s_dep:.2f})")
            if s_co > 0.3:
                reasons.append(f"Historical co-change correlation ({s_co:.2f})")
            if s_test > 0.3:
                reasons.append(f"Strong test linkage ({s_test:.2f})")
            if s_graph > 0.1:
                reasons.append(f"Multi-hop knowledge graph path connectivity ({s_graph:.2f})")

            breakdown_dict = {
                "semantic_relevance": round(s_sem, 4),
                "dependency_evidence": round(s_dep, 4),
                "historical_cochange": round(s_co, 4),
                "test_relationship": round(s_test, 4)
            }
            if system_mode == "History-RAG + Graph":
                breakdown_dict["graph_connectivity"] = round(s_graph, 4)

            results.append({
                "component": c,
                "score": score,
                "impact_level": level,
                "breakdown": breakdown_dict,
                "reasons": reasons or ["Baseline contextual relevance"]
            })

        # Deterministic sorting: higher score first, then component name alphabetically
        results.sort(key=lambda x: (-x["score"], x["component"]))
        return results

    def _compute_semantic_scores(self, components: List[str], pack: EvidencePack) -> Dict[str, float]:
        scores = {c: 0.0 for c in components}
        query_text = pack.query_or_change.lower()

        # Check explicit mention in query text
        for c in components:
            if re.search(r"\b" + re.escape(c.lower()) + r"\b", query_text):
                scores[c] += 0.65

        # Check hits in code evidence
        for item in pack.code_evidence:
            comp = item.get("component")
            if comp in scores:
                scores[comp] += item.get("similarity", 0.5) * 0.3

        # Check hits in commits/issues/PRs
        for item in pack.commit_evidence + pack.issue_evidence + pack.pr_evidence:
            comp = item.get("component")
            if comp in scores:
                scores[comp] += item.get("similarity", 0.4) * 0.2

        # Normalize max to 1.0
        max_val = max(scores.values()) if scores else 1.0
        if max_val > 1.0:
            scores = {k: v / max_val for k, v in scores.items()}
        return scores

    def _compute_dependency_scores(self, components: List[str], pack: EvidencePack) -> Dict[str, float]:
        scores = {c: 0.0 for c in components}
        for dep in pack.dependency_evidence:
            src = dep.get("source_component")
            tgt = dep.get("target_component")
            if src in scores:
                scores[src] += 0.35
            if tgt in scores:
                scores[tgt] += 0.35

        max_val = max(scores.values()) if scores else 1.0
        if max_val > 1.0:
            scores = {k: v / max_val for k, v in scores.items()}
        return scores

    def _compute_cochange_scores(self, components: List[str], pack: EvidencePack) -> Dict[str, float]:
        scores = {c: 0.0 for c in components}
        for comp, peers in pack.cochange_evidence.items():
            for peer, count in peers.items():
                if peer in scores:
                    scores[peer] += min(1.0, count * 0.25)

        max_val = max(scores.values()) if scores else 1.0
        if max_val > 1.0:
            scores = {k: v / max_val for k, v in scores.items()}
        return scores

    def _compute_test_scores(self, components: List[str], pack: EvidencePack) -> Dict[str, float]:
        scores = {c: 0.0 for c in components}
        for test in pack.available_tests:
            test_lower = test.lower()
            for c in components:
                if f"test_{c}" in test_lower or f"/{c}/" in test_lower:
                    scores[c] += 0.2
        max_val = max(scores.values()) if scores else 1.0
        if max_val > 1.0:
            scores = {k: v / max_val for k, v in scores.items()}
        return scores
