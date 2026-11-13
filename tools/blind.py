#!/usr/bin/env python3
"""Blind verification helpers.

  blind.py make  [chunk=60]   -> review/blind/<PREFIX>_<k>.md   (questions WITHOUT answers/solutions)
  blind.py compare            -> review/mismatch.jsonl + summary (reads review/blind/*_answers.jsonl)

Answer files (written by solver agents), one JSON per line:
  {"id": "...", "answer": "B" | ["A","C"] | 12.5, "confidence": "high|medium|low", "issue": ""}
"""
import json, os, glob, sys, re, html

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
B = os.path.join(ROOT, 'review', 'blind')
L = 'ABCD'


def bank():
    out = []
    for f in sorted(glob.glob(os.path.join(ROOT, 'bank', '*.jsonl'))):
        for line in open(f, encoding='utf-8'):
            if line.strip(): out.append(json.loads(line))
    return out


def fig_note(p):
    """Absolute path of a viewable PNG for a figure (writers keep PNG copies in review/figs)."""
    name = os.path.splitext(os.path.basename(p))[0]
    for c in (os.path.join(ROOT, 'review', 'figs', name + '.png'), os.path.join(ROOT, 'site', p)):
        if os.path.exists(c) and c.endswith('.png'): return c
    return os.path.join(ROOT, 'site', p) + '  (SVG - if you cannot view it, say so in "issue")'


def render(q):
    s = [f'### {q["id"]}  ·  {q["section"]} · {q["topic"]} · {q["marks"]} mark · {q["type"]}', '', q['q']]
    if q.get('chart'):
        c = q['chart']
        s += ['', f'[Chart: {c.get("type")} — {c.get("title", "")}; x = {c.get("xLabel", "")}, y = {c.get("yLabel", "")}]']
        s += [f'labels: {c.get("labels")}'] + [f'series "{x.get("name", "")}": {x.get("values")}' for x in c.get('series', [])]
    if q.get('figure'): s += ['', f'[Figure: {fig_note(q["figure"])}]']
    if q['type'] in ('MCQ', 'MSQ'):
        s.append('')
        for i, o in enumerate(q['options']):
            extra = f'  [option figure: {fig_note(q["option_figures"][i])}]' if q.get('option_figures') else ''
            s.append(f'({L[i]}) {o}{extra}')
    if q['type'] == 'MSQ': s.append('\n(one or more options may be correct)')
    if q['type'] == 'NAT': s.append('\n(numerical answer)')
    return '\n'.join(s) + '\n'


def make(chunk):
    os.makedirs(B, exist_ok=True)
    by = {}
    for q in bank(): by.setdefault(q['id'].split('-')[0], []).append(q)
    files = []
    for pre, qs in sorted(by.items()):
        for k in range(0, len(qs), chunk):
            fn = os.path.join(B, f'{pre}_{k // chunk + 1}.md')
            open(fn, 'w', encoding='utf-8').write('\n---\n\n'.join(render(q) for q in qs[k:k + chunk]))
            files.append((fn, len(qs[k:k + chunk])))
    for f, n in files: print(n, f)


def norm(a, t):
    if t == 'MSQ':
        if isinstance(a, str): a = re.findall(r'[A-D]', a.upper())
        return sorted(set(x.strip().upper() for x in a)) if isinstance(a, list) else None
    if t == 'MCQ':
        return str(a).strip().upper()[:1] if a is not None else None
    try: return float(a)
    except Exception: return None


def compare():
    qs = {q['id']: q for q in bank()}
    got = {}
    for f in glob.glob(os.path.join(B, '*_answers.jsonl')):
        for line in open(f, encoding='utf-8'):
            if line.strip():
                try: r = json.loads(line)
                except Exception: continue
                got[r['id']] = r
    mism, flagged, missing = [], [], []
    for qid, q in qs.items():
        r = got.get(qid)
        if not r: missing.append(qid); continue
        t = q['type']; a = norm(r.get('answer'), t)
        if t == 'NAT':
            ok = a is not None and q['answer']['min'] - 1e-6 <= a <= q['answer']['max'] + 1e-6
        elif t == 'MSQ': ok = a == sorted(q['answer'])
        else: ok = a == q['answer']
        rec = {'id': qid, 'key': q['answer'], 'solver': r.get('answer'), 'confidence': r.get('confidence'), 'issue': r.get('issue', '')}
        if not ok: mism.append(rec)
        elif (r.get('issue') or '').strip(): flagged.append(rec)
    with open(os.path.join(ROOT, 'review', 'mismatch.jsonl'), 'w', encoding='utf-8') as f:
        for r in mism: f.write(json.dumps(dict(r, kind='mismatch'), ensure_ascii=False) + '\n')
        for r in flagged: f.write(json.dumps(dict(r, kind='flag'), ensure_ascii=False) + '\n')
    print(f'{len(qs)} questions · answered {len(qs) - len(missing)} · mismatches {len(mism)} · agreed-but-flagged {len(flagged)} · missing {len(missing)}')
    by = {}
    for r in mism: by[r['id'].split('-')[0]] = by.get(r['id'].split('-')[0], 0) + 1
    print('mismatches by file:', by)
    if missing: print('missing:', ' '.join(missing[:40]), '...' if len(missing) > 40 else '')


if __name__ == '__main__':
    cmd = sys.argv[1] if len(sys.argv) > 1 else ''
    if cmd == 'make': make(int(sys.argv[2]) if len(sys.argv) > 2 else 60)
    elif cmd == 'compare': compare()
    else: print(__doc__)
