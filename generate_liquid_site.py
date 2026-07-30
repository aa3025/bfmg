import os
import re
import glob
from datetime import datetime
from pathlib import Path

# Base directory is the directory containing this script (bfmg/)
out_base = Path(__file__).parent.resolve()
content_dir = out_base / 'content'
pages_dir = content_dir / 'pages'
posts_dir = content_dir / 'posts'

pages_out = out_base / 'pages'
posts_out = out_base / 'posts'
media_out = out_base / 'media'

pages_out.mkdir(parents=True, exist_ok=True)
posts_out.mkdir(parents=True, exist_ok=True)
media_out.mkdir(parents=True, exist_ok=True)

pages = []
posts = []

def parse_frontmatter(md_filepath):
    with open(md_filepath, 'r', encoding='utf-8') as f:
        text = f.read()
        
    frontmatter = {}
    content = text
    
    fm_match = re.match(r'^---\s*\n(.*?)\n---\s*\n(.*)$', text, re.DOTALL)
    if fm_match:
        fm_text, content = fm_match.groups()
        for line in fm_text.split('\n'):
            if ':' in line:
                key, val = line.split(':', 1)
                key = key.strip()
                val = val.strip().strip('"').strip("'")
                frontmatter[key] = val
                
    title = frontmatter.get('title', md_filepath.stem.replace('-', ' ').title())
    date_str = frontmatter.get('date', '')
    slug = frontmatter.get('slug', md_filepath.stem)
    post_type = frontmatter.get('type', 'post' if 'posts' in str(md_filepath) else 'page')
    
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
    except Exception:
        try:
            dt = datetime.strptime(date_str, "%Y-%m-%d")
        except Exception:
            dt = datetime.min
            
    return {
        'title': title,
        'slug': slug,
        'date_str': date_str,
        'formatted_date': dt.strftime("%B %d, %Y") if dt != datetime.min else "",
        'dt': dt,
        'content': content.strip(),
        'type': post_type
    }

# Read all pages (.md)
for md_file in sorted(pages_dir.glob('*.md')):
    pages.append(parse_frontmatter(md_file))

# Read all posts (.md)
for md_file in sorted(posts_dir.glob('*.md')):
    posts.append(parse_frontmatter(md_file))

# Sort pages chronologically ascending (earliest left, latest right)
pages.sort(key=lambda x: x['dt'])

# Sort posts chronologically descending (newest first)
posts.sort(key=lambda x: x['dt'], reverse=True)

# Helper function to convert double newlines to paragraphs like WordPress wpautop
def wpautop(text):
    if not text:
        return ""
    text = text.replace('\r\n', '\n')
    
    # Split text into double newline blocks
    blocks = re.split(r'\n\s*\n', text)
    processed_blocks = []
    
    for block in blocks:
        block = block.strip()
        if not block:
            continue
        # If block contains HTML block elements like h1-h6, ul, ol, li, blockquote, div
        if re.search(r'<(p|h[1-6]|ul|ol|li|blockquote|div|table|section|article)', block, re.IGNORECASE):
            clean_block = re.sub(r'</(h[1-6]|li|ul|ol|p|div)>\s*\n\s*', r'</\1>\n', block)
            processed_blocks.append(clean_block)
        else:
            lines = block.split('\n')
            p_content = "<br />\n".join(lines)
            processed_blocks.append(f"<p>{p_content}</p>")
            
    res = "\n\n".join(processed_blocks)
    # Remove erroneous <br /> tags directly around block-level HTML tags
    res = re.sub(r'<br\s*/?>\s*(</?(?:ul|ol|li|h[1-6]|p|div|section|article)[^>]*>)', r'\1', res)
    res = re.sub(r'(</?(?:ul|ol|li|h[1-6]|p|div|section|article)[^>]*>)\s*<br\s*/?>', r'\1', res)
    return res

# Build HTML template generator
def build_page_html(current_item, is_post=False, is_home=False):
    root_rel = "/"
    pages_rel = "/pages/"
    posts_rel = "/posts/"
    media_rel = "/media/"
    
    # Process media links in content
    item_content = current_item['content']
    
    # Replace Quebec flag image tag and regional indicator prefix with Quebec flag emoji ⚜️
    item_content = re.sub(r'[\U000e0060-\U000e007f]*<img[^>]*Flag-Quebec[^>]*>', '⚜️ ', item_content)
    
    # Strip inline width/height attributes from <img> tags so CSS 100% width rule takes effect
    item_content = re.sub(r'\s+(width|height)="[0-9]+"', '', item_content)
    
    # Isolate inline text captions right before images
    item_content = re.sub(r'([^\s>\n])\s*(<a[^>]*>\s*<img|<img)', r'\1<br /><br />\2', item_content)
    
    item_content = wpautop(item_content)
    
    # Format inline text right before image links as clean subheaders
    item_content = re.sub(r'(?:<p>)?\s*([A-Za-z0-9\s,\.\-—\(\)]+):\s*<br\s*/?>\s*<br\s*/?>\s*(<a[^>]*>\s*<img|<img)', r'<h4 class="text-xl font-bold text-blue-300 mt-6 mb-2">\1</h4>\n\2', item_content)
    
    # Replace any media/ links with root-relative /media/ path while preserving src and href attributes
    def replace_media_attr(m):
        attr = m.group(1)
        filename = m.group(2)
        return f'{attr}="{media_rel}{filename}"'
    item_content = re.sub(r'\b(href|src)=["\'](?:\.\./|\./)?media/([^"\']+)["\']', replace_media_attr, item_content)
    
    # Replace wordpress domain images with local media paths
    domain_pat = r'https?://bfmg\.maths\.coventry\.domains/wp-content/uploads/\d+/\d+/([^"\'\s>]+)'
    def replace_media(match):
        filename = os.path.basename(match.group(1))
        return media_rel + filename
        
    item_content = re.sub(domain_pat, replace_media, item_content)
    
    # Also replace any direct links to media files
    item_content = re.sub(r'https?://[^\s"\']+\.(jpg|jpeg|png|gif|pdf|docx|xlsx)', lambda m: media_rel + os.path.basename(m.group(0)), item_content)

    # Navigation pages links
    pages_nav_html = ""
    for p in pages:
        is_p_home = (p['slug'] == 'home' or p['title'].lower() in ['home', 'about bfmg', 'about'])
        p_link = "/index.html" if is_p_home else f"/pages/{p['slug']}.html"
        active_cls = "active" if p['slug'] == current_item['slug'] else ""
        pages_nav_html += f'''
        <div class="button-wrap">
            <a href="{p_link}" class="knoll-btn {active_cls}">
                <span class="flex items-center gap-1.5"><i data-lucide="file-text" class="w-4 h-4"></i> {p["title"]}</span>
            </a>
            <div class="button-shadow"></div>
        </div>
        '''

    # If on Posts archive page, append full interactive grid of all posts
    if current_item['slug'] == 'posts':
        all_posts_grid = '<div class="grid grid-cols-1 sm:grid-cols-2 gap-4 mt-6">'
        for p in posts:
            post_url = f"/posts/{p['slug']}.html"
            all_posts_grid += f'''
            <a href="{post_url}" class="glass-panel p-5 block hover:border-blue-400/50 hover:bg-white/10 transition-all text-decoration-none group rounded-2xl">
                <div class="flex items-center gap-2 mb-2 text-xs text-blue-300 font-mono">
                    <i data-lucide="calendar" class="w-3.5 h-3.5"></i> {p['formatted_date']}
                </div>
                <h3 class="text-base font-bold text-white group-hover:text-blue-300 transition-colors mb-3 leading-snug">{p['title']}</h3>
                <span class="inline-flex items-center gap-1.5 text-xs font-semibold text-blue-400 group-hover:translate-x-1 transition-transform">
                    Read Article <i data-lucide="arrow-right" class="w-3.5 h-3.5"></i>
                </span>
            </a>
            '''
        all_posts_grid += '</div>'
        item_content += "\n\n" + all_posts_grid

    # If on Practice & Learn page, append interactive Problem Bank App
    if current_item['slug'] == 'practice':
        problems_json_path = out_base / 'data' / 'problems.json'
        problems_data = "[]"
        if problems_json_path.exists():
            with open(problems_json_path, 'r', encoding='utf-8') as f:
                problems_data = f.read()
                
        practice_app_html = f'''
        <div id="practice-app" class="mt-8 space-y-6">
            <!-- Filter Bar -->
            <div class="glass-panel p-6 space-y-4">
                <h3 class="text-lg font-bold text-white flex items-center gap-2 font-['Outfit']">
                    <i data-lucide="sliders" class="w-5 h-5 text-blue-400"></i>
                    Select Problem Category & Stage
                </h3>
                
                <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    <div>
                        <label class="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">Category / Grade Level</label>
                        <select id="catFilter" onchange="filterProblems()" class="w-full bg-slate-900/90 border border-white/20 rounded-xl px-3.5 py-2.5 text-sm text-white focus:outline-none focus:border-blue-400">
                            <option value="ALL">All Categories & Grade Levels</option>
                            <option value="CE">CE — Primary (Year 5)</option>
                            <option value="CM">CM — Primary / Middle (Year 6-7)</option>
                            <option value="C1">C1 — Lower Secondary (Year 8-9)</option>
                            <option value="C2">C2 — Upper Secondary (Year 10-11)</option>
                            <option value="L1">L1 — Post-Mandatory School</option>
                            <option value="GP">GP — General Public / Adults</option>
                            <option value="L2">L2 — University / High Competition</option>
                            <option value="HC">HC — Top Competition</option>
                        </select>
                    </div>
                    
                    <div>
                        <label class="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">Competition Stage</label>
                        <select id="stageFilter" onchange="filterProblems()" class="w-full bg-slate-900/90 border border-white/20 rounded-xl px-3.5 py-2.5 text-sm text-white focus:outline-none focus:border-blue-400">
                            <option value="ALL">All Stages</option>
                            <option value="20">Semi-Finals</option>
                            <option value="30">UK National Finals</option>
                            <option value="41">International Finals (Day 1)</option>
                            <option value="42">International Finals (Day 2)</option>
                        </select>
                    </div>
                </div>
                
                <div class="pt-2 flex flex-wrap items-center justify-between gap-3">
                    <span id="probCountBadge" class="text-xs text-blue-300 font-mono">Loading problem bank...</span>
                    
                    <div class="button-wrap">
                        <button id="drawBtn" onclick="drawRandomProblem()" class="knoll-btn">
                            <span class="flex items-center gap-2"><i data-lucide="sparkles" class="w-4 h-4 text-amber-300"></i> Draw Random Problem</span>
                        </button>
                        <div class="button-shadow"></div>
                    </div>
                </div>
            </div>

            <!-- Interactive Problem Card -->
            <div id="problemCard" class="glass-panel p-6 sm:p-8 space-y-6">
                <!-- Badges & Meta Header -->
                <div class="flex flex-wrap items-center justify-between gap-3 pb-4 border-b border-white/10">
                    <div class="flex flex-wrap items-center gap-2">
                        <span id="probYear" class="px-3 py-1 rounded-full text-xs font-semibold bg-blue-500/20 text-blue-300 border border-blue-400/30">—</span>
                        <span id="probStage" class="px-3 py-1 rounded-full text-xs font-semibold bg-purple-500/20 text-purple-300 border border-purple-400/30">—</span>
                        <span id="probCoeff" class="px-3 py-1 rounded-full text-xs font-semibold bg-amber-500/20 text-amber-300 border border-amber-400/30">—</span>
                    </div>
                    <span id="probNum" class="text-xs font-mono text-slate-400">—</span>
                </div>

                <!-- Problem Statement -->
                <div>
                    <h2 id="probTitle" class="text-2xl font-bold text-white font-['Outfit'] mb-3">Loading Problem...</h2>
                    <div id="probStatement" class="text-slate-200 text-base leading-relaxed whitespace-pre-line bg-slate-900/50 p-6 rounded-2xl border border-white/10 font-sans">
                        Select your category and click "Draw Random Problem" to begin!
                    </div>
                </div>

                <!-- Solution & Explanation Accordion -->
                <div class="pt-4 border-t border-white/10 space-y-4">
                    <button onclick="toggleSolution()" class="px-4 py-2.5 rounded-xl bg-blue-600/30 border border-blue-400/40 text-blue-200 text-sm font-semibold hover:bg-blue-600/50 transition-all flex items-center gap-2">
                        <i data-lucide="help-circle" class="w-4 h-4"></i>
                        <span id="solBtnText">Show Step-by-Step Solution</span>
                    </button>

                    <div id="solBox" class="hidden bg-slate-900/90 border border-blue-500/30 rounded-2xl p-6 space-y-4">
                        <h4 class="text-base font-bold text-blue-300 flex items-center gap-2 font-['Outfit']">
                            <i data-lucide="lightbulb" class="w-5 h-5 text-amber-400"></i>
                            Step-by-Step Explanation & Solution
                        </h4>
                        <div id="solSteps" class="space-y-3 text-sm text-slate-200">
                            <!-- Steps dynamically populated -->
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <script>
            const ALL_PROBLEMS = {problems_data};
            let filteredProblems = [];
            let currentProblem = null;

            function filterProblems() {{
                const cat = document.getElementById('catFilter').value;
                const stage = document.getElementById('stageFilter').value;

                filteredProblems = ALL_PROBLEMS.filter(p => {{
                    const matchCat = (cat === 'ALL') || (p.categories && p.categories.includes(cat));
                    const matchStage = (stage === 'ALL') || (String(p.stage_code) === String(stage));
                    return matchCat && matchStage;
                }});

                const badge = document.getElementById('probCountBadge');
                if (badge) {{
                    badge.innerText = filteredProblems.length + " Problems Matching Filters";
                }}
            }}

            function drawRandomProblem() {{
                filterProblems();
                if (filteredProblems.length === 0) {{
                    alert("No problems match your selected filters. Try choosing 'All Categories'.");
                    return;
                }}

                const idx = Math.floor(Math.random() * filteredProblems.length);
                currentProblem = filteredProblems[idx];
                renderProblem(currentProblem);
            }}

            function renderProblem(p) {{
                document.getElementById('probYear').innerText = p.year || '';
                document.getElementById('probStage').innerText = p.stage || '';
                document.getElementById('probCoeff').innerText = "Coefficient " + (p.coefficient || p.number);
                document.getElementById('probNum').innerText = "Problem #" + p.number + " (" + (p.complexity_label || '') + ")";
                document.getElementById('probTitle').innerText = "Problem " + p.number + ": " + p.title;
                document.getElementById('probStatement').innerText = p.statement || "No statement text extracted.";

                // Reset Solution Box
                const solBox = document.getElementById('solBox');
                solBox.classList.add('hidden');
                document.getElementById('solBtnText').innerText = "Show Step-by-Step Solution";

                const solSteps = document.getElementById('solSteps');
                let html = "<ol class='list-decimal list-inside space-y-2'>";
                if (p.solution && p.solution.steps) {{
                    p.solution.steps.forEach(step => {{
                        html += "<li class='leading-relaxed'>" + step + "</li>";
                    }});
                }}
                html += "</ol>";
                solSteps.innerHTML = html;
                
                if (window.lucide) lucide.createIcons();
            }}

            function toggleSolution() {{
                const solBox = document.getElementById('solBox');
                const btnText = document.getElementById('solBtnText');
                if (solBox.classList.contains('hidden')) {{
                    solBox.classList.remove('hidden');
                    btnText.innerText = "Hide Solution";
                }} else {{
                    solBox.classList.add('hidden');
                    btnText.innerText = "Show Step-by-Step Solution";
                }}
            }}

            // Auto-initialize on page load
            document.addEventListener('DOMContentLoaded', () => {{
                filterProblems();
                if (ALL_PROBLEMS.length > 0) {{
                    drawRandomProblem();
                }}
            }});
        </script>
        '''
        item_content += "\n\n" + practice_app_html

    # Posts navigation timeline list (last 12 posts)
    posts_nav_html = ""
    recent_posts = posts[:12]
    for p in recent_posts:
        post_url = f"/posts/{p['slug']}.html"
        active_cls = "active" if p['slug'] == current_item['slug'] else ""
        date_badge = p['formatted_date']
        posts_nav_html += f'''
        <a href="{post_url}" class="glass-post-item {active_cls} group">
            <div class="font-medium text-slate-100 text-sm leading-snug group-hover:text-blue-300 transition-colors flex items-start gap-2">
                <i data-lucide="mail" class="w-4 h-4 text-blue-400 mt-0.5 shrink-0"></i>
                <span>{p['title']}</span>
            </div>
            <div class="text-xs text-blue-200/60 mt-1 flex items-center gap-1.5 font-mono pl-6">
                <i data-lucide="calendar" class="w-3 h-3 opacity-70"></i>
                {date_badge}
            </div>
        </a>
        '''

    html_str = f'''<!DOCTYPE html>
<html lang="en" class="dark">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{current_item['title']} - British Federation of Mathematical Games</title>
    <meta name="description" content="{current_item['title']} - British Federation of Mathematical Games">
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://unpkg.com/lucide@latest"></script>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=Outfit:wght@400;500;600;700&display=swap" rel="stylesheet">
    
    <style>
        :root {{
            --glass-bg: rgba(255, 255, 255, 0.05);
            --glass-border: rgba(255, 255, 255, 0.18);
            --glass-highlight: rgba(255, 255, 255, 0.7);
        }}
        
        body {{
            font-family: 'Plus Jakarta Sans', sans-serif;
            background-color: #080c14;
            color: #f1f5f9;
            min-height: 100vh;
            overflow-x: hidden;
        }}

        /* Ambient Fluid Background Orbs */
        .ambient-bg {{
            position: fixed;
            inset: 0;
            z-index: -1;
            overflow: hidden;
            pointer-events: none;
            background: radial-gradient(circle at 50% 0%, #0f172a 0%, #07090e 100%);
        }}

        .orb {{
            position: absolute;
            border-radius: 50%;
            filter: blur(90px);
            opacity: 0.45;
            animation: float 20s ease-in-out infinite alternate;
        }}

        .orb-1 {{
            top: -10%;
            left: 15%;
            width: 500px;
            height: 500px;
            background: linear-gradient(135deg, #3b82f6, #8b5cf6);
        }}

        .orb-2 {{
            top: 40%;
            right: -10%;
            width: 600px;
            height: 600px;
            background: linear-gradient(135deg, #06b6d4, #3b82f6);
            animation-delay: -7s;
        }}

        .orb-3 {{
            bottom: -15%;
            left: 20%;
            width: 550px;
            height: 550px;
            background: linear-gradient(135deg, #6366f1, #ec4899);
            animation-delay: -14s;
        }}

        @keyframes float {{
            0% {{ transform: translate(0, 0) scale(1); }}
            50% {{ transform: translate(40px, 60px) scale(1.08); }}
            100% {{ transform: translate(-30px, 30px) scale(0.95); }}
        }}

        /* Petr Knoll Liquid Glass Button Defs & Styles */
        @property --angle-1 {{
          syntax: "<angle>";
          inherits: false;
          initial-value: -75deg;
        }}

        @property --angle-2 {{
          syntax: "<angle>";
          inherits: false;
          initial-value: -45deg;
        }}

        .button-wrap {{
          position: relative;
          z-index: 2;
          border-radius: 999vw;
          background: transparent;
          pointer-events: none;
          transition: all 400ms cubic-bezier(0.25, 1, 0.5, 1);
          display: inline-block;
        }}

        .button-shadow {{
          --shadow-cuttoff-fix: 2em;
          position: absolute;
          width: calc(100% + var(--shadow-cuttoff-fix));
          height: calc(100% + var(--shadow-cuttoff-fix));
          top: calc(0% - var(--shadow-cuttoff-fix) / 2);
          left: calc(0% - var(--shadow-cuttoff-fix) / 2);
          filter: blur(clamp(2px, 0.125em, 12px));
          -webkit-filter: blur(clamp(2px, 0.125em, 12px));
          overflow: visible;
          pointer-events: none;
        }}

        .button-shadow::after {{
          content: "";
          position: absolute;
          z-index: 0;
          inset: 0;
          border-radius: 999vw;
          background: linear-gradient(180deg, rgba(0, 0, 0, 0.35), rgba(0, 0, 0, 0.15));
          width: calc(100% - var(--shadow-cuttoff-fix) - 0.25em);
          height: calc(100% - var(--shadow-cuttoff-fix) - 0.25em);
          top: calc(var(--shadow-cuttoff-fix) - 0.5em);
          left: calc(var(--shadow-cuttoff-fix) - 0.875em);
          padding: 0.125em;
          box-sizing: border-box;
          mask: linear-gradient(#000 0 0) content-box, linear-gradient(#000 0 0);
          mask-composite: exclude;
          transition: all 400ms cubic-bezier(0.25, 1, 0.5, 1);
          overflow: visible;
          opacity: 1;
        }}

        .knoll-btn {{
          --border-width: clamp(1px, 0.0625em, 3px);
          all: unset;
          cursor: pointer;
          position: relative;
          -webkit-tap-highlight-color: rgba(0, 0, 0, 0);
          pointer-events: auto;
          z-index: 3;
          display: inline-flex;
          align-items: center;
          justify-content: center;
          text-decoration: none;
          background: linear-gradient(
            -75deg,
            rgba(255, 255, 255, 0.08),
            rgba(255, 255, 255, 0.25),
            rgba(255, 255, 255, 0.08)
          );
          border-radius: 999vw;
          box-shadow: inset 0 0.125em 0.125em rgba(0, 0, 0, 0.1),
            inset 0 -0.125em 0.125em rgba(255, 255, 255, 0.6),
            0 0.25em 0.125em -0.125em rgba(0, 0, 0, 0.3),
            0 0 0.1em 0.25em inset rgba(255, 255, 255, 0.25);
          backdrop-filter: blur(8px);
          -webkit-backdrop-filter: blur(8px);
          transition: all 400ms cubic-bezier(0.25, 1, 0.5, 1);
        }}

        .knoll-btn.active {{
          background: linear-gradient(
            -75deg,
            rgba(59, 130, 246, 0.4),
            rgba(147, 197, 253, 0.6),
            rgba(139, 92, 246, 0.4)
          );
        }}

        .knoll-btn:hover {{
          transform: scale(0.975);
          backdrop-filter: blur(0.01em);
          -webkit-backdrop-filter: blur(0.01em);
          box-shadow: inset 0 0.125em 0.125em rgba(0, 0, 0, 0.1),
            inset 0 -0.125em 0.125em rgba(255, 255, 255, 0.7),
            0 0.15em 0.05em -0.1em rgba(0, 0, 0, 0.3),
            0 0 0.05em 0.1em inset rgba(255, 255, 255, 0.6);
        }}

        .knoll-btn span {{
          position: relative;
          display: flex;
          align-items: center;
          gap: 0.4rem;
          user-select: none;
          font-family: "Plus Jakarta Sans", sans-serif;
          letter-spacing: -0.02em;
          font-weight: 600;
          font-size: 0.875rem;
          color: #ffffff;
          text-shadow: 0em 0.15em 0.1em rgba(0, 0, 0, 0.4);
          transition: all 400ms cubic-bezier(0.25, 1, 0.5, 1);
          padding-inline: 1.15em;
          padding-block: 0.6em;
        }}

        .knoll-btn span::after {{
          content: "";
          display: block;
          position: absolute;
          z-index: 1;
          width: calc(100% - var(--border-width));
          height: calc(100% - var(--border-width));
          top: calc(0% + var(--border-width) / 2);
          left: calc(0% + var(--border-width) / 2);
          box-sizing: border-box;
          border-radius: 999vw;
          overflow: clip;
          background: linear-gradient(
            var(--angle-2),
            rgba(255, 255, 255, 0) 0%,
            rgba(255, 255, 255, 0.55) 40% 50%,
            rgba(255, 255, 255, 0) 55%
          );
          z-index: 3;
          mix-blend-mode: screen;
          pointer-events: none;
          background-size: 200% 200%;
          background-position: 0% 50%;
          background-repeat: no-repeat;
          transition: background-position 500ms cubic-bezier(0.25, 1, 0.5, 1),
            --angle-2 500ms cubic-bezier(0.25, 1, 0.5, 1);
        }}

        .knoll-btn:hover span::after {{
          background-position: 25% 50%;
        }}

        .knoll-btn::after {{
          content: "";
          position: absolute;
          z-index: 1;
          inset: 0;
          border-radius: 999vw;
          width: calc(100% + var(--border-width));
          height: calc(100% + var(--border-width));
          top: calc(0% - var(--border-width) / 2);
          left: calc(0% - var(--border-width) / 2);
          padding: var(--border-width);
          box-sizing: border-box;
          background: conic-gradient(
              from var(--angle-1) at 50% 50%,
              rgba(0, 0, 0, 0.5),
              rgba(0, 0, 0, 0) 5% 40%,
              rgba(0, 0, 0, 0.5) 50%,
              rgba(0, 0, 0, 0) 60% 95%,
              rgba(0, 0, 0, 0.5)
            ),
            linear-gradient(180deg, rgba(255, 255, 255, 0.6), rgba(255, 255, 255, 0.6));
          mask: linear-gradient(#000 0 0) content-box, linear-gradient(#000 0 0);
          mask-composite: exclude;
          transition: all 400ms cubic-bezier(0.25, 1, 0.5, 1),
            --angle-1 500ms ease;
          box-shadow: inset 0 0 0 calc(var(--border-width) / 2) rgba(255, 255, 255, 0.5);
        }}

        .knoll-btn:hover::after {{
          --angle-1: -125deg;
        }}

        .button-wrap:has(.knoll-btn:hover) .button-shadow {{
          filter: blur(clamp(2px, 0.0625em, 6px));
          -webkit-filter: blur(clamp(2px, 0.0625em, 6px));
        }}

        .button-wrap:has(.knoll-btn:hover) .button-shadow::after {{
          top: calc(var(--shadow-cuttoff-fix) - 0.875em);
          opacity: 1;
        }}

        /* Liquid Glass Cards */
        .glass-panel {{
            background: rgba(15, 23, 42, 0.55);
            backdrop-filter: blur(24px) saturate(190%);
            -webkit-backdrop-filter: blur(24px) saturate(190%);
            border: 1px solid rgba(255, 255, 255, 0.15);
            border-radius: 24px;
            box-shadow: 
                inset 0 1.5px 1px rgba(255, 255, 255, 0.35),
                inset 0 -1.5px 2px rgba(0, 0, 0, 0.4),
                0 20px 50px rgba(0, 0, 0, 0.4);
        }}

        /* Post Sidebar Item */
        .glass-post-item {{
            display: block;
            padding: 0.85rem 1.1rem;
            border-radius: 14px;
            background: rgba(255, 255, 255, 0.03);
            border: 1px solid rgba(255, 255, 255, 0.08);
            transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1);
            text-decoration: none;
            margin: 0;
        }}

        .glass-post-item:hover {{
            background: rgba(255, 255, 255, 0.09);
            border-color: rgba(255, 255, 255, 0.25);
            transform: translateX(4px);
        }}

        .glass-post-item.active {{
            background: linear-gradient(135deg, rgba(59, 130, 246, 0.2), rgba(139, 92, 246, 0.15));
            border-color: rgba(96, 165, 250, 0.4);
            box-shadow: inset 0 1px 1px rgba(255, 255, 255, 0.4);
        }}

        /* Typography & Post Content Styling */
        .prose-custom h1, .prose-custom h2, .prose-custom h3, .prose-custom h4 {{
            font-family: 'Outfit', sans-serif;
            color: #f8fafc !important;
            font-weight: 700 !important;
            letter-spacing: -0.02em;
            margin-top: 2rem !important;
            margin-bottom: 1rem !important;
        }}

        .prose-custom h1 {{ font-size: 2.25rem; line-height: 1.25; }}
        .prose-custom h2 {{ font-size: 1.65rem; line-height: 1.3; border-bottom: 1px solid rgba(255,255,255,0.12); padding-bottom: 0.5rem; color: #93c5fd !important; }}
        .prose-custom h3 {{ font-size: 1.35rem; color: #e0e7ff !important; }}

        .prose-custom p {{
            line-height: 1.8;
            color: #cbd5e1;
            margin-bottom: 1.25rem;
            font-size: 1.05rem;
        }}

        .prose-custom strong {{
            color: #ffffff !important;
            font-weight: 700;
        }}

        .prose-custom a {{
            color: #60a5fa;
            text-decoration: underline;
            text-underline-offset: 4px;
            transition: color 0.2s;
        }}

        .prose-custom a:hover {{
            color: #93c5fd;
        }}

        /* Force ALL content photos to identical full-container width */
        .prose-custom img {{
            border-radius: 18px;
            width: 100% !important;
            max-width: 100% !important;
            height: auto !important;
            display: block !important;
            margin: 2rem 0 !important;
            border: 1px solid rgba(255, 255, 255, 0.2);
            box-shadow: 0 15px 35px rgba(0, 0, 0, 0.35);
            transition: transform 0.3s ease, border-color 0.3s ease;
        }}

        /* Small Logos & Badges: Centered at ~25% width */
        .prose-custom img[src*="logo"], .prose-custom img[src*="300x300"], .prose-custom img.logo-img {{
            width: 25% !important;
            min-width: 150px !important;
            max-width: 250px !important;
            height: auto !important;
            margin: 2.5rem auto !important;
            display: block !important;
        }}

        .prose-custom img:hover {{
            transform: scale(1.01);
            border-color: rgba(255, 255, 255, 0.4);
        }}

        /* Explicit List & Bullet Point Styling */
        .prose-custom ul {{
            list-style-type: disc !important;
            padding-left: 2rem !important;
            margin-top: 1rem !important;
            margin-bottom: 1.5rem !important;
            display: block !important;
        }}

        .prose-custom ol {{
            list-style-type: decimal !important;
            padding-left: 2rem !important;
            margin-top: 1rem !important;
            margin-bottom: 1.5rem !important;
            display: block !important;
        }}

        .prose-custom li {{
            margin-bottom: 0.6rem !important;
            color: #cbd5e1 !important;
            display: list-item !important;
            line-height: 1.6 !important;
        }}
    </style>
</head>
<body class="antialiased text-slate-100 min-h-screen flex flex-col justify-between">

    <!-- Ambient Fluid Background Orbs -->
    <div class="ambient-bg">
        <div class="orb orb-1"></div>
        <div class="orb orb-2"></div>
        <div class="orb orb-3"></div>
    </div>

    <!-- Header Navigation -->
    <header class="sticky top-0 z-50 px-4 py-4 backdrop-blur-md bg-slate-950/40 border-b border-white/10">
        <div class="max-w-7xl mx-auto flex flex-wrap items-center justify-between gap-4">
            <a href="/index.html" class="flex items-center gap-3 group text-decoration-none">
                <div class="relative w-10 h-10 rounded-2xl bg-slate-900/80 flex items-center justify-center shadow-lg shadow-blue-500/20 border border-white/30 group-hover:scale-105 transition-transform overflow-hidden">
                    <canvas id="hexLogoCanvas" width="80" height="80" class="w-10 h-10"></canvas>
                </div>
                <div>
                    <div class="font-bold text-lg leading-none tracking-tight text-white font-['Outfit']">BFMG</div>
                    <div class="text-xs text-blue-200/70 font-medium tracking-wide">British Federation of Mathematical Games</div>
                </div>
            </a>

            <!-- Liquid Glass Top Nav Buttons -->
            <nav class="flex flex-wrap items-center gap-2">
                {pages_nav_html}
            </nav>
        </div>
    </header>

    <!-- Main Workspace Container -->
    <main class="max-w-7xl mx-auto px-4 py-8 flex-1 w-full">
        <div class="grid grid-cols-1 lg:grid-cols-12 gap-8">

            <!-- Content Area (Left/Main 8 cols) -->
            <section class="lg:col-span-8">
                <article class="glass-panel p-6 sm:p-10">
                    
                    <header class="mb-8 border-b border-white/10 pb-6">
                        <div class="flex items-center gap-2 mb-3">
                            <span class="px-3 py-1 rounded-full text-xs font-semibold bg-blue-500/20 text-blue-300 border border-blue-400/30 flex items-center gap-1.5">
                                <i data-lucide="{ 'book-open' if is_post else 'layout' }" class="w-3.5 h-3.5"></i>
                                { 'Post Entry' if is_post else 'Official Page' }
                            </span>
                            { f'<span class="text-xs text-slate-400 font-mono flex items-center gap-1"><i data-lucide="clock" class="w-3.5 h-3.5"></i> {current_item["formatted_date"]}</span>' if current_item["formatted_date"] else '' }
                        </div>
                        <h1 class="text-3xl sm:text-4xl font-extrabold text-white font-['Outfit'] tracking-tight leading-tight">
                            {current_item['title']}
                        </h1>
                    </header>

                    <div class="prose-custom">
                        {item_content}
                    </div>

                </article>
            </section>

            <!-- Sidebar Navigation Tree (Right 4 cols) -->
            <aside class="lg:col-span-4 space-y-6">
                
                <!-- Recent Posts Sidebar List (Last 12 Posts) -->
                <div class="glass-panel p-6">
                    <div class="flex items-center justify-between mb-4 pb-3 border-b border-white/10">
                        <h3 class="font-bold text-base text-white font-['Outfit'] flex items-center gap-2">
                            <i data-lucide="history" class="w-4 h-4 text-blue-400"></i>
                            Recent Posts
                        </h3>
                        <span class="text-xs font-mono px-2 py-0.5 rounded bg-blue-500/20 text-blue-300 border border-blue-400/20">
                            {len(recent_posts)} Recent
                        </span>
                    </div>

                    <div class="flex flex-col gap-2.5">
                        {posts_nav_html}
                    </div>
                </div>

                <!-- Page Directory -->
                <div class="glass-panel p-6">
                    <h3 class="font-bold text-base text-white font-['Outfit'] mb-4 pb-3 border-b border-white/10 flex items-center gap-2">
                        <i data-lucide="folder-tree" class="w-4 h-4 text-indigo-400"></i>
                        Site Pages Directory
                    </h3>
                    <div class="space-y-2">
                        {"".join([f'<a href="{("/index.html") if (page["slug"] == "home" or page["title"].lower() in ["home", "about bfmg", "about"]) else ("/pages/" + page["slug"] + ".html")}" class="flex items-center justify-between p-2.5 rounded-xl bg-white/5 border border-white/10 text-sm text-slate-200 hover:bg-white/10 hover:text-white transition-all"><span class="flex items-center gap-2"><i data-lucide="file-text" class="w-4 h-4 text-blue-300"></i> {page["title"]}</span><i data-lucide="chevron-right" class="w-4 h-4 opacity-50"></i></a>' for page in pages])}
                    </div>
                </div>

            </aside>

        </div>
    </main>

    <!-- Footer -->
    <footer class="mt-12 py-8 border-t border-white/10 backdrop-blur-md bg-slate-950/60 text-center text-slate-400 text-sm">
        <div class="max-w-7xl mx-auto px-4 flex flex-col md:flex-row items-center justify-between gap-4">
            <div class="flex items-center gap-2 font-medium text-slate-300">
                <div class="w-6 h-6 rounded-lg bg-blue-600/40 border border-blue-400/30 flex items-center justify-center">
                    <i data-lucide="sparkles" class="w-3.5 h-3.5 text-blue-300"></i>
                </div>
                <span>British Federation of Mathematical Games</span>
            </div>
            <div class="flex items-center justify-center">
                <a href="https://forms.office.com/e/6XyWriHgHT" target="_blank" rel="noopener" class="text-blue-400 hover:text-blue-300 transition-colors flex items-center gap-1.5 font-medium px-4 py-1.5 rounded-full bg-blue-500/10 border border-blue-400/20 shadow-sm">
                    <i data-lucide="mail" class="w-3.5 h-3.5"></i>
                    Contact BFMG
                </a>
            </div>
            <div class="text-xs text-slate-500 font-mono">
                Ported & Rendered with Liquid Glass UI
            </div>
        </div>
    </footer>

    <script>
        lucide.createIcons();

        // Animated Hexflake Logo Canvas Renderer
        (function() {{
            const canvas = document.getElementById('hexLogoCanvas');
            if (!canvas) return;
            const ctx = canvas.getContext('2d');
            let angle = 0;

            function getHexPoints(x, y, radius) {{
                const points = [];
                for (let i = 0; i < 6; i++) {{
                    const a = (Math.PI / 3) * i + (Math.PI / 6);
                    points.push({{ x: x + radius * Math.cos(a), y: y + radius * Math.sin(a) }});
                }}
                return points;
            }}

            function drawHexagon(context, x, y, radius) {{
                const pts = getHexPoints(x, y, radius);
                context.beginPath();
                context.moveTo(pts[0].x, pts[0].y);
                for (let i = 1; i < 6; i++) context.lineTo(pts[i].x, pts[i].y);
                context.closePath();
                context.stroke();
            }}

            function drawHexflake(context, x, y, radius, depth) {{
                if (radius < 0.5) return;
                if (depth === 0) {{
                    drawHexagon(context, x, y, radius);
                    return;
                }}
                const newRadius = radius / 3;
                for (let i = 0; i < 6; i++) {{
                    const a = (Math.PI / 3) * i + (Math.PI / 6);
                    const nx = x + (radius * 2 / 3) * Math.cos(a);
                    const ny = y + (radius * 2 / 3) * Math.sin(a);
                    drawHexflake(context, nx, ny, newRadius, depth - 1);
                }}
            }}

            function animate() {{
                ctx.clearRect(0, 0, 80, 80);
                ctx.save();
                ctx.translate(40, 40);
                ctx.rotate(angle);
                ctx.strokeStyle = '#60a5fa';
                ctx.lineWidth = 1.2;
                drawHexflake(ctx, 0, 0, 32, 2);
                ctx.restore();
                angle += 0.008;
                requestAnimationFrame(animate);
            }}
            animate();
        }})();
    </script>
</body>
</html>
'''
    return html_str

print("Generating Pages...")
for p in pages:
    is_p_home = (p['slug'] == 'home' or p['title'].lower() in ['home', 'about bfmg', 'about'])
    if is_p_home:
        out_path = out_base / 'index.html'
        print(f"Writing Home Page: {out_path}")
        with open(out_path, 'w', encoding='utf-8') as f:
            f.write(build_page_html(p, is_post=False, is_home=True))
    else:
        out_path = pages_out / f"{p['slug']}.html"
        print(f"Writing Page: {out_path}")
        with open(out_path, 'w', encoding='utf-8') as f:
            f.write(build_page_html(p, is_post=False, is_home=False))

print("Generating Posts...")
for p in posts:
    file_name = f"{p['slug']}.html"
    out_path = posts_out / file_name
    print(f"Writing Post: {out_path}")
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(build_page_html(p, is_post=True, is_home=False))

print("Site Generation Finished Successfully!")
