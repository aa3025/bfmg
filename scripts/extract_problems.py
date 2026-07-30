import os
import re
import json
import glob
import pypdf
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
    
    # Extract page images
    page_images = {}
    for page_idx, page in enumerate(reader.pages):
        imgs = []
        try:
            for img_obj in page.images:
                # Convert tiff/png/jpg to saved media asset
                ext = Path(img_obj.name).suffix or '.png'
                img_name = f"{edition}_{stage_code}_page{page_idx+1}_{img_obj.name}"
                img_path = diagrams_dir / img_name
                with open(img_path, 'wb') as f:
                    f.write(img_obj.data)
                imgs.append(f"/media/problem_diagrams/{img_name}")
        except Exception:
            pass
        page_images[page_idx + 1] = imgs

    full_text = "\n".join([page.extract_text() or "" for page in reader.pages])

    text = re.sub(r'FFJM\s*–.*?\n', '', full_text)
    text = re.sub(r'Information and results at http://www.fsjm.ch/.*?\n', '', text)
    text = re.sub(r'START for ALL PARTICIPANTS.*?\n', '', text)
    text = re.sub(r'END for CE PARTICIPANTS.*?\n', '', text)

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
            statement = re.sub(r'FOR PARTICIPANTS.*', '', statement, flags=re.DOTALL).strip()
            
            pid = f"{edition}_{stage_code}_p{p_num}"
            cats = get_categories(p_num)
            comp_label = get_complexity_label(p_num)
            
            # Map page images (estimate page based on problem number: 1-5 page 1, 6-11 page 2, etc.)
            p_page = 1 if p_num <= 5 else (2 if p_num <= 10 else (3 if p_num <= 14 else 4))
            diagram_list = page_images.get(p_page, [])
            
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
                "diagrams": diagram_list,
                "solution": {
                    "answer": f"Solution for Problem {p_num} ({title})",
                    "steps": [
                        f"Analyze the problem conditions for {title}.",
                        f"Apply logic and constraints for category {comp_label}.",
                        f"Calculate and verify final answer."
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
        
    print(f"Successfully extracted {len(all_problems)} problems with diagrams into {problems_file}")

if __name__ == "__main__":
    main()
