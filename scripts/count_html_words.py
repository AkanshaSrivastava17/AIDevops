from bs4 import BeautifulSoup
import re

def analyze_html():
    with open('paper/History_RAG_Research_Paper.html', 'r', encoding='utf-8') as f:
        html = f.read()

    soup = BeautifulSoup(html, 'html.parser')
    
    # Title
    title = soup.find('h1', class_='paper-title').get_text().strip()
    title_words = len(title.split())
    print(f"Title: {title_words} words: {title}")

    # Abstract
    abstract_div = soup.find('div', class_='abstract-container')
    abstract_text = abstract_div.get_text().replace('Abstract—', '').replace('Abstract-', '').strip()
    abstract_words = len(re.findall(r'\b\w+\b', abstract_text))
    print(f"Abstract: {abstract_words} words (Target: 200-250)")

    # Terms
    terms_div = soup.find('div', class_='index-terms')
    terms_text = terms_div.get_text().replace('Index Terms—', '').replace('Index Terms-', '').strip()
    terms = [t.strip() for t in terms_text.split(',') if t.strip()]
    print(f"Index Terms: {len(terms)} terms (Target: 4-6): {terms}")

    # Sections
    h2_tags = soup.find_all('h2', class_='section-heading')
    print("\n--- HTML SECTION WORD COUNTS ---")
    total_words = 0
    for h2 in h2_tags:
        sec_title = h2.get_text().strip()
        if "REFERENCES" in sec_title or "AI-USE" in sec_title:
            continue
        
        # Collect text until next h2
        sec_text = ""
        curr = h2.next_sibling
        while curr and getattr(curr, 'name', None) != 'h2':
            if getattr(curr, 'get_text', None):
                # Exclude tables and caption text from main prose count or check both
                sec_text += " " + curr.get_text()
            curr = curr.next_sibling
        
        words = len(re.findall(r'\b[a-zA-Z0-9_\-]+\b', sec_text))
        print(f"{sec_title}: {words} words")
        total_words += words

    print(f"\nTOTAL MAIN PROSE WORDS IN HTML: {total_words} (Target: 4,500 - 5,500)")

if __name__ == '__main__':
    analyze_html()
