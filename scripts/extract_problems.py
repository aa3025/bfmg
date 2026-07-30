import os
import re
import json
import glob
import pypdf
from pathlib import Path

bfmg_dir = Path(__file__).parent.parent.resolve()
papers_dir = bfmg_dir / 'media' / 'past_papers'
data_dir = bfmg_dir / 'data'
data_dir.mkdir(parents=True, exist_ok=True)

problems_file = data_dir / 'problems.json'

# Category mapping based on problem number ranges
def get_categories(p_num):
    cats = []
    # CE: 1-5
    if 1 <= p_num <= 5:
        cats.append("CE")
    # CM: 1-8
    if 1 <= p_num <= 8:
        cats.append("CM")
    # C1: 1-11
    if 1 <= p_num <= 11:
        cats.append("C1")
    # C2: 1-14
    if 1 <= p_num <= 14:
        cats.append("C2")
    # L1, GP: 1-16
    if 1 <= p_num <= 16:
        cats.append("L1")
        cats.append("GP")
    # L2, HC: 1-18
    if 1 <= p_num <= 18:
        cats.append("L2")
        cats.append("HC")
    return cats

def get_complexity_label(p_num):
    if p_num <= 5:
        return "Primary (Year 5)"
    elif p_num <= 8:
        return "Middle School (Year 6-7)"
    elif p_num <= 11:
        return "Lower Sec (Year 8-9)"
    elif p_num <= 14:
        return "Upper Sec (Year 10-11)"
    elif p_num <= 16:
        return "Adults / General Public"
    else:
        return "Top Competition / L2"

def parse_pdf_problems(pdf_path):
    filename = os.path.basename(pdf_path)
    # File format example: 40_30_CH_en_questions.pdf
    m = re.match(r'(\d+)_(\d+)_([A-Za-z0-9_]+)_(questions|answers)\.pdf', filename)
    if not m:
        return []
    
    edition = int(m.group(1))
    stage_code = int(m.group(2))
    doc_type = m.group(4) # questions or answers
    
    # Year calculation: 40 = 2025-2026, 39 = 2024-2025, etc.
    year_start = 1986 + edition
    year_str = f"{year_start}-{year_start+1} ({edition}th Edition)"
    
    stage_names = {
        20: "Semi-Final",
        30: "UK National Final",
        41: "International Final (Day 1)",
        42: "International Final (Day 2)"
    }
    stage_name = stage_names.get(stage_code, f"Stage {stage_code}")
    
    reader = pypdf.PdfReader(pdf_path)
    full_text = "\n".join([page.extract_text() or "" for page in reader.pages])
    
    if doc_type != "questions":
        return []

    # Clean text
    text = re.sub(r'FFJM\s*–.*?\n', '', full_text)
    text = re.sub(r'Information and results at http://www.fsjm.ch/.*?\n', '', text)
    text = re.sub(r'START for ALL PARTICIPANTS.*?\n', '', text)
    text = re.sub(r'END for CE PARTICIPANTS.*?\n', '', text)
    text = re.sub(r'END for CM PARTICIPANTS.*?\n', '', text)

    # Match problems: e.g. "1. Stickers (coefficient 1)" or "1 - Stickers (coefficient 1)"
    # Pattern to find problem headers: \n(\d+)\.\s*([^\n\(]+?)(?:\s*\((?:coefficient|coeff\.)\s*(\d+)\))?
    problem_splits = re.split(r'\n(?=\d+\.\s+[A-Z])', text)
    
    extracted = []
    for chunk in problem_splits:
        chunk = chunk.strip()
        header_match = re.match(r'^(\d+)\.\s*([^\n\(]+?)(?:\s*\((?:coefficient|coeff\.|coef\.)\s*(\d+)\))?\n(.*)$', chunk, re.DOTALL)
        if header_match:
            p_num = int(header_match.group(1))
            title = header_match.group(2).strip()
            coeff = int(header_match.group(3)) if header_match.group(3) else p_num
            statement = header_match.group(4).strip()
            
            # Clean statement trailing headers/footers
            statement = re.sub(r'FOR PARTICIPANTS.*', '', statement, flags=re.DOTALL).strip()
            
            pid = f"{edition}_{stage_code}_p{p_num}"
            cats = get_categories(p_num)
            comp_label = get_complexity_label(p_num)
            
            extracted.append({
                "id": pid,
                "edition": edition,
                "year": year_str,
                "stage": stage_name,
                "stage_code": stage_code,
                "number": p_num,
                "title": title,
                "coefficient": coeff,
                "categories": cats,
                "complexity_label": comp_label,
                "statement": statement,
                "solution": {
                    "answer": f"Solution and answer for Problem {p_num} ({title})",
                    "steps": [
                        f"Analyze the initial conditions given in Problem {p_num}.",
                        f"Apply logic and category constraints for {comp_label}.",
                        f"Calculate final result for {title}."
                    ]
                }
            })
            
    return extracted

def main():
    pdf_files = sorted(glob.glob(str(papers_dir / "*_questions.pdf")))
    all_problems = []
    seen_ids = set()
    
    for pdf in pdf_files:
        probs = parse_pdf_problems(pdf)
        for p in probs:
            if p["id"] not in seen_ids:
                seen_ids.add(p["id"])
                all_problems.append(p)
                
    all_problems.sort(key=lambda x: (x["edition"], x["stage_code"], x["number"]), reverse=True)
    
    with open(problems_file, 'w', encoding='utf-8') as f:
        json.dump(all_problems, f, indent=2, ensure_ascii=False)
        
    print(f"Successfully extracted {len(all_problems)} problems into {problems_file}")

if __name__ == "__main__":
    main()
