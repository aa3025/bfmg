# BFMG Website — Project Journal

**Last Updated:** 2026-07-30  
**Session:** Building the BFMG (British Federation of Mathematical Games) website with problem bank, crop extraction, and step-by-step solutions.

---

## 📁 Project Structure

```
/Volumes/Elements-aa3025/GitLab/aa3025.github.io/bfmg/
├── content/
│   ├── pages/          # Markdown source for pages (practice.md, etc.)
│   └── posts/          # Markdown source for blog posts
├── data/
│   ├── problems.json   # 318 problems extracted from PDFs (AUTO-GENERATED, do not edit)
│   └── solutions/      # ← Manually written step-by-step solution files (SOURCE OF TRUTH)
│       ├── 35_20_p1.md # ✅ DONE: Squares (answer=4, verified correct)
│       └── 35_20_p2.md … 35_20_p8.md # ✅ DONE: Darts through Jigsaw Puzzle Pieces
├── media/
│   ├── past_papers/    # Source PDF question + answer files
│   └── problem_crops/  # 318 high-res PNG crops (AUTO-GENERATED via extract_problems.py)
├── pages/              # Generated HTML pages (do NOT edit directly)
├── posts/              # Generated HTML posts (do NOT edit directly)
├── scripts/
│   └── extract_problems.py  # Extracts problem crops from PDFs → problem_crops/ + problems.json
├── generate_liquid_site.py  # Site generator: merges solutions → HTML pages
├── deploy.sh           # ⛔ PAUSED — do not run until testing confirmed
└── index.html          # Generated home page
```

---

## ✅ Completed Work

### 1. PDF Problem Crop Extraction (`scripts/extract_problems.py`)
- Extracts 318 problems from 18 question PDFs at 300 DPI
- Detects problem headers using `(coefficient N)` or `(coeff. N)` or `(coef. N)` pattern
- **Column layout:** Left column `x0=15, x1=292`; Right column `x0=295, x1=588`
- **Top boundary:** `prob_y0 = h['y0'] - 2.0` — tight, no previous-problem text bleed
- **Bottom boundary:** word-level baseline `max(w[3] for w in col_words) + 4.0`; fallback `785.0pt`
- **Multi-column continuation:** Part 1 uses word-level baseline; Part 2 starts at `y0=50.0` (skips page header/URL lines)
- **Sponsor banners excluded:** Detects PICTET, ETH, SOUTIEN, Swiss Federation text + sponsor images at y0>650

### 2. Site Generator (`generate_liquid_site.py`)
- Reads `data/problems.json` + all `data/solutions/*.md` files
- **Merges solutions:** `**Answer: X**` → answer box; `### Step N – Title` → numbered steps
- **Renders Markdown tables:** pipe tables inside solution steps are converted to styled, horizontally scrollable HTML tables
- **Publishes only manual solutions:** generated placeholder entries in `problems.json` are removed; only matching `data/solutions/*.md` files count as completed
- Generates `pages/practice.html` with all 318 problems embedded as inline JSON
- Relative paths used throughout for local `file://` compatibility

### 3. Practice Page (`pages/practice.html`)
- Filter by category (CE/CM/C1/C2/L1/L2/HC/GP) and competition stage
- "Draw Random Problem" button
- Paper and question dropdowns for opening a specific problem directly
- Shows official high-res problem card image
- **"Show Step-by-Step Solution"** reveals:
  - Green answer box: `Answer: [value]`
  - Numbered step-by-step with bold headers
  - Falls back to "coming soon" for unsolved problems

### 4. Specific Crop Fixes Applied
| Problem | Issue | Fix |
|---------|-------|-----|
| `35_30_p3` Assemblies | False multi-column split gluing wrong content | Fixed split detection logic |
| `35_30_p12` A Remarkable Year | Bottom line cut off | Increased fallback bottom 772→785pt |
| `36_20_p15` This Year's Stars | Sponsor banner included | Added banner/image detection |
| `36_41_p3` Bowls | Previous problem text bleeding in at top | Reduced top padding -8→-2pt |
| `36_41_p10` Nine Letters | Part 1 bottom line cut off | Word-level baseline detection |
| `36_41_p13` Square Tables | Part 1 bottom line cut off | Word-level baseline detection |
| `36_42_p4` Exam Room | Part 2 had header/URL at top | part2_y0=50.0 to skip page header |
| `36_42_p18` Phil McCan's Garden | Triangle diagram right edge clipped | Right col x1 expanded to 588.0 |

---

## 🗃️ Available Answer PDFs (in `media/past_papers/`)

| PDF | Paper |
|-----|-------|
| `36_30_CH_en_answers.pdf` | 36th Edition UK National Final |
| `37_41_CH_en_answers.pdf` | 37th Edition International Final Day 1 |
| `37_42_CH_en_answers.pdf` | 37th Edition International Final Day 2 |
| `38_41_CH_en_answers.pdf` | 38th Edition International Final Day 1 |
| `38_42_CH_en_answers.pdf` | 38th Edition International Final Day 2 |

**FSJM Online Archive:** `https://fsjm.ch/static/archives/{ed}_{stage}_CH_fr_answers.pdf`
(also try `_CH_fr_answers_2.pdf` or `_CH_en_answers.pdf`)

---

## 📝 Solution File Format

File: `data/solutions/{edition}_{stage}_p{num}.md`

```markdown
# Solution: 35_20_p1 — Squares

**Answer: 4**

## Step-by-Step Solution

### Step 1 – Understand the goal
{explanation with **bold** and *italic* markdown supported}

### Step 2 – ...
{explanation}

*(Verified from official FSJM answers: "...")*
```

---

## 📋 Solutions Status (18 / 318 done)

### 35_20 — 35th Edition Semi-Final 2020-2021
*Answers: https://fsjm.ch/static/archives/35_20_CH_fr_answers_2.pdf*
| # | Title | Official Answer | Done |
|---|-------|----------------|------|
| 1 | Squares | 4 | ✅ |
| 2 | Darts | 17 | ✅ |
| 3 | Chambers in the Labyrinth | 6 paths | ✅ |
| 4 | Eight-sided Die | 7 | ✅ |
| 5 | Sharing a Chocolate Bar | 3 forms | ✅ |
| 6 | Ceiling Lamp | 9 spots | ✅ |
| 7 | The ConsecYears | 17990 | ✅ |
| 8 | Jigsaw Puzzle Pieces | 15 piles | ✅ |
| 9 | Even Smaller | 6 rhombuses | ✅ |
| 10 | Eight Divisors | 24 | ✅ |
| 11 | Gift Wrapping | 2 sol: 81cm or 137cm | ✅ |
| 12 | Diagonals | 50 regions | ✅ |
| 13 | Play the Lottery | 60 grids | ✅ |
| 14 | Fair Shares | 10 sol: 3;4;7;8;11;12;15;16;19;20 | ✅ |
| 15 | The Robot | 2262 cm | ✅ |
| 16 | Kryptonian Square | 1 sol: 117 | ✅ |
| 17 | Four Small Cubes | 601/3456 | ✅ |
| 18 | Sharing the Garden | BD=27, BE=40 | ✅ |

### 35_30 — 35th Edition UK National Final
*No local answers. Fetch from FSJM archive.*
| # | Title | Done |
|---|-------|------|
| 1 | Matthew's Addition | ⬜ |
| 2 | Carpenter's Rule | ⬜ |
| 3 | Assemblies | ⬜ |
| 4 | Gears | ⬜ |
| 5 | Matilda's Game | ⬜ |
| 6 | Complete the Multiplication | ⬜ |
| 7 | Triangle of the Year | ⬜ |
| 8 | Birthday | ⬜ |
| 9 | Black Squares | ⬜ |
| 10 | Tiling | ⬜ |
| 11 | The Zoo | ⬜ |
| 12 | A Remarkable Year | ⬜ |
| 13 | The Jewel Box | ⬜ |
| 14 | Augmentation Operation | ⬜ |
| 15 | Attic | ⬜ |
| 16 | Signed Pyramid | ⬜ |
| 17 | So many triangles! | ⬜ |
| 18 | Duke Hunter's Wetland | ⬜ |

### 36_20 — 36th Edition Semi-Final
*No local answers. Fetch from FSJM archive.*
All 18 ⬜: Nine Tokens, Ariadne's Thread, From 1 to 7, Matilda's number, Cannonballs,
Matilda's Pyramid, Matthew's Cards, 3 Squares on a Rectangle, Posts and Enclosures,
8 Cards, A Total of a Year, Lottery Tickets, Diana's Paving, LEON and NOEL,
This Year's Stars, A Triangle in a Pentagon, Matilda's Polygons, Integral Triangle

### 36_30 — 36th Edition UK National Final
*✅ LOCAL ANSWERS: media/past_papers/36_30_CH_en_answers.pdf*
| # | Title | Official Answer | Done |
|---|-------|----------------|------|
| 1 | 22 Marbles | 20 | ⬜ |
| 2 | Pizza | 4 choices | ⬜ |
| 3 | Triangles | 7 triangles | ⬜ |
| 4 | Cut that out! | 4 dm | ⬜ |
| 5 | Around the Square | a=7, b=8 | ⬜ |
| 6 | Ludiland | 14 coins | ⬜ |
| 7 | Just Three Letters | 1908 | ⬜ |
| 8 | Insomnia | 2h 30min | ⬜ |
| 9 | The Year Grid | 2 sol: a=7,b=6 and a=5,b=4 | ⬜ |
| 10 | Benjamin's Puzzle | 4 sol: 145, 1237, 4568, 23678 | ⬜ |
| 11 | Add to the Multiplication | 1 sol: 34 | ⬜ |
| 12 | Eight Divisors | 4 sol: 66, 78, 105, 136 | ⬜ |
| 13 | Three Triangles | 1 sol: 23 | ⬜ |
| 14 | Composite Numbers | 232,792,560 | ⬜ |
| 15 | Mr. Modulus' Number | 2 sol: 769, 923 | ⬜ |
| 16 | Spiral | 2152 | ⬜ |
| 17 | Orchard | 2 sol: 3m, 12m | ⬜ |
| 18 | Equiangular Hexagons | 4 solutions | ⬜ |

### 36_41 — 36th Edition International Final Day 1
*No local answers.*  18 problems ⬜

### 36_42 — 36th Edition International Final Day 2
*No local answers.*  17 problems ⬜

### 37_20 — 37th Edition Semi-Final
*No local answers.*  18 problems ⬜

### 37_30 — 37th Edition UK National Final
*No local answers.*  17 problems ⬜

### 37_41 — 37th Edition International Final Day 1
*✅ LOCAL ANSWERS: media/past_papers/37_41_CH_en_answers.pdf (tabular format)*
Answers p1–p18: 8 | 2 | 13 | 3 | 8 | 9 | 8 | 4448 | (+ more on page 2)
18 problems ⬜

### 37_42 — 37th Edition International Final Day 2
*✅ LOCAL ANSWERS: media/past_papers/37_42_CH_en_answers.pdf (tabular format)*
Answers p1–p8: 7 | 17 | 4 | 1 | 15 | 98 | 1h40min | 11
18 problems ⬜

### 38_20 — 38th Edition Semi-Final
*No local answers.*  17 problems ⬜

### 38_30 — 38th Edition UK National Final
*No local answers.*  18 problems ⬜

### 38_41 — 38th Edition International Final Day 1
*✅ LOCAL ANSWERS: media/past_papers/38_41_CH_en_answers.pdf*
| # | Answer | | # | Answer |
|---|--------|-|---|--------|
| 1 | 39 | | 10 | 2170 cm² |
| 2 | 3 | | 11 | 3 sol: 42; 49; 61 |
| 3 | a=4, b=8 | | 12 | 13 |
| 4 | 7 (3 solutions) | | 13 | 4723 m² |
| 5 | 20 | | 14 | 5 |
| 6 | 5 | | 15 | 8h |
| 7 | 882 | | 16 | 3 sol: 2202, 2206, 2213 |
| 8 | 6 | | 17 | 59 cm² |
| 9 | 3 solutions | | 18 | 8 solutions |
18 problems ⬜

### 38_42 — 38th Edition International Final Day 2
*✅ LOCAL ANSWERS: media/past_papers/38_42_CH_en_answers.pdf*
| # | Answer | | # | Answer |
|---|--------|-|---|--------|
| 1 | 43 | | 10 | 19.99 |
| 2 | 4 and 9 | | 11 | 2 sol: 1456, 4589 |
| 3 | 47 | | 12 | 28900 m² |
| 4 | 4 | | 13 | 3 sol: a=2,b=5; a=2,b=6; a=3,b=7 |
| 5 | 9 | | 14 | 187.5 cm² |
| 6 | (cross-calc puzzle) | | 15 | 5 cm |
| 7 | 63 | | 16 | 6 sol: 64;196;576;676;900;1600 |
| 8 | a=3, b=7 | | 17 | 12978 m² |
| 9 | (diagram) | | 18 | 3600 |
18 problems ⬜

### 39_20 — 39th Edition Semi-Final
*No local answers.*  17 problems ⬜

### 39_30 — 39th Edition UK National Final
*No local answers.*  18 problems ⬜

### 39_41 — 39th Edition International Final Day 1
*No local answers.*  17 problems ⬜

### 39_42 — 39th Edition International Final Day 2
*No local answers.*  18 problems ⬜

### 40_20 — 40th Edition Semi-Final 2025-2026
*No local answers.*  17 problems ⬜

### 40_30 — 40th Edition UK National Final
*No local answers.*  18 problems ⬜

---

## 🔧 Open Issues / Next Steps

### High Priority
1. **⛔ DEPLOYMENTS PAUSED** — `./deploy.sh` must NOT be run until:
   - All problem crops verified (no cut-off text, no banners, no bleed)
   - Practice page works locally with correct image loading
   - Navigation links work in local `file://` mode

2. **Column crop width rule** (requested but not yet audited):
   > "Do not cut left edge of left column or right edge of right column; no artificial cuts between columns"
   - Currently: left `x0=15`, right `x1=588` — close to natural margins
   - Still needs a full visual audit pass across all 318 crops

3. **Write solutions for all 300 remaining problems**
   - Priority 1: Papers with local answer PDFs (`36_30`, `37_41`, `37_42`, `38_41`, `38_42`)
   - Priority 2: Fetch FSJM archive PDFs for remaining papers
   - Suggest: tackle 1 full paper per session

### Medium Priority
4. **Local navigation links broken** — `index.html` top nav doesn't work in `file://` mode
5. **Problem crop images not loading locally** — path issue in JS when opened as `file://`

### Audit note — 2026-07-30
- `data/solutions/` now contains eight manually written, answer-verified solution files: `35_20_p1.md` through `35_20_p8.md`.
- `python3 generate_liquid_site.py` completed successfully and incorporated all eight into `pages/practice.html`.
- `data/problems.json` currently contains a generated placeholder `solution` object for **every** problem. These placeholders are not equivalent to completed solutions; manual files in `data/solutions/` remain the authoritative completion count.

---

## 🔑 Key Commands

```bash
# 1. (⛔ PAUSED) Re-extract all problem crops from PDFs (takes ~30s) --> some were edited by hand
cd /Volumes/Elements-aa3025/GitLab/aa3025.github.io/bfmg
python3 scripts/extract_problems.py

# 2. Regenerate the full website (merges solutions → practice.html)
python3 generate_liquid_site.py

# 3. Open locally to test
open pages/practice.html

# 4. Deploy (⛔ PAUSED)
# ./deploy.sh
```

---

## 📖 Solution Writing Workflow (Per Problem)

1. View crop: `media/problem_crops/{id}_full_crop.png`
2. Solve the problem
3. Check official answer in local PDF or fetch: `https://fsjm.ch/static/archives/{ed}_{stage}_CH_fr_answers.pdf`
4. Write `data/solutions/{id}.md` using the format in the "Solution File Format" section
5. Run `python3 generate_liquid_site.py`
6. Open `pages/practice.html` → find problem → verify "Show Step-by-Step Solution"

---

*End of journal. Continue here next session.*
