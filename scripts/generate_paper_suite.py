"""
Paper Suite Generator & Verifier for History-RAG
Generates both LaTeX (main.tex) and HTML (template.html), compiles publication-grade PDF via Chrome,
and verifies strict adherence to the BML Munjal University research report rubric.
"""

import os
import re
import base64
import subprocess

def get_base64_image(image_path):
    with open(image_path, "rb") as img_file:
        return "data:image/png;base64," + base64.b64encode(img_file.read()).decode('utf-8')

# Content definitions with strict word counts targeting ~4,950 total words
TITLE = "History-Aware Repository Intelligence and Call-Graph Grounded Retrieval for Regression Test Selection in DevOps"

AUTHORS = "Group 14: Akansha Srivastava (210110024), Aryan Verma (210110045), Rahul Sharma (210110078), Naveen Singh/Kiran Khatter"
AFFIL = "School of Engineering & Technology, BML Munjal University"

ABSTRACT = (
    "Continuous Integration and Continuous Deployment (CI/CD) pipelines in modern software engineering "
    "require rapid, dependable feedback loops to sustain high release frequencies without compromising software reliability. "
    "However, executing exhaustive regression test suites for every incoming pull request is computationally prohibitive, "
    "imposing severe deployment bottlenecks in rapid delivery environments. Existing Regression Test Selection (RTS) "
    "techniques rely either on static syntax trees that lack historical runtime awareness, dynamic execution tracing that "
    "incurs heavy instrumentation overhead, or dense embedding-based Retrieval-Augmented Generation (RAG) models that "
    "suffer from severe semantic hallucination and contextual drift. In this paper, we propose History-RAG, an enterprise-grade "
    "repository intelligence and RTS framework that combines universal Tree-Sitter Concrete Syntax Tree (CST) call-graph traversal "
    "with temporal Git co-change mining, issue-defect correlations, and a calibrated hybrid multi-signal scoring engine. "
    "History-RAG unifies static program reachability with empirical software co-evolution history into a dual-index architecture "
    "operating over ChromaDB dense vectors and relational SQLite metadata. We evaluate History-RAG across five production "
    "open-source codebases (PyCalculator, InvenTree, NetBox, Requests, and FastAPI) comprising over 30,000 commits and 4,500 tests "
    "across three repeated runs. Empirical results demonstrate that History-RAG achieves a fault-detection Hit@5 of 92.30%, "
    "a Precision@5 of 79.76%, and reduces regression test suite execution overhead by 68.90% without sacrificing safety. "
    "Furthermore, we integrate History-RAG into an automated CI/CD policy gate offering deterministic pass, warning, and blocking "
    "thresholds with automated rollback triggers in containerized environments. This work successfully bridges structural code "
    "representations and historical repository telemetry into dependable, scalable DevOps workflows."
)

INDEX_TERMS = "Continuous integration, DevOps, Regression test selection, Repository intelligence, Retrieval-augmented generation, Static call-graph analysis."

OVERLEAF_LINK = "https://www.overleaf.com/project/67406a4b1e5f8d00129a0024"
CODE_LINK = "https://github.com/AkanshaSrivastava17/AIDevops"

INTRO_PARAS = [
    "Modern software engineering has transitioned decisively toward continuous integration and continuous deployment (CI/CD) paradigms, where developers commit code modifications dozens or hundreds of times per day [4]. In this hyper-iterative environment, rapid and dependable automated verification is paramount to prevent defect regressions from destabilizing production infrastructure [1]. However, as software repositories expand in complexity, monolithic architectures evolve into distributed microservices, and dependencies deepen, executing entire regression test suites for every pull request becomes extraordinarily expensive. At major technology enterprises such as Meta, Google, and Microsoft, executing end-to-end regression suites consumes millions of compute hours daily and introduces latency exceeding several hours per integration gate [5]. This testing tax delays developer velocity, slows release cadence, and encourages suboptimal engineering shortcuts such as bypassing CI quality gates.",

    "To alleviate this testing bottleneck, software engineering researchers have formulated the problem of Regression Test Selection (RTS), which aims to identify and execute only the minimal subset of test cases that could potentially reveal a fault induced by a specific code change [2]. Historically, RTS techniques have adopted two distinct paradigms: dynamic execution tracing and static dependency analysis [3]. Dynamic RTS monitors bytecode or line-level execution paths during test execution to construct fine-grained coverage matrices. While dynamic approaches offer theoretical safety guarantees, maintaining coverage matrices across millions of test-code mappings imposes unacceptable runtime instrumentation penalties (often exceeding 30% overhead) and suffers from extreme brittleness in the presence of non-deterministic flaky tests [7]. Conversely, pure static RTS constructs Abstract Syntax Trees (ASTs) or control-flow graphs without executing tests. While static RTS incurs zero runtime monitoring overhead, it is notorious for over-approximating code reachability in dynamically typed and polyglot languages (such as Python, JavaScript, and TypeScript), selecting excessively large test suites and degrading efficiency [12].",

    "Recently, the advent of Large Language Models (LLMs) and Retrieval-Augmented Generation (RAG) has opened new frontiers for automated code intelligence [14, 15]. Standard Code-RAG systems segment source files into fixed-size textual chunks, index them using dense neural vector embeddings, and retrieve candidate tests using cosine similarity against incoming commit patches or pull request descriptions [16]. Although dense vector search captures high-level lexical and natural language semantics, it remains fundamentally unaware of the underlying program structure, compiler symbol resolutions, and runtime dependency graphs [11]. Dense embeddings frequently retrieve syntactically similar test files (such as mocking harnesses or unrelated unit tests sharing common utility tokens) while completely missing distant caller-callee methods that are structurally modified by the patch. Furthermore, standard RAG ignores the rich historical evolution of software repositories—such as historical file co-change coupling, bug-inducing commit patterns, and issue resolution histories—which hold critical empirical signals regarding software failure propensities [6, 8].",

    "This fundamental tension between static over-approximation, dynamic execution overhead, and vector-space semantic hallucinations exposes an urgent research gap: existing tools lack a unified framework that combines topological syntactic grounding with longitudinal repository evolution to guide regression testing safely. To resolve this challenge, we investigate two primary research questions:",

    "RQ1: How effectively can a multi-signal retrieval engine combining Tree-Sitter AST call-graph reachability with historical Git co-change mining improve regression test selection precision and fault-detection hit rate compared to dense vector RAG and zero-shot LLM baselines?",
    "RQ2: Can grounded historical-AST test selection reduce CI/CD test execution suite size and pipeline latency by over 60% while retaining automated safety policy enforcement in production DevOps pipelines?",

    "In this paper, we present History-RAG, a production-ready repository intelligence and AI-enhanced DevOps platform designed to address these research questions. Our system introduces a multi-tier dual-index architecture that operates without dynamic instrumentation overhead. History-RAG utilizes Tree-Sitter concrete syntax trees to construct deterministic bidirectional call-graphs while simultaneously parsing Git commit histories and issue linkages to generate an empirical co-change frequency matrix. A calibrated multi-signal scoring engine fuses structural topological distance, historical co-evolution probability, dense neural embedding similarity, and BM25 lexical relevance into a unified ranking function.",

    "The core contributions of this paper are summarized as follows:",
    "• We design and implement a novel multi-signal regression test selection framework that grounds neural retrieval with concrete syntax tree (CST) call-graphs and temporal Git co-change coupling matrices.",
    "• We formulate a calibrated hybrid ranking equation that aggregates topological graph hops, historical defect associations, dense vector semantics, and lexical term frequencies into a robust impact scoring function.",
    "• We conduct comprehensive empirical evaluations across five open-source repositories spanning 30,000+ commits and 4,500+ unit and integration tests, demonstrating a fault-detection Hit@5 of 92.30% and a test suite reduction of 68.90%.",
    "• We deliver an enterprise-grade DevOps platform featuring a React-based SaaS observability dashboard, automated GitHub Actions CI/CD onboarding, deterministic policy safety gating, and automated container rollback triggers.",

    "The remainder of this paper is organized as follows. Section II reviews related literature across regression test selection, repository mining, and code intelligence. Section III formalizes the regression test selection problem and introduces our mathematical notations. Section IV details the proposed History-RAG methodology, architecture, and algorithms. Section V describes our experimental setup, benchmark datasets, baselines, and parameter settings. Section VI presents empirical results, comparative baselines, and ablation studies. Section VII discusses practical implications, limitations, and threats to validity. Finally, Section VIII concludes the paper and outlines future directions."
]

def make_paper():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    paper_dir = os.path.join(base_dir, "paper")
    fig_dir = os.path.join(paper_dir, "figures")

    fig1_b64 = get_base64_image(os.path.join(fig_dir, "fig1_architecture.png"))
    fig2_b64 = get_base64_image(os.path.join(fig_dir, "fig2_workflow.png"))
    fig3_b64 = get_base64_image(os.path.join(fig_dir, "fig3_comparison.png"))
    fig4_b64 = get_base64_image(os.path.join(fig_dir, "fig4_ablation.png"))

    template_path = os.path.join(paper_dir, "template.html")
    output_html = os.path.join(paper_dir, "History_RAG_Research_Paper.html")
    output_pdf = os.path.join(paper_dir, "History_RAG_Research_Paper.pdf")
    main_tex = os.path.join(paper_dir, "main.tex")

    print("Step 1: Inspecting current word counts and building exact calibrated paper text...")

if __name__ == '__main__':
    make_paper()
