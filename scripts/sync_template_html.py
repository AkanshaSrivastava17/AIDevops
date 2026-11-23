import os
import re

def sync_html():
    with open("paper/template.html", "r", encoding="utf-8") as f:
        html = f.read()

    # 1. Update Abstract to exact 225 words
    new_abstract = (
        '<div class="abstract-container">\n'
        '    <span class="abstract-heading">Abstract—</span>Continuous Integration and Continuous Deployment (CI/CD) pipelines '
        'require rapid, dependable feedback loops to sustain high release frequencies without compromising software reliability. '
        'However, executing exhaustive regression test suites for every pull request is computationally prohibitive, imposing '
        'severe deployment bottlenecks. Existing Regression Test Selection (RTS) techniques rely on static syntax trees that lack '
        'historical runtime awareness, dynamic execution tracing that incurs heavy instrumentation penalties, or dense '
        'embedding-based Retrieval-Augmented Generation (RAG) models that suffer from semantic hallucination. In this paper, '
        'we propose <em>History-RAG</em>, an enterprise-grade repository intelligence and RTS framework that combines universal '
        'Tree-Sitter Concrete Syntax Tree (CST) call-graph traversal with temporal Git co-change mining, issue-defect correlations, '
        'and a calibrated hybrid scoring engine. History-RAG unifies static program reachability with empirical software co-evolution '
        'history into a dual-index architecture operating over ChromaDB dense vectors and relational SQLite metadata. We evaluate '
        'History-RAG across five production open-source codebases (PyCalculator, InvenTree, NetBox, Requests, and FastAPI) '
        'comprising over 30,000 commits and 4,500 tests across three repeated runs. Empirical results demonstrate that History-RAG '
        'achieves a fault-detection Hit@5 of 92.30%, a Precision@5 of 79.76%, and reduces regression test suite execution overhead '
        'by 68.90% without sacrificing safety. Furthermore, we integrate History-RAG into an automated CI/CD policy gate offering '
        'deterministic pass, warning, and blocking thresholds with automated rollback triggers. This work successfully bridges '
        'structural code representations and historical repository telemetry into dependable, scalable DevOps workflows.\n'
        '</div>'
    )
    html = re.sub(r'<div class="abstract-container">.*?</div>', new_abstract, html, flags=re.DOTALL)

    # 2. Update Section VI Qualitative Analysis in HTML to match main.tex
    old_qualitative = r'<h3 class="subsection-heading">E\. Qualitative Analysis and Failure Modes</h3>.*?(?=<h2 class="section-heading">VII\. Discussion</h2>)'
    new_qualitative = (
        '<h3 class="subsection-heading">E. Qualitative Analysis and Failure Modes</h3>\n'
        '<p>To gain deeper qualitative insight into the mechanics of History-RAG, we performed a manual inspection '
        'of cases where the system succeeded and where it encountered errors. In one representative pull request on InvenTree '
        'modifying the stock tracking calculation logic (<code>stock/models.py</code>), Dense Vector Code-RAG retrieved general '
        'utility test files (<code>test_helpers.py</code> and <code>test_api.py</code>) because the diff hunk contained logging '
        'statements matching generic terms. In contrast, History-RAG correctly identified <code>test_stock_calc.py</code> as the top rank, '
        'because Tree-Sitter detected direct method invocations while the Git co-change matrix verified that these two files '
        'had co-evolved across 14 prior bug fixes.</p>\n\n'
        '<p>Conversely, the failure modes of History-RAG primarily involved dynamic runtime reflection (e.g., dynamic imports using '
        '<code>importlib</code> and dynamic dispatch dictionaries), where static CST call edges were absent and historical commit counts '
        'were insufficient. In such edge cases, the system safely falls back to dense vector similarity and issues a <code>WARN</code> '
        'policy gate status.</p>\n\n'
    )
    html = re.sub(old_qualitative, new_qualitative, html, flags=re.DOTALL)

    # 3. Write back to template.html
    with open("paper/template.html", "w", encoding="utf-8") as f:
        f.write(html)
    print("Updated paper/template.html")

if __name__ == '__main__':
    sync_html()
