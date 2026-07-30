import os
import re
import json
import glob
import io
import pypdf
from PIL import Image
from pathlib import Path

bfmg_dir = Path(__file__).parent.parent.resolve()
papers_dir = bfmg_dir / 'media' / 'past_papers'
diagrams_dir = bfmg_dir / 'media' / 'problem_diagrams'
data_dir = bfmg_dir / 'data'

diagrams_dir.mkdir(parents=True, exist_ok=True)
data_dir.mkdir(parents=True, exist_ok=True)

problems_file = data_dir / 'problems.json'

def get_categories(p_num):
    cats = []
    if 1 <= p_num <= 5: cats.append("CE")
    if 1 <= p_num <= 8: cats.append("CM")
    if 1 <= p_num <= 11: cats.append("C1")
    if 1 <= p_num <= 14: cats.append("C2")
    if 1 <= p_num <= 16: cats.append("L1"); cats.append("GP")
    if 1 <= p_num <= 18: cats.append("L2"); cats.append("HC")
    return cats

def get_complexity_label(p_num):
    if p_num <= 5: return "Primary (Year 5)"
    elif p_num <= 8: return "Middle School (Year 6-7)"
    elif p_num <= 11: return "Lower Sec (Year 8-9)"
    elif p_num <= 14: return "Upper Sec (Year 10-11)"
    elif p_num <= 16: return "Adults / General Public"
    else: return "Top Competition / L2"

def parse_pdf_problems(pdf_path):
    filename = os.path.basename(pdf_path)
    m = re.match(r'(\d+)_(\d+)_([A-Za-z0-9_]+)_(questions|answers)\.pdf', filename)
    if not m or m.group(4) != "questions":
        return []
    
    edition = int(m.group(1))
    stage_code = int(m.group(2))
    
    # 40th Edition = 2025-2026, 39th Edition = 2024-2025, 38th Edition = 2023-2024
    year_start = 1985 + edition
    year_str = f"{year_start}-{year_start+1} ({edition}th Edition)"
    
    stage_names = {
        20: "Semi-Final",
        30: "UK National Final",
        41: "International Final (Day 1)",
        42: "International Final (Day 2)"
    }
    stage_name = stage_names.get(stage_code, f"Stage {stage_code}")
    
    reader = pypdf.PdfReader(pdf_path)
    
    # 1. Extract valid diagram images (>80x80px, non-banner) per page
    page_diagrams = {}
    for page_idx, page in enumerate(reader.pages):
        imgs = []
        try:
            for img_idx, img_obj in enumerate(page.images):
                try:
                    im = Image.open(io.BytesIO(img_obj.data))
                    w, h = im.size
                    # Filter out logos, header banners, or tiny icons
                    if w >= 80 and h >= 80 and (w / h < 4.0) and (h / w < 4.0):
                        img_name = f"{edition}_{stage_code}_pg{page_idx+1}_{img_idx+1}_{img_obj.name}"
                        if not img_name.endswith(('.png', '.jpg', '.jpeg', '.webp')):
                            img_name += '.png'
                        img_path = diagrams_dir / img_name
                        with open(img_path, 'wb') as f:
                            f.write(img_obj.data)
                        imgs.append(f"/media/problem_diagrams/{img_name}")
                except Exception:
                    pass
        except Exception:
            pass
        page_diagrams[page_idx + 1] = imgs

    # 2. Sequential line-by-line problem parsing
    full_text = "\n".join([page.extract_text() or "" for page in reader.pages])
    
    # Normalize problem header newlines
    full_text = re.sub(r'START for ALL PARTICIPANTS\s*', '\n', full_text, flags=re.I)
    full_text = re.sub(r'(\s+)(\d{1,2})\.\s+([A-Z])', r'\n\2. \3', full_text)

    lines = full_text.split('\n')
    problems = []
    current_prob = None
    expected_num = 1

    for line in lines:
        line_str = line.strip()
        if not line_str:
            continue
            
        m_prob = re.match(r'^(' + str(expected_num) + r')\.\s+(.+)$', line_str)
        if m_prob:
            if current_prob:
                problems.append(current_prob)
            rest_text = m_prob.group(2).strip()
            
            coeff_match = re.search(r'\((?:coefficient|coeff\.|coef\.)\s*(\d+)\)', rest_text, re.I)
            coeff = int(coeff_match.group(1)) if coeff_match else expected_num
            
            title = rest_text
            extra_statement = ""
            if coeff_match:
                title = rest_text[:coeff_match.start()].strip()
                extra_statement = rest_text[coeff_match.end():].strip()
            elif "  " in rest_text:
                parts = rest_text.split("  ", 1)
                title = parts[0].strip()
                extra_statement = parts[1].strip()
                
            current_prob = {
                'number': expected_num,
                'title': title,
                'coefficient': coeff,
                'lines': [extra_statement] if extra_statement else []
            }
            expected_num += 1
        elif current_prob:
            # Skip header / footer / category divider lines
            if re.search(r'\b(?:END|START)\s+for\b', line_str, re.I):
                continue
            if re.search(r'FFJM\s*–|Information and results at|http://|Problems \d+ to \d+:|The Swiss Federation of Mathematical Games', line_str, re.I):
                continue
            current_prob['lines'].append(line_str)

    if current_prob:
        problems.append(current_prob)

    # 3. Format statement text & attach relevant diagrams
    extracted = []
    diagram_keywords = ['figure', 'disc', 'token', 'square', 'grid', 'triangle', 'example', 'shown', 'diagram', 'illustration', 'pattern', 'drawing', 'card', 'logo', 'shield', 'as in', 'map', 'cactus', 'tetramino', 'horseshoe']

    for p in problems:
        p_num = p['number']
        statement_text = " ".join(p['lines'])
        
        # Clean instruction lines from body text
        statement_text = re.sub(r'\b(?:END|START)\s+for\s+[A-Za-z0-9,\s]+PARTICIPANTS\b.*', '', statement_text, flags=re.I)
        statement_text = re.sub(r'The Swiss Federation of Mathematical Games.*', '', statement_text, flags=re.I)
        statement_text = re.sub(r'(\w+)-\s+(\w+)', r'\1\2', statement_text)
        statement_text = re.sub(r'\s+', ' ', statement_text).strip()
        
        # Determine page estimate (1-5 -> p1, 6-10 -> p2, 11-14 -> p3, 15-18 -> p4)
        p_page = 1 if p_num <= 5 else (2 if p_num <= 10 else (3 if p_num <= 14 else 4))
        
        # Only attach diagram if problem text explicitly mentions a visual reference
        diagram_list = []
        has_visual_ref = any(kw in statement_text.lower() for kw in diagram_keywords) or any(kw in p['title'].lower() for kw in diagram_keywords)
        if has_visual_ref and p_page in page_diagrams and len(page_diagrams[p_page]) > 0:
            diagram_list = [page_diagrams[p_page][0]]
            
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
            "title": p["title"],
            "coefficient": p["coefficient"],
            "categories": cats,
            "complexity_label": comp_label,
            "statement": statement_text,
            "diagrams": diagram_list,
            "solution": {
                "answer": f"Solution for Problem {p_num} ({p['title']})",
                "steps": [
                    f"Read and analyze the given conditions for {p['title']}.",
                    f"Apply logical deduction for category {comp_label}.",
                    f"Calculate and verify final result."
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
        
    print(f"Successfully extracted {len(all_problems)} problems with exact title & statement separation into {problems_file}")

if __name__ == "__main__":
    main()
