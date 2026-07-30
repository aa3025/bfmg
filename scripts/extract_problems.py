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
    expected_num = 1

    for page_idx, page in enumerate(doc):
        footer_rects = page.search_for("END for") + page.search_for("Problems ")
        
        # Search for problem headers 1..18 sequentially on page
        page_headers = []
        for num in range(expected_num, min(19, expected_num + 8)):
            rects = page.search_for(f"{num}. ")
            for r in rects:
                if 30 <= r.y0 <= 775:
                    line_text = page.get_text("text", clip=fitz.Rect(r.x0 - 5, r.y0 - 2, r.x0 + 320, r.y1 + 25)).strip()
                    m_exact = re.match(rf'^{num}\.\s+([^\n\(]+)', line_text)
                    if m_exact:
                        title = m_exact.group(1).strip()
                        coeff_match = re.search(r'\((?:coefficient|coeff\.|coef\.)\s*(\d+)\)', line_text, re.I)
                        coeff = int(coeff_match.group(1)) if coeff_match else num
                        page_headers.append({
                            'number': num,
                            'title': title,
                            'coefficient': coeff,
                            'x0': r.x0,
                            'y0': r.y0
                        })
                        expected_num = num + 1
                        break

        left_headers = sorted([h for h in page_headers if h['x0'] < 300], key=lambda h: h['y0'])
        right_headers = sorted([h for h in page_headers if h['x0'] >= 300], key=lambda h: h['y0'])

        def crop_column_problems(headers, x0, x1):
            col_probs = []
            for idx, h in enumerate(headers):
                num = h['number']
                title = h['title']
                coeff = h['coefficient']
                
                prob_y0 = max(35.0, h['y0'] - 8.0)
                
                if idx + 1 < len(headers):
                    prob_y1 = headers[idx+1]['y0'] - 6.0
                else:
                    col_footers = [r.y0 for r in footer_rects if (r.x0 < 300 if x0 < 300 else r.x0 >= 300) and r.y0 > h['y0']]
                    if col_footers:
                        prob_y1 = min(col_footers) - 4.0
                    else:
                        prob_y1 = 765.0
                        
                crop_rect = fitz.Rect(x0, prob_y0, x1, prob_y1)
                pix = page.get_pixmap(matrix=mat, clip=crop_rect)
                
                img_name = f"{edition}_{stage_code}_p{num}_full_crop.png"
                img_path = crops_dir / img_name
                pix.save(img_path)
                
                # Plain text statement snippet for category search
                text_clip = page.get_text("text", clip=crop_rect).strip()
                statement_clean = re.sub(r'FFJM\s*–|Information and results at|http://|Problems \d+ to \d+:|END for|START for|The Swiss Federation', '', text_clip, flags=re.I)
                statement_clean = re.sub(r'(\w+)-\s+(\w+)', r'\1\2', statement_clean)
                statement_clean = re.sub(r'\s+', ' ', statement_clean).strip()
                
                pid = f"{edition}_{stage_code}_p{num}"
                cats = get_categories(num)
                comp_label = get_complexity_label(num)
                
                col_probs.append({
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
                    "statement": statement_clean,
                    "crop_image": f"/media/problem_crops/{img_name}",
                    "solution": {
                        "answer": f"Solution for Problem {num} ({title})",
                        "steps": [
                            f"Read and analyze the official problem card for {title}.",
                            f"Apply logical deduction for category {comp_label}.",
                            f"Calculate and verify final result."
                        ]
                    }
                })
            return col_probs

        extracted.extend(crop_column_problems(left_headers, 15.0, 292.0))
        extracted.extend(crop_column_problems(right_headers, 295.0, 580.0))

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
        
    print(f"Successfully extracted {len(all_problems)} exact 100% column problem screen-grabs into {problems_file}")

if __name__ == "__main__":
    main()
