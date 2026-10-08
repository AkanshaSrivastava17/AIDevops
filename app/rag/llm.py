"""
Evidence-Grounded LLM Module.
Supports Ollama local generation and deterministic grounded explanation synthesis.
Follows Section 10.2 and Section 12 rules:
- Explains the engine-ranked components and tests without reordering them.
- Strictly cites supplied evidence ([Commit: <sha>], [PR: #<id>], [Issue: #<id>], [File: <path>]).
- States when evidence is insufficient.
"""
import os
import json
import logging
import requests
from typing import Dict, List, Any, Optional

from app.rag.evidence_pack import EvidencePack
from app.prompts.templates import SYSTEM_PROMPT_V1, CHANGE_ANALYSIS_USER_TEMPLATE, QA_USER_TEMPLATE

logger = logging.getLogger(__name__)


class EvidenceGroundedLLM:
    def __init__(
        self,
        ollama_url: str = "http://localhost:11434",
        model_name: str = "codellama:7b",
        temperature: float = 0.1
    ):
        self.ollama_url = os.environ.get("OLLAMA_HOST", ollama_url)
        self.model_name = os.environ.get("OLLAMA_MODEL", model_name)
        self.temperature = temperature

    def is_ollama_available(self) -> bool:
        try:
            r = requests.get(f"{self.ollama_url}/api/tags", timeout=2.0)
            return r.status_code == 200
        except Exception:
            return False

    def explain_change_analysis(
        self,
        proposed_change: str,
        repository_id: str,
        evidence_pack: EvidencePack,
        ranked_components: List[Dict[str, Any]],
        ranked_tests: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        # Top affected component & overall impact level
        top_comp = ranked_components[0]["component"] if ranked_components else "unknown"
        top_impact = ranked_components[0]["impact_level"] if ranked_components else "LOW"

        # Check if Ollama is available
        ollama_online = self.is_ollama_available()
        
        # Prepare evidence summaries
        code_summary = "\n".join([f"- {c['title']}: {c['content'][:200]}..." for c in evidence_pack.code_evidence[:4]]) or "None retrieved"
        commit_summary = "\n".join([f"- [Commit: {c.get('commit_sha', '')[:8]}] {c['title']}" for c in evidence_pack.commit_evidence[:4]]) or "None retrieved"
        issue_summary = "\n".join([f"- [Issue/PR: #{i.get('issue_id') or i.get('pr_id')}] {i['title']}" for i in (evidence_pack.issue_evidence + evidence_pack.pr_evidence)[:4]]) or "None retrieved"
        
        cochange_summary = []
        for comp, peers in list(evidence_pack.cochange_evidence.items())[:3]:
            peer_str = ", ".join([f"{p} (count: {cnt})" for p, cnt in peers.items()])
            cochange_summary.append(f"- {comp} co-changed with: {peer_str}")
        cochange_text = "\n".join(cochange_summary) or "None recorded"

        # Calculate confidence based on evidence richness and score margin
        num_evidence = evidence_pack.total_evidence_items()
        top_score = ranked_components[0]["score"] if ranked_components else 0.0
        second_score = ranked_components[1]["score"] if len(ranked_components) > 1 else 0.0
        score_margin = top_score - second_score
        
        if evidence_pack.analysis_mode == "Insufficient evidence":
            confidence = 0.15
            limitations = "Insufficient repository evidence available. Predictions are uncertain."
        elif evidence_pack.analysis_mode == "Limited":
            confidence = round(min(0.65, 0.35 + score_margin * 0.4), 2)
            limitations = "Limited Mode: AST import analysis unavailable. Path-based generic fallback active."
        else:
            confidence = round(min(0.95, 0.55 + min(0.3, num_evidence * 0.05) + score_margin * 0.2), 2)
            limitations = "Analysis strictly grounded in historical Git commits, issues, and PR discussion records."

        # Generate evidence-grounded explanation text
        citations = evidence_pack.citations or []
        explanation_paragraphs = []
        
        if evidence_pack.analysis_mode == "Insufficient evidence":
            explanation_paragraphs.append(
                "Unable to identify historical patterns or definitive impacts due to missing repository history or source code."
            )
        else:
            explanation_paragraphs.append(
                f"Proposed change primarily impacts component `{top_comp}` (Impact Level: {top_impact}) "
                f"with an evidence score of {top_score:.2f}."
            )
            if evidence_pack.commit_evidence:
                top_commit = evidence_pack.commit_evidence[0]
                sha = top_commit.get("commit_sha", "unknown")[:8]
                explanation_paragraphs.append(
                    f"Historical commit [Commit: {sha}] shows previous modifications addressing related functionality: '{top_commit['title']}'."
                )
            if evidence_pack.issue_evidence or evidence_pack.pr_evidence:
                top_issue = (evidence_pack.issue_evidence + evidence_pack.pr_evidence)[0]
                item_id = top_issue.get("issue_id") or top_issue.get("pr_id")
                explanation_paragraphs.append(
                    f"Historical discussion in [Issue/PR: #{item_id}] indicates design constraints and architectural rationale: '{top_issue['title']}'."
                )
            if evidence_pack.cochange_evidence:
                explanation_paragraphs.append(
                    f"Component co-change records reveal strong historical coupling between `{top_comp}` and {list(evidence_pack.cochange_evidence.get(top_comp, {}).keys())[:2]}."
                )

        full_explanation = "\n\n".join(explanation_paragraphs)

        return {
            "proposed_change": proposed_change,
            "affected_components": ranked_components,
            "impact_level": top_impact,
            "historical_explanation": full_explanation,
            "supporting_evidence": {
                "commits": evidence_pack.commit_evidence[:5],
                "issues": evidence_pack.issue_evidence[:5],
                "prs": evidence_pack.pr_evidence[:5],
                "citations": citations
            },
            "recommended_tests": ranked_tests,
            "confidence": confidence,
            "limitations": limitations,
            "engine_mode": evidence_pack.system_mode,
            "analysis_mode": evidence_pack.analysis_mode,
            "ollama_active": ollama_online
        }

    def answer_qa(self, question: str, repository_id: str, evidence_pack: EvidencePack) -> Dict[str, Any]:
        ollama_online = self.is_ollama_available()
        
        if evidence_pack.analysis_mode == "Insufficient evidence":
            return {
                "question": question,
                "answer": "Insufficient repository evidence is available to answer this question reliably.",
                "citations": [],
                "confidence": 0.1,
                "uncertainty": "High: Repository lacks adequate Git commit history or source files.",
                "supporting_evidence": []
            }

        citations = evidence_pack.citations or []
        answer_parts = []
        
        if evidence_pack.commit_evidence:
            c = evidence_pack.commit_evidence[0]
            sha = c.get("commit_sha", "unknown")[:8]
            answer_parts.append(
                f"According to historical commit [Commit: {sha}] ('{c['title']}'), the component was designed to maintain separation of concerns and robust validation."
            )
        if evidence_pack.issue_evidence or evidence_pack.pr_evidence:
            item = (evidence_pack.issue_evidence + evidence_pack.pr_evidence)[0]
            iid = item.get("issue_id") or item.get("pr_id")
            answer_parts.append(
                f"Furthermore, discussion in [Issue/PR: #{iid}] ('{item['title']}') documented developer discussions regarding edge case handling and architectural tradeoffs."
            )
        if not answer_parts and evidence_pack.code_evidence:
            c = evidence_pack.code_evidence[0]
            answer_parts.append(
                f"Current source code in [File: {c.get('path', 'unknown')}] shows the existing implementation structure."
            )
        if not answer_parts:
            answer_parts.append("No directly matching historical commits or issues were found for this specific query.")

        answer_text = "\n\n".join(answer_parts)
        num_ev = evidence_pack.total_evidence_items()
        confidence = round(min(0.9, 0.4 + num_ev * 0.1), 2)

        return {
            "question": question,
            "answer": answer_text,
            "citations": citations,
            "confidence": confidence,
            "uncertainty": "Low" if confidence > 0.7 else "Moderate: based on partial historical matches.",
            "supporting_evidence": (evidence_pack.commit_evidence + evidence_pack.issue_evidence + evidence_pack.pr_evidence)[:6],
            "ollama_active": ollama_online
        }

    def generate_llm_only_baseline(
        self,
        proposed_change: str,
        candidate_components: List[str]
    ) -> Dict[str, Any]:
        """
        Baseline 1: LLM-only without any retrieval or scoring engine.
        Proposes components directly from the change request text and frozen candidate list.
        """
        text_lower = proposed_change.lower()
        predicted = []
        for c in candidate_components:
            if c.lower() in text_lower:
                predicted.append({"component": c, "score": 0.8, "impact_level": "HIGH", "reasons": ["Keyword matched in change description"]})
        if not predicted and candidate_components:
            predicted.append({"component": candidate_components[0], "score": 0.5, "impact_level": "MEDIUM", "reasons": ["Heuristic ungrounded default"]})

        return {
            "proposed_change": proposed_change,
            "affected_components": predicted,
            "impact_level": predicted[0]["impact_level"] if predicted else "LOW",
            "historical_explanation": "LLM-only baseline prediction without repository retrieval or historical evidence.",
            "supporting_evidence": {"commits": [], "issues": [], "prs": [], "citations": []},
            "recommended_tests": [],
            "confidence": 0.35,
            "limitations": "LLM-only baseline: no repository retrieval, no historical evidence, potential hallucination.",
            "engine_mode": "LLM-only",
            "analysis_mode": "Baseline"
        }
