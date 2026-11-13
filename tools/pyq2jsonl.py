#!/usr/bin/env python3
"""Convert the verified GATE GA previous-year questions (research/*.md) into bank/PYQ.jsonl.

Sources: Notes/_tools/GA_src/research/{recent_ga,classic_ga,da_ga}.md
Figures: only Notes/_tools/GA_src/img/pyq/*.png (copied to site/img/pyq/).
Run:  tools/.venv/bin/python -I tools/pyq2jsonl.py [--list]
"""
import html, json, os, re, shutil, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, '..', '..', 'Notes', '_tools', 'GA_src')
SRC = os.path.normpath(SRC)
RES = os.path.join(SRC, 'research')
IMG = os.path.join(SRC, 'img', 'pyq')
OUT_IMG = os.path.join(ROOT, 'site', 'img', 'pyq')
OUT = os.path.join(ROOT, 'bank', 'PYQ.jsonl')
STATUS = os.path.join(ROOT, 'status', 'PYQ.txt')

EXCLUDE = {'R3': 'duplicate of classic 10.3.1', 'R38': 'duplicate of classic 11.15.1',
           'R101': 'duplicate of classic 10.4.3'}
SECTION = {'A': 'Verbal', 'B': 'Quant', 'C': 'Analytical', 'D': 'Spatial'}

# ----------------------------------------------------------------------------------------
# topic mapping: (file, sub-section) -> canonical topic; per-entry overrides below
SUB_TOPIC = {
    'recent': {
        'A1': 'Grammar', 'A2': 'Grammar', 'A3': 'Grammar', 'A4': 'Grammar', 'A5': 'Grammar', 'A6': 'Grammar',
        'A7': 'Grammar', 'A8': 'Vocabulary', 'A9': 'Vocabulary', 'A10': 'Reading Comprehension',
        'A11': 'Sentence Ordering',
        'B1': 'Data Interpretation', 'B2': 'Data Interpretation', 'B3': 'Data Interpretation',
        'B4': 'Data Interpretation', 'B5': 'Data Interpretation', 'B6': 'Ratio, Proportion & Mixtures',
        'B7': 'Percentages', 'B8': 'Powers & Logarithms', 'B9': 'Powers & Logarithms',
        'B10': 'Permutations & Combinations', 'B11': 'Series & Progressions', 'B12': 'Numerical Estimation',
        'B13': 'Geometry', 'B14': 'Statistics', 'B15': 'Probability',
        'C1': 'Syllogisms', 'C2': 'Logical Deduction', 'C3': 'Series & Patterns', 'C4': 'Series & Patterns',
        'C5': 'Puzzles', 'C6': 'Coding-Decoding', 'C7': 'Clocks & Calendars', 'C8': 'Puzzles',
        'D1': 'Transformations', 'D2': 'Mirror & Rotation', 'D3': 'Paper Folding & Cutting',
        'D4': 'Patterns & Projections', 'D5': 'Patterns & Projections',
    },
    'classic': {
        'A1': 'Vocabulary', 'A2': 'Vocabulary', 'A3': 'Vocabulary', 'A4': 'Word Analogy', 'A5': 'Vocabulary',
        'A6': 'Grammar', 'A7': 'Grammar', 'A8': 'Grammar', 'A9': 'Grammar', 'A10': 'Grammar', 'A11': 'Grammar',
        'A12': 'Reading Comprehension', 'A13': 'Verbal Reasoning', 'A14': 'Sentence Ordering',
        'B1': 'Number System', 'B2': 'Number System', 'B3': 'Number System', 'B4': 'Number System',
        'B5': 'Powers & Logarithms', 'B6': 'Ratio, Proportion & Mixtures', 'B7': 'Percentages',
        'B8': 'Profit, Loss & Interest', 'B9': 'Profit, Loss & Interest', 'B10': 'Ratio, Proportion & Mixtures',
        'B11': 'Averages', 'B12': 'Time & Work', 'B13': 'Speed, Time & Distance', 'B14': 'Clocks & Calendars',
        'B15': 'Algebra & Functions', 'B16': 'Algebra & Functions', 'B17': 'Series & Progressions',
        'B18': 'Permutations & Combinations', 'B19': 'Probability', 'B20': 'Statistics', 'B21': 'Geometry',
        'B22': 'Mensuration', 'B23': 'Data Interpretation', 'B24': 'Puzzles', 'B25': 'Algebra & Functions',
        'C1': 'Logical Deduction', 'C2': 'Syllogisms', 'C3': 'Coding-Decoding', 'C4': 'Directions',
        'C5': 'Blood Relations', 'C6': 'Arrangements', 'C7': 'Series & Patterns', 'C8': 'Series & Patterns',
        'C9': 'Puzzles',
        'D1': 'Counting Figures', 'D2': 'Patterns & Projections', 'D3': 'Paper Folding & Cutting',
        'D4': 'Mirror & Rotation', 'D5': 'Mirror & Rotation', 'D6': 'Patterns & Projections',
    },
}
TOPIC_SECTION = {}
for _s, _ts in {'Quant': 'Number System|Powers & Logarithms|Series & Progressions|Algebra & Functions|Percentages|'
                         'Profit, Loss & Interest|Ratio, Proportion & Mixtures|Averages|Speed, Time & Distance|'
                         'Time & Work|Permutations & Combinations|Probability|Statistics|Geometry|Mensuration|'
                         'Data Interpretation|Numerical Estimation',
                'Verbal': 'Grammar|Vocabulary|Word Analogy|Reading Comprehension|Verbal Reasoning|Sentence Ordering',
                'Analytical': 'Logical Deduction|Syllogisms|Arrangements|Directions|Blood Relations|Coding-Decoding|'
                              'Series & Patterns|Clocks & Calendars|Puzzles',
                'Spatial': 'Cubes & Dice|Paper Folding & Cutting|Mirror & Rotation|Counting Figures|'
                           'Patterns & Projections|Transformations'}.items():
    for _t in _ts.split('|'):
        TOPIC_SECTION[_t] = _s

# per-entry overrides: id -> topic (section follows from the topic)
TOPIC_OVR = {
    # recent
    'R131': 'Word Analogy', 'R57': 'Profit, Loss & Interest', 'R193': 'Profit, Loss & Interest',
    'R137': 'Mensuration', 'R159': 'Mensuration', 'R189': 'Mensuration',
    'R7': 'Word Analogy', 'R96': 'Word Analogy',
    'R17': 'Arrangements', 'R162': 'Arrangements', 'R119': 'Logical Deduction', 'R64': 'Blood Relations',
    'R275': 'Arrangements',
    'R139': 'Mirror & Rotation',
    'R50': 'Mirror & Rotation', 'R301': 'Mirror & Rotation', 'R345': 'Mirror & Rotation',
    'R59': 'Cubes & Dice', 'R74': 'Cubes & Dice', 'R184': 'Counting Figures', 'R125': 'Counting Figures',
    'R114': 'Counting Figures',
    # classic
    '11.17.1': 'Verbal Reasoning', '9.17.3': 'Averages',
    '8.5.13': 'Arrangements', '8.5.11': 'Puzzles', '8.12.15': 'Logical Deduction',
    '9.32.16': 'Counting Figures', '9.32.3': 'Cubes & Dice', '10.4.3': 'Mirror & Rotation',
}
# per-entry difficulty overrides
DIFF_OVR = {}
# DA entries: id -> topic
DA_TOPIC = {
    'DA2024-Q1': 'Word Analogy', 'DA2024-Q2': 'Puzzles', 'DA2024-Q3': 'Permutations & Combinations',
    'DA2024-Q4': 'Series & Progressions', 'DA2024-Q5': 'Data Interpretation', 'DA2024-Q6': 'Reading Comprehension',
    'DA2024-Q7': 'Probability', 'DA2024-Q8': 'Percentages', 'DA2024-Q9': 'Cubes & Dice',
    'DA2024-Q10': 'Patterns & Projections',
    'DA2025-Q1': 'Word Analogy', 'DA2025-Q2': 'Grammar', 'DA2025-Q3': 'Data Interpretation', 'DA2025-Q4': 'Puzzles',
    'DA2025-Q5': 'Percentages', 'DA2025-Q6': 'Vocabulary', 'DA2025-Q7': 'Logical Deduction',
    'DA2025-Q8': 'Patterns & Projections', 'DA2025-Q9': 'Powers & Logarithms', 'DA2025-Q10': 'Data Interpretation',
    'DA2026-Q1': 'Word Analogy', 'DA2026-Q2': 'Number System', 'DA2026-Q3': 'Patterns & Projections',
    'DA2026-Q4': 'Powers & Logarithms', 'DA2026-Q5': 'Verbal Reasoning', 'DA2026-Q6': 'Grammar',
    'DA2026-Q7': 'Statistics', 'DA2026-Q8': 'Puzzles', 'DA2026-Q9': 'Puzzles', 'DA2026-Q10': 'Geometry',
}

# ----------------------------------------------------------------------------------------
# text conversion

SUPMAP = str.maketrans('⁰¹²³⁴⁵⁶⁷⁸⁹⁻', '0123456789-')
SUBMAP = str.maketrans('₀₁₂₃₄₅₆₇₈₉', '0123456789')


def tex_inner(s):
    """plain/unicode math text -> KaTeX source."""
    s = re.sub(r'#(\w+)', r'\\text{\\#\1}', s).replace('−', '-').replace('×', r'\times ').replace('·', r'\cdot ').replace('√', r'\sqrt ')
    s = re.sub(r'([⁰¹²³⁴⁵⁶⁷⁸⁹⁻]+)', lambda m: '^{' + m.group(1).translate(SUPMAP) + '}', s)
    s = re.sub(r'log([₀₁₂₃₄₅₆₇₈₉]+)', lambda m: r'\log_{' + m.group(1).translate(SUBMAP) + '}', s)
    s = re.sub(r'(?<!\\)\blog\b', r'\\log', s)
    return s


def balanced(s, i):
    """s[i] == '(' or '{' -> index of the matching close bracket."""
    o = s[i]; c = {'(': ')', '{': '}'}[o]; d = 0
    for j in range(i, len(s)):
        if s[j] == o: d += 1
        elif s[j] == c:
            d -= 1
            if d == 0: return j
    raise ValueError(s)


def powers_to_tex(s):
    """a^(b), a^{b}, a^b  ->  $a^{b}$  (base: number/word or a parenthesised group)."""
    out, i = [], 0
    while True:
        k = s.find('^', i)
        if k < 0:
            out.append(s[i:]); break
        # base
        j = k
        if j > 0 and s[j - 1] == ')':
            d = 0
            while True:
                j -= 1
                d += {')': 1, '(': -1}.get(s[j], 0)
                if d == 0: break
            # allow a function-ish word before the bracket?  (not needed)
        else:
            while j > 0 and re.match(r'[A-Za-z0-9.]', s[j - 1]): j -= 1
        base = s[j:k]
        # exponent
        if k + 1 < len(s) and s[k + 1] in '({':
            e_end = balanced(s, k + 1)
            exp = s[k + 2:e_end]; nxt = e_end + 1
        else:
            m = re.match(r'[A-Za-z0-9]+', s[k + 1:])
            exp = m.group(0); nxt = k + 1 + len(exp)
        # absorb an immediately following unicode square, e.g. (2^x)²
        m2 = re.match(r'[⁰¹²³⁴⁵⁶⁷⁸⁹]+', s[nxt:])
        tail = ''
        if m2:
            tail = '^{' + m2.group(0).translate(SUPMAP) + '}'; nxt += len(m2.group(0))
        prefix = s[i:j]
        # merge with a previous math chunk directly adjacent (e.g. 3^{999}×7^{1000})
        if out and out[-1].endswith('$') and re.fullmatch(r'\s*[×·+−\-/]\s*', prefix):
            out[-1] = out[-1][:-1] + tex_inner(prefix) + tex_inner(base) + '^{' + tex_inner(exp) + '}' + tail + '$'
        else:
            out.append(prefix)
            out.append('$' + tex_inner(base) + '^{' + tex_inner(exp) + '}' + tail + '$')
        i = nxt
    return ''.join(out)


def inline(s):
    s = html.escape(s, quote=False)
    s = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', s)
    s = re.sub(r'(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])', r'<i>\1</i>', s)
    s = re.sub(r'`([^`]+)`', r'\1', s)
    s = re.sub(r'(\d+)\((\d+)\)/\((\d+)\)', r'$\1\\frac{\2}{\3}$', s)   # 64(6)/(11) -> 64 6/11
    s = re.sub(r'\((\d+)\)/\((\d+)\)', r'$\\frac{\1}{\2}$', s)            # (1)/(3) -> 1/3
    if '^' in s:
        s = powers_to_tex(s)
        s = re.sub(r'\$(\d+\^\{\d+\})\$([+−])(\d+)\b', lambda m: '$' + m.group(1) + m.group(2).replace('−', '-') + m.group(3) + '$', s)
    parts = re.split(r'(\$[^$]*\$)', s)
    for k in range(0, len(parts), 2):
        t = parts[k]
        t = re.sub(r'\blog_\{([^{}]+)\}', r'$\\log_{\1}$', t)
        t = re.sub(r'\blog_([A-Za-z0-9]+)', r'$\\log_{\1}$', t)
        parts[k] = t
    parts = re.split(r'(\$[^$]*\$)', ''.join(parts))
    for k in range(0, len(parts), 2):
        t = parts[k]
        t = re.sub(r'\bL_(train|platform)\b', r'$L_{\\text{\1}}$', t)
        t = re.sub(r'(?<![A-Za-z])([A-Za-z])_\{([^{}]+)\}', r'$\1_{\2}$', t)
        t = re.sub(r'(?<![A-Za-z])([A-Za-z])_([A-Za-z0-9]+)\b', r'$\1_{\2}$', t)
        parts[k] = t
    return ''.join(parts)


def blocks(lines, drop_code=False):
    """markdown-ish lines -> html (paragraphs joined by <br>, bullets, tables, code fences)."""
    out, i, para = [], 0, []

    def flush():
        if para:
            out.append('<br>'.join(inline(p.strip()) for p in para))
            para.clear()
    while i < len(lines):
        l = lines[i]
        if l.strip().startswith('```'):
            flush(); j = i + 1; code = []
            while not lines[j].strip().startswith('```'):
                code.append(lines[j]); j += 1
            if not drop_code:
                out.append(code_block(code))
            i = j + 1; continue
        if l.strip().startswith('|'):
            flush(); rows = []
            while i < len(lines) and lines[i].strip().startswith('|'):
                cells = [c.strip() for c in lines[i].strip().strip('|').split('|')]
                if not all(re.fullmatch(r':?-+:?', c) for c in cells):
                    rows.append(cells)
                i += 1
            head = rows[0]
            t = '<table>' + ''.join(
                '<tr>' + ''.join(f'<{"th" if r == 0 else "td"}>{inline(c)}</{"th" if r == 0 else "td"}>' for c in row) + '</tr>'
                for r, row in enumerate(rows)) + '</table>'
            out.append(t); continue
        m = re.match(r'^(\s*)([-*]|\d+\.) (.*)', l)
        if m:
            flush(); items = []
            while i < len(lines):
                m = re.match(r'^(\s*)([-*]|\d+\.) (.*)', lines[i])
                if lines[i].strip().startswith(('|', '```')):
                    break
                if not m:
                    if lines[i].strip() and lines[i].startswith('   ') and items:
                        items[-1] += ' ' + lines[i].strip(); i += 1; continue
                    break
                ind = len(m.group(1)); mark = m.group(2); txt = m.group(3)
                if mark[0].isdigit():
                    items.append((ind, mark + ' ' + txt))
                else:
                    items.append((ind, ('• ' if ind == 0 else '– ') + txt))
                i += 1
            out.append('<br>'.join(('&nbsp;&nbsp;&nbsp;' if ind else '') + inline(t) for ind, t in items))
            continue
        if not l.strip():
            flush(); i += 1; continue
        para.append(l); i += 1
    flush()
    return '<br>'.join(x for x in out if x)


def code_block(code):
    """a fenced block (grids, nets) -> monospace table-free rendering."""
    txt = '\n'.join(code)
    return '<span style="font-family:monospace;white-space:pre">' + html.escape(txt, quote=False).replace('\n', '<br>') + '</span>'


OPT_RE = re.compile(r'(?:^|(?<=\s\s)|(?<=\n))([A-D])\.\s+')


def parse_opts(text):
    parts = OPT_RE.split(text.strip())
    assert parts[0].strip() == '', (parts[0], text)
    opts = [(parts[k], parts[k + 1].strip()) for k in range(1, len(parts), 2)]
    assert [o[0] for o in opts] == list('ABCD'), text
    return [o[1] for o in opts]


def opt_html(o):
    return '<br>'.join(inline(x.strip()) for x in o.split('\n') if x.strip())


# ----------------------------------------------------------------------------------------
# figures

used_imgs = []


def img(name):
    p = os.path.join(IMG, name)
    if os.path.exists(p):
        used_imgs.append(name)
        return 'img/pyq/' + name
    return None


def combine(names, out_name):
    """stack the question figure above the options figure into one PNG."""
    from PIL import Image
    ims = [Image.open(os.path.join(IMG, n)).convert('RGBA') for n in names]
    w = max(i.size[0] for i in ims); gap = 24
    h = sum(i.size[1] for i in ims) + gap * (len(ims) - 1)
    canvas = Image.new('RGBA', (w, h), (255, 255, 255, 255))
    y = 0
    for im in ims:
        bg = Image.new('RGBA', im.size, (255, 255, 255, 255)); bg.alpha_composite(im)
        canvas.paste(bg, ((w - im.size[0]) // 2, y)); y += im.size[1] + gap
    os.makedirs(OUT_IMG, exist_ok=True)
    canvas.convert('RGB').save(os.path.join(OUT_IMG, out_name))
    return 'img/pyq/' + out_name


# ----------------------------------------------------------------------------------------
# parsing: recent_ga.md / classic_ga.md

def split_entries(name):
    t = open(os.path.join(RES, f'{name}_ga.md'), encoding='utf-8').read()
    body = t[t.index('## A. VERBAL'):]
    body = body[:body.index('\n## E. Dropped')]
    chunks = re.split(r'\n(?=## [A-D]\. |### [A-D]\d+\. |### \d|### R\d)', '\n' + body)
    sec = sub = subtitle = None
    for c in chunks:
        c = c.strip('\n')
        if not c: continue
        g = re.match(r'## ([A-D])\. ', c)
        if g: sec = g.group(1); continue
        s = re.match(r'### ([A-D]\d+)\. (.*)', c)
        if s: sub, subtitle = s.group(1), s.group(2).split('\n')[0]; continue
        if c.startswith('### '):
            yield sec, sub, subtitle, c


def parse_entry(kind, sec, sub, subtitle, e):
    pre_ = kind
    lines = e.rstrip('\n').split('\n')
    m = re.match(r'### (R\d+|\d+(?:\.\d+)+)\. (GATE .*)$', lines[0])
    assert m, lines[0]
    gid, rest = m.groups()
    rest = rest.replace('[post-2020]', '').strip()
    parts = [p.strip() for p in rest.split('·')]
    marks = int(re.match(r'(\d)', next(p for p in parts if 'mark' in p)).group(1))
    typ = next(p for p in parts[1:] if re.match(r'(MCQ|NAT|MSQ)', p)).split()[0]
    if kind == 'recent':
        # "GATE 2025 ECE Q2" / "GATE 2026 ME Q9; CE Set 2 Q9"
        papers = [p.strip() for p in parts[0].split(';')]
        m0 = re.match(r'(GATE \d{4} .*?) (Q\d+)$', papers[0])
        source = f'{m0.group(1)} · {m0.group(2)}'
        if len(papers) > 1:
            source += ' (also ' + '; '.join(papers[1:]) + ')'
    else:
        qn = next((p for p in parts[1:] if re.fullmatch(r'Q\d+', p)), None)
        source = parts[0] + (f' · {qn}' if qn else '')
    txt = '\n'.join(lines[1:])
    ans_m = re.search(r'\*\*Answer \((?:GO |official )?key\): (.+?)\*\*', txt)
    key = ans_m.group(1).strip()
    pre, post = txt[:ans_m.start()], txt[ans_m.end():]
    sol_m = re.search(r'\*\*Solution\.\*\*(.*?)(?=\*\*Trap/pattern\.\*\*|\nVerified:|\Z)', post, re.S)
    trap_m = re.search(r'\*\*Trap/pattern\.\*\*(.*?)(?=\nVerified:|\Z)', post, re.S)
    sol = sol_m.group(1).strip() if sol_m else ''
    trap = trap_m.group(1).strip() if trap_m else ''
    fig_ref = bool(re.search(r'Figure: figs/|^\**Figure data|^Figure \(', pre, re.M))
    main = os.path.exists(os.path.join(IMG, f'{pre_}_{gid}.png'))
    optimg = os.path.exists(os.path.join(IMG, f'{pre_}_{gid}_opts.png'))
    q_lines, opt_text, fig_data = [], None, []
    pl = pre.split('\n'); i = 0
    while i < len(pl):
        l = pl[i]
        if l.startswith('Source checked') or l.startswith('Figure: ') or l.startswith('Key source'):
            i += 1; continue
        if l.startswith('Figure data') or l.startswith('Options (') or l.startswith('**Figure data'):
            j = i
            while j < len(pl) and pl[j].strip() and not re.match(r'^A\. ', pl[j]):
                fig_data.append(pl[j]); j += 1
            i = j; continue
        if re.match(r'^A\. ', l):
            j = i; buf = []
            while j < len(pl) and not pl[j].startswith('**') and not pl[j].startswith('Figure data') \
                    and not pl[j].startswith('Options ('):
                if pl[j].strip(): buf.append(pl[j])
                j += 1
            opt_text = '\n'.join(buf); i = j; continue
        q_lines.append(l); i += 1
    while q_lines and not q_lines[-1].strip(): q_lines.pop()
    while q_lines and not q_lines[0].strip(): q_lines.pop(0)
    fig_opts = optimg or opt_text is None or '(as described)' in (opt_text or '') or '(figure option' in (opt_text or '')
    opts = None if fig_opts else parse_opts(opt_text)
    return dict(gid=gid, kind=kind, sec=sec, sub=sub, subtitle=subtitle, marks=marks, type=typ, source=source,
                key=key, q_lines=q_lines, opts=opts, fig_opts=fig_opts, fig_ref=fig_ref, main=main, optimg=optimg,
                fig_data=fig_data, sol=sol, trap=trap)


# ----------------------------------------------------------------------------------------
# parsing: da_ga.md

def da_entries():
    t = open(os.path.join(RES, 'da_ga.md'), encoding='utf-8').read()
    summ = {f'DA{y}-Q{q}': k for y, q, k in re.findall(r'^\| (20\d\d) \| (\d+) \|.*\| ([A-D]) \|$', t, re.M)}
    assert len(summ) == 30
    t = t[:t.index('## Summary table')]
    for c in re.split(r'\n(?=### DA20)', t)[1:]:
        c = c.split('\n---')[0].strip('\n')
        lines = c.split('\n')
        m = re.match(r'### DA(\d{4}) Q(\d+) — (.*?) — (MCQ|NAT|MSQ), (\d) marks?', lines[0])
        assert m, lines[0]
        year, qn, title, typ, marks = m.groups()
        body = '\n'.join(lines[1:])
        km = re.search(r'\*\*Official answer:\*\* ([A-D])', body)
        key = summ[f'DA{year}-Q{qn}']
        if km: assert km.group(1) == key, (year, qn)
        cut = km.start() if km else body.index('**Solution.**')
        qpart, post = body[:cut], body[cut:]
        sol = re.search(r'\*\*Solution\.\*\*(.*?)(?=\*\*Concept / trap\.\*\*)', post, re.S).group(1).strip()
        trap = re.search(r'\*\*Concept / trap\.\*\*(.*?)(?=\*\*Verified:?\*\*|\Z)', post, re.S).group(1).strip()
        # figure block
        figname = f'da{year}_q{qn}.png'
        fm = re.search(r'\n\*\*Figure \(.*', qpart, re.S)
        fig_block = ''
        if fm:
            fig_block = fm.group(0); qpart = qpart[:fm.start()]
        qpart = qpart.replace('**Question.**', '').strip()
        # options: from the first line starting with (A)
        ql = qpart.split('\n')
        k = next(i for i, l in enumerate(ql) if l.startswith('(A)'))
        q_lines, opt_lines = ql[:k], [l for l in ql[k:] if l.strip()]
        opt_text = '\n'.join(opt_lines)
        if opt_text.startswith('(A)/(B)'):
            opts = None
        else:
            ps = re.split(r'(?:^|\s|\n)\(([A-D])\)\s', opt_text)
            assert ps[0].strip() == '' and ps[1::2] == list('ABCD'), opt_text
            opts = [x.strip() for x in ps[2::2]]
        while q_lines and not q_lines[-1].strip(): q_lines.pop()
        yield dict(gid=f'DA{year}-Q{qn}', kind='da', sec=None, sub=title, subtitle=title, marks=int(marks), type=typ,
                   source=f'GATE DA {year} · Q{qn}', key=key, q_lines=q_lines, opts=opts, fig_opts=opts is None,
                   fig_ref=bool(fm), main=os.path.exists(os.path.join(IMG, figname)), optimg=False,
                   fig_data=fig_block.split('\n'), sol=sol, trap=trap, figname=figname)


def all_entries():
    out = []
    for kind in ('recent', 'classic'):
        for sec, sub, subtitle, c in split_entries(kind):
            e = parse_entry(kind, sec, sub, subtitle, c)
            out.append(e)
    out += list(da_entries())
    return out


if __name__ == '__main__' and '--list' in sys.argv:
    for e in all_entries():
        stem = ' '.join(e['q_lines'])[:90]
        print(f"{e['gid']:10} {e['kind'][:2]} {str(e['sub'])[:28]:28} {e['marks']} {e['type']} key={e['key']:4} "
              f"fig={'F' if e['fig_ref'] else '-'}{'M' if e['main'] else '-'}{'O' if e['optimg'] else '-'}"
              f"{'L' if e['fig_opts'] else '-'} | {stem}")
    sys.exit()


# ----------------------------------------------------------------------------------------
# build

def subtopic(e):
    t = e['subtitle']
    if e['kind'] == 'da':
        t = t.split('/', 1)[1].strip() if '/' in t else t
    else:
        t = re.sub(r'\s*\[post-2020\]', '', t)
        t = t.split(' — ', 1)[1] if ' — ' in t else t
    return t.strip()


def difficulty(e, sol_len):
    if e['gid'] in DIFF_OVR: return DIFF_OVR[e['gid']]
    if e['marks'] == 1:
        return 1 if sol_len < 420 else 2
    return 2 if sol_len < 700 else 3


GRIDS = {}
# typeset a few unicode-math stems in KaTeX (applied to the converted HTML)
STEM_FIX = {
    'R134': [('x&gt;1 ,<br>1/log₂x + 1/log₃x + 1/log₄x = 1<br>',
              'x &gt; 1,$$\\frac{1}{\\log_2 x}+\\frac{1}{\\log_3 x}+\\frac{1}{\\log_4 x}=1$$')],
    'DA2025-Q9': [('$3^{x^{2}}$ = 27 × $9^{x}$', '$3^{x^{2}} = 27 \\times 9^{x}$'),
                  ('$2^{x^{2}}$ / ($2^{x}$)²', '$\\dfrac{2^{x^{2}}}{(2^{x})^{2}}$')],
}
SOL_FIX = {'DA2024-Q9': ('; the code checks this', '')}


def q_special(e, q_lines):
    """entry-specific stem fixes (figure transcriptions kept as text)."""
    if e['gid'] == '8.5.28':
        out, i = [], 0
        while i < len(q_lines):
            l = q_lines[i]
            if l.startswith('Figure (3×3 grid'):
                i += 1; continue
            if l.strip().startswith('```'):
                j = i + 1; rows = []
                while not q_lines[j].strip().startswith('```'):
                    rows.append(q_lines[j].split()); j += 1
                GRIDS[e['gid']] = ('<table>' + ''.join('<tr>' + ''.join(f'<td>{"" if c == "." else c}</td>' for c in r) + '</tr>'
                                               for r in rows) + '</table>')
                out.append('@@GRID@@')
                i = j + 1; continue
            out.append(l); i += 1
        return out
    return q_lines


def build(e):
    gid = e['gid']
    if e['kind'] == 'da':
        qid = 'PYQ-' + gid
        topic = DA_TOPIC[gid]
    else:
        qid = ('PYQ-' if e['kind'] == 'recent' else 'PYQ-C') + gid
        topic = TOPIC_OVR.get(gid) or SUB_TOPIC[e['kind']][e['sub']]
    section = TOPIC_SECTION[topic]
    q_lines = q_special(e, e['q_lines'])
    qh = blocks(q_lines)
    for a, b in STEM_FIX.get(gid, []):
        assert a in qh, (gid, a); qh = qh.replace(a, b)
    if gid in GRIDS:
        qh = qh.replace('<br>@@GRID@@', '@@GRID@@').replace('@@GRID@@', GRIDS[gid])
    q = {'id': qid, 'section': section, 'topic': topic, 'subtopic': subtopic(e)}
    # figure
    fig = None
    if e['kind'] == 'da':
        if e['main']:
            fig = img(e['figname'])
    else:
        pre_ = e['kind']
        names = [n for n, ok in ((f'{pre_}_{gid}.png', e['main']), (f'{pre_}_{gid}_opts.png', e['optimg'])) if ok]
        if len(names) == 2:
            for n in names: used_imgs.append(n)
            fig = combine(names, f'{pre_}_{gid}_full.png')
        elif names:
            fig = img(names[0])
    if e['fig_ref'] and not fig and gid != '8.5.28':
        return None, 'figure needed but not available in img/pyq'
    typ = e['type']
    if typ == 'NAT':
        v = float(e['key']); v = int(v) if v.is_integer() else v
        answer = {'min': v, 'max': v}; options = None
    else:
        assert re.fullmatch(r'[A-D]', e['key']), (gid, e['key'])
        answer = e['key']
        if e['fig_opts']:
            options = ['A', 'B', 'C', 'D']
            qh += '<br><i>Options are labelled in the figure.</i>'
        else:
            options = [opt_html(o) for o in e['opts']]
    sol = blocks(e['sol'].split('\n'), drop_code=True)
    trap = blocks(e['trap'].split('\n'), drop_code=True)
    if gid in SOL_FIX:
        a, b = SOL_FIX[gid]; assert a in sol; sol = sol.replace(a, b)
    solution = sol + ('<br><b>Trap:</b> ' + trap if trap else '')
    q.update({'difficulty': difficulty(e, len(e['sol'])), 'marks': e['marks'], 'type': typ, 'q': qh})
    if options: q['options'] = options
    q['answer'] = answer
    q['solution'] = solution
    q['source'] = e['source']
    q['pyq'] = True
    if fig: q['figure'] = fig
    return q, None


def main():
    items, dropped, skipped = [], [], []
    for e in all_entries():
        if e['gid'] in EXCLUDE:
            skipped.append((e['gid'], EXCLUDE[e['gid']])); continue
        q, why = build(e)
        if q is None:
            dropped.append((e['gid'], e['source'], why)); continue
        items.append(q)
    # difficulty: 1-mark -> 1/2, 2-mark -> 2/3, split at the median solution length of its (marks, section) group
    import statistics
    for m in (1, 2):
        for sec in ('Verbal', 'Quant', 'Analytical', 'Spatial'):
            grp = [q for q in items if q['marks'] == m and q['section'] == sec]
            if not grp: continue
            med = statistics.median(len(q['solution']) for q in grp)
            for q in grp:
                gid = q['id'].replace('PYQ-C', '').replace('PYQ-', '')
                q['difficulty'] = DIFF_OVR.get(gid) or (m + (1 if len(q['solution']) > med else 0))
    os.makedirs(OUT_IMG, exist_ok=True)
    for n in sorted(set(used_imgs)):
        shutil.copy2(os.path.join(IMG, n), os.path.join(OUT_IMG, n))
    with open(OUT, 'w', encoding='utf-8') as f:
        for q in items:
            f.write(json.dumps(q, ensure_ascii=False) + '\n')
    print(len(items), 'items written;', len(dropped), 'dropped;', len(skipped), 'skipped (duplicates)')
    for d in dropped: print('DROPPED', d)
    return items, dropped, skipped


if __name__ == '__main__':
    main()
