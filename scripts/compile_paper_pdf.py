"""
Academic Research Paper PDF Compiler for History-RAG
Compiles the complete single-column A4 12pt IEEE-styled paper into a publication-grade PDF.
"""

import os
import re
import base64
import subprocess

def get_base64_image(image_path):
    with open(image_path, "rb") as img_file:
        return "data:image/png;base64," + base64.b64encode(img_file.read()).decode('utf-8')

def compile_pdf():
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

    with open(template_path, "r", encoding="utf-8") as f:
        html = f.read()

    html = html.replace("__FIG1_B64__", fig1_b64)
    html = html.replace("__FIG2_B64__", fig2_b64)
    html = html.replace("__FIG3_B64__", fig3_b64)
    html = html.replace("__FIG4_B64__", fig4_b64)

    with open(output_html, "w", encoding="utf-8") as f:
        f.write(html)
    print("HTML document generated at:", output_html)

    chrome_candidates = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"
    ]
    
    chrome_path = None
    for p in chrome_candidates:
        if os.path.exists(p):
            chrome_path = p
            break

    if not chrome_path:
        raise FileNotFoundError("Could not find Chrome or Edge executable.")

    print(f"Using browser at: {chrome_path}")
    cmd = [
        chrome_path,
        "--headless",
        "--no-sandbox",
        "--disable-gpu",
        "--disable-software-rasterizer",
        f"--print-to-pdf={output_pdf}",
        output_html
    ]

    print("Running browser print-to-pdf...")
    res = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    if res.returncode == 0 and os.path.exists(output_pdf):
        print(f"SUCCESS: PDF compiled at: {output_pdf}")
        print(f"File size: {os.path.getsize(output_pdf):,} bytes")
    else:
        print(f"Compilation error (return code {res.returncode}):")
        print(res.stderr)

if __name__ == '__main__':
    compile_pdf()
