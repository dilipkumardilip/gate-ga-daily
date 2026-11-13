#!/usr/bin/env python3
"""Validate question-bank JSONL files for the GATE GA daily-test site.

Usage:  tools/.venv/bin/python -I tools/validate.py bank/QN1.jsonl [more files...]
        tools/.venv/bin/python -I tools/validate.py --all

Checks every line for:
  * schema (fields, enums, 4 distinct options, answer format)
  * KaTeX: every $...$ / $$...$$ segment must render (node tools/katex_check.mjs)
  * figures: referenced files must exist under site/
  * verify code (when present): executed in a fresh python subprocess; the computed
    `ans` must agree with the stored answer (see BRIEF.md "verify" rules)
Prints a report; exit code 1 if any ERROR.
"""
import json, os, re, subprocess, sys, glob, collections
from fractions import Fraction

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = os.path.join(ROOT, 'site')
PY = os.path.join(ROOT, 'tools', '.venv', 'bin', 'python')
SECTIONS = {'Verbal', 'Quant', 'Analytical', 'Spatial'}
TYPES = {'MCQ', 'MSQ', 'NAT'}
LET = 'ABCD'

RUNNER = r'''
import json, sys, signal, math, itertools, fractions, collections, functools, re, string, random
def _h(*a): raise TimeoutError("verify timed out")
signal.signal(signal.SIGALRM, _h)
items = json.load(sys.stdin)
out = {}
for qid, code in items:
    ns = {"__name__": "__verify__"}
    signal.alarm(20)
    try:
        exec(code, ns)
        a = ns.get("ans", "__MISSING__")
        if isinstance(a, fractions.Fraction): a = float(a)
        if isinstance(a, (set, frozenset, tuple)): a = sorted(a)
        try:
            import numpy as _np
            if isinstance(a, _np.generic): a = a.item()
        except Exception: pass
        if not isinstance(a, (int, float, str, list)) or isinstance(a, bool): a = repr(a)
        out[qid] = {"ok": True, "ans": a}
    except BaseException as e:
        out[qid] = {"ok": False, "err": type(e).__name__ + ": " + str(e)[:200]}
    finally:
        signal.alarm(0)
print(json.dumps(out))
'''


def parse_num(s):
    """Best-effort numeric value of an option string; None if not a plain number."""
    t = s.strip()
    t = re.sub(r'<[^>]+>', '', t)
    t = t.replace('$', '').replace('\\,', '').replace(',', '').replace('₹', '').replace('Rs.', '').replace('Rs', '')
    t = t.replace('\\%', '%').replace('\\text{', '').replace('\\mathrm{', '')
    t = t.replace('−', '-').replace('\\dfrac', '\\frac').replace('\\tfrac', '\\frac').strip()
    t = re.sub(r'\s+', ' ', t)
    unit = r'(?:\s*(?:%|km/h|km/hr|kmph|m/s|km|m|cm|mm|kg|g|litres|liters|litre|L|hours|hour|hrs|hr|h|minutes|minute|min|seconds|sec|s|days|day|years|year|yrs|units|sq\.? ?cm|cm\^2|m\^2|cm\^3|m\^3|degrees|°|\^\\circ|\^\{\\circ\})\}?)?'
    m = re.fullmatch(r'(-?\d+(?:\.\d+)?)' + unit + r'\}?', t)
    if m: return float(m.group(1))
    m = re.fullmatch(r'(-?)\\frac\{(\d+)\}\{(\d+)\}' + unit, t)
    if m: return (-1 if m.group(1) else 1) * int(m.group(2)) / int(m.group(3))
    m = re.fullmatch(r'(-?\d+)\s*/\s*(\d+)' + unit, t)
    if m: return int(m.group(1)) / int(m.group(2))
    m = re.fullmatch(r'(-?\d+)\s*\\frac\{(\d+)\}\{(\d+)\}' + unit, t)   # mixed number 3\frac{1}{2}
    if m:
        w = int(m.group(1)); f = int(m.group(2)) / int(m.group(3))
        return w - f if w < 0 else w + f
    return None


def close(a, b):
    return abs(a - b) <= 1e-6 * max(1, abs(a), abs(b))


def math_segments(s):
    segs = re.findall(r'\$\$(.+?)\$\$', s, flags=re.S)
    rest = re.sub(r'\$\$(.+?)\$\$', ' ', s, flags=re.S)
    if rest.count('$') % 2:
        return segs, 'odd number of $ signs (use ₹ for money, never $)'
    segs += re.findall(r'\$(.+?)\$', rest, flags=re.S)
    return segs, None


def check_file(path, seen_ids, report):
    items = []
    with open(path, encoding='utf-8') as f:
        for n, line in enumerate(f, 1):
            line = line.strip()
            if not line: continue
            try:
                items.append((n, json.loads(line)))
            except Exception as e:
                report.append(('ERROR', f'{os.path.basename(path)}:{n}', f'bad JSON: {e}'))
    math_jobs, verify_jobs, byid = [], [], {}
    for n, q in items:
        qid = q.get('id', f'line{n}')
        where = f'{os.path.basename(path)}:{qid}'
        E = lambda msg: report.append(('ERROR', where, msg))
        W = lambda msg: report.append(('WARN', where, msg))
        if qid in seen_ids: E(f'duplicate id (also in {seen_ids[qid]})')
        seen_ids[qid] = os.path.basename(path)
        byid[qid] = q
        for k in ('id', 'section', 'topic', 'difficulty', 'marks', 'type', 'q', 'answer', 'solution', 'source'):
            if k not in q: E(f'missing field {k}')
        if q.get('section') not in SECTIONS: E(f'bad section {q.get("section")}')
        if q.get('type') not in TYPES: E(f'bad type {q.get("type")}')
        if q.get('marks') not in (1, 2): E('marks must be 1 or 2')
        if q.get('difficulty') not in (1, 2, 3): E('difficulty must be 1, 2 or 3')
        t = q.get('type')
        opts = q.get('options')
        if t in ('MCQ', 'MSQ'):
            ofig = q.get('option_figures')
            if not isinstance(opts, list) or len(opts) != 4: E('MCQ/MSQ need exactly 4 options'); opts = None
            else:
                norm = [re.sub(r'\s+', ' ', str(o)).strip().lower() for o in opts]
                if not ofig and len(set(norm)) != 4: E('options are not distinct')
                if any(not str(o).strip() for o in opts) and not ofig: E('empty option')
                for o in opts:
                    if re.search(r'all of the above|none of the above|both \(?a\)? and \(?b\)?', str(o), re.I):
                        W('avoid "all/none of the above"-style options')
            a = q.get('answer')
            if t == 'MCQ' and a not in list(LET): E('MCQ answer must be one letter A-D')
            if t == 'MSQ' and not (isinstance(a, list) and a and all(x in LET for x in a) and len(set(a)) == len(a)):
                E('MSQ answer must be a non-empty list of letters')
        elif t == 'NAT':
            a = q.get('answer')
            if not (isinstance(a, dict) and isinstance(a.get('min'), (int, float)) and isinstance(a.get('max'), (int, float)) and a['min'] <= a['max']):
                E('NAT answer must be {"min": x, "max": y}')
            if opts: E('NAT must not have options')
        for fk in ('figure',):
            if q.get(fk) and not os.path.exists(os.path.join(SITE, q[fk])): E(f'{fk} file missing: {q[fk]}')
        for p in q.get('option_figures') or []:
            if not os.path.exists(os.path.join(SITE, p)): E(f'option figure missing: {p}')
        if q.get('chart'):
            c = q['chart']
            if c.get('type') not in ('bar', 'line', 'pie', 'groupbar', 'stackbar'): E('chart.type must be bar|groupbar|stackbar|line|pie')
            labs = c.get('labels') or []
            for s in c.get('series') or []:
                if len(s.get('values', [])) != len(labs): E('chart series length != labels length')
        if len(str(q.get('solution', ''))) < 40: W('solution is very short')
        texts = [('q', q.get('q', '')), ('solution', q.get('solution', ''))] + [(f'opt{i}', str(o)) for i, o in enumerate(opts or [])]
        for field, s in texts:
            segs, err = math_segments(str(s))
            if err: E(f'{field}: {err}')
            for sg in segs: math_jobs.append((where, field, sg))
            if re.search(r'\\\(|\\\[', str(s)): E(f'{field}: use $..$ not \\( \\)')
        if q.get('verify'):
            verify_jobs.append((qid, q['verify']))
        elif q.get('section') == 'Quant' and q.get('source', '').startswith('Original'):
            W('Quant original without verify code')
    # KaTeX
    if math_jobs:
        p = subprocess.run(['node', os.path.join(ROOT, 'tools', 'katex_check.mjs')], input=json.dumps([j[2] for j in math_jobs]),
                           capture_output=True, text=True, cwd=os.path.join(ROOT, 'tools'))
        if p.returncode != 0:
            report.append(('ERROR', os.path.basename(path), 'katex checker failed: ' + p.stderr[:300]))
        else:
            for i, err in json.loads(p.stdout):
                report.append(('ERROR', math_jobs[i][0], f'KaTeX error in {math_jobs[i][1]}: {err[:150]}  [{math_jobs[i][2][:60]}]'))
    # verify code
    if verify_jobs:
        p = subprocess.run([PY, '-I', '-c', RUNNER], input=json.dumps(verify_jobs), capture_output=True, text=True, timeout=1800)
        if p.returncode != 0:
            report.append(('ERROR', os.path.basename(path), 'verify runner crashed: ' + p.stderr[-400:]))
            return len(items)
        res = json.loads(p.stdout)
        for qid, r in res.items():
            q = byid[qid]; where = f'{os.path.basename(path)}:{qid}'
            if not r['ok']:
                report.append(('ERROR', where, 'verify code error: ' + r['err'])); continue
            got, t, a = r['ans'], q.get('type'), q.get('answer')
            msg = verdict(got, t, a, q.get('options') or [])
            if msg: report.append(('ERROR', where, msg))
    return len(items)


def verdict(got, t, a, opts):
    if got == '__MISSING__': return 'verify code did not set ans'
    if t == 'MCQ':
        if isinstance(got, str) and got.strip().upper() in LET:
            return None if got.strip().upper() == a else f'verify says {got}, answer is {a}'
        try: g = float(Fraction(got)) if isinstance(got, str) else float(got)
        except Exception: return f'verify returned {got!r}: neither a letter nor a number'
        vals = [parse_num(str(o)) for o in opts]
        if any(v is None for v in vals):
            return f'verify returned a number ({g}) but options are not all plain numbers - return the letter instead'
        hits = [LET[i] for i, v in enumerate(vals) if close(v, g)]
        if len(hits) != 1: return f'verify value {g} matches options {hits} (need exactly one)'
        if len(set(round(v, 9) for v in vals)) != 4: return 'two options have the same numeric value'
        return None if hits[0] == a else f'verify value {g} is option {hits[0]}, answer is {a}'
    if t == 'MSQ':
        g = sorted(x.strip().upper() for x in got) if isinstance(got, list) else None
        return None if g == sorted(a) else f'verify says {got}, answer is {a}'
    if t == 'NAT':
        try: g = float(got)
        except Exception: return f'verify returned {got!r}, not a number'
        return None if a['min'] - 1e-9 <= g <= a['max'] + 1e-9 else f'verify value {g} outside [{a["min"]}, {a["max"]}]'
    return None


def main():
    args = sys.argv[1:]
    files = sorted(glob.glob(os.path.join(ROOT, 'bank', '*.jsonl'))) if args == ['--all'] or not args else args
    report, seen, total = [], {}, 0
    for f in files:
        total += check_file(f, seen, report)
    errs = [r for r in report if r[0] == 'ERROR']
    for r in report: print(f'{r[0]:5} {r[1]}  {r[2]}')
    # answer-letter balance + mix summary
    stats = collections.Counter(); mix = collections.Counter()
    for f in files:
        for line in open(f, encoding='utf-8'):
            if not line.strip(): continue
            try: q = json.loads(line)
            except Exception: continue
            if q.get('type') == 'MCQ': stats[q.get('answer')] += 1
            mix[(q.get('type'), q.get('marks'), q.get('difficulty'))] += 1
    print(f'\n{total} questions in {len(files)} file(s); {len(errs)} error(s), {len(report) - len(errs)} warning(s)')
    print('MCQ answer letters:', dict(sorted(stats.items())))
    print('type/marks/difficulty mix:', dict(sorted(mix.items(), key=str)))
    sys.exit(1 if errs else 0)


if __name__ == '__main__':
    main()
