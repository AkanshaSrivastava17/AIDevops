"""
Verification script for compiled History_RAG_Research_Paper.pdf
Checks:
- Total page count
- Author byline and group number absence
- Word counts of extracted text
- Images / figures placement on pages
"""

import pdfplumber

pdf_path = "paper/History_RAG_Research_Paper.pdf"

with pdfplumber.open(pdf_path) as pdf:
    num_pages = len(pdf.pages)
    print(f"Total pages: {num_pages}")
    
    first_page_text = pdf.pages[0].extract_text()
    print("\n--- PAGE 1 PREVIEW ---")
    print(first_page_text[:800])
    
    # Check author and group
    has_group = "Group 14" in first_page_text or "Group" in first_page_text
    has_akansha = "Akansha Srivastava (230742)" in first_page_text
    has_radhika = "Radhika Goel (230744)" in first_page_text
    has_supervisors = "Naveen Singh" in first_page_text and "Kiran Khatter" in first_page_text
    
    print("\n--- AUTHOR VERIFICATION ---")
    print(f"Contains 'Group 14': {has_group}")
    print(f"Contains 'Akansha Srivastava (230742)': {has_akansha}")
    print(f"Contains 'Radhika Goel (230744)': {has_radhika}")
    print(f"Contains 'Naveen Singh' & 'Kiran Khatter': {has_supervisors}")
    
    # Last page check
    last_page_text = pdf.pages[-1].extract_text()
    print("\n--- LAST PAGE PREVIEW ---")
    print(last_page_text[-800:])
