import os
import re
import json
import glob
import fitz # PyMuPDF
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
    diagram_keywords = ['figure', 'disc', 'token', 'square', 'grid', 'triangle', 'example', 'shown', 'diagram', 'illustration', 'pattern', 'drawing', 'card', 'logo', 'shield', 'as in', 'map', 'cactus', 'tetramino', 'horseshoe', 'pyramid', 'maze', 'discs', 'crossword', 'dots', 'circle', 'quadrilateral', 'domino']

    extracted = []

    for page_idx, page in enumerate(doc):
        page_num = page_idx + 1
        blocks = page.get_text("blocks")
        drawings = page.get_drawings()
        
        # Sort blocks vertically then horizontally
        blocks.sort(key=lambda b: (b[1], b[0]))
        
        # Find problem headers on this page
        prob_headers = []
        for b_idx, b in enumerate(blocks):
            b_text = b[4].strip()
            m_h = re.search(r'^(?:START[^\n]*?)?\s*(\d{1,2})\.\s+([^\n\(]+?)(?:\s*\((?:coefficient|coeff\.|coef\.)\s*(\d+)\))?', b_text, re.I)
            if m_h:
                num = int(m_h.group(1))
                if 1 <= num <= 18:
                    title = m_h.group(2).strip()
                    coeff_match = re.search(r'\((?:coefficient|coeff\.|coef\.)\s*(\d+)\)', b_text, re.I)
                    coeff = int(coeff_match.group(1)) if coeff_match else num
                    prob_headers.append({
                        'number': num,
                        'title': title,
                        'coefficient': coeff,
                        'rect': fitz.Rect(b[0], b[1], b[2], b[3]),
                        'block_idx': b_idx
                    })

        # Process each problem on page
        for i, p_info in enumerate(prob_headers):
            num = p_info['number']
            title = p_info['title']
            coeff = p_info['coefficient']
            h_rect = p_info['rect']
            
            # Vertical & horizontal bounds for this problem:
            next_y = prob_headers[i+1]['rect'].y0 if i+1 < len(prob_headers) else 780.0
            
            # Restrict drawing rects to problem's column
            col_min_x = max(20.0, h_rect.x0 - 25.0)
            col_max_x = min(580.0, h_rect.x0 + 260.0)
            
            p_drawings = []
            for d in drawings:
                r = d["rect"]
                if h_rect.y0 - 10 <= r.y0 < next_y and col_min_x <= r.x0 <= col_max_x and r.height < 450 and r.width < 350:
                    # Exclude full page border lines
                    if r.height > 700 or r.width > 550:
                        continue
                    p_drawings.append(r)

            diag_union_rect = None
            if p_drawings:
                diag_union_rect = p_drawings[0]
                for r in p_drawings[1:]:
                    diag_union_rect |= r

            statement_lines = []
            for b in blocks:
                # Check if block falls within this problem's vertical band & column
                if h_rect.y0 - 15 <= b[1] < next_y and col_min_x - 10 <= b[0] <= col_max_x + 30:
                    txt = b[4].strip()
                    b_rect = fitz.Rect(b[0], b[1], b[2], b[3])
                    
                    # Skip instruction lines / banners / headers
                    if re.search(r'FFJM\s*–|Information and results at|http://|Problems \d+ to \d+:|END for|START for|The Swiss Federation', txt, re.I):
                        continue
                        
                    # Filter out loose diagram text blocks inside vector drawing bounding rect
                    if diag_union_rect and (diag_union_rect.intersects(b_rect) or diag_union_rect.contains(b_rect)):
                        if not re.search(r'\b(?:what|how|find|calculate|is|are|the|how many)\b', txt, re.I):
                            continue
                            
                    # Clean header line text if present
                    txt_clean = re.sub(r'^\s*\d{1,2}\.\s+[^\n\(]+?(?:\s*\((?:coefficient|coeff\.|coef\.)\s*\d+\))?', '', txt, flags=re.I).strip()
                    if txt_clean:
                        statement_lines.append(txt_clean)

            statement_text = " ".join(statement_lines)
            statement_text = re.sub(r'(\w+)-\s+(\w+)', r'\1\2', statement_text)
            statement_text = re.sub(r'\s+', ' ', statement_text).strip()
            
            # Crop high-res diagram PNG if problem has vector drawings and mentions visual keywords
            diagram_list = []
            has_visual_ref = any(kw in statement_text.lower() for kw in diagram_keywords) or any(kw in title.lower() for kw in diagram_keywords)
            
            if has_visual_ref and diag_union_rect and diag_union_rect.width >= 30 and diag_union_rect.height >= 30:
                pad_rect = fitz.Rect(diag_union_rect.x0 - 5, diag_union_rect.y0 - 5, diag_union_rect.x1 + 5, diag_union_rect.y1 + 5)
                zoom = 300 / 72
                mat = fitz.Matrix(zoom, zoom)
                pix = page.get_pixmap(matrix=mat, clip=pad_rect)
                
                img_name = f"{edition}_{stage_code}_p{num}_vector_diag.png"
                img_path = diagrams_dir / img_name
                pix.save(img_path)
                diagram_list = [f"/media/problem_diagrams/{img_name}"]
                
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
                "diagrams": diagram_list,
                "solution": {
                    "answer": f"Solution for Problem {num} ({title})",
                    "steps": [
                        f"Read and analyze the given conditions for {title}.",
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
        
    print(f"Successfully extracted {len(all_problems)} pristine problems with column-scoped vector diagram crops into {problems_file}")

if __name__ == "__main__":
    main()
