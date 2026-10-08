"""
Versioned prompt templates for evidence-grounded repository intelligence.
Strictly conforms to Section 12 of the implementation plan.
"""

SYSTEM_PROMPT_V1 = """ROLE
You are a repository-history analysis assistant.

RULES
1. Use supplied repository evidence for historical claims.
2. Do not invent historical reasons.
3. Distinguish direct evidence from inference.
4. State when evidence is insufficient.
5. Cite commit, issue, PR, file or test evidence explicitly (e.g. [Commit: <sha>], [PR: #<id>], [Issue: #<id>], [File: <path>]).
6. Recommend only tests that appear in the supplied evidence.
7. Explain the supplied component and test ranking; do not add, remove or reorder items.

OUTPUT
- Proposed change
- Affected components
- Impact level
- Historical explanation
- Supporting evidence
- Recommended existing tests
- Confidence / uncertainty
- Limitations
"""

CHANGE_ANALYSIS_USER_TEMPLATE = """PROPOSED CHANGE:
{proposed_change}

REPOSITORY: {repository_id}
ANALYSIS MODE: {analysis_mode}
SYSTEM MODE: {system_mode}

ENGINE-RANKED AFFECTED COMPONENTS (Deterministic Ground Truth - Do not reorder):
{ranked_components_text}

ENGINE-RANKED RECOMMENDED EXISTING TESTS:
{ranked_tests_text}

SUPPLIED REPOSITORY EVIDENCE PACK:
--- CODE SNIPPETS ---
{code_evidence_text}

--- HISTORICAL COMMITS ---
{commit_evidence_text}

--- HISTORICAL ISSUES & PRs ---
{issue_pr_evidence_text}

--- COMPONENT CO-CHANGE & DEPENDENCIES ---
{cochange_deps_text}

Provide the structured evidence-grounded explanation now following all rules.
"""

QA_USER_TEMPLATE = """REPOSITORY QUESTION:
{question}

REPOSITORY: {repository_id}
ANALYSIS MODE: {analysis_mode}
SYSTEM MODE: {system_mode}

SUPPLIED REPOSITORY EVIDENCE PACK:
--- CODE SNIPPETS ---
{code_evidence_text}

--- HISTORICAL COMMITS ---
{commit_evidence_text}

--- HISTORICAL ISSUES & PRs ---
{issue_pr_evidence_text}

Answer the developer's question grounded strictly on the supplied evidence. State any uncertainties if evidence is insufficient.
"""
