import os
import re
import json
import glob
import fitz # PyMuPDF
from PIL import Image
from pathlib import Path

bfmg_dir = Path(__file__).parent.parent.resolve()
papers_dir = bfmg_dir / 'media' / 'past_papers'
crops_dir = bfmg_dir / 'media' / 'problem_crops'
data_dir = bfmg_dir / 'data'

crops_dir.mkdir(parents=True, exist_ok=True)
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
    
    # 40th Edition = 2025-2026, 39th Edition = 2024-2025
    year_start = 1985 + edition
    year_str = f"{year_start}-{year_start+1} ({edition}th Edition)"
    
    stage_names = {
        20: "Semi-Final",
        30: "UK National Final",
        41: "International Final (Day 1)",
        42: "International Final (Day 2)"
    }
    stage_name = stage_names.get(stage_code, f"Stage {stage_code}")
    
    doc = fitz.open(pdf_path)
    zoom = 300 / 72
    mat = fitz.Matrix(zoom, zoom)

    extracted = []

    for page_idx, page in enumerate(doc):
        page_num = page_idx + 1
        blocks = page.get_text("blocks")
        
        # Sort blocks vertically then horizontally
        blocks.sort(key=lambda b: (b[1], b[0]))
        
        # Find problem headers on this page
        headers = []
        for b in blocks:
            b_text = b[4].strip()
            m_h = re.search(r'^(?:START[^\n]*?)?\s*(\d{1,2})\.\s+([^\n\(]+?)(?:\s*\((?:coefficient|coeff\.|coef\.)\s*(\d+)\))?', b_text, re.I)
            if m_h:
                num = int(m_h.group(1))
                if 1 <= num <= 18:
                    title = m_h.group(2).strip()
                    coeff_match = re.search(r'\((?:coefficient|coeff\.|coef\.)\s*(\d+)\)', b_text, re.I)
                    coeff = int(coeff_match.group(1)) if coeff_match else num
                    headers.append({
                        'number': num,
                        'title': title,
                        'coefficient': coeff,
                        'x0': b[0],
                        'y0': b[1],
                        'x1': b[2],
                        'y1': b[3]
                    })

        # Render full high-res problem screen-grabs
        for i, h in enumerate(headers):
            num = h['number']
            title = h['title']
            coeff = h['coefficient']
            
            y0 = max(0.0, h['y0'] - 10.0)
            y1 = headers[i+1]['y0'] - 5.0 if i+1 < len(headers) else 770.0
            
            # Left or Right column crop
            if h['x0'] < 300:
                x0, x1 = 15.0, 292.0
            else:
                x0, x1 = 295.0, 580.0
                
            crop_rect = fitz.Rect(x0, y0, x1, y1)
            pix = page.get_pixmap(matrix=mat, clip=crop_rect)
            
            img_name = f"{edition}_{stage_code}_p{num}_full_crop.png"
            img_path = crops_dir / img_name
            pix.save(img_path)
            
            # Clean plain text statement for search/category metadata
            statement_lines = []
            for b in blocks:
                if y0 <= b[1] < y1 and crop_rect.x0 - 5 <= b[0] <= crop_rect.x1 + 5:
                    txt = b[4].strip()
                    if not re.search(r'FFJM\s*–|Information and results at|http://|Problems \d+ to \d+:|END for|START for|The Swiss Federation', txt, re.I):
                        txt_clean = re.sub(r'^\s*\d{1,2}\.\s+[^\n\(]+?(?:\s*\((?:coefficient|coeff\.|coef\.)\s*\d+\))?', '', txt, flags=re.I).strip()
                        if txt_clean and len(txt_clean) > 10:
                            statement_lines.append(txt_clean)

            statement_text = " ".join(statement_lines)
            statement_text = re.sub(r'(\w+)-\s+(\w+)', r'\1\2', statement_text)
            statement_text = re.sub(r'\s+', ' ', statement_text).strip()
            
            pid = f"{edition}_{stage_code}_p{num}"
            cats = get_categories(num)
            comp_label = get_complexity_label(num)
            
            extracted.append({
                "id": pid,
                "edition": edition,
                "year": year_str,
                "stage": stage_name,
                "stage_code": stage_code,
                "number": num,
                "title": title,
                "coefficient": coeff,
                "categories": cats,
                "complexity_label": comp_label,
                "statement": statement_text,
                "crop_image": f"/media/problem_crops/{img_name}",
                "solution": {
                    "answer": f"Solution for Problem {num} ({title})",
                    "steps": [
                        f"Read and analyze the problem card for {title}.",
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
        
    print(f"Successfully extracted {len(all_problems)} full high-res problem screen-grabs into {problems_file}")

if __name__ == "__main__":
    main()
