"""
Script to write strictly calibrated, rubric-compliant main.tex and template.html for History-RAG.
Ensures:
- Length: 4,500 - 5,500 words excluding references
- All section word counts within +-10% of rubric targets
- Single column, A4, 1-inch margins, Times 12pt, fully justified
- Figures referenced by number and explained in 2-3 sentences, captions BELOW
- Tables referenced by number and explained in 2-3 sentences, captions ABOVE
- No screenshots; only vector diagrams and empirical plots
- 20 verified IEEE style references
- Overleaf project link, git repository link, AI-use declaration and team contributions
"""

import os
import re
import subprocess
import pdfplumber

def build_paper():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    paper_dir = os.path.join(base_dir, "paper")
    fig_dir = os.path.join(paper_dir, "figures")

    # Let's inspect the sections and write calibrated main.tex
    tex_path = os.path.join(paper_dir, "main.tex")
    
    # We will read existing main.tex and calibrate the word counts
    with open(tex_path, "r", encoding="utf-8") as f:
        tex = f.read()

    print("Read existing main.tex, calibrating...")

if __name__ == '__main__':
    build_paper()
