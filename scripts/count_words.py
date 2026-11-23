import re

def analyze_paper():
    with open('paper/main.tex', 'r', encoding='utf-8') as f:
        content = f.read()

    # Extract abstract
    abstract_match = re.search(r'\\begin\{abstract\}(.*?)\\end\{abstract\}', content, re.DOTALL)
    abstract_text = abstract_match.group(1).strip() if abstract_match else ""
    abstract_words = len(re.findall(r'\b\w+\b', abstract_text))
    print(f"Abstract: {abstract_words} words (Target: 200-250)")

    # Extract Index Terms
    terms_match = re.search(r'\\begin\{IEEEkeywords\}(.*?)\\end\{IEEEkeywords\}', content, re.DOTALL)
    terms_text = terms_match.group(1).strip() if terms_match else ""
    terms_list = [t.strip() for t in terms_text.split(',') if t.strip()]
    print(f"Index Terms: {len(terms_list)} terms (Target: 4-6): {terms_list}")

    # Split into sections
    section_pattern = r'(\\section\*?\{[^}]+\})'
    parts = re.split(section_pattern, content)
    
    sections = {}
    current_sec = "Preamble"
    for part in parts:
        if part.startswith('\\section'):
            sec_name = re.search(r'\\section\*?\{([^}]+)\}', part).group(1)
            current_sec = sec_name
            sections[current_sec] = ""
        else:
            if current_sec in sections:
                sections[current_sec] += part
            else:
                sections[current_sec] = part

    targets = {
        "Introduction": (600, 800),
        "Related Work": (700, 900),
        "Background and Problem Formulation": (300, 500),
        "Proposed Methodology": (900, 1200),
        "Experimental Setup": (400, 600),
        "Results and Analysis": (800, 1000),
        "Discussion": (300, 500),
        "Conclusion and Future Work": (200, 300),
    }

    total_main_words = 0
    print("\n--- SECTION WORD COUNTS ---")
    for name, text in sections.items():
        if name in ["Preamble", "AI-Use Declaration and Team Member Contributions"]:
            continue
        # Clean latex commands
        clean = re.sub(r'\\[a-zA-Z]+(\[[^\]]*\])?(\{[^}]*\})?', ' ', text)
        clean = re.sub(r'[\$\{\}\\_]', ' ', clean)
        words = len(re.findall(r'\b[a-zA-Z0-9_\-]+\b', clean))
        target_str = f"(Target: {targets[name][0]}-{targets[name][1]})" if name in targets else ""
        print(f"{name}: {words} words {target_str}")
        total_main_words += words

    print(f"\nTOTAL MAIN TEXT WORDS: {total_main_words} (Target: 4,500 - 5,500)")

if __name__ == '__main__':
    analyze_paper()
