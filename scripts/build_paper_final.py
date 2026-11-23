"""
Final Comprehensive Paper Generator for History-RAG
Produces:
1. paper/main.tex (LaTeX document for Overleaf)
2. paper/template.html (High-fidelity HTML formatted with Times 12pt, A4, 1-inch margins, justified text)
3. paper/History_RAG_Research_Paper.pdf (Compiled via headless Chrome)
4. paper/History_RAG_Overleaf_Package.zip (Ready-to-upload zip containing main.tex, references.bib, and figures)
"""

import os
import re
import base64
import subprocess
import zipfile

def get_base64_image(image_path):
    with open(image_path, "rb") as img_file:
        return "data:image/png;base64," + base64.b64encode(img_file.read()).decode('utf-8')

def build_all():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    paper_dir = os.path.join(base_dir, "paper")
    fig_dir = os.path.join(paper_dir, "figures")

    tex_path = os.path.join(paper_dir, "main.tex")
    html_template_path = os.path.join(paper_dir, "template.html")
    compiled_html_path = os.path.join(paper_dir, "History_RAG_Research_Paper.html")
    compiled_pdf_path = os.path.join(paper_dir, "History_RAG_Research_Paper.pdf")
    zip_path = os.path.join(paper_dir, "History_RAG_Overleaf_Package.zip")

    # Read base64 figures
    fig1_b64 = get_base64_image(os.path.join(fig_dir, "fig1_architecture.png"))
    fig2_b64 = get_base64_image(os.path.join(fig_dir, "fig2_workflow.png"))
    fig3_b64 = get_base64_image(os.path.join(fig_dir, "fig3_comparison.png"))
    fig4_b64 = get_base64_image(os.path.join(fig_dir, "fig4_ablation.png"))

    # Compile HTML
    with open(html_template_path, "r", encoding="utf-8") as f:
        html = f.read()

    html = html.replace("__FIG1_B64__", fig1_b64)
    html = html.replace("__FIG2_B64__", fig2_b64)
    html = html.replace("__FIG3_B64__", fig3_b64)
    html = html.replace("__FIG4_B64__", fig4_b64)

    with open(compiled_html_path, "w", encoding="utf-8") as f:
        f.write(html)
    print("1. Compiled HTML document at:", compiled_html_path)

    # Compile PDF via Chrome
    chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    cmd = [
        chrome_path,
        "--headless",
        "--no-sandbox",
        "--disable-gpu",
        "--disable-software-rasterizer",
        "--no-pdf-header-footer",
        f"--print-to-pdf={compiled_pdf_path}",
        compiled_html_path
    ]
    print("2. Compiling PDF via headless Chrome...")
    res = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    if res.returncode == 0 and os.path.exists(compiled_pdf_path):
        print(f"SUCCESS: PDF compiled at: {compiled_pdf_path}")
        print(f"File size: {os.path.getsize(compiled_pdf_path):,} bytes")
    else:
        print(f"Compilation error (return code {res.returncode}):", res.stderr)

    # Package Overleaf zip
    print("3. Packaging Overleaf zip bundle...")
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        zipf.write(tex_path, arcname="main.tex")
        zipf.write(os.path.join(paper_dir, "references.bib"), arcname="references.bib")
        for fig in ["fig1_architecture.pdf", "fig1_architecture.png",
                    "fig2_workflow.pdf", "fig2_workflow.png",
                    "fig3_comparison.pdf", "fig3_comparison.png",
                    "fig4_ablation.pdf", "fig4_ablation.png"]:
            fig_path = os.path.join(fig_dir, fig)
            if os.path.exists(fig_path):
                zipf.write(fig_path, arcname=f"figures/{fig}")
    print(f"SUCCESS: Overleaf package created at: {zip_path}")
    print(f"File size: {os.path.getsize(zip_path):,} bytes")

if __name__ == '__main__':
    build_all()
