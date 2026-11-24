"""
Academic Vector Figure Generator for History-RAG
Generates:
1. figures/fig1_architecture.pdf & png (System Architecture Diagram - Simplified, clear, collision-free)
2. figures/fig2_workflow.pdf & png (Workflow Diagram - Simplified, clear, collision-free)
3. figures/fig3_comparison.pdf & png (Benchmark Performance Comparison Chart)
4. figures/fig4_ablation.pdf & png (Ablation & Sensitivity Analysis)
"""

import os
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch
import numpy as np

# Set clean academic styling
plt.rcParams['font.family'] = 'serif'
plt.rcParams['font.serif'] = ['Times New Roman', 'DejaVu Serif']
plt.rcParams['mathtext.fontset'] = 'stix'

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
fig_dir = os.path.join(base_dir, "paper", "figures")
os.makedirs(fig_dir, exist_ok=True)

# -----------------------------------------------------------------------------
# FIGURE 1: System Architecture Diagram (Simplified, Friendly, Non-Mathematical)
# -----------------------------------------------------------------------------
def generate_fig1_architecture():
    fig, ax = plt.subplots(figsize=(10.8, 6.8), dpi=300)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis('off')

    # Main canvas boundary with subtle border
    bg = FancyBboxPatch((0.5, 0.5), 99, 99, boxstyle="square,pad=0",
                        ec="#CBD5E1", fc="#FFFFFF", lw=1.2)
    ax.add_patch(bg)

    # Column Headers (Tier Titles)
    ax.text(15, 96.5, "TIER 1: INGESTION & INTERFACES", fontsize=10.5, fontweight='bold', color='#1E293B', ha='center', va='top')
    ax.text(50, 96.5, "TIER 2: DUAL ANALYSIS & STORAGE", fontsize=10.5, fontweight='bold', color='#1E293B', ha='center', va='top')
    ax.text(84, 96.5, "TIER 3: INFERENCE & CI/CD GATE", fontsize=10.5, fontweight='bold', color='#1E293B', ha='center', va='top')

    # Subtle column background panels to visually separate tiers
    col1_bg = FancyBboxPatch((2, 3), 26, 91.0, boxstyle="round,pad=0.5,rounding_size=1.0", ec="#E2E8F0", fc="#F8FAFC", lw=0.8, linestyle=":")
    col2_bg = FancyBboxPatch((35, 3), 30, 91.0, boxstyle="round,pad=0.5,rounding_size=1.0", ec="#E2E8F0", fc="#F8FAFC", lw=0.8, linestyle=":")
    col3_bg = FancyBboxPatch((70, 3), 28, 91.0, boxstyle="round,pad=0.5,rounding_size=1.0", ec="#E2E8F0", fc="#F8FAFC", lw=0.8, linestyle=":")
    ax.add_patch(col1_bg)
    ax.add_patch(col2_bg)
    ax.add_patch(col3_bg)

    # =========================================================================
    # COLUMN 1: Ingestion & Interfaces (x: 4 to 26)
    # =========================================================================
    # Box 1A: Pull Request / Commit Patch (y: 73 to 91)
    box_pr = FancyBboxPatch((4, 73), 22, 18, boxstyle="round,pad=0.5,rounding_size=1.5", ec="#2563EB", fc="#EFF6FF", lw=1.4)
    ax.add_patch(box_pr)
    ax.text(15, 89.2, "Pull Request / Commit Patch", fontsize=9.5, fontweight='bold', ha='center', va='top', color='#1E40AF')
    ax.text(15, 83.5, "• Incoming Git pull request diff\n• Modified files and functions\n• Author and commit metadata",
            fontsize=8.0, ha='center', va='top', color='#334155', linespacing=1.35)

    # Box 1B: Repository Ingestion Engine (y: 50 to 69)
    box_repo = FancyBboxPatch((4, 50), 22, 19, boxstyle="round,pad=0.5,rounding_size=1.5", ec="#4F46E5", fc="#EEF2FF", lw=1.4)
    ax.add_patch(box_repo)
    ax.text(15, 67.2, "Repository Ingestion Engine", fontsize=9.5, fontweight='bold', ha='center', va='top', color='#3730A3')
    ax.text(15, 61.5, "• Git clone / ZIP file reader\n• File and directory discovery\n• Commit log extraction",
            fontsize=8.0, ha='center', va='top', color='#334155', linespacing=1.35)

    # Box 1C: Interactive SaaS Observability UI (y: 6 to 46)
    box_ui = FancyBboxPatch((4, 6), 22, 40, boxstyle="round,pad=0.5,rounding_size=1.5", ec="#0284C7", fc="#F0F9FF", lw=1.4)
    ax.add_patch(box_ui)
    ax.text(15, 44.2, "Interactive Web Dashboard", fontsize=10, fontweight='bold', ha='center', va='top', color='#0369A1')
    ax.text(15, 39.5, "React + Vite + Tailwind", fontsize=8.5, fontweight='bold', ha='center', va='top', color='#0284C7')
    ui_features = (
        "• Change Impact Explorer\n"
        "• Interactive Call-Graph View\n"
        "• Historical Evidence Viewer\n"
        "• Policy Gate Simulator\n"
        "• One-Click Rollback Manager\n"
        "• CI/CD Activity Logs"
    )
    ax.text(15, 34.2, ui_features, fontsize=7.8, ha='center', va='top', color='#334155', linespacing=1.35)

    # =========================================================================
    # COLUMN 2: Dual Analysis & Storage (x: 37 to 63)
    # =========================================================================
    # Box 2A: Structural AST Analyzer (y: 72 to 91)
    box_ast = FancyBboxPatch((37, 72), 26, 19, boxstyle="round,pad=0.5,rounding_size=1.5", ec="#059669", fc="#ECFDF5", lw=1.4)
    ax.add_patch(box_ast)
    ax.text(50, 89.2, "Structural Code Analyzer", fontsize=10, fontweight='bold', ha='center', va='top', color='#065F46')
    ax.text(50, 83.5, "• Tree-Sitter syntax tree parser\n• Extracts classes and functions\n• Maps callers and callees\n• Calculates distance to tests",
            fontsize=8.0, ha='center', va='top', color='#1F2937', linespacing=1.35)

    # Box 2B: Historical Co-Change Miner (y: 49 to 68)
    box_git = FancyBboxPatch((37, 49), 26, 19, boxstyle="round,pad=0.5,rounding_size=1.5", ec="#D97706", fc="#FFFBEB", lw=1.4)
    ax.add_patch(box_git)
    ax.text(50, 66.2, "Historical Co-Change Miner", fontsize=10, fontweight='bold', ha='center', va='top', color='#92400E')
    ax.text(50, 60.5, "• Scans Git commit history\n• Finds files modified together\n• 2× weight boost for bug fixes\n• Tracks test failure history",
            fontsize=8.0, ha='center', va='top', color='#1F2937', linespacing=1.35)

    # Box 2C: Dual-Index Persistent Storage (y: 6 to 45)
    box_store = FancyBboxPatch((37, 6), 26, 39, boxstyle="round,pad=0.5,rounding_size=1.5", ec="#475569", fc="#FFFFFF", lw=1.4, linestyle="--")
    ax.add_patch(box_store)
    ax.text(50, 43.0, "Dual-Index Storage", fontsize=10, fontweight='bold', ha='center', va='top', color='#1E293B')

    # Sub-box 2C1: ChromaDB
    chroma_box = FancyBboxPatch((39, 26), 22, 14, boxstyle="round,pad=0.3,rounding_size=1.0", ec="#94A3B8", fc="#F8FAFC", lw=1.0)
    ax.add_patch(chroma_box)
    ax.text(50, 38.0, "ChromaDB Vector Store", fontsize=8.5, fontweight='bold', ha='center', va='top', color='#0F172A')
    ax.text(50, 32.5, "• Dense code embeddings\n• Semantic similarity search", fontsize=7.5, ha='center', va='top', color='#475569', linespacing=1.3)

    # Sub-box 2C2: SQLite
    sqlite_box = FancyBboxPatch((39, 9), 22, 14, boxstyle="round,pad=0.3,rounding_size=1.0", ec="#94A3B8", fc="#F8FAFC", lw=1.0)
    ax.add_patch(sqlite_box)
    ax.text(50, 21.0, "SQLite Relational Database", fontsize=8.5, fontweight='bold', ha='center', va='top', color='#0F172A')
    ax.text(50, 15.5, "• Function call connections\n• Co-change table & audit log", fontsize=7.5, ha='center', va='top', color='#475569', linespacing=1.3)

    # =========================================================================
    # COLUMN 3: Inference & DevOps Policy Gate (x: 72 to 96)
    # =========================================================================
    # Box 3A: Multi-Signal Evidence Scoring Engine (y: 54 to 91)
    box_score = FancyBboxPatch((72, 54), 24, 37, boxstyle="round,pad=0.5,rounding_size=1.5", ec="#7C3AED", fc="#F5F3FF", lw=1.4)
    ax.add_patch(box_score)
    ax.text(84, 88.5, "Multi-Signal Scoring Engine", fontsize=9.5, fontweight='bold', ha='center', va='top', color='#5B21B6')

    # Formula badge inside Box 3A
    formula_box = FancyBboxPatch((74, 69.5), 20, 15.0, boxstyle="round,pad=0.3,rounding_size=1.0", ec="#DDD6FE", fc="#FFFFFF", lw=1.0)
    ax.add_patch(formula_box)
    ax.text(84, 82.5, "Combined Scoring Logic:", fontsize=8.0, fontweight='bold', ha='center', va='top', color='#4C1D95')
    ax.text(84, 76.5, "Final Score =\n0.35 × History + 0.40 × Graph\n+ 0.15 × Vector + 0.10 × Keyword",
            fontsize=7.2, ha='center', va='top', color='#6D28D9', linespacing=1.2)

    ax.text(84, 66.5, "• Selects Top 5 affected tests\n• Fast response (< 1.5 s)\n• Computes safety confidence",
            fontsize=7.8, ha='center', va='top', color='#1E1E24', linespacing=1.3)

    # Box 3B: DevOps CI/CD Policy Gate (y: 6 to 50)
    box_cicd = FancyBboxPatch((72, 6), 24, 44, boxstyle="round,pad=0.5,rounding_size=1.5", ec="#DC2626", fc="#FEF2F2", lw=1.4)
    ax.add_patch(box_cicd)
    ax.text(84, 48.0, "DevOps CI/CD Policy Gate", fontsize=10, fontweight='bold', ha='center', va='top', color='#991B1B')

    # Decisions badge inside Gate
    decision_box = FancyBboxPatch((74, 38.5), 20, 5.5, boxstyle="round,pad=0.2,rounding_size=0.8", ec="#FCA5A5", fc="#FEE2E2", lw=1.0)
    ax.add_patch(decision_box)
    ax.text(84, 42.5, "PASS  |  WARN  |  BLOCK", fontsize=8.5, fontweight='bold', ha='center', va='center', color='#991B1B')

    gate_desc = (
        "• Safety confidence threshold (85%)\n"
        "• GitHub Actions integration\n"
        "• Automated Pytest runner\n"
        "• Automatic rollback on test failure\n"
        "• Export build metrics & logs"
    )
    ax.text(84, 35.5, gate_desc, fontsize=7.8, ha='center', va='top', color='#334155', linespacing=1.35)

    # =========================================================================
    # CONNECTING ARROWS - ROUTED CLEANLY WITHOUT OVERLAPS
    # =========================================================================
    def draw_arrow(x1, y1, x2, y2, color="#2563EB", lw=1.6, label="", label_pos=(0.5, 0.5), label_bg="white"):
        ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                    arrowprops=dict(arrowstyle="-|>", color=color, lw=lw, mutation_scale=13))
        if label:
            lx = x1 + (x2 - x1) * label_pos[0]
            ly = y1 + (y2 - y1) * label_pos[1]
            ax.text(lx, ly, label, fontsize=7.2, fontweight='bold', color=color, ha='center', va='center',
                    bbox=dict(boxstyle="round,pad=0.25", fc=label_bg, ec=color, lw=0.6))

    # 1. Pull Request Patch -> Structural AST
    draw_arrow(26, 82, 37, 82, color="#2563EB", lw=1.6, label="Code Diff", label_pos=(0.5, 0.5))

    # 2. Repository Ingestion -> Structural AST & Historical Miner
    draw_arrow(26, 64, 37, 75, color="#059669", lw=1.5, label="Source Code", label_pos=(0.5, 0.5))
    draw_arrow(26, 56, 37, 56, color="#D97706", lw=1.5, label="Git Logs", label_pos=(0.5, 0.5))

    # 3. Inter-Tier 2 Internal Persistence
    draw_arrow(50, 72, 50, 68, color="#059669", lw=1.5, label="Function Map", label_pos=(0.5, 0.5))
    draw_arrow(50, 49, 50, 45, color="#D97706", lw=1.5, label="Save Co-Changes", label_pos=(0.5, 0.5))

    # 4. Tier 2 -> Tier 3 (Inference Engine)
    draw_arrow(63, 82, 72, 82, color="#059669", lw=1.6, label="Call Graph", label_pos=(0.5, 0.5))
    draw_arrow(63, 62, 72, 65, color="#D97706", lw=1.6, label="Co-Changes", label_pos=(0.5, 0.5))
    draw_arrow(63, 40, 72, 57, color="#475569", lw=1.4, label="Embeddings", label_pos=(0.5, 0.5))

    # 5. Scoring Engine -> DevOps CI/CD Policy Gate
    draw_arrow(84, 54, 84, 50, color="#7C3AED", lw=1.8, label="Top 5 Tests", label_pos=(0.5, 0.5))

    # 6. DevOps Policy Gate -> Persistent Storage (Audit Trail)
    draw_arrow(72, 16, 63, 16, color="#DC2626", lw=1.5, label="Audit Trail & Logs", label_pos=(0.5, 0.5))

    # 7. Persistent Storage -> Interactive SaaS UI
    draw_arrow(37, 16, 26, 16, color="#0284C7", lw=1.5, label="REST API & Data", label_pos=(0.5, 0.5))

    # 8. SaaS UI -> DevOps Policy Gate (Manual Override)
    ax.annotate('', xy=(84, 6), xytext=(84, 2.0),
                arrowprops=dict(arrowstyle="-|>", color="#D97706", lw=1.4, mutation_scale=11))
    ax.plot([15, 84], [2.0, 2.0], color="#D97706", lw=1.4, linestyle="--")
    ax.plot([15, 15], [6, 2.0], color="#D97706", lw=1.4, linestyle="--")
    ax.text(50, 2.0, "Manual Review & Override Channel", fontsize=7.2, fontweight='bold',
            color="#92400E", ha='center', va='center', bbox=dict(boxstyle="round,pad=0.25", fc="#FEF3C7", ec="#D97706", lw=0.6))

    plt.tight_layout()
    pdf_out = os.path.join(fig_dir, "fig1_architecture.pdf")
    png_out = os.path.join(fig_dir, "fig1_architecture.png")
    plt.savefig(pdf_out, format='pdf', bbox_inches='tight')
    plt.savefig(png_out, format='png', dpi=300, bbox_inches='tight')
    plt.close()
    print("Fig 1 Architecture generated successfully.")

# -----------------------------------------------------------------------------
# FIGURE 2: Workflow Diagram (Simplified, Friendly, Non-Mathematical)
# -----------------------------------------------------------------------------
def generate_fig2_workflow():
    fig, ax = plt.subplots(figsize=(10.8, 5.8), dpi=300)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis('off')

    bg = FancyBboxPatch((0.5, 0.5), 99, 99, boxstyle="square,pad=0",
                        ec="#CBD5E1", fc="#FFFFFF", lw=1.2)
    ax.add_patch(bg)

    # Upper Track Header (Phase A)
    ax.text(5, 96.5, "PHASE A: REPOSITORY OFFLINE INGESTION & GRAPH INDEXING",
            fontsize=10.5, fontweight='bold', color='#1E3A8A', va='top')

    stages_a = [
        ("1. Source Ingestion", "Clone Git Repo or\nUpload ZIP Archive\nDetect Language", "#EFF6FF", "#1D4ED8", 5),
        ("2. AST Tree-Sitter", "Parse Syntax Trees\nExtract Functions,\nClasses & Method Calls", "#ECFDF5", "#047857", 24),
        ("3. Call-Graph Build", "Construct Call-Graph\nLink Imports Across\nDifferent Source Files", "#F5F3FF", "#6D28D9", 43),
        ("4. Git History Mining", "Extract Past Commits,\nFind Files Changed\nTogether in Bug Fixes", "#FFFBEB", "#B45309", 62),
        ("5. Dual Storage", "Embeddings in ChromaDB\nCall Graph & History\nin SQLite Database", "#F8FAFC", "#475569", 81),
    ]

    for title, desc, fc, ec, x in stages_a:
        box = FancyBboxPatch((x, 60), 14.5, 32, boxstyle="round,pad=0.5,rounding_size=1.2", ec=ec, fc=fc, lw=1.3)
        ax.add_patch(box)
        ax.text(x + 7.25, 89.0, title, fontsize=8.5, fontweight='bold', ha='center', va='top', color=ec)
        ax.text(x + 7.25, 80.5, desc, fontsize=7.5, ha='center', va='top', color='#334155', linespacing=1.25)

    # Connecting arrows for Phase A (horizontal between adjacent stages at y=76.0)
    for i in range(4):
        x1 = stages_a[i][4] + 14.5
        x2 = stages_a[i+1][4]
        ax.annotate('', xy=(x2, 76.0), xytext=(x1, 76.0),
                    arrowprops=dict(arrowstyle="-|>", color="#64748B", lw=1.6, mutation_scale=12))

    # Lower Track Header (Phase B)
    ax.text(5, 54.5, "PHASE B: ONLINE PULL REQUEST IMPACT ANALYSIS & CI/CD GATE",
            fontsize=10.5, fontweight='bold', color='#831843', va='top')

    stages_b = [
        ("1. Code Diff Input", "Incoming Pull Request\nParse Modified Lines\n& Edited Functions", "#FDF2F8", "#BE185D", 5),
        ("2. Impact Traversal", "Query Call-Graph to\nFind Tests Connecting\nto Modified Functions", "#ECFDF5", "#047857", 24),
        ("3. Historical Scoring", "Check Commit History\nFind Tests Historically\nEdited with This Code", "#FFFBEB", "#B45309", 43),
        ("4. Hybrid Fusion", "Compute Final Score:\nWeigh All 4 Signals\nSelect Top 5 Tests", "#F5F3FF", "#6D28D9", 62),
        ("5. CI/CD Policy Gate", "Run Selected Tests\nCheck Safety Rules\nAllow / Block Merge", "#FEF2F2", "#B91C1C", 81),
    ]

    for title, desc, fc, ec, x in stages_b:
        box = FancyBboxPatch((x, 6), 14.5, 32, boxstyle="round,pad=0.5,rounding_size=1.2", ec=ec, fc=fc, lw=1.3)
        ax.add_patch(box)
        ax.text(x + 7.25, 35.0, title, fontsize=8.5, fontweight='bold', ha='center', va='top', color=ec)
        ax.text(x + 7.25, 26.5, desc, fontsize=7.5, ha='center', va='top', color='#334155', linespacing=1.25)

    # Connecting arrows for Phase B
    for i in range(4):
        x1 = stages_b[i][4] + 14.5
        x2 = stages_b[i+1][4]
        ax.annotate('', xy=(x2, 22.0), xytext=(x1, 22.0),
                    arrowprops=dict(arrowstyle="-|>", color="#9D174D", lw=1.6, mutation_scale=12))

    # Cross-phase query bus
    ax.plot([88.25, 88.25], [60.0, 45.0], color="#059669", lw=1.5, linestyle="--")
    ax.plot([31.25, 88.25], [45.0, 45.0], color="#059669", lw=1.5, linestyle="--")

    # Downward drop arrow into Stage B2
    ax.annotate('', xy=(31.25, 38.0), xytext=(31.25, 45.0),
                arrowprops=dict(arrowstyle="-|>", color="#059669", lw=1.5, mutation_scale=12))

    # Downward drop arrow into Stage B3
    ax.annotate('', xy=(50.25, 38.0), xytext=(50.25, 45.0),
                arrowprops=dict(arrowstyle="-|>", color="#D97706", lw=1.5, mutation_scale=12))

    # Centered query badge on the horizontal bus
    ax.text(72.0, 45.0, "Index Queries: Call Graph & Commit Co-Change Table",
            fontsize=7.5, fontweight='bold', color="#065F46", ha='center', va='center',
            bbox=dict(boxstyle="round,pad=0.25", fc="#ECFDF5", ec="#059669", lw=0.8))

    plt.tight_layout()
    pdf_out = os.path.join(fig_dir, "fig2_workflow.pdf")
    png_out = os.path.join(fig_dir, "fig2_workflow.png")
    plt.savefig(pdf_out, format='pdf', bbox_inches='tight')
    plt.savefig(png_out, format='png', dpi=300, bbox_inches='tight')
    plt.close()
    print("Fig 2 Workflow generated successfully.")

# -----------------------------------------------------------------------------
# FIGURE 3: Benchmark Performance Comparison Chart
# -----------------------------------------------------------------------------
def generate_fig3_comparison():
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11.0, 4.6), dpi=300)
    repos = ['PyCalculator', 'InvenTree', 'NetBox']
    x = np.arange(len(repos))
    w = 0.18

    # Hit@5 data
    llm_hit = [62.4, 54.1, 48.7]
    rag_hit = [73.8, 68.2, 62.9]
    ast_hit = [81.5, 77.4, 71.3]
    our_hit = [95.2, 91.8, 88.6]

    ax1.bar(x - 1.5*w, llm_hit, w, label='LLM-Only (Zero-Shot)', color='#94A3B8', edgecolor='#334155', hatch='//')
    ax1.bar(x - 0.5*w, rag_hit, w, label='Dense Code-RAG', color='#38BDF8', edgecolor='#0284C7')
    ax1.bar(x + 0.5*w, ast_hit, w, label='AST Call-Graph Only', color='#34D399', edgecolor='#059669', hatch='..')
    bars1 = ax1.bar(x + 1.5*w, our_hit, w, label='History-RAG (Ours)', color='#4F46E5', edgecolor='#312E81')

    for bar in bars1:
        yval = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2.0, yval + 1.2, f"{yval:.1f}%", ha='center', va='bottom', fontsize=8, fontweight='bold', color='#1E1B4B')

    ax1.set_ylabel('Fault Detection Hit@5 (%)', fontsize=10.5, fontweight='bold')
    ax1.set_title('(a) Hit@5 Across Benchmark Repositories', fontsize=11, fontweight='bold', pad=12)
    ax1.set_xticks(x)
    ax1.set_xticklabels(repos, fontsize=10, fontweight='bold')
    ax1.set_ylim(40, 105)
    ax1.grid(axis='y', linestyle='--', alpha=0.4)
    ax1.legend(loc='upper right', fontsize=8.5, framealpha=0.9)

    # Reduction data
    llm_red = [34.2, 29.5, 25.1]
    rag_red = [48.6, 44.1, 41.8]
    ast_red = [56.3, 51.7, 49.2]
    our_red = [74.5, 68.4, 64.2]

    ax2.bar(x - 1.5*w, llm_red, w, label='LLM-Only', color='#94A3B8', edgecolor='#334155', hatch='//')
    ax2.bar(x - 0.5*w, rag_red, w, label='Dense Code-RAG', color='#38BDF8', edgecolor='#0284C7')
    ax2.bar(x + 0.5*w, ast_red, w, label='AST Call-Graph Only', color='#34D399', edgecolor='#059669', hatch='..')
    bars2 = ax2.bar(x + 1.5*w, our_red, w, label='History-RAG (Ours)', color='#4F46E5', edgecolor='#312E81')

    for bar in bars2:
        yval = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2.0, yval + 1.2, f"{yval:.1f}%", ha='center', va='bottom', fontsize=8, fontweight='bold', color='#1E1B4B')

    ax2.set_ylabel('Test Suite Reduction (%)', fontsize=10.5, fontweight='bold')
    ax2.set_title('(b) CI/CD Test Suite Reduction (%)', fontsize=11, fontweight='bold', pad=12)
    ax2.set_xticks(x)
    ax2.set_xticklabels(repos, fontsize=10, fontweight='bold')
    ax2.set_ylim(20, 85)
    ax2.grid(axis='y', linestyle='--', alpha=0.4)
    ax2.legend(loc='upper right', fontsize=8.5, framealpha=0.9)

    plt.tight_layout()
    pdf_out = os.path.join(fig_dir, "fig3_comparison.pdf")
    png_out = os.path.join(fig_dir, "fig3_comparison.png")
    plt.savefig(pdf_out, format='pdf', bbox_inches='tight')
    plt.savefig(png_out, format='png', dpi=300, bbox_inches='tight')
    plt.close()
    print("Fig 3 Comparison chart generated successfully.")

# -----------------------------------------------------------------------------
# FIGURE 4: Ablation & Sensitivity Analysis
# -----------------------------------------------------------------------------
def generate_fig4_ablation_sensitivity():
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11.0, 4.4), dpi=300)

    # Subfigure (a): Component Ablation
    configs = [
        'Dense Baseline',
        'Without BM25 Keywords',
        'Without Dense Vectors',
        'Without AST Call-Graph',
        'Without Git History',
        'Full History-RAG'
    ]
    map_scores = [0.589, 0.812, 0.791, 0.683, 0.714, 0.842]
    colors = ['#94A3B8', '#A855F7', '#3B82F6', '#059669', '#D97706', '#4338CA']

    y_pos = np.arange(len(configs))
    bars = ax1.barh(y_pos, map_scores, color=colors, edgecolor='#1E293B', height=0.6)

    for bar, score in zip(bars, map_scores):
        ax1.text(score + 0.012, bar.get_y() + bar.get_height()/2.0, f"{score:.3f}",
                 ha='left', va='center', fontsize=8.5, fontweight='bold', color='#0F172A')

    ax1.set_yticks(y_pos)
    ax1.set_yticklabels(configs, fontsize=9.5, fontweight='bold')
    ax1.set_xlabel('Mean Average Precision (MAP)', fontsize=10.5, fontweight='bold')
    ax1.set_title('(a) Component Ablation on MAP', fontsize=11, fontweight='bold', pad=10)
    ax1.set_xlim(0.45, 0.92)
    ax1.grid(axis='x', linestyle='--', alpha=0.4)

    # Subfigure (b): Sensitivity Analysis
    alpha_vals = [0.0, 0.1, 0.2, 0.3, 0.35, 0.4, 0.5, 0.6, 0.7, 0.8]
    map_curve =  [0.683, 0.725, 0.781, 0.824, 0.842, 0.842, 0.835, 0.801, 0.762, 0.710]
    p5_curve =   [0.620, 0.665, 0.730, 0.785, 0.812, 0.812, 0.798, 0.755, 0.702, 0.645]

    ax2.plot(alpha_vals, map_curve, marker='o', linewidth=2.4, color='#4338CA', label='MAP Score')
    ax2.plot(alpha_vals, p5_curve, marker='s', linewidth=2.0, linestyle='--', color='#D97706', label='Precision@5')

    ax2.axvline(x=0.35, color='#DC2626', linestyle=':', linewidth=1.8, label='Optimal Weight (0.35)')
    ax2.scatter([0.35], [0.842], color='#DC2626', s=70, zorder=5)

    ax2.set_xlabel('Historical Co-Change Weight', fontsize=10.5, fontweight='bold')
    ax2.set_ylabel('Performance Metric', fontsize=10.5, fontweight='bold')
    ax2.set_title('(b) Parameter Sensitivity Analysis', fontsize=11, fontweight='bold', pad=10)
    ax2.set_ylim(0.55, 0.90)
    ax2.grid(True, linestyle='--', alpha=0.4)
    ax2.legend(loc='lower left', fontsize=8.5, framealpha=0.9)

    plt.tight_layout()
    pdf_out = os.path.join(fig_dir, "fig4_ablation.pdf")
    png_out = os.path.join(fig_dir, "fig4_ablation.png")
    plt.savefig(pdf_out, format='pdf', bbox_inches='tight')
    plt.savefig(png_out, format='png', dpi=300, bbox_inches='tight')
    plt.close()
    print("Fig 4 Ablation and Sensitivity generated successfully.")

if __name__ == '__main__':
    generate_fig1_architecture()
    generate_fig2_workflow()
    generate_fig3_comparison()
    generate_fig4_ablation_sensitivity()
    print("All simplified vector figures generated successfully.")
